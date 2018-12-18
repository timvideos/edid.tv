# E1002: Use of super on an old style class
# R0201: Method could be a function (no-self-use)
# R0902: Too many instance attributes
# R0912: Too many branches
# R0915: Too many statements
# W0201: Attribute 'xxxx' defined outside __init__
# pylint: disable-msg=E1002,R0201,R0902,R0912,R0915,W0201
from __future__ import division

import re
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.urlresolvers import reverse

from edid_parser.edid_parser import (DisplayType, DisplayStereoMode,
                                     TimingSyncScheme,
                                     CVTSupportDefinitionPreferredAspectRatio,
                                     ColorBitDepth, DigitalVideoInterface)


class Manufacturer(models.Model):
    # Full name
    name = models.CharField(max_length=255, blank=True)
    # ID, 3 characters
    name_id = models.CharField(max_length=3)

    class Meta(object):
        ordering = ['name_id']

    def __unicode__(self):
        return "%s: %s" % (self.name_id, self.name)


class EDIDPublicManager(models.Manager):
    """
    A manager to filter private EDIDs from public interface.
    """

    def get_query_set(self):
        return super(EDIDPublicManager, self).get_query_set() \
            .exclude(status=EDID.STATUS_PRIVATE)


class EDID(models.Model):
    objects = EDIDPublicManager()
    all_objects = models.Manager()

    manufacturer = models.ForeignKey(Manufacturer)

    # Initialized and basic data auto-added
    STATUS_INITIALIZED = 0
    # Standard and detailed timings auto-added
    STATUS_TIMINGS_ADDED = 1
    # Manually edited by users
    STATUS_EDITED = 2
    # Private, hidden from public
    STATUS_PRIVATE = 3
    STATUS_CHOICES = ((STATUS_INITIALIZED, 'Initialized'),
                      (STATUS_TIMINGS_ADDED, 'Timings Added'),
                      (STATUS_EDITED, 'Edited'),
                      (STATUS_PRIVATE, 'Private'))
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES,
                                              default=STATUS_INITIALIZED)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)

    # Binary file encoded in base64
    file_base64 = models.TextField(editable=False)

    ### Header
    # ID Product Code
    manufacturer_product_code = models.CharField(max_length=4, blank=True)
    # ID Serial Number, 32-bit
    manufacturer_serial_number = models.PositiveIntegerField(blank=True,
                                                             null=True)
    # Week of manufacture, 1-54, 0==Unknown
    week_of_manufacture = models.PositiveSmallIntegerField(blank=True, null=True)
    # Year of manufacture, 1990-2245
    year_of_manufacture = models.PositiveSmallIntegerField(blank=True, null=True)
    # Model year, 1990-2245
    model_year = models.PositiveSmallIntegerField(blank=True, null=True)

    # EDID version and revision
    VERSION_1_0 = 0
    VERSION_1_1 = 1
    VERSION_1_2 = 2
    VERSION_1_3 = 3
    VERSION_1_4 = 4
    VERSION_2_0 = 5
    VERSION_CHOICES = (
        (VERSION_1_0, '1.0'),
        (VERSION_1_1, '1.1'),
        (VERSION_1_2, '1.2'),
        (VERSION_1_3, '1.3'),
        (VERSION_1_4, '1.4'),
        (VERSION_2_0, '2.0'),
    )
    version = models.PositiveSmallIntegerField(choices=VERSION_CHOICES)

    ### ASCII Text Descriptors
    # Monitor Name, from Monitor Descriptor Description (type 0xFC)
    monitor_name = models.CharField(max_length=13, blank=True)
    # Monitor Serial Number, from Monitor Descriptor Description (type 0xFF)
    monitor_serial_number = models.CharField(max_length=13, blank=True)
    # Monitor Data String, from Monitor Descriptor Description (type 0xFE)
    monitor_data_string = models.CharField(max_length=13, blank=True)

    ### bdp=Basic display parameters
    bdp_video_input_analog = 0
    bdp_video_input_digital = 1
    BDP_VIDEO_INPUT_CHOICES = ((bdp_video_input_analog, 'Analog'),
                               (bdp_video_input_digital, 'Digital'))
    bdp_video_input = models.PositiveSmallIntegerField(
        'video input',
        choices=BDP_VIDEO_INPUT_CHOICES,
        default=bdp_video_input_analog
    )

    # Analog Input
    bdp_signal_level_std_0700_0300 = 0
    bdp_signal_level_std_0714_0286 = 1
    bdp_signal_level_std_1000_0400 = 2
    bdp_signal_level_std_0700_0000 = 3
    BDP_SIGNAL_LVL_STD_CHOICE = (
        (bdp_signal_level_std_0700_0300, '(0.700, 0.300)'),
        (bdp_signal_level_std_0714_0286, '(0.714, 0.286)'),
        (bdp_signal_level_std_1000_0400, '(1.000, 0.400)'),
        (bdp_signal_level_std_0700_0000, '(0.700, 0.000)'),
    )
    bdp_signal_level_standard = models.PositiveSmallIntegerField(
        'signal level standard', choices=BDP_SIGNAL_LVL_STD_CHOICE,
        blank=True, null=True)

    bdp_blank_to_black_setup = models.NullBooleanField(
        'blank-to-black setup level')
    bdp_separate_syncs = models.NullBooleanField('separate sync')
    bdp_composite_sync = models.NullBooleanField(
        'composite sync signal on horizontal')
    bdp_sync_on_green_video = models.NullBooleanField(
        'composite sync signal on green video')
    bdp_vsync_serration = models.NullBooleanField(
        'serration on the vertical sync')

    # Digital Input
    BDP_COLOR_BIT_DEPTH_CHOICE = (
        (ColorBitDepth.Undefined, 'Undefined'),
        (ColorBitDepth.Depth_6_bit, '6 bit'),
        (ColorBitDepth.Depth_8_bit, '8 bit'),
        (ColorBitDepth.Depth_10_bit, '10 bit'),
        (ColorBitDepth.Depth_12_bit, '12 bit'),
        (ColorBitDepth.Depth_14_bit, '14 bit'),
        (ColorBitDepth.Depth_16_bit, '16 bit'),
    )
    bdp_color_bit_depth = models.PositiveSmallIntegerField(
        'color bit depth', choices=BDP_COLOR_BIT_DEPTH_CHOICE, blank=True,
        null=True)

    BDP_DIGITAL_VIDEO_INTERFACE_CHOICE = (
        (DigitalVideoInterface.Undefined, 'Undefined'),
        (DigitalVideoInterface.DVI, 'DVI'),
        (DigitalVideoInterface.HDMI_A, 'HDMI-A'),
        (DigitalVideoInterface.HDMI_B, 'HDMI-B'),
        (DigitalVideoInterface.MDDI, 'MDDI'),
        (DigitalVideoInterface.DisplayPort, 'DisplayPort'),
    )
    bdp_digital_video_interface = models.PositiveSmallIntegerField(
        'digital video interface', choices=BDP_DIGITAL_VIDEO_INTERFACE_CHOICE,
        blank=True, null=True)

    bdp_video_input_dfp_1 = models.NullBooleanField('digital flat panel 1.x')

    BDP_ASPECT_RATIO_CHOICE = (
        (Decimal('1.78'), '16:9'),
        (Decimal('0.56'), '9:16'),
        (Decimal('1.60'), '16:10'),
        (Decimal('0.62'), '10:16'),
        (Decimal('1.33'), '4:3'),
        (Decimal('0.75'), '3:4'),
        (Decimal('1.25'), '5:4'),
        (Decimal('0.80'), '4:5'),
    )
    bdp_aspect_ratio = models.DecimalField('aspect ratio', max_digits=3,
       decimal_places=2, blank=True, null=True, choices=BDP_ASPECT_RATIO_CHOICE)
    bdp_horizontal_screen_size = models.PositiveSmallIntegerField(
        'horizontal screen size', blank=True, null=True)
    bdp_vertical_screen_size = models.PositiveSmallIntegerField(
        'vertical screen size', blank=True, null=True)

    bdp_max_horizontal_image_size = models.PositiveSmallIntegerField(
        'maximum horizontal image size', blank=True, null=True)
    bdp_max_vertical_image_size = models.PositiveSmallIntegerField(
        'maximum vertical image size', blank=True, null=True)
    bdp_display_gamma = models.DecimalField('display gamma', max_digits=3,
                                            decimal_places=2, blank=True,
                                            null=True)

    BDP_FEATURE_DISPLAY_TYPE_CHOICE = (
        (DisplayType.Monochrome, 'Monochrome or grayscale display'),
        (DisplayType.RGB, 'RGB color display'),
        (DisplayType.Non_RGB, 'Non-RGB multicolor display'),
        (DisplayType.Undefined, 'Undefined'),
    )

    bdp_feature_standby = models.BooleanField('standby mode')
    bdp_feature_suspend = models.BooleanField('suspend mode')
    bdp_feature_active_off = models.BooleanField(
        'active off/very low power mode')
    bdp_feature_display_type = models.PositiveSmallIntegerField(
        'display color type', choices=BDP_FEATURE_DISPLAY_TYPE_CHOICE,
        blank=True, null=True)
    bdp_feature_standard_srgb = models.BooleanField('standard sRGB')
    bdp_feature_pref_timing_mode = models.BooleanField(
        'preferred timing mode')
    bdp_feature_default_gtf = models.NullBooleanField('default GTF')

    bdp_feature_rgb444 = models.NullBooleanField('RGB 4:4:4 supported')
    bdp_feature_ycrcb444 = models.NullBooleanField('YCrCb 4:4:4 supported')
    bdp_feature_ycrcb422 = models.NullBooleanField('YCrCb 4:2:2 supported')
    bdp_feature_continuous_frequency = models.NullBooleanField(
        'continuous frequency')

    ### chr=Chromaticity
    chr_red_x = models.DecimalField(
        'red x', max_digits=4, decimal_places=3)
    chr_red_y = models.DecimalField(
        'red y', max_digits=4, decimal_places=3)
    chr_green_x = models.DecimalField(
        'green x', max_digits=4, decimal_places=3)
    chr_green_y = models.DecimalField(
        'green y', max_digits=4, decimal_places=3)
    chr_blue_x = models.DecimalField(
        'blue x', max_digits=4, decimal_places=3)
    chr_blue_y = models.DecimalField(
        'blue y', max_digits=4, decimal_places=3)
    chr_white_x = models.DecimalField(
        'white x', max_digits=4, decimal_places=3)
    chr_white_y = models.DecimalField(
        'white y', max_digits=4, decimal_places=3)

    ### est_timings=Established Timings
    est_timings_720_400_70 = models.BooleanField('720x400@70Hz')
    est_timings_720_400_88 = models.BooleanField('720x400@88Hz')
    est_timings_640_480_60 = models.BooleanField('640x480@60Hz')
    est_timings_640_480_67 = models.BooleanField('640x480@67Hz')
    est_timings_640_480_72 = models.BooleanField('640x480@72Hz')
    est_timings_640_480_75 = models.BooleanField('640x480@75Hz')
    est_timings_800_600_56 = models.BooleanField('800x600@56Hz')
    est_timings_800_600_60 = models.BooleanField('800x600@60Hz')
    est_timings_800_600_72 = models.BooleanField('800x600@72Hz')
    est_timings_800_600_75 = models.BooleanField('800x600@75Hz')
    est_timings_832_624_75 = models.BooleanField('832x624@75Hz')
    est_timings_1024_768_87 = models.BooleanField('1024x768@87Hz')
    est_timings_1024_768_60 = models.BooleanField('1024x768@60Hz')
    est_timings_1024_768_70 = models.BooleanField('1024x768@70Hz')
    est_timings_1024_768_75 = models.BooleanField('1024x768@75Hz')
    est_timings_1280_1024_75 = models.BooleanField('1280x1024@75Hz')

    ### mrl=Monitor range limits, optional starting from v1.1
    monitor_range_limits = models.BooleanField('monitor range limits')

    # in kHz
    mrl_min_horizontal_rate = models.PositiveSmallIntegerField(
        'minimum horizontal rate', blank=True, null=True)
    mrl_max_horizontal_rate = models.PositiveSmallIntegerField(
        'maximum horizontal rate', blank=True, null=True)

    # in Hz
    mrl_min_vertical_rate = models.PositiveSmallIntegerField(
        'minimum vertical rate', blank=True, null=True)
    mrl_max_vertical_rate = models.PositiveSmallIntegerField(
        'maximum vertical rate', blank=True, null=True)

    # in MHz (0.25 MHz steps, max 256 MHz)
    mrl_max_pixel_clock = models.DecimalField(
        'maximum supported pixel clock', max_digits=5, decimal_places=2, blank=True, null=True)

    mrl_secondary_gtf_curve_support = models.NullBooleanField(
        'secondary GTF curve')

    # in kHz
    mrl_secondary_gtf_start_freq = models.PositiveSmallIntegerField(
        'start frequency', blank=True, null=True)
    mrl_secondary_gtf_c = models.PositiveSmallIntegerField(
        'C', blank=True, null=True)
    mrl_secondary_gtf_m = models.PositiveSmallIntegerField(
        'M', blank=True, null=True)
    mrl_secondary_gtf_k = models.PositiveSmallIntegerField(
        'K', blank=True, null=True)
    mrl_secondary_gtf_j = models.PositiveSmallIntegerField(
        'J', blank=True, null=True)

    mrl_coordinated_video_timing_support = models.NullBooleanField(
        'coordinated video timing support')
    mrl_cvt_max_active_pixels_per_line = models.PositiveIntegerField(
        'maximum active pixels per line', blank=True, null=True)
    mrl_cvt_aspect_ratio_4_3_supported = models.NullBooleanField('4:3')
    mrl_cvt_aspect_ratio_16_9_supported = models.NullBooleanField('16:9')
    mrl_cvt_aspect_ratio_16_10_supported = models.NullBooleanField('16:10')
    mrl_cvt_aspect_ratio_5_4_supported = models.NullBooleanField('5:4')
    mrl_cvt_aspect_ratio_15_9_supported = models.NullBooleanField('15:9')

    Preferred_Aspect_Ratio = CVTSupportDefinitionPreferredAspectRatio
    PREFERRED_ASPECT_RATIO_CHOICES = (
        (Preferred_Aspect_Ratio.AR_4_3, '4:3'),
        (Preferred_Aspect_Ratio.AR_16_9, '16:9'),
        (Preferred_Aspect_Ratio.AR_16_10, '16:10'),
        (Preferred_Aspect_Ratio.AR_5_4, '5:4'),
        (Preferred_Aspect_Ratio.AR_15_9, '15:9'),
    )
    mrl_cvt_preferred_aspect_ratio = models.PositiveSmallIntegerField(
        'preferred aspect ratio',
        choices=PREFERRED_ASPECT_RATIO_CHOICES,
        blank=True,
        null=True
    )

    mrl_cvt_standard_blanking_supported = models.NullBooleanField('CVT standard blanking supported')
    mrl_cvt_reduced_blanking_supported = models.NullBooleanField('CVT reduced blanking supported')
    mrl_cvt_horizontal_shrink_supported = models.NullBooleanField('horizontal shrink supported')
    mrl_cvt_horizontal_stretch_supported = models.NullBooleanField('horizontal stretch supported')
    mrl_cvt_vertical_shrink_supported = models.NullBooleanField('vertical shrink supported')
    mrl_cvt_vertical_stretch_supported = models.NullBooleanField('vertical stretch supported')

    # in Hz
    mrl_cvt_preferred_vertical_refresh_rate = models.PositiveSmallIntegerField(
        'preferred vertical refresh rate', blank=True, null=True)

    @classmethod
    def create(cls, file_base64, edid_data):
        edid = cls(file_base64=file_base64)

        # Add basic data
        edid._populate_from_edid_parser(edid_data)

        return edid

    def _populate_from_edid_parser(self, edid):
        ### Header
        try:
            self.manufacturer = Manufacturer.objects.get(
                name_id=edid['ID_Manufacturer_Name'])
        except ObjectDoesNotExist:
            # UNK is reserved for unknown manufacturer
            self.manufacturer = Manufacturer.objects.get(name_id='UNK')

        self.manufacturer_product_code = edid['ID_Product_Code']
        self.manufacturer_serial_number = edid['ID_Serial_Number']

        if 'Model_Year' in edid:
            self.model_year = edid['Model_Year']
        else:
            self.week_of_manufacture = edid['Week_of_manufacture']
            self.year_of_manufacture = edid['Year_of_manufacture']

        if edid['EDID_version'] == 1:
            if edid['EDID_revision'] == 0:
                self.version = self.VERSION_1_0
            elif edid['EDID_revision'] == 1:
                self.version = self.VERSION_1_1
            elif edid['EDID_revision'] == 2:
                self.version = self.VERSION_1_2
            elif edid['EDID_revision'] == 3:
                self.version = self.VERSION_1_3
            elif edid['EDID_revision'] == 4:
                self.version = self.VERSION_1_4
        elif edid['EDID_version'] == 2:
            if edid['EDID_revision'] == 0:
                self.version = self.VERSION_2_0

        if self.version is None:
            raise ValidationError('Invalid EDID version and revision.')

        ### ASCII Text Descriptors
        if 'Monitor_Name' in edid:
            self.monitor_name = edid['Monitor_Name']

        if 'Monitor_Serial_Number' in edid:
            self.monitor_serial_number = edid['Monitor_Serial_Number']

        if 'Monitor_Data_String' in edid:
            self.monitor_data_string = edid['Monitor_Data_String']

        ### Basic display parameters
        bdp = edid['Basic_display_parameters']
        self.bdp_video_input = bdp['Video_Input']

        if not self.bdp_video_input:
            # Analog Input
            if bdp['Signal_Level_Standard'] == (0.700, 0.300):
                self.bdp_signal_level_standard = \
                    self.bdp_signal_level_std_0700_0300
            elif bdp['Signal_Level_Standard'] == (0.714, 0.286):
                self.bdp_signal_level_standard = \
                    self.bdp_signal_level_std_0714_0286
            elif bdp['Signal_Level_Standard'] == (1.000, 0.400):
                self.bdp_signal_level_standard = \
                    self.bdp_signal_level_std_1000_0400
            elif bdp['Signal_Level_Standard'] == (0.700, 0.000):
                self.bdp_signal_level_standard = \
                    self.bdp_signal_level_std_0700_0000
            else:
                raise ValidationError(
                    'Invalid signal level standard can not be parsed.'
                )

            self.bdp_blank_to_black_setup = bdp['Blank-to-black_setup']
            self.bdp_separate_syncs = bdp['Separate_syncs']
            self.bdp_composite_sync = bdp['Composite_sync']
            self.bdp_sync_on_green_video = bdp['Sync_on_green_video']
            self.bdp_vsync_serration = bdp['Vsync_serration']
        else:
            # Digital Input
            if self.version == self.VERSION_1_4:
                self.bdp_color_bit_depth = bdp['Color_Bit_Depth']
                self.bdp_digital_video_interface = \
                    bdp['Digital_Video_Interface']
                self.bdp_feature_rgb444 = \
                    bdp['Feature_Support']['Color_Encoding_RGB444_Supported']
                self.bdp_feature_ycrcb444 = \
                    bdp['Feature_Support']['Color_Encoding_YCrCb444_Supported']
                self.bdp_feature_ycrcb422 = \
                    bdp['Feature_Support']['Color_Encoding_YCrCb422_Supported']
            else:
                self.bdp_video_input_dfp_1 = bdp['Video_Input_DFP_1']

        if self.version == self.VERSION_1_4:
            if 'Aspect_Ratio' in bdp:
                self.bdp_aspect_ratio = bdp['Aspect_Ratio']

            if 'Horizontal_Screen_Size' in bdp:
                self.bdp_horizontal_screen_size = \
                    bdp['Horizontal_Screen_Size']
                self.bdp_vertical_screen_size = bdp['Vertical_Screen_Size']

            self.bdp_feature_continuous_frequency = \
                bdp['Feature_Support']['Continuous_Frequency']
        else:
            self.bdp_max_horizontal_image_size = bdp[
                'Max_Horizontal_Image_Size']
            self.bdp_max_vertical_image_size = bdp['Max_Vertical_Image_Size']

            self.bdp_feature_default_gtf = bdp['Feature_Support']['Default_GTF']

        self.bdp_display_gamma = bdp['Display_Gamma']

        self.bdp_feature_standby = bdp['Feature_Support']['Standby']
        self.bdp_feature_suspend = bdp['Feature_Support']['Suspend']
        self.bdp_feature_active_off = bdp['Feature_Support']['Active-off']
        self.bdp_feature_standard_srgb = \
            bdp['Feature_Support']['Standard-sRGB']
        self.bdp_feature_pref_timing_mode = \
            bdp['Feature_Support']['Preferred_Timing_Mode']

        if 'Display_Type' in bdp['Feature_Support']:
            self.bdp_feature_display_type = \
                bdp['Feature_Support']['Display_Type']

        ### Chromaticity
        self.chr_red_x = edid['Chromaticity']['Red_x']
        self.chr_red_y = edid['Chromaticity']['Red_y']
        self.chr_green_x = edid['Chromaticity']['Green_x']
        self.chr_green_y = edid['Chromaticity']['Green_y']
        self.chr_blue_x = edid['Chromaticity']['Blue_x']
        self.chr_blue_y = edid['Chromaticity']['Blue_y']
        self.chr_white_x = edid['Chromaticity']['White_x']
        self.chr_white_y = edid['Chromaticity']['White_y']

        ### Established Timings
        self.est_timings_720_400_70 = \
            edid['Established_Timings']['720x400@70Hz']
        self.est_timings_720_400_88 = \
            edid['Established_Timings']['720x400@88Hz']
        self.est_timings_640_480_60 = \
            edid['Established_Timings']['640x480@60Hz']
        self.est_timings_640_480_67 = \
            edid['Established_Timings']['640x480@67Hz']
        self.est_timings_640_480_72 = \
            edid['Established_Timings']['640x480@72Hz']
        self.est_timings_640_480_75 = \
            edid['Established_Timings']['640x480@75Hz']
        self.est_timings_800_600_56 = \
            edid['Established_Timings']['800x600@56Hz']
        self.est_timings_800_600_60 = \
            edid['Established_Timings']['800x600@60Hz']
        self.est_timings_800_600_72 = \
            edid['Established_Timings']['800x600@72Hz']
        self.est_timings_800_600_75 = \
            edid['Established_Timings']['800x600@75Hz']
        self.est_timings_832_624_75 = \
            edid['Established_Timings']['832x624@75Hz']
        self.est_timings_1024_768_87 = \
            edid['Established_Timings']['1024x768@87Hz']
        self.est_timings_1024_768_60 = \
            edid['Established_Timings']['1024x768@60Hz']
        self.est_timings_1024_768_70 = \
            edid['Established_Timings']['1024x768@70Hz']
        self.est_timings_1024_768_75 = \
            edid['Established_Timings']['1024x768@75Hz']
        self.est_timings_1280_1024_75 = \
            edid['Established_Timings']['1280x1024@75Hz']

    def populate_timings_from_parser(self, edid):
        for item in edid['Standard_Timings']:
            data = edid['Standard_Timings'][item]
            identification = re.search(r"^Identification_(\d+)$", item,
                                       re.IGNORECASE)

            if data['Image_aspect_ratio'] == (1, 1):
                aspect_ratio = StandardTiming.ASPECT_RATIO_1_1
            elif data['Image_aspect_ratio'] == (16, 10):
                aspect_ratio = StandardTiming.ASPECT_RATIO_16_10
            elif data['Image_aspect_ratio'] == (4, 3):
                aspect_ratio = StandardTiming.ASPECT_RATIO_4_3
            elif data['Image_aspect_ratio'] == (5, 4):
                aspect_ratio = StandardTiming.ASPECT_RATIO_5_4
            elif data['Image_aspect_ratio'] == (16, 9):
                aspect_ratio = StandardTiming.ASPECT_RATIO_16_9
            else:
                raise ValidationError(
                    'Invalid aspect ratio can not be parsed.'
                )

            timing = StandardTiming(
                identification=identification.group(1),
                user=self.user,
                horizontal_active=data['Horizontal_active'],
                vertical_active=data['Vertical_active'],
                refresh_rate=data['Refresh_Rate'],
                aspect_ratio=aspect_ratio
            )

            self.standardtiming_set.add(timing)

        for item in edid['Descriptors']:
            data = edid['Descriptors'][item]
            identification = re.search(r"^Timing_Descriptor_(\d+)$", item,
                                       re.IGNORECASE)
            if not identification:
                # Not timing descriptor
                break

            timing = DetailedTiming(
                identification=identification.group(1),
                user=self.user,
                pixel_clock=data['Pixel_clock'],
                horizontal_active=data['Horizontal_Active'],
                horizontal_blanking=data['Horizontal_Blanking'],
                horizontal_sync_offset=data['Horizontal_Sync_Offset'],
                horizontal_sync_pulse_width=data[
                    'Horizontal_Sync_Pulse_Width'
                ],
                horizontal_image_size=data['Horizontal_Image_Size'],
                horizontal_border=data['Horizontal_Border'],
                vertical_active=data['Vertical_Active'],
                vertical_blanking=data['Vertical_Blanking'],
                vertical_sync_offset=data['Vertical_Sync_Offset'],
                vertical_sync_pulse_width=data['Vertical_Sync_Pulse_Width'],
                vertical_image_size=data['Vertical_Image_Size'],
                vertical_border=data['Vertical_Border'],
                flags_interlaced=data['Flags']['Interlaced'],
                flags_stereo_mode=data['Flags']['Stereo_Mode'],
                flags_sync_scheme=data['Flags']['Sync_Scheme']
            )

            if (timing.flags_sync_scheme ==
                    DetailedTiming.Sync_Scheme.Digital_Separate):
                timing.flags_horizontal_polarity = \
                    data['Flags']['Horizontal_Polarity']
                timing.flags_vertical_polarity = \
                    data['Flags']['Vertical_Polarity']
            else:
                timing.flags_serrate = data['Flags']['Serrate']

                if (timing.flags_sync_scheme ==
                        DetailedTiming.Sync_Scheme.Digital_Composite):
                    timing.flags_composite_polarity = \
                        data['Flags']['Composite_Polarity']
                else:
                    timing.flags_sync_on_rgb = data['Flags']['Sync_On_RGB']

            self.detailedtiming_set.add(timing)

        if 'Monitor_Range_Limits_Descriptor' in edid['Descriptors']:
            self.monitor_range_limits = True
            data = edid['Descriptors']['Monitor_Range_Limits_Descriptor']

            self.mrl_min_horizontal_rate = data['Min_Horizontal_rate']
            self.mrl_max_horizontal_rate = data['Max_Horizontal_rate']
            self.mrl_min_vertical_rate = data['Min_Vertical_rate']
            self.mrl_max_vertical_rate = data['Max_Vertical_rate']
            self.mrl_max_pixel_clock = data['Max_Supported_Pixel_Clock']
            self.mrl_secondary_gtf_curve_support = \
                data['Secondary_GTF_curve_supported']
            self.mrl_coordinated_video_timing_support = \
                data['Coordinated_Video_Timings_supported']

            if self.mrl_secondary_gtf_curve_support:
                self.mrl_secondary_gtf_start_freq = \
                    data['Secondary_GTF']['start_frequency']
                self.mrl_secondary_gtf_c = data['Secondary_GTF']['C']
                self.mrl_secondary_gtf_m = data['Secondary_GTF']['M']
                self.mrl_secondary_gtf_k = data['Secondary_GTF']['K']
                self.mrl_secondary_gtf_j = data['Secondary_GTF']['J']

            if self.mrl_coordinated_video_timing_support:
                self.mrl_cvt_max_active_pixels_per_line = \
                    data['Max_Active_Pixels_per_Line']
                self.mrl_cvt_aspect_ratio_4_3_supported = \
                    data['Aspect_Ratio_4:3_supported']
                self.mrl_cvt_aspect_ratio_16_9_supported = \
                    data['Aspect_Ratio_16:9_supported']
                self.mrl_cvt_aspect_ratio_16_10_supported = \
                    data['Aspect_Ratio_16:10_supported']
                self.mrl_cvt_aspect_ratio_5_4_supported = \
                    data['Aspect_Ratio_5:4_supported']
                self.mrl_cvt_aspect_ratio_15_9_supported = \
                    data['Aspect_Ratio_15:9_supported']
                self.mrl_cvt_preferred_aspect_ratio = \
                    data['Preferred_Aspect_Ratio']
                self.mrl_cvt_standard_blanking_supported = \
                    data['CVT_Standard_Blanking_supported']
                self.mrl_cvt_reduced_blanking_supported = \
                    data['CVT_Reduced_Blanking_supported']
                self.mrl_cvt_horizontal_shrink_supported = \
                    data['Horizontal_Shrink_supported']
                self.mrl_cvt_horizontal_stretch_supported = \
                    data['Horizontal_Stretch_supported']
                self.mrl_cvt_vertical_shrink_supported = \
                    data['Vertical_Shrink_supported']
                self.mrl_cvt_vertical_stretch_supported = \
                    data['Vertical_Stretch_supported']
                self.mrl_cvt_preferred_vertical_refresh_rate = \
                    data['Preferred_Vertical_Refresh_Rate']
        else:
            self.monitor_range_limits = False

        self.status = self.STATUS_TIMINGS_ADDED

    def get_absolute_url(self):
        return reverse('edid-detail', kwargs={'pk': self.pk})

    def get_comments(self):
        comments = list(Comment.objects.filter(EDID=self)
                                       .select_related('user').all())

        ordered_comments = self._get_nested_comments(comments, 0)

        return ordered_comments

    def _get_nested_comments(self, comments, level, parent=None):
        nested_comments = []

        for comment in comments:
            if comment.level == level and comment.parent == parent:
                deep_nested_comments = {'comment': comment}

                deeper_nested_comments = self._get_nested_comments(
                    comments, comment.level + 1, comment
                )
                if deeper_nested_comments:
                    deep_nested_comments['subcomments'] = \
                        deeper_nested_comments

                nested_comments.append(deep_nested_comments)

        if not nested_comments:
            return None

        return nested_comments

    def get_est_timings(self):
        """
        Returns established timings in a dictionary.
        """

        return [
            {'horizontal_active': 720, 'vertical_active': 400,
             'refresh_rate': 70, 'supported': self.est_timings_720_400_70},
            {'horizontal_active': 720, 'vertical_active': 400,
             'refresh_rate': 88, 'supported': self.est_timings_720_400_88},

            {'horizontal_active': 640, 'vertical_active': 480,
             'refresh_rate': 60, 'supported': self.est_timings_640_480_60},
            {'horizontal_active': 640, 'vertical_active': 480,
             'refresh_rate': 67, 'supported': self.est_timings_640_480_67},
            {'horizontal_active': 640, 'vertical_active': 480,
             'refresh_rate': 72, 'supported': self.est_timings_640_480_72},
            {'horizontal_active': 640, 'vertical_active': 480,
             'refresh_rate': 75, 'supported': self.est_timings_640_480_75},

            {'horizontal_active': 800, 'vertical_active': 600,
             'refresh_rate': 56, 'supported': self.est_timings_800_600_56},
            {'horizontal_active': 800, 'vertical_active': 600,
             'refresh_rate': 60, 'supported': self.est_timings_800_600_60},
            {'horizontal_active': 800, 'vertical_active': 600,
             'refresh_rate': 72, 'supported': self.est_timings_800_600_72},
            {'horizontal_active': 800, 'vertical_active': 600,
             'refresh_rate': 75, 'supported': self.est_timings_800_600_75},

            {'horizontal_active': 832, 'vertical_active': 624,
             'refresh_rate': 75, 'supported': self.est_timings_832_624_75},

            {'horizontal_active': 1024, 'vertical_active': 768,
             'refresh_rate': 87, 'supported': self.est_timings_1024_768_87},
            {'horizontal_active': 1024, 'vertical_active': 768,
             'refresh_rate': 60, 'supported': self.est_timings_1024_768_60},
            {'horizontal_active': 1024, 'vertical_active': 768,
             'refresh_rate': 70, 'supported': self.est_timings_1024_768_70},
            {'horizontal_active': 1024, 'vertical_active': 768,
             'refresh_rate': 75, 'supported': self.est_timings_1024_768_75},

            {'horizontal_active': 1280, 'vertical_active': 1024,
             'refresh_rate': 75, 'supported': self.est_timings_1280_1024_75},
        ]

    def get_maximum_resolution(self):
        """
        Returns parameters of the maximum resolution supported by timings.
        """

        maximum_resolution = {
            'horizontal_active': 0, 'vertical_active': 0, 'refresh_rate': 0
        }

        for timing in self.get_est_timings():
            if timing['supported']:
                maximum_resolution = self._update_maximum_resolution(
                    maximum_resolution,
                    timing['horizontal_active'],
                    timing['vertical_active'],
                    timing['refresh_rate']
                )

        for timing in self.standardtiming_set.all():
            maximum_resolution = self._update_maximum_resolution(
                maximum_resolution,
                timing.horizontal_active,
                timing.vertical_active,
                timing.refresh_rate
            )

        for timing in self.detailedtiming_set.all():
            maximum_resolution = self._update_maximum_resolution(
                maximum_resolution,
                timing.horizontal_active,
                timing.vertical_active,
                timing.get_refresh_rate()
            )

        return maximum_resolution

    def _update_maximum_resolution(self, maximum_resolution, horizontal_active,
                                   vertical_active, refresh_rate):
        """
        Updates maximum_resolution if the new timing have higher resolution.

        Higher resolution is determined by the total number of pixels.
        """

        maximum_resolution_pixels = maximum_resolution['horizontal_active'] \
            * maximum_resolution['vertical_active']

        resolution_pixels = horizontal_active * vertical_active

        if resolution_pixels > maximum_resolution_pixels \
            or (resolution_pixels == maximum_resolution_pixels
                and refresh_rate > maximum_resolution['refresh_rate']):
            maximum_resolution = {
                'horizontal_active': horizontal_active,
                'vertical_active': vertical_active,
                'refresh_rate': refresh_rate
            }

        return maximum_resolution

    def __unicode__(self):
        return "%s %s" % (self.manufacturer.name, self.monitor_name)


