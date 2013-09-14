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
	-$(ACTIVATE) && pip install -r private/requirements.txt

install: install-ez_setup install-distribute install-packages

createinitialrevisions:
	$(ACTIVATE) && python manage.py createinitialrevisions

prepare-serve:
	$(ACTIVATE) && python manage.py collectstatic --noinput
	$(ACTIVATE) && python manage.py syncdb


#### Tests

test: parsertest clitest firefoxtest

parsertest:
	$(ACTIVATE) && python edid_parser/tests.py

clitest:
	$(ACTIVATE) && python manage.py test --settings=test_settings \
	    frontend.django_tests

firefoxtest:
	$(ACTIVATE) && TEST_DISPLAY=1 python manage.py test \
	    --settings=test_settings frontend.selenium_tests

coverage:
	$(ACTIVATE) && coverage run --source=edid_parser edid_parser/tests.py
	$(ACTIVATE) && coverage run -a --source=frontend manage.py test \
	    --settings=test_settings frontend.django_tests
	$(ACTIVATE) && TEST_DISPLAY=1 coverage run -a --source=frontend manage.py \
	    test --settings=test_settings frontend.selenium_tests
	$(ACTIVATE) && coverage html -d coverage_report
	$(ACTIVATE) && coverage erase

pep8:
	-$(ACTIVATE) && pep8 --statistics *.py
	-$(ACTIVATE) && pep8 --statistics edid_parser/
	-$(ACTIVATE) && pep8 --statistics frontend/

lint:
	@# C0303 - Disable "Trailing whitespace"
	@# E1103 - Disable "Instance of 'x' has no 'y' member
	@#         (but some types could not be inferred)"
	@# I0011 - Disable "Locally disabling 'xxxx'"
	@# R0801 - Disable "Duplication/Similar lines in %s files"
	@# R0904 - Disable "Too many public methods"
	@# W0212 - Disable "Access to a protected member _meta of a client class"
	@# W0511 - Disable "FIXME/TODO"
	@# W0613 - Disable "Unused argument 'xxxx'"
	$(ACTIVATE) && pylint \
		--disable=C0303 \
		--disable=E1103 \
		--disable=I0011 \
		--disable=R0801 \
		--disable=R0904 \
		--disable=W0212 \
		--disable=W0511 \
		--disable=W0613 \
		--reports=n \
		--msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" \
		*.py edid_parser/*.py frontend/*.py

###############################################################################
###############################################################################

serve: prepare-serve
	$(ACTIVATE) && python manage.py runserver
