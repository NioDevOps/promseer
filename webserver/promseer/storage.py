from multiprocessing import Lock
from django.core.cache import cache
# MEM_STORAGE = {}
TASK_STATUS_STORAGE = {}

L = Lock()


def atom_increase_counter(sm):
	with L:
		sm.value += 1


def list_task_result():
	return [
				{
					'task_id': x[0],
					'ready': x[1]['ready'].value,
					'total': x[1]['total'],
					'percent': x[1]['ready'].value * 100 / x[1]['total'],
					't':x[1]['t']
				} for x in TASK_STATUS_STORAGE.items()
	]


def store_task(uid, t, counter, total):
	TASK_STATUS_STORAGE[uid] = {'ready': counter, 'total': total, 't': t}


def get_task_result(uid):
	if uid not in TASK_STATUS_STORAGE:
		raise KeyError('no such task is running %r' % uid)
	return TASK_STATUS_STORAGE[uid].get('ready'), TASK_STATUS_STORAGE[uid].get('total')


def finish_task(uid):
	del TASK_STATUS_STORAGE[uid]


def read(k):
	cache.get('mem_storage_%s' % k)

def read_all():
	return [cache.get(x) for x in cache.keys('mem_storage_*')]

def write(k, v):
	if cache.has_key('mem_storage_%s' % k):
		cache_value = cache.get(k)
		cache_value['model'] = v
		cache.set(k, cache_value, timeout=None)
	else:
		cache.set('mem_storage_%s' % k, {'data': None, 'model': v}, timeout=None)


def write_data(k, v, data):
	if cache.has_key('mem_storage_%s' % k):
		cache_value = cache.get('mem_storage_%s' % k)
		cache_value['data'] = data
		cache.set('mem_storage_%s' % k, cache_value, timeout=None)
	else:
		cache.set('mem_storage_%s' % k, {'data': data, 'model': v}, timeout=None)
		#raise KeyError("no such predict target")


def delete(k):
	cache.delete_pattern('mem_storage_%s' % k)
