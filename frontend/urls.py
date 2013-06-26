from django.conf.urls import patterns, include, url

from frontend import views

urlpatterns = patterns('',
    #EDID
    url(r'^edid/upload/$', views.EDIDUpload.as_view(), name='edid-upload'),
    url(r'^edid/(?P<pk>\d+)/$', views.EDIDDetailView.as_view(), name='edid-detail'),
    url(r'^edid/(?P<pk>\d+)/update/$', views.EDIDUpdate.as_view(), name='edid-update'),

    #Index
    url(r'^$', views.EDIDList.as_view(), name='index'),
   )
