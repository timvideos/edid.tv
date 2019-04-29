from django.contrib.auth import get_user_model
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import \
    text_to_be_present_in_element, url_to_be
from selenium.webdriver.support.wait import WebDriverWait

from base import EDIDReadySeleniumTestCase


class LoginSeleniumTestCase(EDIDReadySeleniumTestCase):
    def test_invalid_login(self):
        """Test client-side actions on login/logout."""

        self.do_login(username="notexisting", password="wrong")

        WebDriverWait(self.browser, 30).until(
            text_to_be_present_in_element((By.TAG_NAME, "html"),
                                          u"The username and/or password you "
                                          u"specified are not correct."),
            'Should have an error message'
        )

    def test_non_admin_login(self):
        """Test client-side actions on login/logout."""

        get_user_model().objects.create_user('tester', '', 'test')
        self.do_login(username='tester', password='test')

        WebDriverWait(self.browser, 30).until(
            url_to_be("%s/accounts/profile/" % self.live_server_url),
            'Should redirect to profile page'
        )

    def test_admin_login(self):
        """Test client-side actions on login/logout."""

        get_user_model().objects.create_superuser('tester', '', 'test')
        self.do_login(username='tester', password='test')

        WebDriverWait(self.browser, 30).until(
            url_to_be("%s/accounts/profile/" % self.live_server_url),
            'Should redirect to profile page'
        )

    def test_logout(self):
        # Non-admin user login
        get_user_model().objects.create_user('tester', '', 'test')
        self.do_login(username='tester', password='test')

        WebDriverWait(self.browser, 30).until(
            url_to_be("%s/accounts/profile/" % self.live_server_url),
            'Should redirect to profile page'
        )

        # Logout
        self.do_logout()

        WebDriverWait(self.browser, 30).until(
            url_to_be("%s/" % self.live_server_url),
            'Should redirect to main page'
        )

        # Check user is really logged out by looking for login link
        self.browser.find_element_by_id('account_menu').click()
        self.browser.find_element_by_id('login_link')
