from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^main_page$', views.main_page, name='main_page'),
    url(r'^get_orgs', views.get_orgs, name='get_orgs'),
    url(r'^main_page/wd_go_edit', views.wd_go_edit, name='wd_go_edit'),
    url(r'^main_page/wd_oauth', views.wd_oauth, name='wd_oauth'),
    url(r'^main_page/wd_oauth_deauth', views.wd_oauth_deauth, name='wd_oauth_deauth'),

]
