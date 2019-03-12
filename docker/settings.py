DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': 'database',
        'NAME': 'edidtv',
        'USER': 'edidtv',
        'PASSWORD': 'edidtv',
    }
}

EMAIL_HOST = 'smtpd'
DEFAULT_FROM_EMAIL = 'noreply@edid.tv'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# SECRET_KEY = ''
# EDID_GRABBER_RELEASE_UPLOAD_API_KEY = ''
# ADMINS = (
# )
# MANAGERS = ADMINS
