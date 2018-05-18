from seahub.settings import *
from hashids import Hashids
import os
import pkgutil


hashids_salt = 'YOU-NEVER-KNOW'
HASHIDS = Hashids(salt=hashids_salt)


SITE_ROOT_URLCONF = 'office.urls'
# INSTALLED_APPS ADD
INSTALLED_APPS += (
    'django.contrib.admin.apps.SimpleAdminConfig',
    'django.contrib.auth',
    'office',
)
MIDDLEWARE_CLASSES += (
    'office.middleware.HashidsMiddleware',
)
TEMPLATE_CONTEXT_PROCESSORS += (
    'office.context_processors.helper',  # REDIRECT_FIELD_NAME in template
)
# overwrite seahub.settings
AUTHENTICATION_BACKENDS = (
    'office.accounts.AuthBackend',
)
WSGI_APPLICATION = 'office.wsgi.application'

DEBUG = bool(os.environ.get('WEB_DEVELOP') == 'True')

django_ext = pkgutil.find_loader('django_extensions')
debug_toolbar = pkgutil.find_loader('debug_toolbar')
DEBUG_EXT = bool(DEBUG and (django_ext and debug_toolbar))

if DEBUG_EXT:
    # for django debug_toolbar
    MIDDLEWARE_CLASSES += (
        'debug_toolbar.middleware.DebugToolbarMiddleware',  # fit: debug_toolbar
    )
    INSTALLED_APPS += (
        'debug_toolbar',
        'django_extensions',
    )
    INTERNAL_IPS = ['127.0.0.1']
    DEBUG_TOOLBAR_CONFIG = {
        'JQUERY_URL': '%soa/js/jquery.min.js' % STATIC_URL,
    }
    TEMPLATE_CONTEXT_PROCESSORS += (
        'office.context_processors.test_helper',
    )