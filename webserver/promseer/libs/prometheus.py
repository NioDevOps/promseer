import requests
import logging
from .toolkits import metric_encoder

STEP = 5

class PrometheusApiClient:
	def __init__(self, url):
		self.url = url

	def query(self, expression, sts, ets):
		all_set_map = {}
		batch_range = 12 * 60 * 60
		tmp_ets = sts + batch_range
		tmp_sts = sts
		if ets - sts < batch_range:
			tmp_ets = ets
			batches = 1
		else:
			batches = (ets - sts) / batch_range
		count = 1
		logging.info("start  request prometheus split by %d batches" % batches)
		while True:
			data = {
				"query": expression,
				"start": tmp_sts,
				"end": tmp_ets,
				"step": "%dm" % STEP
			}
			r = requests.get("%s/api/v1/query_range" % self.url, params=data)
			if r.status_code > 300:
				raise Exception("request error:%s" % r.text)
			if len(all_set_map) == 0:
				all_set_map = {metric_encoder(x['metric']): x for x in r.json()['data']['result']}
			else:
				for x in r.json()['data']['result']:
					tmp_encode_metric = metric_encoder(x['metric'])
					if tmp_encode_metric in all_set_map:
						all_set_map[tmp_encode_metric]['values'].extend(x['values'])
					else:
						all_set_map[tmp_encode_metric] = x
			logging.info("finish a request batch %d" % count)
			count += 1
			if ets - batch_range > tmp_ets:
				tmp_ets += (batch_range + (STEP * 60))
				tmp_sts += (batch_range + (STEP * 60))
			elif ets > tmp_ets:
				tmp_sts = tmp_ets + (STEP * 60)
				tmp_ets = ets
			else:
				break
		return list(all_set_map.values())
