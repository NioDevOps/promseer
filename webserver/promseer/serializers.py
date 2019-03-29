from django.contrib.auth.models import User, Group
from .models import *
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = User
		fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = Group
		fields = ('url', 'name')


class LabelSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = Label
		fields = ('k', 'v')


class PredictTargetSerializer(serializers.ModelSerializer):
	labels = LabelSerializer(many=True,read_only=True)

	class Meta:
		model = PredictTarget
		fields = ('id', 'url', 'created_t', 'last_modified_t', 'register_metric', 'labels')


class RegisterMetricSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = RegisterMetric
		fields = (
			'id',
			'metric',
			'name',
			'train_period',
			'predict_period',
			'min_v',
			'max_v',
			'daily_seasonality',
			'weekly_seasonality',
			'created_t',
			'last_modified_t',
			'train_status',
			'task_id',
			'url',
			'cron',
		)


