from django.db import models
from django.conf import settings
from .libs.prometheus import PrometheusApiClient as pc
from .libs.toolkits import metric_encoder, load_obj, dump_obj
import pandas as pd
import numpy as np
from fbprophet import Prophet
import time
from datetime import timedelta
import logging
import webserver.promseer.storage as storage
from django.db import transaction
import multiprocessing
import threading
import uuid
from django.db.models.signals import pre_delete
logger = logging.getLogger("ml")
logger.setLevel(logging.DEBUG)


def lower_reform(df, mins):
	df[df < mins] = np.nan
	df = df.fillna(mins)
	return df


def upper_reform(df, maxs):
	df[df > maxs] = np.nan
	df = df.fillna(maxs)
	return df


def predict_train(d_i_m):
	i = d_i_m[0]
	d = d_i_m[1]
	max_v = d_i_m[2]
	min_v = d_i_m[3]
	daily_seasonality = d_i_m[4]
	weekly_seasonality = d_i_m[5]
	predict_period = d_i_m[6]
	ct = d_i_m[7]
	delta = timedelta(hours=8)
	# predict and train or just predict
	if len(d_i_m) == 8:
		df = pd.DataFrame(data=d['values'], columns=['ds', 'y'])
		df['ds'] = pd.to_datetime(df['ds'], unit="s") + delta
		if max_v is not None:
			df['cap'] = max_v
		if min_v is not None:
			df['floor'] = min_v
		m = Prophet(
			daily_seasonality=daily_seasonality,
			weekly_seasonality=weekly_seasonality,
			growth='logistic' if max_v and min_v else 'linear')
		m.fit(df)
	else:
		m = d_i_m[8]
	futures = m.make_future_dataframe(periods=int(predict_period * 60 / 5), freq='5MIN')
	if min_v is not None:
		futures['floor'] = min_v
	if max_v is not None:
		futures['cap'] = max_v
	forecast = m.predict(futures)
	forecast['timestamp'] = forecast['ds']
	forecast = forecast[['timestamp', 'yhat', 'yhat_lower', 'yhat_upper']]
	forecast = forecast.set_index('timestamp')
	if min_v is not None:
		forecast = lower_reform(forecast, min_v)
	if max_v is not None:
		forecast = upper_reform(forecast, max_v)
	# if max_v is not None:
	# 	forecast['cap'] = max_v
	# if min_v is not None:
	# 	forecast['floor'] = min_v
	if ct is not None:
		storage.atom_increase_counter(ct)
	return i, m, forecast


def generate_pt(metric, m, forecast, rm):
	with transaction.atomic():
		pt, _ = PredictTarget.objects.get_or_create(
			metric_encode=metric_encoder(metric),
			register_metric=rm,
		)
		for x in metric.items():
			Label.objects.get_or_create(k=x[0], v=x[1], target=pt)
	# ignore_conflicts support by django 2.2a1
	# Label.objects.bulk_create([ Label(k=x[0], v=x[1], target=pt) for x in labels.items()], ignore_conflicts=True)
	logger.debug("[pt:%r]load predict target %r" % (pt.pk, pt.metric_encode))
	pt.refresh_model(m)
	storage.delete(pt.pk)
	storage.write_data(pt.pk, pt, forecast)

# def train_and_predict(d_rm):
# 	d = d_rm[0]
# 	rm = d_rm[1]
# 	with transaction.atomic():
# 		pt, _ = PredictTarget.objects.get_or_create(
# 			metric_encode=metric_encoder(d['metric']),
# 			register_metric=rm,
# 		)
# 		for x in d['metric'].items():
# 			Label.objects.get_or_create(k=x[0], v=x[1], target=pt)
# 	# ignore_conflicts support by django 2.2a1
# 	# Label.objects.bulk_create([ Label(k=x[0], v=x[1], target=pt) for x in labels.items()], ignore_conflicts=True)
# 	logger.debug("[pt:%r]load predict target %r" % (pt.pk, pt.metric_encode))
# 	df = pd.DataFrame(data=d['values'], columns=['ds', 'y'])
# 	df['ds'] = pd.to_datetime(df['ds'], unit="s")
# 	pt.train(tsd=df)
# 	pt_pd = pt.predict()
# 	return pt.pk, pt, pt_pd

# Create your models here.


NOT_YET = 0
RUNNING = 1
SUCCESS = 2
ERROR = 3


