from django.conf.urls import patterns, include, url

from frontend import views

urlpatterns = patterns('',
    url(r'^edid/(?P<edid_id>\d+)/$', views.show_edid),
    url(r'^upload$', views.upload),
    url(r'^$', views.index),
   )
