from django.test import TestCase

from frontend.django_tests.base import EDIDTestMixin
from frontend.forms import (EDIDTextUploadForm, EDIDUpdateForm, CommentForm,
                            StandardTimingForm, DetailedTimingForm)
from frontend.models import EDID, StandardTiming, DetailedTiming, Comment


class FormTestMixin(object):
    def _get_form(self, data):
        if 'timing' in self.__dict__:
            return self.form(data, instance=self.timing,
                             initial={'edid': self.edid})
        else:
            return self.form(data, instance=self.edid)

    def _test_field_error(self, data, field, error_message):
        form = self._get_form(data)
        self.assertEqual(form.errors[field], [error_message])

    def _test_nulled_fields(self, data, fields):
        form = self._get_form(data)
        self.assertTrue(form.is_valid())

        for field in fields:
            self.assertEqual(form.cleaned_data[field], None)


### EDID Tests
class EDIDUpdateFormTestCase(FormTestMixin, EDIDTestMixin, TestCase):
    form = EDIDUpdateForm

    def setUp(self):
        super(EDIDUpdateFormTestCase, self).setUp()

        self.valid_data = EDID.objects.filter(pk=self.edid.pk) \
                                      .values(*EDIDUpdateForm._meta.fields)[0]

        self.mrl_fields = [
            'mrl_min_horizontal_rate', 'mrl_max_horizontal_rate',
            'mrl_min_vertical_rate', 'mrl_max_vertical_rate',
            'mrl_max_pixel_clock'
        ]
        self.mrl_secondary_GTF_fields = [
            'mrl_secondary_GTF_start_frequency', 'mrl_secondary_GTF_C',
            'mrl_secondary_GTF_M', 'mrl_secondary_GTF_K', 'mrl_secondary_GTF_J'
        ]

    def test_valid(self):
        # Test valid data
        form = self._get_form(self.valid_data)
        self.assertTrue(isinstance(form.instance, EDID))
        self.assertEqual(form.instance.pk, self.edid.pk)
        self.assertEqual(len(form.errors), 0)

    def test_week_of_manufacture(self):
        # Test negative value
        data = self.valid_data
        data['week_of_manufacture'] = -1
        self._test_field_error(
            data, 'week_of_manufacture',
            u'Ensure this value is greater than or equal to 0.'
        )

        # Test out of range value
        data = self.valid_data
        data['week_of_manufacture'] = 55
        self._test_field_error(
            data, 'week_of_manufacture',
            u'This field allowed range is 0-54 or 255.'
        )

        # Test over range value
        data = self.valid_data
        data['week_of_manufacture'] = 256
        self._test_field_error(
            data, 'week_of_manufacture',
            u'This field allowed range is 0-54 or 255.'
        )

    def test_mrl_max_pixel_clock(self):
        # Test an invalid value
        data = self.valid_data
        data['mrl_max_pixel_clock'] = 222
        self._test_field_error(
            data, 'mrl_max_pixel_clock',
            u'This field should be a multiple of 10MHz.'
        )

    def test_nulled_fields(self):
        # Test bdp_video_input = Analog
        data = self.valid_data
        data['bdp_video_input'] = EDID.bdp_video_input_analog
        data['bdp_signal_level_standard'] = \
            EDID.bdp_signal_level_standard_0700_0300
        self._test_nulled_fields(
            data, ['bdp_video_input_DFP_1']
        )

        # Test bdp_video_input = Digital
        data = self.valid_data
        data['bdp_video_input'] = EDID.bdp_video_input_digital
        self._test_nulled_fields(
            data, ['bdp_signal_level_standard', 'bdp_blank_to_black_setup',
                   'bdp_separate_syncs', 'bdp_composite_sync',
                   'bdp_sync_on_green_video', 'bdp_vsync_serration']
        )

        # Test monitor_range_limits = True
        data = self.valid_data
        data['monitor_range_limits'] = True
        data['mrl_secondary_GTF_curve_supported'] = False
        self._test_nulled_fields(data, self.mrl_secondary_GTF_fields)

        # Test monitor_range_limits = False
        data = self.valid_data
        data['monitor_range_limits'] = False
        self._test_nulled_fields(data, self.mrl_fields +
                                       ['mrl_secondary_GTF_curve_supported'] +
                                       self.mrl_secondary_GTF_fields
        )

    def test_required_field(self):
        # Test bdp_video_input = Analog
        data = self.valid_data
        data['bdp_video_input'] = EDID.bdp_video_input_analog
        data['bdp_signal_level_standard'] = None
        self._test_field_error(
            data, 'bdp_signal_level_standard', u'This field is required.'
        )

        # Test monitor_range_limits = True and
        # mrl_secondary_GTF_curve_supported = True
        data = self.valid_data
        data['monitor_range_limits'] = True
        data['mrl_secondary_GTF_curve_supported'] = True
        for field in self.mrl_fields + self.mrl_secondary_GTF_fields:
            data[field] = None
            self._test_field_error(data, field, u'This field is required.')

        # Test monitor_range_limits = True and
        # mrl_secondary_GTF_curve_supported = False
        data = self.valid_data
        data['monitor_range_limits'] = True
        data['mrl_secondary_GTF_curve_supported'] = False
        for field in self.mrl_fields:
            data[field] = None
            self._test_field_error(data, field, u'This field is required.')

    def test_save(self):
        data = self.valid_data
        data['status'] = EDID.STATUS_INITIALIZED

        form = self._get_form(data)
        form.save()

        self.assertEqual(self.edid.status, EDID.STATUS_EDITED)


