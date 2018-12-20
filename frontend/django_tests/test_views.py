from copy import copy
from tempfile import TemporaryFile
import json
import os

from django.core.urlresolvers import reverse
from django.test import TestCase

from frontend.django_tests.base import EDIDTestMixin
from frontend.forms import (EDIDUpdateForm, StandardTimingForm,
                            DetailedTimingForm)
from frontend.models import (EDID, Manufacturer, StandardTiming,
                             DetailedTiming, Comment)


### EDID Tests
class EDIDUploadTestCase(EDIDTestMixin, TestCase):
    def setUp(self):
        Manufacturer.objects.bulk_create([
            Manufacturer(name_id='TSB', name='Toshiba'),
            Manufacturer(name_id='UNK', name='Unknown'),
        ])

        self.edid_binary = "\x00\xFF\xFF\xFF\xFF\xFF\xFF\x00\x52\x62\x06\x02" \
                           "\x01\x01\x01\x01\xFF\x13\x01\x03\x80\x59\x32\x78" \
                           "\x0A\xF0\x9D\xA3\x55\x49\x9B\x26\x0F\x47\x4A\x21" \
                           "\x08\x00\x81\x80\x8B\xC0\x01\x01\x01\x01\x01\x01" \
                           "\x01\x01\x01\x01\x01\x01\x02\x3A\x80\x18\x71\x38" \
                           "\x2D\x40\x58\x2C\x45\x00\x76\xF2\x31\x00\x00\x1E" \
                           "\x66\x21\x50\xB0\x51\x00\x1B\x30\x40\x70\x36\x00" \
                           "\x76\xF2\x31\x00\x00\x1E\x00\x00\x00\xFC\x00\x54" \
                           "\x4F\x53\x48\x49\x42\x41\x2D\x54\x56\x0A\x20\x20" \
                           "\x00\x00\x00\xFD\x00\x17\x3D\x0F\x44\x0F\x00\x0A" \
                           "\x20\x20\x20\x20\x20\x20\x01\x24"

    def create_temp_file(self, edid_binary):
        edid_file = TemporaryFile()
        edid_file.write(edid_binary)
        edid_file.flush()
        edid_file.seek(0)

        return edid_file

    def test_valid(self):
        edid_file = self.create_temp_file(self.edid_binary)

        # Upload the file and check for redirection to EDID detail view
        response = self.client.post(reverse('edid-upload-binary'), {
            'name': 'edid.bin',
            'edid_file': edid_file
        })

        self.assertRedirects(response, reverse('edid-detail',
                                               kwargs={'pk': 1}))

        # Upload the file again and check error message
        edid_file.seek(0)
        response = self.client.post(reverse('edid-upload-binary'), {
            'name': 'edid.bin',
            'edid_file': edid_file
        })

        self.assertFormError(response, 'form', 'edid_file',
                             'This file have been uploaded before.')

        edid_file.close()

    def test_valid_with_user(self):
        # Login
        user = self._login()
        # Upload EDID
        self.test_valid()
        # Get EDID object
        edid = EDID.objects.get(pk=1)
        # Check EDID user is set correctly
        self.assertEqual(edid.user, user)

    def test_invalid_size(self):
        # Make truncated EDID file
        edid_binary = "\x00\xFF\xFF\xFF\xFF\xFF\xFF\x00\x24"

        # Save EDID to temporary file
        edid_file = self.create_temp_file(edid_binary)

        # Upload EDID file
        response = self.client.post(reverse('edid-upload-binary'), {
            'name': 'edid.bin',
            'edid_file': edid_file
        })

        # Check for error message
        self.assertFormError(response, 'form', 'edid_file',
                             'Binary file is smaller than 128 bytes.')

        edid_file.close()

    def test_invalid_header(self):
        # Sabotage EDID header
        edid_binary = self.edid_binary[:3] + '\x00\x00' + self.edid_binary[5:]

        # Save EDID to temporary file
        edid_file = self.create_temp_file(edid_binary)

        # Upload EDID file
        response = self.client.post(reverse('edid-upload-binary'), {
            'name': 'edid.bin',
            'edid_file': edid_file
        })

        # Check for error message
        self.assertFormError(response, 'form', 'edid_file',
                             'Input is not an EDID file.')

        edid_file.close()

    def test_invalid_checksum(self):
        # Sabotage EDID checksum
        edid_binary = self.edid_binary[:127] + '\xFF'

        # Save EDID to temporary file
        edid_file = self.create_temp_file(edid_binary)

        # Upload EDID file
        response = self.client.post(reverse('edid-upload-binary'), {
            'name': 'edid.bin',
            'edid_file': edid_file
        })

        # Check for error message
        self.assertFormError(response, 'form', 'edid_file',
                             'Checksum is corrupt.')

        edid_file.close()


