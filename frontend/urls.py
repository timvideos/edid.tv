from django.conf.urls import patterns, include, url

from frontend import views

urlpatterns = patterns('',
    #EDID
    url(r'^edid/upload/$', views.EDIDUpload.as_view(), name='edid-upload'),
    url(r'^edid/(?P<pk>\d+)/$', views.EDIDDetailView.as_view(),
        name='edid-detail'),
    url(r'^edid/(?P<pk>\d+)/update/$', views.EDIDUpdate.as_view(),
        name='edid-update'),

    #Standard Timing
    url(r'^edid/(?P<edid_pk>\d+)/standard_timing/new/$',
        views.StandardTimingCreate.as_view(), name='standard-timing-create'),
    url(r'^edid/(?P<edid_pk>\d+)/standard_timing/(?P<identification>\d+)/'
        r'update/$', views.StandardTimingUpdate.as_view(),
        name='standard-timing-update'),
    url(r'^edid/(?P<edid_pk>\d+)/standard_timing/(?P<identification>\d+)/'
        r'delete/$', views.StandardTimingDelete.as_view(),
        name='standard-timing-delete'),
    url(r'^edid/(?P<edid_pk>\d+)/standard_timing/(?P<identification>\d+)/'
        r'move_(?P<direction>up|down)/$',
        views.StandardTimingReorder.as_view(), name='standard-timing-reorder'),

    #Detailed Timing
    url(r'^edid/(?P<edid_pk>\d+)/detailed_timing/new/$',
        views.DetailedTimingCreate.as_view(), name='detailed-timing-create'),
    url(r'^edid/(?P<edid_pk>\d+)/detailed_timing/(?P<identification>\d+)/'
        r'update/$', views.DetailedTimingUpdate.as_view(),
        name='detailed-timing-update'),
    url(r'^edid/(?P<edid_pk>\d+)/detailed_timing/(?P<identification>\d+)/'
        r'delete/$', views.DetailedTimingDelete.as_view(),
        name='detailed-timing-delete'),
    url(r'^edid/(?P<edid_pk>\d+)/detailed_timing/(?P<identification>\d+)/'
        r'move_(?P<direction>up|down)/$',
        views.DetailedTimingReorder.as_view(), name='detailed-timing-reorder'),

    #Index
    url(r'^$', views.EDIDList.as_view(), name='index'),
   )