class EDIDTextUploadFormTestCase(FormTestMixin, TestCase):
    def setUp(self):
        super(EDIDTextUploadFormTestCase, self).setUp()

        self.valid_data = {'text': 'Something', 'text_type': 'hex'}

    def _get_form(self, data):
        return EDIDTextUploadForm(data)

    def test_text_empty(self):
        # Test an invalid value
        data = self.valid_data
        data['text'] = ''
        self._test_field_error(
            data, 'text',
            u'This field is required.'
        )

    def test_text_type_empty(self):
        # Test an invalid value
        data = self.valid_data
        data['text_type'] = ''
        self._test_field_error(
            data, 'text_type',
            u'This field is required.'
        )

    def test_text_type_invalid(self):
        # Test an invalid value
        data = self.valid_data
        data['text_type'] = 'invalid'
        self._test_field_error(
            data, 'text_type',
            u'Text type is invalid.'
        )


### Timing Tests
class StandardTimingFormTestCase(FormTestMixin, EDIDTestMixin, TestCase):
    form = StandardTimingForm

    def setUp(self):
        super(StandardTimingFormTestCase, self).setUp()

        self.timing = self.edid.standardtiming_set.get(identification=1)
        self.valid_data = self.edid.standardtiming_set \
                                   .filter(identification=1) \
                                   .values(*StandardTimingForm._meta.fields)[0]

    def test_valid(self):
        # Test valid data
        form = self._get_form(self.valid_data)
        self.assertTrue(isinstance(form.instance, StandardTiming))
        self.assertEqual(form.instance.pk, self.timing.pk)
        self.assertEqual(len(form.errors), 0)

    def test_horizontal_active(self):
        # Test an invalid value
        data = self.valid_data
        data['horizontal_active'] = 258
        self._test_field_error(
            data, 'horizontal_active',
            u'This field should be a multiple of 8.'
        )

    def test_aspect_ratio(self):
        old_versions = [EDID.VERSION_1_0, EDID.VERSION_1_1, EDID.VERSION_1_2]
        new_versions = [EDID.VERSION_1_3, EDID.VERSION_1_4, EDID.VERSION_2_0]

        for version in old_versions + new_versions:
            # Test an invalid value
            self.edid.version = version
            data = self.valid_data

            if version in old_versions:
                data['aspect_ratio'] = StandardTiming.ASPECT_RATIO_16_10
                self._test_field_error(
                    data, 'aspect_ratio',
                    u'16:10 aspect ratio is not allowed prior to EDID 1.3.'
                )
            elif version in new_versions:
                data['aspect_ratio'] = StandardTiming.ASPECT_RATIO_1_1
                self._test_field_error(
                    data, 'aspect_ratio',
                    u'1:1 aspect ratio is not allowed with EDID 1.3 or newer.'
                )