class Timing(models.Model):
    EDID = models.ForeignKey(EDID)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)

    # Identification
    identification = models.IntegerField()

    class Meta(object):
        abstract = True
        ordering = ['identification']

    def delete(self, using=None):
        super(Timing, self).delete(using)

        # Get all subsequent timings
        timings = self.__class__.objects.filter(
            EDID=self.EDID,
            identification__gt=self.identification
        ).all()

        # Move them up
        for timing in timings:
            timing.identification -= 1
            timing.save()


class StandardTiming(Timing):
    # Horizontal active, 256-2288 pixels
    horizontal_active = models.IntegerField()
    # Vertical active, pixels
    vertical_active = models.IntegerField()
    # Refresh rate, 60-123 Hz
    refresh_rate = models.IntegerField()

    ASPECT_RATIO_1_1 = 0
    ASPECT_RATIO_16_10 = 1
    ASPECT_RATIO_4_3 = 2
    ASPECT_RATIO_5_4 = 3
    ASPECT_RATIO_16_9 = 4
    ASPECT_RATIO_CHOICES = (
        (ASPECT_RATIO_1_1, '1:1'),
        (ASPECT_RATIO_16_10, '16:10'),
        (ASPECT_RATIO_4_3, '4:3'),
        (ASPECT_RATIO_5_4, '5:4'),
        (ASPECT_RATIO_16_9, '16:9'),
    )
    aspect_ratio = models.SmallIntegerField(choices=ASPECT_RATIO_CHOICES)

    def __unicode__(self):
        return "%dx%d@%dHz" % (self.horizontal_active, self.vertical_active,
                               self.refresh_rate)