class EDIDTextUploadTestCase(TestCase):
    def setUp(self):
        Manufacturer.objects.bulk_create([
            Manufacturer(name_id='SEC', name='Seiko Epson Corporation'),
            Manufacturer(name_id='UNK', name='Unknown'),
        ])

        self.post_url = reverse('edid-upload-text')

    def _read_from_file(self, filename):
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        with open(os.path.join(data_dir, filename), 'r') as text_file:
            return text_file.read()

    def test_hex(self):
        hex_text = self._read_from_file('hex.log')

        # Submit Hex
        response = self.client.post(
            self.post_url, {'text': hex_text, 'text_type': 'hex'}
        )

        # Check an EDID was parsed and added
        self.assertEqual(response.context_data['succeeded'], 1)
        self.assertEqual(response.context_data['failed'], 0)
        self.assertEqual(response.context_data['duplicate'], 0)

        # Check some of EDID values
        edid = EDID.objects.get(pk=1)
        self.assertEqual(
            len([timing for timing in edid.get_est_timings()
                 if timing['supported']]),
            0
        )
        self.assertEqual(edid.manufacturer.name_id, 'SEC')
        self.assertEqual(edid.bdp_video_input, EDID.bdp_video_input_digital)
        self.assertEqual(edid.monitor_range_limits, False)

        ## Duplicate test
        # Submit Hex again
        response = self.client.post(
            self.post_url, {'text': hex_text, 'text_type': 'hex'}
        )

        # Check an EDID was parsed and rejected for duplicate
        self.assertEqual(response.context_data['succeeded'], 0)
        self.assertEqual(response.context_data['failed'], 0)
        self.assertEqual(response.context_data['duplicate'], 1)

        ## Failure test
        # Sabotage Hex, corrupting EDID header
        hex_text = hex_text[:18] + '00' + hex_text[20:]

        # Submit Hex again
        response = self.client.post(
            self.post_url, {'text': hex_text, 'text_type': 'hex'}
        )

        # Check an EDID failed parsed
        self.assertEqual(response.context_data['succeeded'], 0)
        self.assertEqual(response.context_data['failed'], 1)
        self.assertEqual(response.context_data['duplicate'], 0)

    def test_xrandr(self):
        xrandr_text = self._read_from_file('xrandr.log')

        # Submit XRandR output
        response = self.client.post(
            self.post_url, {'text': xrandr_text, 'text_type': 'xrandr'}
        )

        # Check an EDID was parsed and added
        self.assertEqual(response.context_data['succeeded'], 1)
        self.assertEqual(response.context_data['failed'], 0)
        self.assertEqual(response.context_data['duplicate'], 0)

        # Check some of EDID values
        edid = EDID.objects.get(pk=1)
        self.assertEqual(
            len([timing for timing in edid.get_est_timings()
                 if timing['supported']]),
            0
        )
        self.assertEqual(edid.manufacturer.name_id, 'SEC')
        self.assertEqual(edid.bdp_video_input, EDID.bdp_video_input_digital)
        self.assertEqual(edid.monitor_range_limits, False)

        ## Duplicate test
        # Submit XRandR output again
        response = self.client.post(
            self.post_url, {'text': xrandr_text, 'text_type': 'xrandr'}
        )

        # Check an EDID was parsed and rejected for duplicate
        self.assertEqual(response.context_data['succeeded'], 0)
        self.assertEqual(response.context_data['failed'], 0)
        self.assertEqual(response.context_data['duplicate'], 1)

        ## Failure test
        # Sabotage XRandR output, corrupting EDID header
        xrandr_text = xrandr_text[:162] + '00' + xrandr_text[164:]

        # Submit XRandR output again
        response = self.client.post(
            self.post_url, {'text': xrandr_text, 'text_type': 'xrandr'}
        )

        # Check an EDID failed parsed
        self.assertEqual(response.context_data['succeeded'], 0)
        self.assertEqual(response.context_data['failed'], 1)
        self.assertEqual(response.context_data['duplicate'], 0)


