from django.conf.urls import patterns, url

urlpatterns = patterns('genewiki.wiki.views',
    url(r'^article/create/(?P<entrez_id>\d+)/$', r'article_create'),
)
