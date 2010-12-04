from django.conf.urls.defaults import *
from output_validator.models import ValidationFailure

info_dict = {
    'queryset': ValidationFailure.objects.all(),
}

urlpatterns = patterns('',
    url(r'^$',
        'django.views.generic.list_detail.object_list',
        dict(info_dict, allow_empty=True),
        name='output_validator.list'),
    url(r'^(?P<object_id>\d+)/$',
        'django.views.generic.list_detail.object_detail',
        info_dict,
        name='output_validator.detail'),
    url(r'^(?P<pk>\d+)/delete/$',
        'output_validator.views.delete',
        name='output_validator.delete'),
    url(r'^delete/$',
        'output_validator.views.bulkdelete',
        name='output_validator.bulkdelete'),
)
