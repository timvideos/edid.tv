from django.contrib import admin
from frontend.models import EDID

class EDIDAdmin(admin.ModelAdmin):
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