class DetailedTiming(Timing):
    # Pixel clock in kHz
    pixel_clock = models.PositiveIntegerField()

    horizontal_active = models.PositiveSmallIntegerField()
    horizontal_blanking = models.PositiveSmallIntegerField()
    horizontal_sync_offset = models.PositiveSmallIntegerField()
    horizontal_sync_pulse_width = models.PositiveSmallIntegerField()
    horizontal_image_size = models.PositiveSmallIntegerField()
    horizontal_border = models.PositiveSmallIntegerField()

    vertical_active = models.PositiveSmallIntegerField()
    vertical_blanking = models.PositiveSmallIntegerField()
    vertical_sync_offset = models.PositiveSmallIntegerField()
    vertical_sync_pulse_width = models.PositiveSmallIntegerField()
    vertical_image_size = models.PositiveSmallIntegerField()
    vertical_border = models.PositiveSmallIntegerField()

    flags_interlaced = models.BooleanField('interlaced')

    Stereo_Mode = DisplayStereoMode
    STEREO_MODE_CHOICES = (
        (Stereo_Mode.Normal_display, 'Normal display, no stereo.'),
        (Stereo_Mode.Field_sequential_right,
            'Field sequential stereo, right image when stereo sync.'),
        (Stereo_Mode.Field_sequential_left,
            'Field sequential stereo, left image when stereo sync.'),
        (Stereo_Mode.Interleaved_2_way_right,
            '2-way interleaved stereo, right image on even lines.'),
        (Stereo_Mode.Interleaved_2_way_left,
            '2-way interleaved stereo, left image on even lines.'),
        (Stereo_Mode.Interleaved_4_way, '4-way interleaved stereo.'),
        (Stereo_Mode.Interleaved_side_by_side,
            'Side-by-Side interleaved stereo.'),
    )
    flags_stereo_mode = models.PositiveSmallIntegerField(
        'stereo mode',
        choices=STEREO_MODE_CHOICES
    )

    Sync_Scheme = TimingSyncScheme
    SYNC_SCHEME_CHOICES = (
        (Sync_Scheme.Analog_Composite, 'Analog Composite'),
        (Sync_Scheme.Bipolar_Analog_Composite, 'Bipolar Analog Composite'),
        (Sync_Scheme.Digital_Composite, 'Digital Composite'),
        (Sync_Scheme.Digital_Separate, 'Digital Separate'),
    )
    flags_sync_scheme = models.PositiveSmallIntegerField(
        'sync scheme',
        choices=SYNC_SCHEME_CHOICES
    )

    # If flags_sync_scheme == Digital_Separate
    flags_horizontal_polarity = models.NullBooleanField('horizontal polarity')
    flags_vertical_polarity = models.NullBooleanField('vertical polarity')

    # If not flags_sync_scheme == Digital_Separate
    flags_serrate = models.NullBooleanField('serrate')

    # If flags_sync_scheme == Digital_Composite
    flags_composite_polarity = models.NullBooleanField('composite polarity')

    # If not flags_sync_scheme == Digital_Composite and
    # not flags_sync_scheme == Digital_Separate
    flags_sync_on_rgb = models.NullBooleanField('sync on RGB')

    def get_refresh_rate(self):
        return round((self.pixel_clock * 1000) /
                     ((self.horizontal_active + self.horizontal_blanking)
                      * (self.vertical_active + self.vertical_blanking)), 2)

    def __unicode__(self):
        return "%dx%d@%fHz" % (self.horizontal_active, self.vertical_active,
                               self.get_refresh_rate())


