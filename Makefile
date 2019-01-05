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
#	git clean -f -d

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
	$(ACTIVATE) && [ ! -f private/requirements.txt ] || pip install -r private/requirements.txt

install: install-ez_setup install-distribute install-packages

createinitialrevisions:
	$(ACTIVATE) && python manage.py createinitialrevisions

prepare-serve:
	$(ACTIVATE) && python manage.py collectstatic --noinput
	$(ACTIVATE) && python manage.py migrate
	$(ACTIVATE) && python manage.py loaddata manufacturer.json


#### Tests

test: parsertest clitest firefoxtest

parsertest:
	$(ACTIVATE) && python edid_parser/tests.py

clitest:
	$(ACTIVATE) && python manage.py test \
	    frontend.django_tests

firefoxtest:
	$(ACTIVATE) && TEST_DISPLAY=1 python manage.py test \
	    frontend.selenium_tests

coverage:
	$(ACTIVATE) && coverage run --source=edid_parser edid_parser/tests.py
	$(ACTIVATE) && coverage run -a --source=frontend manage.py test \
	    frontend.django_tests
	$(ACTIVATE) && TEST_DISPLAY=1 coverage run -a --source=frontend manage.py \
	    test frontend.selenium_tests
	$(ACTIVATE) && coverage html -d coverage_report
	$(ACTIVATE) && coverage erase

pep8:
	-$(ACTIVATE) && pep8 --statistics *.py
	-$(ACTIVATE) && pep8 --statistics edid_parser/
	-$(ACTIVATE) && pep8 --statistics frontend/

lint:
	@# C0303 - Disable "Trailing whitespace"
	$(ACTIVATE) && pylint \
		--disable=C0303 \
		--reports=n \
		--msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" \
		*.py edid_parser/*.py frontend/*.py

###############################################################################
###############################################################################

serve: prepare-serve
	$(ACTIVATE) && python manage.py runserver
