from django.contrib.auth import get_user_model

from frontend.django_tests.base import EDIDTestMixin

from base import SeleniumTestCase


class LoginSeleniumTestCase(EDIDTestMixin, SeleniumTestCase):
    def test_invalid_login(self):
        """Test client-side actions on login/logout."""

        self.doLogin(username="notexisting", password="wrong")

        #Should have an error message
        self.assertIn(u"The username and/or password you specified are not "
                      u"correct.", self.browser.page_source)

    def test_non_admin_login(self):
        """Test client-side actions on login/logout."""

        get_user_model().objects.create_user('tester', '', 'test')
        self.doLogin(username='tester', password='test')

        self.assertEqual(self.browser.current_url,
                         "%s/accounts/profile/" % self.live_server_url)

    def test_admin_login(self):
        """Test client-side actions on login/logout."""

        get_user_model().objects.create_superuser('tester', '', 'test')
        self.doLogin(username='tester', password='test')

        self.assertEqual(self.browser.current_url,
                         "%s/accounts/profile/" % self.live_server_url)
