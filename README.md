[![Build Status](https://travis-ci.org/timsvideo/edid.tv.png?branch=master)](https://travis-ci.org/timsvideo/edid.tv)

EDID.tv
===============

Extended display identification data (EDID) is a data structure provided by a digital display to describe its capabilities to a video source (eg. graphics card or set-top box). It is what enables a modern personal computer to know what kinds of monitors are connected to it. Despite EDID information being important in telling the computer how the display works, many devices ship with bad or misleading EDID information.

This website lists monitors EDID information, allows users to browse, search and update them. It supports uploading binary EDID files to add new monitors.

Changes are stored in revisions to track malicious changes, only staff can revert revisions.

EDID files are parsed by EDID Parser. EDID Grabber collects EDID files from operating system and uploads them to this website.


Installation Instructions
---

1. Clone this repository.
2. `make install`
3. `make serve`
  * You may need to import `frontend/sql/manufacturer.sql` manually if it failed.

Running Tests
---

* `make clitest` for unittests.
* `make firefoxtest` for Firefox integration tests.

Production Deployment
---

Currently deploying using [nginx](http://nginx.org) and [uwsgi](https://github.com/unbit/uwsgi/). Debian 7 includes uwsgi with [Emperor mode](http://uwsgi-docs.readthedocs.org/en/latest/Emperor.html) which makes deploying apps as easy as deploying sites on nginx.

nginx and uwsgi configuration files: https://gist.github.com/sewar/6182820

In your `local_settings.py` make sure to set these settings:

* `DEBUG` and `TEMPLATE_DEBUG` to `False`.
* `ADMINS` and `MANAGERS` for receiving emails for errors.
* `ALLOWED_HOSTS` to to a list of served domains, like `['.edid.co', '.edid.tv']`.
* `DATABASES` to your production database settings.
* For static files:

        import os
        SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
        STATIC_ROOT = os.path.join(SITE_ROOT, 'static')
        STATIC_URL = '/'

* To support additional social sites for accounts:

        EXTEND_APPS = (
            'allauth.socialaccount.providers.google',
        )


When deploying new version:

1. `git pull`
1. `make prepare-serve`
2. `sudo /etc/init.d/uwsgi restart edid.tv`
