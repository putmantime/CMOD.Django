from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^map/', include('genewiki.mapping.urls')),
    url(r'^wiki/', include('genewiki.wiki.urls')),
    url(r'^report/', include('genewiki.report.urls')),

    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

