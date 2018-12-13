from django.core.exceptions import ValidationError
from django.test import TestCase

from edid_parser.edid_parser import EDIDParser

from frontend.django_tests.base import EDIDTestMixin
from frontend.models import EDID, Manufacturer, StandardTiming, Comment


### EDID Tests
class EDIDTestCase(EDIDTestMixin, TestCase):
    def test_manufacturer(self):
        manufacturer = Manufacturer.objects.get(name_id='TSB')

        self.assertEqual(self.edid.manufacturer, manufacturer)

    def test_status(self):
        self.assertEqual(self.edid.status, EDID.STATUS_TIMINGS_ADDED)

    def test_version(self):
        self.assertEqual(self.edid.version, EDID.VERSION_1_3)

    def test_private(self):
        # Check we have 1 non-private EDID
        self.assertEqual(EDID.objects.count(), 1)
        # Change status to private
        EDID.objects.filter(pk=1).update(status=EDID.STATUS_PRIVATE)
        # Check we have 0 non-private EDID
        self.assertEqual(EDID.objects.count(), 0)

    def test_est_timings(self):
        est_timings = self.edid.get_est_timings()

        # Check we have 3 established timings
        self.assertEqual(
            len([timing for timing in est_timings if timing['supported']]),
            3
        )

    def test_timings(self):
        self.assertEqual(self.edid.standardtiming_set.count(), 2)
        self.assertEqual(self.edid.detailedtiming_set.count(), 2)

    def test_get_comments(self):
        # Create nested comments
        user = self._login()
        comment_1 = Comment(EDID=self.edid, user=user, level=0, content='')
        comment_1.save()

        comment_2 = Comment(EDID=self.edid, user=user, level=1,
                            parent=comment_1, content='')
        comment_2.save()

        comment_3 = Comment(EDID=self.edid, user=user, level=0, content='')
        comment_3.save()

        comment_4 = Comment(EDID=self.edid, user=user, level=2,
                            parent=comment_2, content='')
        comment_4.save()

        # Get all comments for EDID
        comments = self.edid.get_comments()

        # Check comments are ordered
        self.assertEqual(
            comments,
            [
                {'comment': comment_1,
                 'subcomments': [
                     {'comment': comment_2,
                      'subcomments': [{'comment': comment_4}]}
                 ]},
                {'comment': comment_3}
            ]
        )

    def test_get_maximum_resolution(self):
        max_res = EDID(est_timings_640_480_60=True,
                       est_timings_800_600_56=True).get_maximum_resolution()

        self.assertEqual(max_res['horizontal_active'], 800)
        self.assertEqual(max_res['vertical_active'], 600)
        self.assertEqual(max_res['refresh_rate'], 56)

        max_res = EDID(est_timings_800_600_56=True,
                       est_timings_800_600_72=True,
                       est_timings_800_600_75=True).get_maximum_resolution()

        self.assertEqual(max_res['horizontal_active'], 800)
        self.assertEqual(max_res['vertical_active'], 600)
        self.assertEqual(max_res['refresh_rate'], 75)

        max_res = EDID(est_timings_640_480_72=True,
                       est_timings_640_480_75=True,
                       est_timings_800_600_60=True).get_maximum_resolution()

        self.assertEqual(max_res['horizontal_active'], 800)
        self.assertEqual(max_res['vertical_active'], 600)
        self.assertEqual(max_res['refresh_rate'], 60)


