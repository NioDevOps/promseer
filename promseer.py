from gevent import monkey
monkey.patch_all()

from gevent.pywsgi import WSGIServer
from webserver.wsgi import application


HOST = '0.0.0.0'
PORT = 8000

WSGIServer((HOST, PORT), application).serve_forever()
