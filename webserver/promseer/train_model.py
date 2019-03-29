from django.db import models
from django.conf import settings
from pytz import timezone
from prometheus_client import CollectorRegistry, Gauge, write_to_textfile
import webserver.promseer.storage as storage
from datetime import datetime, timedelta
import logging
import os.path
import time

TMP_FILE = '/tmp/promseer.txt'


def train_from_storage():
	for x in storage.read_all():
		x['model'].predict()


def generate_prometheus_exporter_from_storage():
	registry = CollectorRegistry()
	common_p_metric = ['yhat', 'yhat_lower', 'yhat_upper']
	t_gap = timedelta(minutes=3)
	# cst_tz = timezone('Asia/Shanghai')
	# tn = datetime.now().replace(tzinfo=cst_tz)
	tn = datetime.now()
	stn_str = (tn-t_gap).strftime('%Y-%m-%d %H:%M')
	etn_str = (tn+t_gap).strftime('%Y-%m-%d %H:%M')
	g_map = {}
	if not os.path.exists(TMP_FILE) or time.time() - os.path.getmtime(TMP_FILE) > (4 * 60):
		for x in storage.read_all():
			nearest_index = x['data'].index.get_loc(tn, method='nearest')
			if nearest_index >= (len(x['data'])-1):
				continue
			# print(len(x['data'].to_csv(index=True)))
			for pm in common_p_metric:
				#metric = "%s_%s_%d" % (pm, x['model'].register_metric.name, x['model'].pk)
				metric = "%s_%s" % (pm, x['model'].register_metric.name)
				if metric not in g_map:
					g_map[metric] = Gauge(
						name=metric,
						documentation=metric,
						labelnames=list([y.k for y in x['model'].labels.all()]),
						# labelvalues=list([y.v for y in x['model'].labels.all()]),
						registry=registry
					)

				print(str(x['model'].labels.all()))
				try:
					g_map[metric].labels(**({y.k: y.v for y in x['model'].labels.all()})).set(x['data'].iloc[[nearest_index]][pm])
				except ValueError as e:
					logging.error("[pt:%d]wrong label: %s" % (x['model'].pk, str(e)))

		write_to_textfile(TMP_FILE, registry)
	with open(TMP_FILE, 'r') as fd:
		return fd.read()


