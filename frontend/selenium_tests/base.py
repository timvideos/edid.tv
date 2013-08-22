import cStringIO as StringIO
import os
import warnings

from django.test import LiveServerTestCase

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary


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

        # self.browser.implicitly_wait(30)

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
