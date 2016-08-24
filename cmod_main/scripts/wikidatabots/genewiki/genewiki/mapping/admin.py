from django.contrib import admin

from genewiki.mapping.models import Relationship, Lookup

admin.site.register(Relationship)
admin.site.register(Lookup)
