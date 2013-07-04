###############################################################################
## Helpful Definitions
###############################################################################
define \n


endef

ACTIVATE = . bin/activate

###############################################################################
# Export the configuration to sub-makes
###############################################################################
export

all: test

virtualenv: bin/activate
lib: bin/activate

distclean: virtualenv-clean clean

virtualenv-clean:
	rm -rf bin include lib lib64 share src

clean:
	find . \( -name \*\.pyc \) -delete
	git clean -f -d

bin/activate:
	virtualenv --no-site-packages .
	-rm distribute*.tar.gz

freeze:
	$(ACTIVATE) && pip freeze > requirements.txt

lib/python2.6/site-packages/distribute-0.6.25-py2.6.egg-info: lib
	$(ACTIVATE) && pip install -U distribute

lib/python2.6/site-packages/ez_setup.py: lib
	$(ACTIVATE) && pip install ez_setup

install-packages: requirements.txt
	$(ACTIVATE) && pip install -r requirements.txt

install: lib/python2.6/site-packages/ez_setup.py lib/python2.6/site-packages/distribute-0.6.25-py2.6.egg-info install-packages

prepare-serve: install
	$(ACTIVATE) && python manage.py collectstatic --noinput
	$(ACTIVATE) && python manage.py syncdb


#### Tests

test: clitest firefoxtest

clitest: install
	$(ACTIVATE) && python manage.py test -v2 frontend.django_tests

firefoxtest: install
	$(ACTIVATE) && TEST_DISPLAY=1 python manage.py test -v 2 frontend.selenium_tests

chrometest: install
	$(ACTIVATE) && TEST_DRIVER="chrome" TEST_DISPLAY=1 python manage.py test -v 2 frontend.selenium_tests

lint: install
	@# R0904 - Disable "Too many public methods" warning
	@# W0221 - Disable "Arguments differ from parent", as get and post will.
	@# E1103 - Disable "Instance of 'x' has no 'y' member (but some types could not be inferred)"
	@# I0011 - Disable "Locally disabling 'xxxx'"
	@# C0111 - Disable "Missing docstring"
	@$(ACTIVATE) && python \
		-W "ignore:disable-msg is:DeprecationWarning:pylint.lint" \
		-c "import sys; from pylint import lint; lint.Run(sys.argv[1:])" \
		--reports=n \
		--include-ids=y \
		--no-docstring-rgx "(__.*__)|(get)|(post)|(main)" \
		--indent-string='    ' \
		--disable=W0221 \
		--disable=R0904 \
		--disable=E1103 \
		--disable=I0011 \
		--disable=C0111 \
		--const-rgx='[a-z_][a-z0-9_]{2,30}$$' \
		*.py frontend/*.py edid_parser/*.py 2>&1 | grep -v 'maximum recursion depth exceeded'

###############################################################################
###############################################################################

serve: prepare-serve install
	$(ACTIVATE) && python manage.py runserver
