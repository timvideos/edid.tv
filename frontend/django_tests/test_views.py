from copy import copy
from tempfile import TemporaryFile
import json

from django.core.urlresolvers import reverse
from django.test import TestCase

from frontend.django_tests.base import EDIDTestMixin
from frontend.forms import (EDIDUpdateForm, StandardTimingForm,
                            DetailedTimingForm)
from frontend.models import (EDID, Manufacturer, StandardTiming,
                             DetailedTiming, Comment)


### EDID Tests
class EDIDUploadTestCase(TestCase):
    def setUp(self):
        Manufacturer.objects.bulk_create([
            Manufacturer(name_id='TSB', name='Toshiba'),
            Manufacturer(name_id='UNK', name='Unknown'),
        ])

    def create_temp_file(self, edid_binary):
        edid_file = TemporaryFile()
        edid_file.write(edid_binary)
        edid_file.flush()
        edid_file.seek(0)

        return edid_file

    def test_valid(self):
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
        response = self.client.post(reverse('edid-upload'), {
            'name': 'edid.bin',
            'edid_file': edid_file
        })

        self.assertRedirects(response, reverse('edid-detail',
                                               kwargs={'pk': 1}))

        # Upload the file again and check error message
        edid_file.seek(0)
        response = self.client.post(reverse('edid-upload'), {
            'name': 'edid.bin',
            'edid_file': edid_file
        })

        self.assertFormError(response, 'form', 'edid_file',
                             'This file have been uploaded before.')

        edid_file.close()

    def test_invalid_size(self):
        edid_binary = "\x00\xFF\xFF\xFF\xFF\xFF\xFF\x00\x24"
        edid_file = self.create_temp_file(edid_binary)

        response = self.client.post(reverse('edid-upload'), {
            'name': 'edid.bin',
            'edid_file': edid_file
        })

        self.assertFormError(response, 'form', 'edid_file',
                             "'Binary file is smaller than 128 bytes.'")

        edid_file.close()

    def test_invalid_header(self):
        edid_binary = "\x00\xFF\xFF\x00\x00\xFF\xFF\x00\x52\x62\x06\x02\x01" \
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

        response = self.client.post(reverse('edid-upload'), {
            'name': 'edid.bin',
            'edid_file': edid_file
        })

        self.assertFormError(response, 'form', 'edid_file',
                             "'Input is not an EDID file.'")

        edid_file.close()

    def test_invalid_checksum(self):
        edid_binary = "\x00\xFF\xFF\xFF\xFF\xFF\xFF\x00\x52\x62\x06\x02\x01" \
                      "\x01\x01\x01\xFF\x13\x01\x03\x80\x59\x32\x78\x0A\xF0" \
                      "\x9D\xA3\x55\x49\x9B\x26\x0F\x47\x4A\x21\x08\x00\x81" \
                      "\x80\x8B\xC0\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01" \
                      "\x01\x01\x02\x3A\x80\x18\x71\x38\x2D\x40\x58\x2C\x45" \
                      "\x00\x76\xF2\x31\x00\x00\x1E\x66\x21\x50\xB0\x51\x00" \
                      "\x1B\x30\x40\x70\x36\x00\x76\xF2\x31\x00\x00\x1E\x00" \
                      "\x00\x00\xFC\x00\x54\x4F\x53\x48\x49\x42\x41\x2D\x54" \
                      "\x56\x0A\x20\x20\x00\x00\x00\xFD\x00\x17\x3D\x0F\x44" \
                      "\x0F\x00\x0A\x20\x20\x20\x20\x20\x20\x01\xFF"
        edid_file = self.create_temp_file(edid_binary)

        response = self.client.post(reverse('edid-upload'), {
            'name': 'edid.bin',
            'edid_file': edid_file
        })

        self.assertFormError(response, 'form', 'edid_file',
                             "'Checksum is corrupt.'")

        edid_file.close()


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
        data['bdp_signal_level_standard'] = 0
        data['mrl_secondary_GTF_start_frequency'] = 0
        data['mrl_secondary_GTF_C'] = 0
        data['mrl_secondary_GTF_M'] = 0
        data['mrl_secondary_GTF_K'] = 0
        data['mrl_secondary_GTF_J'] = 0

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
        response = self.client.post(reverse('edid-upload'), {
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
        data['bdp_signal_level_standard'] = 0
        data['mrl_secondary_GTF_start_frequency'] = 0
        data['mrl_secondary_GTF_C'] = 0
        data['mrl_secondary_GTF_M'] = 0
        data['mrl_secondary_GTF_K'] = 0
        data['mrl_secondary_GTF_J'] = 0

        response = self.client.post(reverse('edid-update', kwargs={'pk': 1}),
                                    data)
        self.assertRedirects(response, reverse('edid-detail', kwargs={
            'pk': 1
        }))
        # Check the field have been updated
        self.assertEqual(EDID.objects.get(pk=1).monitor_range_limits, False)

        # Check there is 2 revisions
        self._check_versions_list(2)

    def test_create_timing(self):
        # Check there is 1 revision
        self._check_versions_list(1)

        # Create timing
        self._login()
        data = StandardTiming.objects \
                             .filter(EDID=1, identification=1) \
                             .values(*StandardTimingForm._meta.fields)[0]

        response = self.client.post(reverse('standard-timing-create',
            kwargs={'edid_pk': 1}), data
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

        response = self.client.post(reverse('standard-timing-update',
            kwargs={'edid_pk': 1, 'identification': 1}), data
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

        response = self.client.post(reverse('standard-timing-create',
            kwargs={'edid_pk': 1}), data
        )
        self.assertRedirects(response, reverse('edid-update', kwargs={
            'pk': 1
        }))

        # Check there is 2 revisions
        self._check_versions_list(2)
        # Check there is 3 standard timings
        self.assertEqual(EDID.objects.get(pk=1).standardtiming_set.count(), 3)

        # Revert with a normal user, will redirect to login page
        response = self.client.delete(reverse('edid-revision-revert',
            kwargs={'edid_pk': 1, 'revision_pk': 1}
        ))
        self.assertNotEqual(response['Location'], reverse(
            'edid-detail', kwargs={'pk': 1}
        ))

        # Revert with no logged in user, will redirect to login page
        self.client.logout()
        response = self.client.delete(reverse('edid-revision-revert',
            kwargs={'edid_pk': 1, 'revision_pk': 1}
        ))
        self.assertNotEqual(response['Location'], reverse(
            'edid-detail', kwargs={'pk': 1}
        ))

        # Revert with a super user, will revert and redirect to detail page
        self._login('supertester', 'test', True)
        response = self.client.delete(reverse('edid-revision-revert',
            kwargs={'edid_pk': 1, 'revision_pk': 1}
        ))
        self.assertRedirects(response, reverse(
            'edid-detail', kwargs={'pk': 1}
        ))

        # Check there is 3 revisions
        self._check_versions_list(3)
        # Check there is 2 standard timing
        self.assertEqual(EDID.objects.get(pk=1).standardtiming_set.count(), 2)


### Timing Tests
class TimingTestMixin(object):
    def setUp(self):
        super(TimingTestMixin, self).setUp()

        self.timings_set = self._get_timings_set()

    def test_create(self):
        data = self.timings_set.filter(identification=1) \
                               .values(*self.form._meta.fields)[0]

        # Create while not logged in, get redirected to login page
        response = self.client.post(reverse('%s-create' % self.urlconf_prefix,
            kwargs={'edid_pk': 1}), data
        )
        self.assertEqual(response.status_code, 302)

        # Check there is still two standard timings left, nothing got created
        self.assertEqual(self.timings_set.count(), 2)

        # Create while logged in, get redirected to EDID update page
        self._login()
        response = self.client.post(reverse('%s-create' % self.urlconf_prefix,
            kwargs={'edid_pk': 1}), data
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
        response = self.client.post(reverse('%s-update' % self.urlconf_prefix,
            kwargs={'edid_pk': 1, 'identification': 1}), data
        )
        self.assertEqual(response.status_code, 302)

        # Check the field have not been updated
        self.assertNotEqual(
            self.timings_set.get(identification=1).horizontal_active,
            1400
        )

        # Update while logged in, get redirected to EDID update page
        self._login()
        response = self.client.post(reverse('%s-update' % self.urlconf_prefix,
            kwargs={'edid_pk': 1, 'identification': 1}), data
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
