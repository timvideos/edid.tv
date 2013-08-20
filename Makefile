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
	rm -rf bin include local lib lib64 share src

clean:
	find . \( -name \*\.pyc \) -delete
	git clean -f -d

bin/activate:
	virtualenv --no-site-packages .
	-rm distribute*.tar.gz

freeze:
	$(ACTIVATE) && pip freeze > requirements.txt

install-distribute: lib
	$(ACTIVATE) && pip install distribute

install-ez_setup: lib
	$(ACTIVATE) && pip install ez_setup

install-packages: requirements.txt
	$(ACTIVATE) && pip install -r requirements.txt

install: install-ez_setup install-distribute install-packages

install-coveralls:
	$(ACTIVATE) && pip install coveralls

createinitialrevisions:
	$(ACTIVATE) && python manage.py createinitialrevisions

prepare-serve:
	$(ACTIVATE) && python manage.py collectstatic --noinput
	$(ACTIVATE) && python manage.py syncdb


#### Tests

test: clitest firefoxtest

clitest:
	$(ACTIVATE) && coverage run --source=frontend manage.py test --verbosity 2 --settings=test_settings frontend.django_tests

firefoxtest:
	$(ACTIVATE) && TEST_DISPLAY=1 python manage.py test --verbosity 2 --settings=test_settings frontend.selenium_tests

#chrometest:
#	$(ACTIVATE) && TEST_DRIVER="chrome" TEST_DISPLAY=1 python manage.py test --verbosity 2 --settings=test_settings frontend.selenium_tests

lint:
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

serve: prepare-serve
	$(ACTIVATE) && python manage.py runserver
