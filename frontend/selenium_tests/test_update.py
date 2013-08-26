from django.contrib.auth import get_user_model

from selenium.common.exceptions import NoSuchElementException

from base import EDIDReadySeleniumTestCase


class UpdateSeleniumTestCase(EDIDReadySeleniumTestCase):
    def test_valid(self):
        get_user_model().objects.create_superuser('tester', '', 'test')
        self.doLogin(username='tester', password='test')
        self.assertEqual(self.browser.current_url,
                         "%s/accounts/profile/" % self.live_server_url)

        edid_detail_url = "%s/edid/1/" % self.live_server_url
        edid_update_url = "%s/edid/1/update/" % self.live_server_url
        edid_revision_url = "%s/edid/1/revision/" % self.live_server_url
        timing_1_update_url = "%s/edid/1/standard_timing/1/update/" % (
            self.live_server_url
        )

        # Go to timing update page
        self.browser.get(timing_1_update_url)

        # Update timing and submit form
        self.browser.find_element_by_id('id_refresh_rate').clear()
        self.browser.find_element_by_id('id_refresh_rate').send_keys('120')
        self.browser.find_element_by_id('submit-id-submit').click()

        # Check we got redirected to EDID update page
        self.assertEqual(self.browser.current_url, edid_update_url)

        # Update EDID and submit form
        self.browser.find_element_by_link_text('Monitor Range Limits').click()
        self.browser.find_element_by_id('id_monitor_range_limits').click()
        self.browser.find_element_by_id('submit-id-submit').click()

        # Check we got redirected to EDID detail page
        self.assertEqual(self.browser.current_url, edid_detail_url)

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
        self.browser.find_element_by_id('revert-id-revert').click()

        # Check we got redirected to EDID detail page
        self.assertEqual(self.browser.current_url, edid_detail_url)

        # Check 'Monitor Range Limits' is enabled
        self.browser.find_element_by_id('monitor_range_limits')
