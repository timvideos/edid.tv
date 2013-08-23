import base64
import cStringIO as StringIO
import os
from time import sleep
import warnings

from django.db import transaction
from django.test import LiveServerTestCase

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

from edid_parser.edid_parser import EDID_Parser

from frontend.models import Manufacturer, EDID


class BrowserQuitter(object):
    """Helper class which always causes the browser object to close."""

    def __init__(self, browser):
        self.browser = browser

    def __del__(self):
        try:
            self.browser.close()
            self.browser.quit()
        except WebDriverException:
            pass


class SeleniumTestCase(LiveServerTestCase):
    def setUp(self):
        super(SeleniumTestCase, self).setUp()

        browser = os.environ.get("TEST_DRIVER", "firefox")
        if browser == "firefox":
            profile = webdriver.FirefoxProfile()
            profile.set_preference('plugins.hide_infobar_for_missing_plugin',
                                   True)

            firefox_bin = os.path.join(os.getcwd(), 'firefox', 'firefox')
            if os.path.exists(firefox_bin):
                self.browser = webdriver.Firefox(
                        firefox_profile=profile,
                        firefox_binary=FirefoxBinary(firefox_bin)
                )
            else:
                warnings.warn("Using your default firefox, this can be "
                              "unreliable")
                self.browser = webdriver.Firefox(firefox_profile=profile)
        elif browser == "chrome":
            chromedriver_bin = os.path.join(os.getcwd(), 'chromedriver')
            if not os.path.exists(chromedriver_bin):
                raise SystemError("""\
Unable to find chromedriver binary.

Please download from http://code.google.com/p/chromedriver/downloads/list and
put in your base directory.
""")
            self.browser = webdriver.Chrome(executable_path=chromedriver_bin)

        self.browser_quitter = BrowserQuitter(self.browser)

        self.browser.implicitly_wait(30)

        self.browser.get("%s" % self.live_server_url)
        self.assertIn('EDID.tv', self.browser.title)
        self.main_window_handle = self.browser.window_handles[0]

    def _formatMessage(self, msg, standardMsg):
        s = StringIO.StringIO()
        s.write(LiveServerTestCase._formatMessage(self, msg, standardMsg))
        s.write("\n")
        s.write("\n")
        s.write("failure url: %s\n" % self.browser.current_url)
        s.write("failure page source\n")
        s.write("-"*80)
        s.write("\n")
        s.write(self.browser.page_source.encode('utf-8'))
        s.write("\n")
        s.write("-"*80)
        s.write("\n")
        return s.getvalue()

    def tearDown(self):
        del self.browser_quitter
        super(SeleniumTestCase, self).tearDown()

    def doLogin(self, username='admin', password='admin'):
        account_menu = self.browser.find_element_by_id('account_menu')
        account_menu.click()

        login_link = self.browser.find_element_by_id('login_link')
        login_link.click()

        self.browser.find_element_by_id('id_login').send_keys(username)
        self.browser.find_element_by_id('id_password').send_keys(password)
        self.browser.find_element_by_id('submit_login').click()

    def doLogout(self):
        self.browser.switch_to_window(self.main_window_handle)
        logout_link = self.browser.find_element_by_id('logout_link')
        logout_link.click()


class EDIDReadySeleniumTestCase(SeleniumTestCase):
    def setUp(self):
        super(EDIDReadySeleniumTestCase, self).setUp()

        with transaction.commit_on_success():
            Manufacturer.objects.bulk_create([
                Manufacturer(name_id='TSB', name='Toshiba'),
                Manufacturer(name_id='UNK', name='Unknown'),
            ])

        edid_binary = "\x00\xFF\xFF\xFF\xFF\xFF\xFF\x00\x52\x62\x06\x02\x01" \
                      "\x01\x01\x01\xFF\x13\x01\x03\x80\x59\x32\x78\x0A\xF0" \
                      "\x9D\xA3\x55\x49\x9B\x26\x0F\x47\x4A\x21\x08\x00\x81" \
                      "\x80\x8B\xC0\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01" \
                      "\x01\x01\x02\x3A\x80\x18\x71\x38\x2D\x40\x58\x2C\x45" \
                      "\x00\x76\xF2\x31\x00\x00\x1E\x66\x21\x50\xB0\x51\x00" \
                      "\x1B\x30\x40\x70\x36\x00\x76\xF2\x31\x00\x00\x1E\x00" \
                      "\x00\x00\xFC\x00\x54\x4F\x53\x48\x49\x42\x41\x2D\x54" \
                      "\x56\x0A\x20\x20\x00\x00\x00\xFD\x00\x17\x3D\x0F\x44" \
                      "\x0F\x00\x0A\x20\x20\x20\x20\x20\x20\x01\x24"

        # Parse EDID file
        edid_data = EDID_Parser(edid_binary).data
        # Encode in base64
        edid_base64 = base64.b64encode(edid_binary)

        # Create EDID entry
        edid_object = EDID.create(file_base64=edid_base64,
                                  edid_data=edid_data)
        edid_object.save()
        edid_object.populate_timings_from_edid_parser(edid_data)
        edid_object.save()

        self.edid = edid_object
