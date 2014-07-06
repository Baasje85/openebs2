# Django settings for openebs2 project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Stefan de Konink', 'stefan@opengeo.nl'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis', # GeoDjango
        'NAME': 'openebs2',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

SITE_ID = 1

TIME_ZONE = 'Europe/Amsterdam'
LANGUAGE_CODE = 'nl-nl'

USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

STATIC_ROOT = 'static/'
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    "openebs2/static",
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'rsy&8z9#0sr4_fpf!p1omymr(!*5upr%p4k7y#d9cz@^et+u)='

LOGIN_URL = 'app_login'
LOGOUT_URL = 'app_logout'
LOGIN_REDIRECT_URL = 'msg_index' # This is temporary

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'openebs2.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'openebs2.wsgi.application'

TEMPLATE_DIRS = (
    "openebs2/templates",
)

INSTALLED_APPS = (
    # Django pieces
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',

    # Our apps
    # Order matters for testing: openebs depends on kv1 not viceversa
    'kv1', # Static data stuff
    'openebs',
    'reports',
    'bigdata',
    'utils', # Load our custom filters

    # Libs
    'south',
    'json_field',
    'floppyforms',
    'crispy_forms',
    'leaflet',

    # Admin & tools
    'django_admin_bootstrapped',
    'django.contrib.admin',
)

# Logging so far
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'logfile': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': "/tmp/openebs.log",
            'maxBytes': 5000000,
            'backupCount': 5,
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'openebs': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propogate' : True
        },
    }
}

# Django Leaflet
LEAFLET_CONFIG = {
    'TILES': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    'RESET_VIEW': False
}

# Crispy = form addon
CRISPY_TEMPLATE_PACK = 'bootstrap3'
CRISPY_FAIL_SILENTLY = not DEBUG

# Verification feed settings
GOVI_VERIFY_FEED = 'tcp://192.168.33.1:8001' #'tcp://node02.kv7.openov.nl:7817'
GOVI_VERIFY_SUB =  "/InTraffic/KV8gen"

# Reporting
KV6_FEED = 'tcp://localhost:7658'

# Push settings
try:
    from settings_push import *
except ImportError:
    PUSH_SETTINGS = False

try:
    from local_settings import *
except ImportError:
    pass
