from django.conf.urls import patterns, include, url
from rest_framework import routers

from genewiki.mapping.views import RelationshipViewSet

router = routers.DefaultRouter()
router.register(r'', RelationshipViewSet)

urlpatterns = patterns('genewiki.mapping.views',
    # REST Framework
    url(r'', include(router.urls)),
    url(r'^wiki/(?P<entrez_id>\d+)/$', r'wiki_mapping'),
)
