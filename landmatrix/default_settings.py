"""
Django settings for landmatrix project.

Generated by 'django-admin startproject' using Django 1.8.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from django.utils.translation import ugettext_lazy as _

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FRONTENDDEV = False

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '#kzlezlh%t2o$c(^y=k^w@x3+jua*r8w2i)45xb(8ezpw_tdan'

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages'
)

if FRONTENDDEV:
    # Needs to be added in this order.
    INSTALLED_APPS += (
        'django_gulp',
        'livereload'
    )

# Rest of the pack

INSTALLED_APPS += (
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.postgres',
    'django.contrib.admin',
    'django.contrib.sites',

    # OL3 widgets must come before GIS
    'ol3_widgets',
    'django.contrib.gis',
    #'django_hstore',

    'tastypie',

    #'debug_toolbar',
    #'template_timings_panel',

    # wagtail and dependencies
    'wagtail.wagtailforms',
    'wagtail.wagtailredirects',
    'wagtail.wagtailembeds',
    'wagtail.wagtailsites',
    'wagtail.wagtailusers',
    'wagtail.wagtailsnippets',
    'wagtail.wagtaildocs',
    'wagtail.wagtailimages',
    'wagtail.wagtailsearch',
    'wagtail.wagtailadmin',
    'wagtail.wagtailcore',
    'blog',

    'modelcluster',
    'compressor',
    'taggit',

    'sass_processor',
    'sekizai',

    'bootstrap3_datetime',

    'treebeard',

    'jstemplate',

    #'simple_history',
    'django_extensions',
    'crispy_forms',
    'wkhtmltopdf',
    'threadedcomments',
    'django_comments',
    'captcha',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_gis',
    'rest_framework_docs',
    'rest_framework_swagger',
    'django.contrib.syndication',
    'file_resubmit',

#   apps of the actual landmatrix project
    'landmatrix',
    'grid',
    'map',
    'charts',
    'editor',
    'wagtail_modeltranslation',
    'wagtailcms',
    'api',
    'notifications',
    'public_comments',
    'feeds',
    'impersonate',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',

    # populate the history user automatically
    'simple_history.middleware.HistoryRequestMiddleware',

    'django.middleware.locale.LocaleMiddleware',
    # 'django.middleware.doc.XViewMiddleware',
    #'cms.middleware.user.CurrentUserMiddleware',
    #'cms.middleware.page.CurrentPageMiddleware',
    #'cms.middleware.toolbar.ToolbarMiddleware',
    #'cms.middleware.language.LanguageCookieMiddleware'

    # wagtail and dependencies
    'wagtail.wagtailcore.middleware.SiteMiddleware',
    'wagtail.wagtailredirects.middleware.RedirectMiddleware',
    'impersonate.middleware.ImpersonateMiddleware',
)

if FRONTENDDEV:
    MIDDLEWARE_CLASSES += 'livereload.middleware.LiveReloadScript',

ROOT_URLCONF = 'landmatrix.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.contrib.auth.context_processors.auth',
                'django.core.context_processors.i18n',
                'django.core.context_processors.media',
                'django.core.context_processors.static',
                'django.core.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'sekizai.context_processors.sekizai',
                'wagtailcms.context_processors.add_root_page',
                'wagtailcms.context_processors.add_data_source_dir',
            ],
        },
    },
]

WSGI_APPLICATION = 'landmatrix.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', _('English')),
    ('es', _('Español')),
    ('fr', _('Français')),
]

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = '/static/'

SASS_PATH = os.path.join(BASE_DIR, 'static/css'),
#print(SASS_PATH)
# SASS include paths
#SASS_PROCESSOR_INCLUDE_DIRS = (
#    SASS_PATH,
#    os.path.join(PROJECT_PATH, 'node_modules'),
#)

#STATICFILES_DIRS = (
#    os.path.join(BASE_DIR, "landmatrix", "static", "vendor"),
#)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
    'sass_processor.finders.CssFinder'
)

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

#
# tastypie
#
API_LIMIT_PER_PAGE = 100

#
# django-cms stuff
#
SITE_ID = 1

CMS_TEMPLATES = (
    ('1-column.html', '1 column'),
    ('start.html', 'Start'),
    ('base-gettheidea.html', 'Get the idea'),
    ('base-map.html', 'Map'),
)

# CMS Editor (ckeditor)

CKEDITOR_SETTINGS = {
    'toolbar': 'CMS',
    'skin': 'moono',
    'stylesSet': [
        {'name': 'Panel', 'element': 'div', 'class': 'panel-lm'}
    ]
}

# enable persistent database connections
# (https://docs.djangoproject.com/en/1.9/ref/databases/#persistent-database-connections)
CONN_MAX_AGE = 0

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    "file_resubmit": {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        "LOCATION": '/tmp/file_resubmit/'
    },
}

COMMENTS_APP = 'public_comments'

WAGTAIL_SITE_NAME = 'Land Matrix'

# Limit all uploads to 20MB, and data sources to 1MB
MAX_UPLOAD_SIZE = 20971520
DATA_SOURCE_MAX_UPLOAD_SIZE = 10485760
DATA_SOURCE_DIR = 'uploads'  # appended to MEDIA_ROOT/MEDIA_URL

# Recaptcha spam protection for comments
# Replace these with real keys and don't commit them
RECAPTCHA_PUBLIC_KEY = '6LfmBB8TAAAAAPntejlNyxcW86R7uBUFH_yAyofS'
RECAPTCHA_PRIVATE_KEY = '6LfmBB8TAAAAAGksxrVZdp7xIBLb6rNlOL6cocPK'
NOCAPTCHA = True
RECAPTCHA_USE_SSL = True

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    )
}

LOGIN_REDIRECT_URL = '/editor/'
IMPERSONATE_REQUIRE_SUPERUSER = True
IMPERSONATE_ALLOW_SUPERUSER = True

TWITTER_TIMELINE = {
    'consumer_key': 'lDSsFwPuVqIvWNTVqYrkPgqVx',
    'consumer_secret': 'zUXtLPCCyV6E1uskfNAOUDqLSeqeNY5ZQDtIHxaq1ZNCdj1YEv',
    'access_token': '182320767-qDBHP42oBPyiLFPtP1IDQHiGhFLUu5eTofcTLfRW',
    'access_token_secret': '5VJCSXUmuenivcm6Z1r23Na1TOwnQkRbcNws9LBg13nN7'
}

ELASTICSEARCH_URL = 'http://localhost:9200/'
ELASTICSEARCH_INDEX_NAME = 'landmatrix'

# CELERY SETTINGS
BROKER_URL = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'template_timings_panel.panels.TemplateTimings.TemplateTimings',
]

BLOG_LIMIT_AUTHOR_CHOICES_GROUP = 'CMS News'