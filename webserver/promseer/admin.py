from django.contrib import admin
from .models import *


# class PredictModelAdmin(admin.ModelAdmin):
# 	list_display = ('id', 'metric', 'labels', 'created_t', 'last_modified_t')


# Register your models here.
admin.site.register(Label)
admin.site.register(PredictModel)
admin.site.register(PredictTarget)
admin.site.register(RegisterMetric)