class EDIDTestCase(EDIDTestMixin, TestCase):
    def test_list(self):
        response = self.client.get(reverse('index'))

        # Manufacturer name
        self.assertContains(response, "Toshiba")
        # Serial number
        self.assertContains(response, "16843009")

    def test_detail(self):
        # Valid pk
        response = self.client.get(reverse('edid-detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['edid'], self.edid)

        # Invalid pk
        response = self.client.get(reverse('edid-detail', kwargs={'pk': 10}))
        self.assertEqual(response.status_code, 404)

    def test_update(self):
        data = EDID.objects.filter(pk=1) \
                           .values(*EDIDUpdateForm._meta.fields)[0]
        data['monitor_range_limits'] = False

        # Fields with null value will fail form validation
        data['week_of_manufacture'] = ''
        data['year_of_manufacture'] = ''
        data['bdp_signal_level_standard'] = 0
        data['mrl_secondary_gtf_start_freq'] = 0
        data['mrl_secondary_gtf_c'] = 0
        data['mrl_secondary_gtf_m'] = 0
        data['mrl_secondary_gtf_k'] = 0
        data['mrl_secondary_gtf_j'] = 0

        # Update while not logged in, get redirected to login page
        response = self.client.post(reverse('edid-update', kwargs={'pk': 1}),
                                    data)
        self.assertEqual(response.status_code, 302)

        # Check the field have not been updated
        self.assertNotEqual(EDID.objects.get(pk=1).monitor_range_limits, False)

        # Update while logged in, get redirected to EDID detail page
        self._login()
        response = self.client.post(reverse('edid-update', kwargs={'pk': 1}),
                                    data)
        self.assertRedirects(response, reverse('edid-detail', kwargs={
            'pk': 1
        }))
        # Check the field have been updated
        self.assertEqual(EDID.objects.get(pk=1).monitor_range_limits, False)


### EDID Revisions Tests
class RevisionsTestCase(EDIDTestMixin, TestCase):
    def setUp(self):
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
        edid_file = self.create_temp_file(edid_binary)

        # Upload the file and check for redirection to EDID detail view
        response = self.client.post(reverse('edid-upload-binary'), {
            'name': 'edid.bin',
            'edid_file': edid_file
        })
        self.assertRedirects(response, reverse('edid-detail',
                                               kwargs={'pk': 1}))

        edid_file.close()

    def create_temp_file(self, edid_binary):
        edid_file = TemporaryFile()
        edid_file.write(edid_binary)
        edid_file.flush()
        edid_file.seek(0)

        return edid_file

    def _check_versions_list(self, count):
        response = self.client.get(reverse(
            'edid-revision-list',
            kwargs={'edid_pk': 1}
        ))
        self.assertEqual(len(response.context['versions_list']), count)

    def test_update_edid(self):
        # Check there is 1 revision
        self._check_versions_list(1)

        # Update EDID
        self._login()
        data = EDID.objects.filter(pk=1) \
                           .values(*EDIDUpdateForm._meta.fields)[0]
        data['monitor_range_limits'] = False

        # We need to fill these to validate the form
        data['week_of_manufacture'] = ''
        data['year_of_manufacture'] = ''
        data['bdp_signal_level_standard'] = 0
        data['mrl_secondary_gtf_start_freq'] = 0
        data['mrl_secondary_gtf_c'] = 0
        data['mrl_secondary_gtf_m'] = 0
        data['mrl_secondary_gtf_k'] = 0
        data['mrl_secondary_gtf_j'] = 0

        response = self.client.post(reverse('edid-update', kwargs={'pk': 1}),
                                    data)
        self.assertRedirects(response, reverse('edid-detail', kwargs={
            'pk': 1
        }))
        # Check the field have been updated
        self.assertEqual(EDID.objects.get(pk=1).monitor_range_limits, False)

        # Check there is 2 revisions
        self._check_versions_list(2)

    def test_revision_detail(self):
        # Check there is 1 revision
        self._check_versions_list(1)

        # Check invalid revision pk
        response = self.client.get(
            reverse('edid-revision-detail',
                    kwargs={'edid_pk': 1, 'revision_pk': 10})
        )

        self.assertEqual(response.status_code, 404)

        # Get revision detail page
        response = self.client.get(
            reverse('edid-revision-detail',
                    kwargs={'edid_pk': 1, 'revision_pk': 1})
        )

        self.assertEqual(response.status_code, 200)

        # Get EDID object
        edid = response.context_data['object']
        self.assertIsInstance(edid, EDID)

        # Check timings are injected in EDID object
        self.assertEqual(len(edid.standardtimings), 2)
        self.assertEqual(len(edid.detailedtimings), 2)

    def test_create_timing(self):
        # Check there is 1 revision
        self._check_versions_list(1)

        # Create timing
        self._login()
        data = StandardTiming.objects \
                             .filter(EDID=1, identification=1) \
                             .values(*StandardTimingForm._meta.fields)[0]

        response = self.client.post(
            reverse('standard-timing-create', kwargs={'edid_pk': 1}), data
        )
        self.assertRedirects(response, reverse('edid-update', kwargs={
            'pk': 1
        }))

        # Check there is 2 revisions
        self._check_versions_list(2)

    def test_update_timing(self):
        # Check there is 1 revision
        self._check_versions_list(1)

        # Update timing
        self._login()
        data = StandardTiming.objects \
                             .filter(EDID=1, identification=1) \
                             .values(*StandardTimingForm._meta.fields)[0]
        data['refresh_rate'] = 120

        response = self.client.post(
            reverse('standard-timing-update',
                    kwargs={'edid_pk': 1, 'identification': 1}),
            data
        )
        self.assertRedirects(response, reverse('edid-update', kwargs={
            'pk': 1
        }))

        # Check there is 2 revisions
        self._check_versions_list(2)

    def test_delete_timing(self):
        # Check there is 1 revision
        self._check_versions_list(1)

        # Delete timing
        self._login()
        response = self.client.delete(
            reverse(
                'standard-timing-delete',
                kwargs={'edid_pk': 1, 'identification': 1}
            )
        )
        self.assertRedirects(response, reverse('edid-update', kwargs={
            'pk': 1
        }))

        # Check there is 2 revisions
        self._check_versions_list(2)

    def test_reorder_timing(self):
        # Check there is 1 revision
        self._check_versions_list(1)

        # Reorder timing
        self._login()
        response = self.client.get(
            reverse(
                'standard-timing-reorder',
                kwargs={'edid_pk': 1, 'identification': 1, 'direction': 'down'}
            )
        )
        self.assertRedirects(
            response, reverse('edid-update', kwargs={'pk': 1})
        )

        # Check there is 2 revisions
        self._check_versions_list(2)

    def test_revert(self):
        # Check there is 1 revision
        self._check_versions_list(1)
        # Check there is 2 standard timings
        self.assertEqual(EDID.objects.get(pk=1).standardtiming_set.count(), 2)

        # Create timing
        self._login()
        data = StandardTiming.objects \
                             .filter(EDID=1, identification=1) \
                             .values(*StandardTimingForm._meta.fields)[0]

        response = self.client.post(
            reverse('standard-timing-create', kwargs={'edid_pk': 1}), data
        )
        self.assertRedirects(response, reverse('edid-update', kwargs={
            'pk': 1
        }))

        # Check there is 2 revisions
        self._check_versions_list(2)
        # Check there is 3 standard timings
        self.assertEqual(EDID.objects.get(pk=1).standardtiming_set.count(), 3)

        # Revert with a normal user, will redirect to login page
        response = self.client.delete(
            reverse('edid-revision-revert',
                    kwargs={'edid_pk': 1, 'revision_pk': 1})
        )
        self.assertNotEqual(response['Location'], reverse(
            'edid-detail', kwargs={'pk': 1}
        ))

        # Revert with no logged in user, will redirect to login page
        self.client.logout()
        response = self.client.delete(
            reverse('edid-revision-revert',
                    kwargs={'edid_pk': 1, 'revision_pk': 1})
        )
        self.assertNotEqual(response['Location'], reverse(
            'edid-detail', kwargs={'pk': 1}
        ))

        # Revert with a super user, will revert and redirect to detail page
        self._login('supertester', 'test', True)
        response = self.client.delete(
            reverse('edid-revision-revert',
                    kwargs={'edid_pk': 1, 'revision_pk': 1})
        )
        self.assertRedirects(response, reverse(
            'edid-detail', kwargs={'pk': 1}
        ))

        # Check there is 3 revisions
        self._check_versions_list(3)
        # Check there is 2 standard timing
        self.assertEqual(EDID.objects.get(pk=1).standardtiming_set.count(), 2)

    def test_revision_in_context(self):
        self._login('supertester', 'test', True)
        response = self.client.get(
            reverse('edid-revision-revert',
                    kwargs={'edid_pk': 1, 'revision_pk': 1})
        )

        self.assertIn('revision', response.context_data)

    def test_no_revision_found(self):
        self._login('supertester', 'test', True)
        response = self.client.delete(
            reverse('edid-revision-revert',
                    kwargs={'edid_pk': 1, 'revision_pk': 100})
        )
        self.assertEqual(response.status_code, 404)

    # def test_no_revert_to_current_revision(self):
    #     self._login('supertester', 'test', True)
    #     response = self.client.delete(reverse('edid-revision-revert',
    #         kwargs={'edid_pk': 1, 'revision_pk': 1}
    #     ))
    #
    #     print(response)
    #     self.assertEqual(response.status_code, 400)
    #     self.assertEqual(
    #         response.content,
    #         'You can not revert to the current revision.'
    #     )


### Timing Tests
class TimingTestMixin(object):
    def setUp(self):
        super(TimingTestMixin, self).setUp()

        self.timings_set = self._get_timings_set()

    def test_create(self):
        data = self.timings_set.filter(identification=1) \
                               .values(*self.form._meta.fields)[0]

        # Create while not logged in, get redirected to login page
        response = self.client.post(
            reverse('%s-create' % self.urlconf_prefix,
                    kwargs={'edid_pk': 1}),
            data
        )
        self.assertEqual(response.status_code, 302)

        # Check there is still two standard timings left, nothing got created
        self.assertEqual(self.timings_set.count(), 2)

        # Create while logged in, get redirected to EDID update page
        self._login()
        response = self.client.post(
            reverse('%s-create' % self.urlconf_prefix,
                    kwargs={'edid_pk': 1}),
            data
        )
        self.assertRedirects(response, reverse('edid-update', kwargs={
            'pk': 1
        }))
        self.assertEqual(self.timings_set.count(), 3)

    def test_update(self):
        data = self.timings_set.filter(identification=1) \
                               .values(*self.form._meta.fields)[0]
        data['horizontal_active'] = 1400

        # Update while not logged in, get redirected to login page
        response = self.client.post(
            reverse('%s-update' % self.urlconf_prefix,
                    kwargs={'edid_pk': 1, 'identification': 1}),
            data
        )
        self.assertEqual(response.status_code, 302)

        # Check the field have not been updated
        self.assertNotEqual(
            self.timings_set.get(identification=1).horizontal_active,
            1400
        )

        # Update while logged in, get redirected to EDID update page
        self._login()
        response = self.client.post(
            reverse('%s-update' % self.urlconf_prefix,
                    kwargs={'edid_pk': 1, 'identification': 1}),
            data
        )
        self.assertRedirects(response, reverse('edid-update', kwargs={
            'pk': 1
        }))
        # Check the field have been updated
        self.assertEqual(
            self.timings_set.get(identification=1).horizontal_active,
            1400
        )

    def test_delete(self):
        # Delete while not logged in, get redirected to login page
        response = self.client.delete(
            reverse(
                '%s-delete' % self.urlconf_prefix,
                kwargs={'edid_pk': self.edid.pk, 'identification': 1}
            )
        )
        self.assertEqual(response.status_code, 302)

        # Check there is still two standard timings left, nothing got deleted
        self.assertEqual(self.timings_set.count(), 2)

        # Delete while logged in, get redirected to EDID update page
        self._login()
        response = self.client.delete(
            reverse(
                '%s-delete' % self.urlconf_prefix,
                kwargs={'edid_pk': 1, 'identification': 1}
            )
        )
        self.assertRedirects(response, reverse('edid-update', kwargs={
            'pk': 1
        }))

        # Check there is one standard timing left
        self.assertEqual(self.timings_set.count(), 1)


class StandardTimingTestCase(TimingTestMixin, EDIDTestMixin, TestCase):
    model = StandardTiming
    form = StandardTimingForm
    urlconf_prefix = 'standard-timing'

    def _get_timings_set(self):
        return self.edid.standardtiming_set


class DetailedTimingTestCase(TimingTestMixin, EDIDTestMixin, TestCase):
    model = DetailedTiming
    form = DetailedTimingForm
    urlconf_prefix = 'detailed-timing'

    def _get_timings_set(self):
        return self.edid.detailedtiming_set


### Timing Reorder Tests
class TimingReorderMixin(object):
    def setUp(self):
        super(TimingReorderMixin, self).setUp()

        self.timing_1 = self.model.objects.get(EDID=1, identification=1)
        self.timing_2 = self.model.objects.get(EDID=1, identification=2)

        self.timing_3 = copy(self.timing_1)
        self.timing_3.pk = None
        self.timing_3.identification = 3
        self.timing_3.save()

        self.timing_4 = copy(self.timing_2)
        self.timing_4.pk = None
        self.timing_4.identification = 4
        self.timing_4.save()

    def test_move_down(self):
        self._login()

        response = self.client.get(
            reverse(
                self.urlconf_name,
                kwargs={'edid_pk': 1, 'identification': 2, 'direction': 'down'}
            )
        )
        self.assertRedirects(
            response, reverse('edid-update', kwargs={'pk': 1})
        )

        moved_timing = self.model.objects.get(pk=self.timing_2.pk)
        affected_timing = self.model.objects.get(pk=self.timing_3.pk)

        self.assertEqual(moved_timing.identification, 3)
        self.assertEqual(affected_timing.identification, 2)

    def test_move_up(self):
        self._login()

        response = self.client.get(
            reverse(
                self.urlconf_name,
                kwargs={'edid_pk': 1, 'identification': 4, 'direction': 'up'}
            )
        )
        self.assertRedirects(
            response, reverse('edid-update', kwargs={'pk': 1})
        )

        moved_timing = self.model.objects.get(pk=self.timing_4.pk)
        affected_timing = self.model.objects.get(pk=self.timing_3.pk)

        self.assertEqual(moved_timing.identification, 3)
        self.assertEqual(affected_timing.identification, 4)

    def test_move_down_first(self):
        self._login()

        response = self.client.get(
            reverse(
                self.urlconf_name,
                kwargs={'edid_pk': 1, 'identification': 1, 'direction': 'up'}
            )
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.content,
            'You can not move up a timing if it is the first one.'
        )

    def test_move_down_last(self):
        self._login()

        response = self.client.get(
            reverse(
                self.urlconf_name,
                kwargs={'edid_pk': 1, 'identification': 4, 'direction': 'down'}
            )
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.content,
            'You can not move down a timing if it is the last one.'
        )


class StandardTimingReorderTestCase(TimingReorderMixin, EDIDTestMixin,
                                    TestCase):
    model = StandardTiming
    urlconf_name = 'standard-timing-reorder'


class DetailedTimingReorderTestCase(TimingReorderMixin, EDIDTestMixin,
                                    TestCase):
    model = DetailedTiming
    urlconf_name = 'detailed-timing-reorder'


### Comment Tests
class CommentTestCase(EDIDTestMixin, TestCase):
    def setUp(self):
        super(CommentTestCase, self).setUp()

        self.post_url = reverse('comment-create',
                                kwargs={'edid_pk': self.edid.pk})
        self.valid_data = {'EDID': self.edid.pk,
                           'parent': '',
                           'content': 'This is a test.'}

    def test_login_required(self):
        # Test login is required to submit comment
        response = self.client.post(self.post_url, self.valid_data)

        self.assertNotEqual(response['Location'], reverse(
            'edid-detail', kwargs={'pk': 1}
        ))

    def test_valid(self):
        # Test valid data
        self._login()
        response = self.client.post(self.post_url, self.valid_data)

        self.assertRedirects(
            response, reverse('edid-detail', kwargs={'pk': 1})
        )
        self.assertEqual(self.edid.comment_set.count(), 1)

        # Get the comment and check its fields
        comment = Comment.objects.get(pk=1)
        self.assertEqual(comment.parent, None)
        self.assertEqual(comment.level, 0)

    def test_empty_content(self):
        # Post comment with no content
        user = self._login()

        data = self.valid_data
        data['content'] = ''

        response = self.client.post(self.post_url, data)

        self.assertFormError(response, 'form', 'content',
                             'This field is required.')

    def test_nesting(self):
        self._login()

        # First comment
        self.client.post(self.post_url, self.valid_data)
        comment = Comment.objects.get(pk=1)
        self.assertEqual(comment.parent, None)
        self.assertEqual(comment.level, 0)

        # Second comment, nested under first comment, level 1
        data = self.valid_data
        data['parent'] = 1
        self.client.post(self.post_url, data)
        comment = Comment.objects.get(pk=2)
        self.assertEqual(comment.parent.pk, 1)
        self.assertEqual(comment.level, 1)

        # Third comment, nested under second comment, level 2
        data = self.valid_data
        data['parent'] = 2
        self.client.post(self.post_url, data)
        comment = Comment.objects.get(pk=3)
        self.assertEqual(comment.parent.pk, 2)
        self.assertEqual(comment.level, 2)

    def test_excessive_nesting(self):
        # Create nested comments up to the limit
        user = self._login()
        comment_1 = Comment(EDID=self.edid, user=user, level=0,
                            content='').save()
        comment_2 = Comment(EDID=self.edid, user=user, level=1,
                            parent=comment_1, content='').save()
        comment_3 = Comment(EDID=self.edid, user=user, level=2,
                            parent=comment_2, content='').save()

        # Post comment with over-limit nesting
        data = self.valid_data
        data['parent'] = 3

        response = self.client.post(self.post_url, data)

        self.assertFormError(response, 'form', 'parent',
                             'Comment nesting limit exceeded.')


### API Upload Tests
class APIUploadTestCase(TestCase):
    def setUp(self):
        Manufacturer.objects.bulk_create([
            Manufacturer(name_id='TSB', name='Toshiba'),
            Manufacturer(name_id='UNK', name='Unknown'),
        ])

        self.post_url = reverse('api-upload')
        self.valid_base64_1 = 'AP///////wBSYgYCAQEBAf8TAQOAWTJ4CvCdo1VJmyYPR' \
                              '0ohCACBgIvAAQEBAQEBAQEBAQEBAjqAGHE4LUBYLEUAdv' \
                              'IxAAAeZiFQsFEAGzBAcDYAdvIxAAAeAAAA/ABUT1NISUJ' \
                              'BLVRWCiAgAAAA/QAXPQ9EDwAKICAgICAgASQ='
        self.valid_base64_2 = 'AP///////wAEcqGt3vdQgyMSAQMILx546t6Vo1RMmSYPU' \
                              'FS/75CpQHFPgUCLwJUAlQ+QQAEBITmQMGIaJ0BosDYA2i' \
                              'gRAAAZAAAA/QA4TR9UEQAKICAgICAgAAAA/wBMQTEwQzA' \
                              '0MTQwMzAKAAAA/ABBTDIyMTZXCiAgICAgAFI='

    def test_valid(self):
        # Prepare data
        data = json.dumps(
            {'edid_list': [self.valid_base64_1, self.valid_base64_2]}
        )

        # Post list of EDIDs
        response = self.client.post(
            self.post_url, data, content_type='application/json'
        )

        # Check JSON output
        self.assertJSONEqual(
            response.content, json.dumps({'failed': 0, 'succeeded': 2})
        )

    def test_invalid(self):
        # Sabotage base64 fields
        self.valid_base64_1 = self.valid_base64_1[:54] + 'M' \
            + self.valid_base64_1[55:]
        self.valid_base64_2 = self.valid_base64_2[:54] + 'M' \
            + self.valid_base64_2[55:]

        # Prepare data
        data = json.dumps(
            {'edid_list': [self.valid_base64_1, self.valid_base64_2]}
        )

        # Post list of EDIDs
        response = self.client.post(
            self.post_url, data, content_type='application/json'
        )

        # Check JSON output
        self.assertJSONEqual(
            response.content, json.dumps({'failed': 2, 'succeeded': 0})
        )

    def test_no_list(self):
        # Empty data
        data = {}

        # Post list of EDIDs
        response = self.client.post(
            self.post_url, data, content_type='application/json'
        )

        # Check JSON output
        self.assertJSONEqual(
            response.content,
            json.dumps({'error_message': 'List of EDIDs is missing.'})
        )

    def test_duplicate(self):
        # Prepare data
        data = json.dumps(
            {'edid_list': [self.valid_base64_1, self.valid_base64_2]}
        )

        # Post list of EDIDs
        response = self.client.post(
            self.post_url, data, content_type='application/json'
        )

        # Check JSON output
        self.assertJSONEqual(
            response.content, json.dumps({'failed': 0, 'succeeded': 2})
        )

        # Post list of EDIDs again
        response = self.client.post(
            self.post_url, data, content_type='application/json'
        )

        # Check JSON output
        self.assertJSONEqual(
            response.content, json.dumps({'failed': 2, 'succeeded': 0})
        )


### API Text Upload Tests
class APITextUploadTestCase(TestCase):
    def setUp(self):
        Manufacturer.objects.bulk_create([
            Manufacturer(name_id='SEC', name='Seiko Epson Corporation'),
            Manufacturer(name_id='UNK', name='Unknown'),
        ])

        self.post_url = reverse('api-upload-text')

    def _read_from_file(self, filename):
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        with open(os.path.join(data_dir, filename), 'r') as text_file:
            return text_file.read()

    def test_hex(self):
        hex_text = self._read_from_file('hex.log')

        # Submit Hex
        response = self.client.post(
            self.post_url, {'text': hex_text, 'text_type': 'hex'}
        )
        data = json.loads(response.content)

        # Check an EDID was parsed and added
        self.assertEqual(data['succeeded'], 1)
        self.assertEqual(data['failed'], 0)
        self.assertEqual(data['duplicate'], 0)

        # Check some of EDID values
        edid = EDID.objects.get(pk=1)
        self.assertEqual(
            len([timing for timing in edid.get_est_timings()
                 if timing['supported']]),
            0
        )
        self.assertEqual(edid.manufacturer.name_id, 'SEC')
        self.assertEqual(edid.bdp_video_input, EDID.bdp_video_input_digital)
        self.assertEqual(edid.monitor_range_limits, False)

        ## Duplicate test
        # Submit Hex again
        response = self.client.post(
            self.post_url, {'text': hex_text, 'text_type': 'hex'}
        )
        data = json.loads(response.content)

        # Check an EDID was parsed and rejected for duplicate
        self.assertEqual(data['succeeded'], 0)
        self.assertEqual(data['failed'], 0)
        self.assertEqual(data['duplicate'], 1)

        ## Failure test
        # Sabotage Hex, corrupting EDID header
        hex_text = hex_text[:18] + '00' + hex_text[20:]

        # Submit Hex again
        response = self.client.post(
            self.post_url, {'text': hex_text, 'text_type': 'hex'}
        )
        data = json.loads(response.content)

        # Check an EDID failed parsed
        self.assertEqual(data['succeeded'], 0)
        self.assertEqual(data['failed'], 1)
        self.assertEqual(data['duplicate'], 0)

    def test_xrandr(self):
        xrandr_text = self._read_from_file('xrandr.log')

        # Submit XRandR output
        response = self.client.post(
            self.post_url, {'text': xrandr_text, 'text_type': 'xrandr'}
        )
        data = json.loads(response.content)

        # Check an EDID was parsed and added
        self.assertEqual(data['succeeded'], 1)
        self.assertEqual(data['failed'], 0)
        self.assertEqual(data['duplicate'], 0)

        # Check some of EDID values
        edid = EDID.objects.get(pk=1)
        self.assertEqual(
            len([timing for timing in edid.get_est_timings()
                 if timing['supported']]),
            0
        )
        self.assertEqual(edid.manufacturer.name_id, 'SEC')
        self.assertEqual(edid.bdp_video_input, EDID.bdp_video_input_digital)
        self.assertEqual(edid.monitor_range_limits, False)

        ## Duplicate test
        # Submit XRandR output again
        response = self.client.post(
            self.post_url, {'text': xrandr_text, 'text_type': 'xrandr'}
        )
        data = json.loads(response.content)

        # Check an EDID was parsed and rejected for duplicate
        self.assertEqual(data['succeeded'], 0)
        self.assertEqual(data['failed'], 0)
        self.assertEqual(data['duplicate'], 1)

        ## Failure test
        # Sabotage XRandR output, corrupting EDID header
        xrandr_text = xrandr_text[:162] + '00' + xrandr_text[164:]

        # Submit XRandR output again
        response = self.client.post(
            self.post_url, {'text': xrandr_text, 'text_type': 'xrandr'}
        )
        data = json.loads(response.content)

        # Check an EDID failed parsed
        self.assertEqual(data['succeeded'], 0)
        self.assertEqual(data['failed'], 1)
        self.assertEqual(data['duplicate'], 0)

    def test_invalid(self):
        response = self.client.post(
            self.post_url, {'text': 'BAD TEXT', 'text_type': 'None'}
        )

        self.assertJSONEqual(response.content, {'error': 'Submittion failed!'})


### Manufacturer Tests
class ManufacturerTestCase(EDIDTestMixin, TestCase):
    def test_list_queryset(self):
        # Get Manufacturer List
        response = self.client.get(
            reverse('manufacturer-list')
        )
        manufacturers = response.context_data['manufacturer_list']

        # Check we have 1 manufacturer
        self.assertEqual(len(manufacturers), 1)
        # Check first manufacturer have 1 edid
        self.assertEqual(manufacturers[0].edid__count, 1)

    def test_detail_context(self):
        # Get Manufacturer Detail
        response = self.client.get(
            reverse('manufacturer-detail', kwargs={'pk': 1})
        )

        # Check for edid_list in context
        self.assertIn('edid_list', response.context_data)
        edid = response.context_data['edid_list'][0]

        # Check for timings count in EDID object
        self.assertEqual(edid.standardtiming__count, 2)
        self.assertEqual(edid.detailedtiming__count, 2)
