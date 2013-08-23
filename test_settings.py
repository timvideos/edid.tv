# Django settings for testing.
# pylint: disable-msg=C0103

from settings import *

TEST_RUNNER = "discover_runner.DiscoverRunner"
TEST_DISCOVER_TOP_LEVEL = SITE_ROOT
TEST_DISCOVER_PATTERN = "test_*"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2',
                                                 # 'mysql', 'sqlite3' or
                                                 # 'oracle'.
        'NAME': ':memory:',     # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',             # Empty for localhost through domain sockets
                                # or '127.0.0.1' for localhost through TCP.
        'PORT': '',             # Set to empty string for default.
    }
}