# Default settings for Comment model
EDID_COMMENT_MAX_THREAD_LEVEL = 2


class Comment(models.Model):
    EDID = models.ForeignKey(EDID)

    # Parent comment
    parent = models.ForeignKey('self', null=True)

    # Nested level
    level = models.PositiveSmallIntegerField()

    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    submitted = models.DateTimeField(auto_now_add=True)

    content = models.TextField()

    class Meta(object):
        ordering = ('level', 'submitted',)

    def get_max_thread_level(self):
        if hasattr(settings, 'EDID_COMMENT_MAX_THREAD_LEVEL'):
            return settings.EDID_COMMENT_MAX_THREAD_LEVEL

        return EDID_COMMENT_MAX_THREAD_LEVEL

    def __unicode__(self):
        return "%s: %s" % (self.pk, self.content[:100])


class GrabberRelease(models.Model):
    # Release platform
    PLATFORM_LINUX = 0
    PLATFORM_MACOSX = 1
    PLATFORM_WINDOWS = 2
    PLATFORM_CHOICES = ((PLATFORM_LINUX, 'Linux'),
                        (PLATFORM_MACOSX, 'Mac OS X'),
                        (PLATFORM_WINDOWS, 'Windows'))
    platform = models.PositiveSmallIntegerField(choices=PLATFORM_CHOICES)

    # Release commit hash
    commit = models.CharField(max_length=40)

    release_file = models.FileField(upload_to='edid-grabber/%Y/%m')

    # Release file checksum
    checksum_md5 = models.CharField(max_length=32)
    checksum_sha1 = models.CharField(max_length=40)

    # Uploaded date
    uploaded = models.DateTimeField(auto_now_add=True)

    # Non-sticky releases will be listed in archive only
    sticky = models.BooleanField(default=False)

    def __unicode__(self):
        return "%s" % (self.commit)
