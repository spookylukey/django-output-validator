from django.conf.urls.defaults import patterns, url
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView

from output_validator.models import ValidationFailure

urlpatterns = \
    patterns('',
             url(r'^$',
                 ListView.as_view(queryset=ValidationFailure.objects.all()),
                 name='output_validator.list'),
             url(r'^(?P<pk>\d+)/$',
                 DetailView.as_view(queryset=ValidationFailure.objects.all()),
                 name='output_validator.detail'),
             url(r'^(?P<object_id>\d+)/delete/$',
                 'output_validator.views.delete',
                 name='output_validator.delete'),
             url(r'^delete/$',
                 'output_validator.views.bulkdelete',
                 name='output_validator.bulkdelete'),
)
