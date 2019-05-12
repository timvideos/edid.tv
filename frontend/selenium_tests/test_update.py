from django.contrib.auth import get_user_model

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.expected_conditions import url_to_be, \
    url_contains
from selenium.webdriver.support.wait import WebDriverWait

from .base import EDIDReadySeleniumTestCase


class UpdateSeleniumTestCase(EDIDReadySeleniumTestCase):
    def test_valid(self):
        get_user_model().objects.create_superuser('tester', '', 'test')
        self.do_login(username='tester', password='test')

        WebDriverWait(self.browser, 30).until(
            url_to_be("%s/accounts/profile/" % self.live_server_url),
            'Should redirect to profile page'
        )

        edid_detail_url = \
            "%s/edid/%i/" % (self.live_server_url, self.edid.id)
        edid_update_url = \
            "%s/edid/%i/update/" % (self.live_server_url, self.edid.id)
        edid_revision_url = \
            "%s/edid/%i/revision/" % (self.live_server_url, self.edid.id)
        timing_1_update_url = "%s/edid/%i/standard_timing/%i/update/" % (
            self.live_server_url,
            self.edid.id,
            self.edid.standardtiming_set.all()[0].id
        )

        # Go to timing update page
        self.browser.get(timing_1_update_url)

        # Update timing and submit form
        self.browser.find_element_by_id('id_refresh_rate').clear()
        self.browser.find_element_by_id('id_refresh_rate').send_keys('120')
        self.browser.find_element_by_id('submit-id-submit').click()

        WebDriverWait(self.browser, 30).until(
            url_to_be(edid_update_url),
            'Should redirect to EDID update page'
        )

        # Update EDID and submit form
        self.browser.find_element_by_link_text('Monitor Range Limits').click()
        self.browser.find_element_by_id('id_monitor_range_limits').click()
        self.browser.find_element_by_id('submit-id-submit').click()

        WebDriverWait(self.browser, 30).until(
            url_contains(edid_detail_url),
            'Should redirect to EDID detail page'
        )

        # Check 'Monitor Range Limits' is disabled
        self.assertRaises(
            NoSuchElementException,
            self.browser.find_element_by_id,
            'monitor_range_limits'
        )

        # Go to EDID revisions page
        self.browser.get(edid_revision_url)

        # Revert revision 1
        self.browser.find_element_by_id('revision-1-revert-link').click()

        # Confirm revert action
        self.browser.find_element_by_id('revert-id-revert').submit()

        WebDriverWait(self.browser, 30).until(
            url_contains(edid_detail_url),
            'Should redirect to EDID detail page'
        )

        # Check 'Monitor Range Limits' is enabled
        self.browser.find_element_by_id('monitor_range_limits')
