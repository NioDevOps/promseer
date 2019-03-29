import base64
import pickle


def metric_encoder(m):
	if isinstance(m, dict):
		return base64.b64encode(str(sorted(m.items())).encode('utf-8')).decode()


def dump_obj(obj):
	return pickle.dumps(obj)


def load_obj(obj_str):
	return pickle.loads(obj_str)