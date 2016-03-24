from api.views.filter_preset_view import FilterPresetView
from api.views.json_view import JSONView
from api.views.filter_view import FilterView

from django.conf.urls import include, url, patterns
from django.views.decorators.cache import cache_page

__author__ = 'Lene Preuss <lp@sinnwerkstatt.com>'

CACHE_TIMEOUT = 24*3600

urlpatterns = patterns('')

urlpatterns.extend([
    url(r'^filter.json', FilterView.as_view(), name='landmatrix_api'),
    url(r'^filter_preset.json', FilterPresetView.as_view(), name='landmatrix_api'),
url(r'^(?P<type>.*\.json)', cache_page(CACHE_TIMEOUT)(JSONView.as_view()), name='landmatrix_api'),
    # url(r'^(?P<type>.*\.json)', JSONView.as_view(), name='landmatrix_api'),
])

