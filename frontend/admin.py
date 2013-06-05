from django.contrib import admin
from frontend.models import EDID

class EDIDAdmin(admin.ModelAdmin):
    pass

admin.site.register(EDID, EDIDAdmin)