class CommonManager(models.Manager):
	use_in_migrations = True


class RegisterMetricManager(models.Manager):
	use_in_migrations = True

	def sync_task_status(self):
		r = storage.list_task_result()
		for x in r:
			rm = super().get(task_id=x['task_id'])
			if x['ready'] == x['total']:
				rm.complete_async_train_status(SUCCESS)
				storage.finish_task(x['task_id'])
			x.pop('t')
		return r


class RegisterMetric(models.Model):
	metric = models.CharField(max_length=255, verbose_name="metric", null=False, blank=False)
	name = models.CharField(max_length=255, verbose_name="name", null=False, blank=False, unique=True)
	min_v = models.FloatField(null=True, default=None)
	max_v = models.FloatField(null=True, default=None)
	daily_seasonality = models.BooleanField(default=True)
	weekly_seasonality = models.BooleanField(default=False)
	train_period = models.IntegerField(default=24, verbose_name="hours")
	predict_period = models.IntegerField(default=24, verbose_name="hours")
	created_t = models.DateTimeField(auto_now_add=True)
	last_modified_t = models.DateTimeField(auto_now=True)
	train_status = models.IntegerField(null=False, blank=False, default=NOT_YET)
	task_id = models.CharField(max_length=255, null=True, default=None)
	cron = models.CharField(max_length=255, null=True, default=None)
	objects = RegisterMetricManager()

	def train(self, background=False):
		if self.train_status == RUNNING:
			raise BlockingIOError("training is running")
		st = time.time()
		logger.info("[rm:%r]starting train and getting ts data from prometheus" % self.pk)
		time_now = int(time.time())
		ds = pc(settings.PROMETHEUS_BASE_URL).query(self.metric, sts=time_now-self.train_period*60*60, ets=time_now)
		logger.info("[rm:%r]starting train metric" % self.pk)

		max_v = self.max_v
		min_v = self.min_v
		daily_seasonality = self.daily_seasonality
		weekly_seasonality = self.weekly_seasonality
		predict_period = self.predict_period

		def run(ct=None):
			pool = multiprocessing.Pool(processes=getattr(settings, 'TRAINNING_PROCESSORS', multiprocessing.cpu_count()))
			r = pool.map(
				predict_train,
				[(x[0], x[1], max_v, min_v, daily_seasonality, weekly_seasonality, predict_period, ct) for x in enumerate(ds)]
			)
			logger.debug("[rm:%r]finish train and predict data, start to write storage" % self.pk)
			for x in r:
				generate_pt(ds[x[0]]['metric'], x[1], x[2], self)
			logger.debug("[rm:%r]finish write storage" % self.pk)
			et = time.time()
			logger.info("[rm:%r]finish training metric in %f seconds" % (self.pk, et-st))
		if background:
			with transaction.atomic():
				task_id = uuid.uuid4().hex
				self.task_id = task_id
				self.train_status = RUNNING
				counter = multiprocessing.Manager().Value('i', 0)
				t = threading.Thread(target=run, args=(counter,))
				t.setDaemon(True)
				t.start()
				storage.store_task(task_id, t, counter, len(ds))
				self.save()
			return task_id
		else:
			run()

	def complete_async_train_status(self, status):
		self.train_status = status
		self.task_id = None
		self.save()

	def predict(self, background=False):
		st = time.time()
		logger.info("[rm:%r]starting predict" % self.pk)
		pts = PredictTarget.objects.filter(register_metric=self)
		pts_map = {pt.pk: pt for pt in pts}
		for pt in pts:
			pt.initial()
			# try:
			# 	storage.write_data(pt.pk, pt, pt.predict())
			# except Exception as e:
			# 	logger.warning("[pt:%r]failed to predict %s " % (pt.pk, str(e)) )

		max_v = self.max_v
		min_v = self.min_v
		daily_seasonality = self.daily_seasonality
		weekly_seasonality = self.weekly_seasonality
		predict_period = self.predict_period

		def run(ct=None):
			pool = multiprocessing.Pool(processes=getattr(settings, 'TRAINNING_PROCESSORS', multiprocessing.cpu_count()))
			r = pool.map(
				predict_train,
				[(pt.pk, None, max_v, min_v, daily_seasonality, weekly_seasonality, predict_period, ct, pt.model_obj) for pt in pts]
			)
			for x in r:
				pk = x[0]
				storage.write_data(pk, pts_map[pk], x[2])
			et = time.time()
			logger.info("[rm:%r]finish predicting metric in %f seconds" % (self.pk, et - st))

		if background:
			with transaction.atomic():
				task_id = uuid.uuid4().hex
				self.task_id = task_id
				self.train_status = RUNNING
				counter = multiprocessing.Manager().Value('i', 0)
				t = threading.Thread(target=run, args=(counter,))
				t.setDaemon(True)
				t.start()
				storage.store_task(task_id, t, counter, len(pts_map))
				self.save()
			return task_id
		else:
			run()