class EDIDParsingTestCase(TestCase):
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
        self.edid_data = EDIDParser(self.edid_binary).data

    def _process_edid(self, edid_data):
        edid_object = EDID.create(file_base64='', edid_data=edid_data)
        # Save the entry
        edid_object.save()
        # Add timings
        edid_object.populate_timings_from_parser(edid_data)
        # Save the updated entry
        edid_object.save()

        return edid_object

    def test_version_revision_valid(self):
        """
        Test all supported EDID versions and revisions.
        """

        edid_data = self.edid_data

        for version in [(1, 0, EDID.VERSION_1_0), (1, 1, EDID.VERSION_1_1),
                        (1, 2, EDID.VERSION_1_2), (1, 3, EDID.VERSION_1_3),
                        (1, 4, EDID.VERSION_1_4), (2, 0, EDID.VERSION_2_0)]:
            edid_data['EDID_version'] = version[0]
            edid_data['EDID_revision'] = version[1]

            edid = self._process_edid(edid_data)

            # Check for correct version
            self.assertEqual(edid.version, version[2])

    def test_version_revision_invalid(self):
        """
        Test unsupported EDID versions and revisions and check for exception.
        """

        edid_data = self.edid_data

        for version in [(0, 1), (1, 5), (2, 1)]:
            edid_data['EDID_version'] = version[0]
            edid_data['EDID_revision'] = version[1]

            with self.assertRaises(ValidationError) as cm:
                self._process_edid(edid_data)

            # Check for exception
            self.assertEqual(cm.exception.messages[0],
                             'Invalid EDID version and revision.')

    def test_bdp_signal_level_standard_valid(self):
        """
        Test all supported signal level standard.
        """

        # Change video input to Analog
        edid_data = self.edid_data
        edid_data['Basic_display_parameters']['Video_Input'] = 0
        edid_data['Basic_display_parameters']['Blank-to-black_setup'] = False
        edid_data['Basic_display_parameters']['Separate_syncs'] = False
        edid_data['Basic_display_parameters']['Composite_sync'] = False
        edid_data['Basic_display_parameters']['Sync_on_green_video'] = False
        edid_data['Basic_display_parameters']['Vsync_serration'] = False

        for standard in [
            ((0.700, 0.300), EDID.bdp_signal_level_std_0700_0300),
            ((0.714, 0.286), EDID.bdp_signal_level_std_0714_0286),
            ((1.000, 0.400), EDID.bdp_signal_level_std_1000_0400),
            ((0.700, 0.000), EDID.bdp_signal_level_std_0700_0000)
        ]:
            edid_data['Basic_display_parameters']['Signal_Level_Standard'] = \
                standard[0]

            edid = self._process_edid(edid_data)

            # Check for correct standard
            self.assertEqual(edid.bdp_signal_level_standard, standard[1])

    def test_bdp_signal_level_standard_invalid(self):
        """
        Test unsupported signal levels.
        """

        # Change video input to Analog
        edid_data = self.edid_data
        edid_data['Basic_display_parameters']['Video_Input'] = 0
        edid_data['Basic_display_parameters']['Blank-to-black_setup'] = False
        edid_data['Basic_display_parameters']['Separate_syncs'] = False
        edid_data['Basic_display_parameters']['Composite_sync'] = False
        edid_data['Basic_display_parameters']['Sync_on_green_video'] = False
        edid_data['Basic_display_parameters']['Vsync_serration'] = False

        for standard in [(0.000, 0.000), (0.300, 0.700), (2.000, 1.000)]:
            edid_data['Basic_display_parameters']['Signal_Level_Standard'] = \
                standard[0]

            with self.assertRaises(ValidationError) as cm:
                self._process_edid(edid_data)

            # Check for exception
            self.assertEqual(
                cm.exception.messages[0],
                'Invalid signal level standard can not be parsed.'
            )

    def test_aspect_ratio_valid(self):
        """
        Test all supported image aspect ratio.
        """

        edid_data = self.edid_data

        for aspect_ratio in [((1, 1), StandardTiming.ASPECT_RATIO_1_1),
                             ((16, 10), StandardTiming.ASPECT_RATIO_16_10),
                             ((4, 3), StandardTiming.ASPECT_RATIO_4_3),
                             ((5, 4), StandardTiming.ASPECT_RATIO_5_4),
                             ((16, 9), StandardTiming.ASPECT_RATIO_16_9)]:
            edid_data['Standard_Timings']['Identification_1'][
                'Image_aspect_ratio'] = aspect_ratio[0]

            edid = self._process_edid(edid_data)

            # Check for correct version
            timing = StandardTiming.objects.get(EDID=edid,
                                                identification=1)
            self.assertEqual(timing.aspect_ratio, aspect_ratio[1])

    def test_aspect_ratio_invalid(self):
        """
        Test unsupported image aspect ratio and check for exception.
        """

        edid_data = self.edid_data

        for aspect_ratio in [(3, 2), (5, 3), (4, 1)]:
            edid_data['Standard_Timings']['Identification_1'][
                'Image_aspect_ratio'] = aspect_ratio

            with self.assertRaises(ValidationError) as cm:
                self._process_edid(edid_data)

            # Check for exception
            self.assertEqual(cm.exception.messages[0],
                             'Invalid aspect ratio can not be parsed.')

    def test_mrl_secondary_GTF_curve(self):
        """
        Test monitor range limits secondary GTF curve.
        """

        edid_data = self.edid_data

        # Store monitor range limits in shorter variable temporarily
        mrl = edid_data['Descriptors']['Monitor_Range_Limits_Descriptor']

        # Enable secondary GTF curve
        mrl['Secondary_GTF_curve_supported'] = True
        mrl['Secondary_GTF'] = {'start_frequency': 64,
                                'C': 64,
                                'M': 64,
                                'K': 64,
                                'J': 64}

        # Inject monitor range limits back to EDID data
        edid_data['Descriptors']['Monitor_Range_Limits_Descriptor'] = mrl

        edid = self._process_edid(edid_data)

        # Check stored values
        self.assertTrue(edid.monitor_range_limits)
        self.assertTrue(edid.mrl_secondary_gtf_curve_support)
        self.assertEqual(edid.mrl_secondary_gtf_start_freq, 64)
        self.assertEqual(edid.mrl_secondary_gtf_c, 64)
        self.assertEqual(edid.mrl_secondary_gtf_m, 64)
        self.assertEqual(edid.mrl_secondary_gtf_k, 64)
        self.assertEqual(edid.mrl_secondary_gtf_j, 64)


