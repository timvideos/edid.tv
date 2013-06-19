from django.conf.urls import patterns, include, url

from frontend import views

urlpatterns = patterns('',
    url(r'^edid/(?P<edid_id>\d+)/edit/$', views.edit_edid, name='edit_edid'),
    url(r'^edid/(?P<edid_id>\d+)/$', views.show_edid, name='show_edid'),
    url(r'^upload$', views.upload_edid, name='upload_edid'),
    url(r'^$', views.index, name='index'),
   )
