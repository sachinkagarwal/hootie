from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from . import apiviews
urlpatterns = [
        url(r'^rootpaths/$',apiviews.RootPathList.as_view()),
        url(r'^volumes/$', apiviews.VolumeList.as_view()),
        url(r'^volumes/(?P<id>[0-9]+)/$', apiviews.VolumeDetail.as_view())
        ]