class DetailedTimingFormTestCase(FormTestMixin, EDIDTestMixin, TestCase):
    form = DetailedTimingForm

    def setUp(self):
        super(DetailedTimingFormTestCase, self).setUp()

        self.timing = self.edid.detailedtiming_set.get(identification=1)
        self.valid_data = self.edid.detailedtiming_set \
                                   .filter(identification=1) \
                                   .values(*DetailedTimingForm._meta.fields)[0]

    def test_valid(self):
        # Test valid data
        form = self._get_form(self.valid_data)
        self.assertTrue(isinstance(form.instance, DetailedTiming))
        self.assertEqual(form.instance.pk, self.timing.pk)
        self.assertEqual(len(form.errors), 0)

    def test_pixel_clock(self):
        # Test an invalid value
        data = self.valid_data
        data['pixel_clock'] = 222
        self._test_field_error(
            data, 'pixel_clock',
            u'This field should be a multiple of 10.'
        )

    def test_nulled_fields(self):
        # Test flags_sync_scheme = Analog_Composite
        data = self.valid_data
        data['flags_sync_scheme'] = DetailedTiming.Sync_Scheme.Analog_Composite
        self._test_nulled_fields(
            data, ['flags_horizontal_polarity', 'flags_vertical_polarity',
                   'flags_composite_polarity']
        )

        # Test flags_sync_scheme = Bipolar_Analog_Composite
        data = self.valid_data
        data['flags_sync_scheme'] = \
            DetailedTiming.Sync_Scheme.Bipolar_Analog_Composite
        self._test_nulled_fields(
            data, ['flags_horizontal_polarity', 'flags_vertical_polarity',
                   'flags_composite_polarity']
        )

        # Test flags_sync_scheme = Digital_Composite
        data = self.valid_data
        data['flags_sync_scheme'] = DetailedTiming.Sync_Scheme.Digital_Composite
        self._test_nulled_fields(
            data, ['flags_horizontal_polarity', 'flags_vertical_polarity',
                   'flags_sync_on_RGB']
        )

        # Test flags_sync_scheme = Digital_Separate
        data = self.valid_data
        data['flags_sync_scheme'] = DetailedTiming.Sync_Scheme.Digital_Separate
        self._test_nulled_fields(
            data, ['flags_serrate', 'flags_composite_polarity',
                   'flags_sync_on_RGB']
        )


class CommentFormTestCase(FormTestMixin, EDIDTestMixin, TestCase):
    def setUp(self):
        super(CommentFormTestCase, self).setUp()

        self.valid_data = {'EDID': self.edid.pk,
                           'parent': '',
                           'content': 'This is a test.'}

    def _get_form(self, data):
        return CommentForm(data, initial={'edid': self.edid})

    def test_valid(self):
        # Test valid data
        form = self._get_form(self.valid_data)
        self.assertTrue(isinstance(form.instance, Comment))
        self.assertEqual(len(form.errors), 0)

    def test_parent(self):
        # Create nested comments up to the limit
        user = self._login()
        comment_1 = Comment(EDID=self.edid, user=user, level=0,
                            content='').save()
        comment_2 = Comment(EDID=self.edid, user=user, level=1,
                            parent=comment_1, content='').save()
        comment_3 = Comment(EDID=self.edid, user=user, level=2,
                            parent=comment_2, content='').save()

        # Try to submit comment with over-limit nesting
        data = self.valid_data
        data['parent'] = 3

        self._test_field_error(
            data, 'parent',
            u'Comment nesting limit exceeded.'
        )