class DetailedTimingParsingTestCase(TestCase):
    def setUp(self):
        Manufacturer.objects.bulk_create([
            Manufacturer(name_id='TSB', name='Toshiba'),
            Manufacturer(name_id='UNK', name='Unknown'),
        ])

    def _create_edid(self, flags, checksum):
        edid_binary = [0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x52,
                       0x62, 0x06, 0x02, 0x01, 0x01, 0x01, 0x01, 0xFF, 0x13,
                       0x01, 0x03, 0x80, 0x59, 0x32, 0x78, 0x0A, 0xF0, 0x9D,
                       0xA3, 0x55, 0x49, 0x9B, 0x26, 0x0F, 0x47, 0x4A, 0x21,
                       0x08, 0x00, 0x81, 0x80, 0x8B, 0xC0, 0x01, 0x01, 0x01,
                       0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01,
                       0x02, 0x3A, 0x80, 0x18, 0x71, 0x38, 0x2D, 0x40, 0x58,
                       0x2C, 0x45, 0x00, 0x76, 0xF2, 0x31, 0x00, 0x00, 0x1E,
                       0x66, 0x21, 0x50, 0xB0, 0x51, 0x00, 0x1B, 0x30, 0x40,
                       0x70, 0x36, 0x00, 0x76, 0xF2, 0x31, 0x00, 0x00, 0x1E,
                       0x00, 0x00, 0x00, 0xFC, 0x00, 0x54, 0x4F, 0x53, 0x48,
                       0x49, 0x42, 0x41, 0x2D, 0x54, 0x56, 0x0A, 0x20, 0x20,
                       0x00, 0x00, 0x00, 0xFD, 0x00, 0x17, 0x3D, 0x0F, 0x44,
                       0x0F, 0x00, 0x0A, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20,
                       0x01, 0x24]

        # Change flags and checksum
        edid_binary[71] = flags
        edid_binary[127] = checksum

        # Convert to string
        edid_binary = ''.join([chr(x) for x in edid_binary])

        edid_data = EDIDParser(edid_binary).data

        edid_object = EDID.create(file_base64='', edid_data=edid_data)
        # Save the entry
        edid_object.save()
        # Add timings
        edid_object.populate_timings_from_parser(edid_data)
        # Save the updated entry
        edid_object.save()

        return edid_object

    def test_flags_sync_scheme_analog_composite(self):
        """
        Test detailed timing sync scheme flag = analog composite.
        """

        edid = self._create_edid(0b00000110, 60)
        timing = edid.detailedtiming_set.get(identification=1)

        # Check for correct flags
        self.assertEqual(timing.flags_sync_scheme,
                         timing.Sync_Scheme.Analog_Composite)
        self.assertEqual(timing.flags_vertical_polarity, None)
        self.assertEqual(timing.flags_horizontal_polarity, None)
        self.assertEqual(timing.flags_serrate, True)
        self.assertEqual(timing.flags_composite_polarity, None)
        self.assertEqual(timing.flags_sync_on_rgb, True)

    def test_flags_sync_scheme_bipolar_analog_composite(self):
        """
        Test detailed timing sync scheme flag = bipolar analog composite.
        """

        edid = self._create_edid(0b00001110, 52)
        timing = edid.detailedtiming_set.get(identification=1)

        # Check for correct flags
        self.assertEqual(timing.flags_sync_scheme,
                         timing.Sync_Scheme.Bipolar_Analog_Composite)
        self.assertEqual(timing.flags_vertical_polarity, None)
        self.assertEqual(timing.flags_horizontal_polarity, None)
        self.assertEqual(timing.flags_serrate, True)
        self.assertEqual(timing.flags_composite_polarity, None)
        self.assertEqual(timing.flags_sync_on_rgb, True)

    def test_flags_sync_scheme_digital_composite(self):
        """
        Test detailed timing sync scheme flag = digital composite.
        """

        edid = self._create_edid(0b00010110, 44)
        timing = edid.detailedtiming_set.get(identification=1)

        # Check for correct flags
        self.assertEqual(timing.flags_sync_scheme,
                         timing.Sync_Scheme.Digital_Composite)
        self.assertEqual(timing.flags_vertical_polarity, None)
        self.assertEqual(timing.flags_horizontal_polarity, None)
        self.assertEqual(timing.flags_serrate, True)
        self.assertEqual(timing.flags_composite_polarity, True)
        self.assertEqual(timing.flags_sync_on_rgb, None)

    def test_flags_sync_scheme_digital_separate(self):
        """
        Test detailed timing sync scheme flag = digital separate.
        """

        edid = self._create_edid(0b00011110, 36)
        timing = edid.detailedtiming_set.get(identification=1)

        # Check for correct flags
        self.assertEqual(timing.flags_sync_scheme,
                         timing.Sync_Scheme.Digital_Separate)
        self.assertEqual(timing.flags_vertical_polarity, True)
        self.assertEqual(timing.flags_horizontal_polarity, True)
        self.assertEqual(timing.flags_serrate, None)
        self.assertEqual(timing.flags_composite_polarity, None)
        self.assertEqual(timing.flags_sync_on_rgb, None)