class PredictTarget(models.Model):
	register_metric = models.ForeignKey(RegisterMetric, on_delete=models.CASCADE)
	metric_encode = models.CharField(max_length=255, verbose_name="metric encode", null=True, blank=True)
	created_t = models.DateTimeField(auto_now_add=True)
	last_modified_t = models.DateTimeField(auto_now=True)
	objects = CommonManager()

	class Meta:
		unique_together = ["register_metric", "metric_encode"]
		index_together = ["register_metric", "metric_encode"]

	def train(self, tsd):
		st = time.time()
		logger.debug("[pt:%r]start training target %r" % (self.pk, self.metric_encode))
		m = Prophet(daily_seasonality=True, weekly_seasonality=True)
		m.fit(tsd)
		logger.debug("[pt:%r]finish training target %r" % (self.pk, self.metric_encode))
		logger.debug("[pt:%r]start dumping model %r" % (self.pk, self.metric_encode))
		self.refresh_model(m)
		logger.debug("[pt:%r]finish dumping model %r" % (self.pk, self.metric_encode))
		et = time.time()
		logger.debug("[pt:%r]finish training target in %f seconds" % (self.pk, et-st))

	def refresh_model(self, m):
		pm, _ = PredictModel.objects.get_or_create(target=self)
		pm.model_bin = dump_obj(m)
		pm.save()
		setattr(self, "model_obj", m)
		setattr(self, "if_init", True)

	def initial(self):
		pm,_ = PredictModel.objects.get_or_create(target=self)
		setattr(self, "model_obj", load_obj(pm.model_bin))
		setattr(self, "if_init", True)

	def predict(self, img=False):
		if not getattr(self, "if_init", False):
			raise KeyError("model has not been initialed")
		st = time.time()
		logger.debug("[pt:%r]start predict model" % self.pk)
		forecast = self.model_obj.predict(self.model_obj.make_future_dataframe(periods=int(self.register_metric.predict_period * 60 / 5), freq='5MIN'))
		if img is True:
			fig1 = self.model_obj.plot(forecast)
			fig1.savefig("/tmp/pt-%d.png" % self.pk)
		forecast['timestamp'] = forecast['ds']
		forecast = forecast[['timestamp', 'yhat', 'yhat_lower', 'yhat_upper']]
		forecast = forecast.set_index('timestamp')
		if self.register_metric.min_v is not None:
			forecast = lower_reform(forecast, self.register_metric.min_v)
		if self.register_metric.max_v is not None:
			forecast = lower_reform(forecast, self.register_metric.max_v)
		et = time.time()

		logger.debug("[pt:%r]finish predict model during %f" % (self.pk, et-st))
		return forecast

	def get_img_fd(self):
		self.initial()
		self.predict(img=True)
		return open("/tmp/pt-%d.png" % self.pk, 'rb')


def pt_redis_delete(sender, instance, **kwargs):
	storage.delete(instance.pk)

pre_delete.connect(pt_redis_delete, sender=PredictTarget)

class Label(models.Model):
	target = models.ForeignKey(PredictTarget, on_delete=models.CASCADE, related_name='labels')
	k = models.CharField(max_length=255, null=False, blank=False)
	v = models.CharField(max_length=255, null=False, blank=False)
	objects = CommonManager()

	class Meta:
		unique_together = ["target", "k", "v"]
		index_together = ["target", "k", "v"]

	def __unicode__(self):
		return '%s: %s' % (self.k, self.v)


class PredictModel(models.Model):
	created_t = models.DateTimeField(auto_now_add=True)
	last_modified_t = models.DateTimeField(auto_now=True)
	target = models.ForeignKey(PredictTarget, on_delete=models.CASCADE, related_name='predict_model')
	model_bin = models.BinaryField()
	objects = CommonManager()



import webserver.promseer.task_tracer

