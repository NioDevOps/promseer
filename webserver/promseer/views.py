from django.contrib.auth.models import User, Group
from .models import *
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from webserver.promseer.serializers import *
import webserver.promseer.train_model
from django.http import HttpResponse, JsonResponse, FileResponse
import uuid
from webserver.promseer.storage import get_task_result, list_task_result


class UserViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	queryset = User.objects.all().order_by('-date_joined')
	serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows groups to be viewed or edited.
	"""
	queryset = Group.objects.all()
	serializer_class = GroupSerializer


class PredictTargetViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows groups to be viewed or edited.
	"""
	queryset = PredictTarget.objects.all()
	serializer_class = PredictTargetSerializer
	# filter_backends = (filters.SearchFilter,)
	# search_fields = ('labels')

	def get_queryset(self):
		queryset = PredictTarget.objects.all()
		search = self.request.query_params.get('search', None)
		if search is not None or search == "":
			queryset = queryset.filter(labels__v__contains=search).distinct()
		return queryset

	@action(methods=['get'], detail=True)
	def get_pic(self, request, *args, **kwargs):
		rm = self.get_object()
		fd = rm.get_img_fd()
		return FileResponse(fd, content_type='image/png')

	@action(methods=['get'], detail=True)
	def predict(self, request, *args, **kwargs):
		rm = self.get_object()
		rm.initial()
		rm.predict(img=False)
		return Response({'success': True})


class RegisterMetricViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows groups to be viewed or edited.
	"""
	queryset = RegisterMetric.objects.all()
	serializer_class = RegisterMetricSerializer

	@action(methods=['get'], detail=True)
	def train(self, request, *args, **kwargs):
		rm = self.get_object()
		rm.train()
		return Response({'success': True})

	@action(methods=['get'], detail=True)
	def train_background(self, request, *args, **kwargs):
		rm = self.get_object()
		task_id = rm.train(background=True)
		return Response({'success': True, 'task_id': task_id})

	@action(methods=['get'], detail=True)
	def predict(self, request, *args, **kwargs):
		rm = self.get_object()
		rm.predict()
		return Response({'success': True})

	@action(methods=['get'], detail=True)
	def predict_background(self, request, *args, **kwargs):
		rm = self.get_object()
		task_id = rm.predict(background=True)
		return Response({'success': True, 'task_id': task_id})

	# @action(methods=['get'], detail=True)
	# def background(self, request, *args, **kwargs):
	# 	task_id = request.query_params['task_id']
	# 	now = None
	# 	if task_id in bg_id:
	# 		counter = bg_id[task_id]
	# 		now = counter.value
	# 	return Response({'success': True, 'now': now})


def background(request):
	task_id = request.GET.get('task_id')
	if task_id is None:
		return JsonResponse({'results': RegisterMetric.objects.sync_task_status()})
	ready, total = get_task_result(task_id)
	return JsonResponse({'success': True, 'ready': ready, 'total': total})


def train_storage(request):
	webserver.promseer.train_model.train_from_storage()
	return JsonResponse({'success': True})


def metrics(request):
	text = webserver.promseer.train_model.generate_prometheus_exporter_from_storage()
	return HttpResponse(text, content_type="text/plain; version=0.0.4")
