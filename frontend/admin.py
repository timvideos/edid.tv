# W0142: Used * or ** magic
# pylint: disable-msg=W0142

from django.contrib import admin

import reversion

from frontend.models import (Manufacturer, EDID, StandardTiming,
                             DetailedTiming, Comment)


class ManufacturerAdmin(admin.ModelAdmin):
    pass

admin.site.register(Manufacturer, ManufacturerAdmin)


class StandardTimingInline(admin.TabularInline):
    model = StandardTiming
    fields = ['identification']


class DetailedTimingInline(admin.TabularInline):
    model = DetailedTiming
    fields = ['identification']


class EDIDAdmin(reversion.VersionAdmin):
    fields = ['manufacturer', 'status']
    inlines = [
        StandardTimingInline,
        DetailedTimingInline,
    ]

    def queryset(self, request):
        """
        Override default manager to list all EDID objects.
        """

        qs = EDID.all_objects.all()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

admin.site.register(EDID, EDIDAdmin)


class CommentAdmin(admin.ModelAdmin):
    fields = ['user', 'parent', 'level', 'content']
    list_display = ('EDID', 'user', 'content')
    list_display_links = ('content',)
    list_filter = ('user',)


admin.site.register(Comment, CommentAdmin)