### Timing Tests
class TimingTestMixin(object):
    def setUp(self):
        super(TimingTestMixin, self).setUp()

        self.timings_set = self._get_timings_set()

    def test_delete_timing(self):
        # Check we have two standard timings
        self.assertEqual(self.timings_set.count(), 2)
        # Get first timing
        timing_1 = self.timings_set.get(EDID=self.edid, identification=1)
        # Get second timing pk
        timing_2_pk = self.timings_set.get(EDID=self.edid, identification=2).pk
        # Delete first timing
        timing_1.delete()
        # Check we have 1 standard timings
        self.assertEqual(self.timings_set.count(), 1)
        # Get second timing by its pk
        timing_2 = self.timings_set.get(pk=timing_2_pk)
        # Check timing_2 have been moved up
        self.assertEqual(timing_2.identification, 1)


class StandardTimingTestCase(TimingTestMixin, EDIDTestMixin, TestCase):
    def _get_timings_set(self):
        return self.edid.standardtiming_set


class DetailedTimingTestCase(TimingTestMixin, EDIDTestMixin, TestCase):
    def _get_timings_set(self):
        return self.edid.detailedtiming_set


### Comment Tests
class CommentTestCase(EDIDTestMixin, TestCase):
    def test_max_thread_level(self):
        """
        Test Comment.get_max_thread_level() method.
        """

        # Create Comment instance
        user = self._login()
        comment = Comment(EDID=self.edid, user=user, level=0, content='')

        self.assertEqual(comment.get_max_thread_level(), 2)

        with self.settings(EDID_COMMENT_MAX_THREAD_LEVEL=5):
            self.assertEqual(comment.get_max_thread_level(), 5)

    def test_unicode(self):
        """
        Test Comment.__unicode__() method.
        """

        # Create Comment instance
        user = self._login()
        comment = Comment(EDID=self.edid, user=user, level=0, content='')
        comment.save()

        self.assertEqual(
            unicode(comment), "%s: %s" % (comment.pk, comment.content[:100])
        )
