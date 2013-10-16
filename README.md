[![Build Status](https://travis-ci.org/timvideos/edid.tv.png)](https://travis-ci.org/timvideos/edid.tv)
[![Coverage Status](https://coveralls.io/repos/timvideos/edid.tv/badge.png)](https://coveralls.io/r/timvideos/edid.tv)
[![githalytics.com alpha](https://cruel-carlota.pagodabox.com/3546d4188a3ed02851bd28932c1abdf3 "githalytics.com")](http://githalytics.com/timvideos/edid.tv)

EDID.tv
===============

Extended display identification data (EDID) is a data structure provided by a digital display to describe its capabilities to a video source (eg. graphics card or set-top box). It is what enables a modern personal computer to know what kinds of monitors are connected to it. Despite EDID information being important in telling the computer how the display works, many devices ship with bad or misleading EDID information.

This website lists monitors EDID information, allows users to browse, search and update them. It supports uploading binary EDID files to add new monitors.

Changes are stored in revisions to track malicious changes, only staff can revert revisions.

EDID files are parsed by EDID Parser. EDID Grabber collects EDID files from operating system and uploads them to this website.


Installation Instructions
---

1. Clone this repository.
2. Create `private/requirements.txt` if needed, you can use it to install additional packages, like database interfaces.
3. Create `private/settings.py`, see `Settings` section below for details, most of the settings are needed only for production deployment only (DEBUG=False).
4. `make install`
5. `make serve`
  * You may need to import `frontend/sql/manufacturer.sql` manually if it failed.

Settings
---

In your `private/settings.py` make sure to set these settings:

* `DEBUG` and `TEMPLATE_DEBUG` to `False`.
* `ADMINS` and `MANAGERS` for receiving emails for errors.
* `ALLOWED_HOSTS` to to a list of served domains, like `['.edid.co', '.edid.tv']`.
* `DATABASES` to your production database settings.
* `EDID_GRABBER_RELEASE_UPLOAD_API_KEY` to API key to be used by [edid_grabber_c](http://github.com/sewar/edid_grabber_c) to publish new releases. Leaving it empty will keep this feature disabled.
* For static files:

        import os
        SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
        STATIC_ROOT = os.path.join(SITE_ROOT, '../static')
        STATIC_URL = '/'

* To support additional social sites for accounts:

        EXTEND_APPS = (
            'allauth.socialaccount.providers.google',
        )

Production Deployment
---

Currently deploying using [nginx](http://nginx.org) and [uwsgi](https://github.com/unbit/uwsgi/). Debian 7 includes uwsgi with [Emperor mode](http://uwsgi-docs.readthedocs.org/en/latest/Emperor.html) which makes deploying apps as easy as deploying sites on nginx.

nginx and uwsgi configuration files: https://gist.github.com/sewar/6182820

Make sure to follow `Installation Instructions` above.

When deploying new version:

1. `git pull`
1. `make prepare-serve`
2. `sudo /etc/init.d/uwsgi restart edid.tv`

Running Tests
---

Tests are run automatically through [Travis CI](https://travis-ci.org/timvideos/edid.tv) and coverage report can be found at [Coveralls](https://coveralls.io/r/timvideos/edid.tv).

To run tests manually use the following commands:
* `make coverage` to run all tests and generate coverage report.
* `make clitest` to run unittests.
* `make firefoxtest` to run Selenium integration tests with Firefox.
* `make pep8` to run [PEP 8](http://www.python.org/dev/peps/pep-0008/) checker.
* `make lint` to run [Pylint](http://www.pylint.org) checker.

Contributing
---

1. [Fork](https://help.github.com/articles/fork-a-repo) this repo.
2. Make your changes and commit them in your fork.
3. Run tests locally as described above if possible.
4. [Create a pull request](https://help.github.com/articles/using-pull-requests).
    Travis-CI will run all tests and make a coverage report.
