from .models import RegisterMetric, SUCCESS, ERROR, RUNNING, NOT_YET
import threading
import time
import logging
from kits.cron import crontab
from .storage import list_task_result, finish_task
INTERVAL = 1


def task_tracer():
	for task in list_task_result():
		task_id = task['task_id']
		t = task['t']
		total = task['total']
		ready = task['ready']
		if t.is_alive():
			continue
		#success
		else:
			rm = RegisterMetric.objects.get(task_id=task_id)
			if rm.train_status == RUNNING:
				rm.train_status = SUCCESS if total == ready else ERROR
				rm.save()
			finish_task(task_id)


def task_tracer_loop():
	logging.info("[task-tracer]start tracing")
	while True:
		try:
			task_tracer()
			time.sleep(INTERVAL)
		except KeyboardInterrupt:
			break
	logging.info("[task-tracer]exit")


def task_cronjob():
	logging.info("[task-cronjob] start")
	while True:
		try:
			rms = RegisterMetric.objects.all()
			for rm in rms:
				if rm.cron:
					c = crontab(rm.cron)
					if c.is_due_now():
						# rm.train()
						rm.predict(background=True)
			# sleep 到下一分钟
			time.sleep(60 - int(time.time() % 60))
		except KeyboardInterrupt:
			break
	logging.info("[task-cronjob] exit")


def reset_train_status():
	rms = RegisterMetric.objects.all()
	for rm in rms:
		if rm.train_status in [RUNNING, SUCCESS]:
			rm.train_status = NOT_YET
			rm.save()

reset_train_status()
t = threading.Thread(target=task_tracer_loop)
t.setDaemon(True)
t.start()

t2 = threading.Thread(target=task_cronjob)
t2.setDaemon(True)
t2.start()
