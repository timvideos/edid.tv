from django.conf.urls import patterns, include, url

from frontend import feeds, views

urlpatterns = patterns('',
    # Manufacturer
    url(r'^manufacturer/$', views.ManufacturerList.as_view(),
        name='manufacturer-list'),
    url(r'^manufacturer/(?P<pk>\d+)/$', views.ManufacturerDetail.as_view(),
        name='manufacturer-detail'),

    # EDID
    url(r'^edid/upload/$', views.EDIDUpload.as_view(), name='edid-upload'),
    url(r'^edid/(?P<pk>\d+)/$', views.EDIDDetailView.as_view(),
        name='edid-detail'),
    url(r'^edid/(?P<pk>\d+)/update/$', views.EDIDUpdate.as_view(),
        name='edid-update'),

    # EDID Revisions
    url(r'^edid/(?P<edid_pk>\d+)/revision/$', views.EDIDRevisionList.as_view(),
        name='edid-revision-list'),
    url(r'^edid/(?P<edid_pk>\d+)/revision/(?P<revision_pk>\d+)/$',
        views.EDIDRevisionDetail.as_view(), name='edid-revision-detail'),
    url(r'^edid/(?P<edid_pk>\d+)/revision/(?P<revision_pk>\d+)/revert/$',
        views.EDIDRevisionRevert.as_view(), name='edid-revision-revert'),

    # Standard Timing
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

    # Detailed Timing
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

    # Comment
    url(r'^edid/(?P<edid_pk>\d+)/comment/new/$',
        views.CommentCreate.as_view(), name='comment-create'),

    # Feeds
    url(r'^feed/uploaded/$', feeds.UploadedEDIDsFeed(), name='uploaded-feed'),
    url(r'^feed/updated/$', feeds.UpdatedEDIDsFeed(), name='updated-feed'),

    # django-allauth
    (r'^accounts/', include('allauth.urls')),

    # User Profile
    url(r'^accounts/profile/$', views.ProfileView.as_view(), name='profile'),

    # Index
    url(r'^$', views.EDIDList.as_view(), name='index'),
)
