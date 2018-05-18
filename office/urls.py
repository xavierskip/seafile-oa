from seahub.urls import *
from office.views import *
from django.conf.urls import url, patterns, include
from django.views.generic.base import TemplateView
from django.conf import settings
from office import admin


def i18n_javascript(request):
    return admin.site.i18n_javascript(request)

oa_patterns = [
    url(r'^$', home, name="officeHome"),
    url(r'^history/$', history, name="officeHistory"),
    # url(r'^page/(?:page-(?P<page>\d+)/)?$', index),
    url(r'^p/(?P<username>\S+)/$', user_index, name='user_index'),
    url(r'^distr/$', distribute_doc, {"distributed": True}, name="distribution"),
    url(r'^distred/$', distribute_doc, {"distributed": False}, name="distributed"),
    url(r'^todo/$', todo_doc, {"todo": True}, name="office_todo"),
    url(r'^done/$', todo_doc, {"todo": False}, name="office_done"),
    url(r'^doc/(?P<hashid>\w+)/$', document_page, name='office_page'),
    url(r'^search/$', search_doc, name='office_search'),
    url(r'^form/(?P<hashid>\w+)/$', print_form, name="print_form"),
    url(r'^loginjump', login_jump, name="office_jump"),
    # post
    url(r'^doc/(?P<hashid>\w+?)/assign$', distribution_document, name='office_assign'),
    url(r'^doc/(?P<hashid>\w+?)/commit$', commit_document, name='office_commit'),
    url(r'^commit/(?P<hashid>\w+?)/edit$', update_commit, name="edit_commit"),
    # ajax
    url(r'^ajax/upload_url$', get_upload_url),
    url(r'^ajax/delete_file$', delete_file),
    url(r'^ajax/issue', get_organization),
    # admin
    url(r'^admin/jsi18n', i18n_javascript),
    url(r'^admin/', include(admin.site.urls), name='officeAdmin'),
]

test_oa_patterns = [
    url(r'^meta$', display_meta, name='meta'),
    url(r'^test/$', test, name='test'),
    url(r'^index/$', TemplateView.as_view(template_name="office_index.html")),
    url(r'^paginator', test_paginator),
]

# fit: add django-debug-toolbar
if settings.DEBUG_EXT:
    import debug_toolbar
    urlpatterns += patterns(
        '',url(r'^__debug__/', include(debug_toolbar.urls)),
    )
    oa_patterns += test_oa_patterns

urlpatterns += patterns('', url(r'^oa/', include(oa_patterns)),)