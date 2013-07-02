import re

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse

from edid_parser.edid_parser import Display_Type, Display_Stereo_Mode, Timing_Sync_Scheme

class Manufacturer(models.Model):
    #Full name
    name = models.CharField(max_length=255, blank=True)
    #ID, 3 characters
    name_id = models.CharField(max_length=3)

    def __unicode__(self):
        return "%s: %s" % (self.name_id, self.name)

class EDIDPublicManager(models.Manager):
    """Manager to filter private EDIDs from public interface."""

    def get_query_set(self):
        return super(EDIDPublicManager, self).get_query_set().exclude(status=EDID.STATUS_PRIVATE)

class EDID(models.Model):
    objects = EDIDPublicManager()
    all_objects = models.Manager()

    manufacturer = models.ForeignKey(Manufacturer)

    #Initialized and basic data auto-added
    STATUS_INITIALIZED = 0
    #Standard and detailed timings auto-added
    STATUS_TIMINGS_ADDED = 1
    #Manually edited by users
    STATUS_EDITED = 2
    #Private, hidden from public
    STATUS_PRIVATE = 3
    STATUS_CHOICES = ((STATUS_INITIALIZED, 'Initialized'),
                      (STATUS_TIMINGS_ADDED, 'Timings Added'),
                      (STATUS_EDITED, 'Edited'),
                      (STATUS_PRIVATE, 'Private'))
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=STATUS_INITIALIZED)

    ### Header
    #ID Product Code
    manufacturer_product_code = models.CharField(max_length=4, blank=True)
    #ID Serial Number, 32-bit
    manufacturer_serial_number = models.PositiveIntegerField(blank=True, null=True)
    #Week of manufacture, 1-54, 0==Unknown, 255==the year model
    week_of_manufacture = models.PositiveSmallIntegerField()
    #Year of manufacture, 1990-2245
    year_of_manufacture = models.PositiveSmallIntegerField()

    #EDID version and revision
    EDID_version_1_0 = 0
    EDID_version_1_1 = 1
    EDID_version_1_2 = 2
    EDID_version_1_3 = 3
    EDID_version_1_4 = 4
    EDID_version_2_0 = 5
    EDID_version_choices = ((EDID_version_1_0, '1.0'),
                            (EDID_version_1_1, '1.1'),
                            (EDID_version_1_2, '1.2'),
                            (EDID_version_1_3, '1.3'),
                            (EDID_version_1_4, '1.4'),
                            (EDID_version_2_0, '2.0'))
    EDID_version = models.PositiveSmallIntegerField(choices=EDID_version_choices)

    ###ASCII Text Descriptors
    #Monitor Name, from Monitor Descriptor Description (type 0xFC)
    monitor_name = models.CharField(max_length=13, blank=True)
    #Monitor Serial Number, from Monitor Descriptor Description (type 0xFF)
    monitor_serial_number = models.CharField(max_length=13, blank=True)
    #Monitor Data String, from Monitor Descriptor Description (type 0xFE)
    monitor_data_string = models.CharField(max_length=13, blank=True)

    ###bdp=Basic display parameters
    bdp_video_input_analog = 0
    bdp_video_input_digital = 1
    bdp_video_input_choices = ((bdp_video_input_analog, 'Analog'),
                              (bdp_video_input_digital, 'Digital'))
    bdp_video_input = models.PositiveSmallIntegerField('video input', choices=bdp_video_input_choices, default=bdp_video_input_analog)
    #Analog Input
    bdp_signal_level_standard_0700_0300 = 0
    bdp_signal_level_standard_0714_0286 = 1
    bdp_signal_level_standard_1000_0400 = 2
    bdp_signal_level_standard_0700_0000 = 3
    bdp_signal_level_standard_choices = ((bdp_signal_level_standard_0700_0300, '(0.700, 0.300)'),
                                        (bdp_signal_level_standard_0714_0286, '(0.714, 0.286)'),
                                        (bdp_signal_level_standard_1000_0400, '(1.000, 0.400)'),
                                        (bdp_signal_level_standard_0700_0000, '(0.700, 0.000)'))
    bdp_signal_level_standard = models.PositiveSmallIntegerField('signal level standard', choices=bdp_signal_level_standard_choices, blank=True, null=True)

    bdp_blank_to_black_setup = models.NullBooleanField('blank-to-black setup level')
    bdp_separate_syncs = models.NullBooleanField('separate sync')
    bdp_composite_sync = models.NullBooleanField('composite sync signal on horizontal')
    bdp_sync_on_green_video = models.NullBooleanField('composite sync signal on green video')
    bdp_vsync_serration = models.NullBooleanField('serration on the vertical sync')
    #Digital Input
    bdp_video_input_DFP_1 = models.NullBooleanField('digital flat panel 1.x')

    bdp_max_horizontal_image_size = models.PositiveSmallIntegerField('maximum horizontal image size')
    bdp_max_vertical_image_size = models.PositiveSmallIntegerField('maximum vertical image size')
    bdp_display_gamma = models.DecimalField('display gamma', max_digits=3, decimal_places=2, blank=True, null=True)

    bdp_feature_display_type_choices = ((Display_Type.Monochrome, 'Monochrome or grayscale display'),
                                        (Display_Type.RGB, 'RGB color display'),
                                        (Display_Type.Non_RGB, 'Non-RGB multicolor display'),
                                        (Display_Type.Undefined, 'Undefined'))

    bdp_feature_standby = models.BooleanField('standby mode')
    bdp_feature_suspend = models.BooleanField('suspend mode')
    bdp_feature_active_off = models.BooleanField('active off/very low power mode')
    bdp_feature_display_type = models.PositiveSmallIntegerField('display color type', choices=bdp_feature_display_type_choices)
    bdp_feature_standard_sRGB = models.BooleanField('standard sRGB')
    bdp_feature_preferred_timing_mode = models.BooleanField('preferred timing mode')
    bdp_feature_default_GTF = models.BooleanField('default GTF')

    ###chr=Chromaticity
    chr_red_x = models.DecimalField('red x', max_digits=4, decimal_places=3)
    chr_red_y = models.DecimalField('red y', max_digits=4, decimal_places=3)
    chr_green_x = models.DecimalField('green x', max_digits=4, decimal_places=3)
    chr_green_y = models.DecimalField('green y', max_digits=4, decimal_places=3)
    chr_blue_x = models.DecimalField('blue x', max_digits=4, decimal_places=3)
    chr_blue_y = models.DecimalField('blue y', max_digits=4, decimal_places=3)
    chr_white_x = models.DecimalField('white x', max_digits=4, decimal_places=3)
    chr_white_y = models.DecimalField('white y', max_digits=4, decimal_places=3)

    ###est_timings=Established Timings
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

    ###mrl=Monitor range limits, optional starting from v1.1
    monitor_range_limits = models.BooleanField('monitor range limits')

    #in kHz
    mrl_min_horizontal_rate = models.PositiveSmallIntegerField('minimum horizontal rate', blank=True, null=True)
    mrl_max_horizontal_rate = models.PositiveSmallIntegerField('maximum horizontal rate', blank=True, null=True)

    #in Hz
    mrl_min_vertical_rate = models.PositiveSmallIntegerField('minimum vertical rate', blank=True, null=True)
    mrl_max_vertical_rate = models.PositiveSmallIntegerField('maximum vertical rate', blank=True, null=True)

    #in MHz
    mrl_max_pixel_clock = models.PositiveSmallIntegerField('maximum supported pixel clock', blank=True, null=True)

    mrl_secondary_GTF_curve_supported = models.NullBooleanField('secondary GTF curve')

    #in kHz
    mrl_secondary_GTF_start_frequency = models.PositiveSmallIntegerField('start frequency', blank=True, null=True)
    mrl_secondary_GTF_C = models.PositiveSmallIntegerField('C', blank=True, null=True)
    mrl_secondary_GTF_M = models.PositiveSmallIntegerField('M', blank=True, null=True)
    mrl_secondary_GTF_K = models.PositiveSmallIntegerField('K', blank=True, null=True)
    mrl_secondary_GTF_J = models.PositiveSmallIntegerField('J', blank=True, null=True)


    def populate_from_edid_parser(self, edid):
        ### Header
        try:
            self.manufacturer = Manufacturer.objects.get(name_id=edid['ID_Manufacturer_Name'])
        except ObjectDoesNotExist:
            #UNK is reserved for unknown manufacturer
            self.manufacturer = Manufacturer.objects.get(name_id='UNK')

        self.manufacturer_product_code = edid['ID_Product_Code']
        self.manufacturer_serial_number = edid['ID_Serial_Number']

        self.week_of_manufacture = edid['Week_of_manufacture']
        self.year_of_manufacture = edid['Year_of_manufacture']

        if edid['EDID_version'] == 1:
            if edid['EDID_revision'] == 0:
                self.EDID_version = self.EDID_version_1_0
            elif edid['EDID_revision'] == 1:
                self.EDID_version = self.EDID_version_1_1
            elif edid['EDID_revision'] == 2:
                self.EDID_version = self.EDID_version_1_2
            elif edid['EDID_revision'] == 3:
                self.EDID_version = self.EDID_version_1_3
            elif edid['EDID_revision'] == 4:
                self.EDID_version = self.EDID_version_1_4
        elif edid['EDID_version'] == 2:
            if edid['EDID_revision'] == 0:
                self.EDID_version = self.EDID_version_2_0

        if not self.EDID_version:
            raise Exception('Invalid EDID version and revision.')

        ###ASCII Text Descriptors
        if 'Monitor_Name' in edid:
            self.monitor_name = edid['Monitor_Name']

        if 'Monitor_Serial_Number' in edid:
            self.monitor_serial_number = edid['Monitor_Serial_Number']

        if 'Monitor_Data_String' in edid:
            self.monitor_data_string = edid['Monitor_Data_String']

        ###Basic display parameters
        self.bdp_video_input = edid['Basic_display_parameters']['Video_Input']
        #Analog Input
        if not self.bdp_video_input:
            if edid['Basic_display_parameters']['Signal_Level_Standard'] == (0.700, 0.300):
                self.bdp_signal_level_standard = self.bdp_signal_level_standard_0700_0300
            elif edid['Basic_display_parameters']['Signal_Level_Standard'] == (0.714, 0.286):
                self.bdp_signal_level_standard = self.bdp_signal_level_standard_0714_0286
            elif edid['Basic_display_parameters']['Signal_Level_Standard'] == (1.000, 0.400):
                self.bdp_signal_level_standard = self.bdp_signal_level_standard_1000_0400
            elif edid['Basic_display_parameters']['Signal_Level_Standard'] == (0.700, 0.000):
                self.bdp_signal_level_standard = self.bdp_signal_level_standard_0700_0000
            else:
                raise Exception('Invalid signal level standard can not be parsed.')

            self.bdp_blank_to_black_setup = edid['Basic_display_parameters']['Blank-to-black_setup']
            self.bdp_separate_syncs = edid['Basic_display_parameters']['Separate_syncs']
            self.bdp_composite_sync = edid['Basic_display_parameters']['Composite_sync']
            self.bdp_sync_on_green_video = edid['Basic_display_parameters']['Sync_on_green_video']
            self.bdp_vsync_serration = edid['Basic_display_parameters']['Vsync_serration']
        #Digital Input
        else:
            self.bdp_video_input_DFP_1 = edid['Basic_display_parameters']['Video_Input_DFP_1']

        self.bdp_max_horizontal_image_size = edid['Basic_display_parameters']['Max_Horizontal_Image_Size']
        self.bdp_max_vertical_image_size = edid['Basic_display_parameters']['Max_Vertical_Image_Size']
        self.bdp_display_gamma = edid['Basic_display_parameters']['Display_Gamma']

        self.bdp_feature_standby = edid['Basic_display_parameters']['Feature_Support']['Standby']
        self.bdp_feature_suspend = edid['Basic_display_parameters']['Feature_Support']['Suspend']
        self.bdp_feature_active_off = edid['Basic_display_parameters']['Feature_Support']['Active-off']
        self.bdp_feature_display_type = edid['Basic_display_parameters']['Feature_Support']['Display_Type']
        self.bdp_feature_standard_sRGB = edid['Basic_display_parameters']['Feature_Support']['Standard-sRGB']
        self.bdp_feature_preferred_timing_mode = edid['Basic_display_parameters']['Feature_Support']['Preferred_Timing_Mode']
        self.bdp_feature_default_GTF = edid['Basic_display_parameters']['Feature_Support']['Default_GTF']

        ###Chromaticity
        self.chr_red_x = edid['Chromaticity']['Red_x']
        self.chr_red_y = edid['Chromaticity']['Red_y']
        self.chr_green_x = edid['Chromaticity']['Green_x']
        self.chr_green_y = edid['Chromaticity']['Green_y']
        self.chr_blue_x = edid['Chromaticity']['Blue_x']
        self.chr_blue_y = edid['Chromaticity']['Blue_y']
        self.chr_white_x = edid['Chromaticity']['White_x']
        self.chr_white_y = edid['Chromaticity']['White_y']

        ###Established Timings
        self.est_timings_720_400_70 = edid['Established_Timings']['720x400@70Hz']
        self.est_timings_720_400_88 = edid['Established_Timings']['720x400@88Hz']
        self.est_timings_640_480_60 = edid['Established_Timings']['640x480@60Hz']
        self.est_timings_640_480_67 = edid['Established_Timings']['640x480@67Hz']
        self.est_timings_640_480_72 = edid['Established_Timings']['640x480@72Hz']
        self.est_timings_640_480_75 = edid['Established_Timings']['640x480@75Hz']
        self.est_timings_800_600_56 = edid['Established_Timings']['800x600@56Hz']
        self.est_timings_800_600_60 = edid['Established_Timings']['800x600@60Hz']
        self.est_timings_800_600_72 = edid['Established_Timings']['800x600@72Hz']
        self.est_timings_800_600_75 = edid['Established_Timings']['800x600@75Hz']
        self.est_timings_832_624_75 = edid['Established_Timings']['832x624@75Hz']
        self.est_timings_1024_768_87 = edid['Established_Timings']['1024x768@87Hz']
        self.est_timings_1024_768_60 = edid['Established_Timings']['1024x768@60Hz']
        self.est_timings_1024_768_70 = edid['Established_Timings']['1024x768@70Hz']
        self.est_timings_1024_768_75 = edid['Established_Timings']['1024x768@75Hz']
        self.est_timings_1280_1024_75 = edid['Established_Timings']['1280x1024@75Hz']

    def get_est_timings(self):
        return [('720x400@70Hz', self.est_timings_720_400_70),
                ('720x400@88Hz', self.est_timings_720_400_88),
                ('640x480@60Hz', self.est_timings_640_480_60),
                ('640x480@67Hz', self.est_timings_640_480_67),
                ('640x480@72Hz', self.est_timings_640_480_72),
                ('640x480@75Hz', self.est_timings_640_480_75),
                ('800x600@56Hz', self.est_timings_800_600_56),
                ('800x600@60Hz', self.est_timings_800_600_60),
                ('800x600@72Hz', self.est_timings_800_600_72),
                ('800x600@75Hz', self.est_timings_800_600_75),
                ('832x624@75Hz', self.est_timings_832_624_75),
                ('1024x768@87Hz', self.est_timings_1024_768_87),
                ('1024x768@60Hz', self.est_timings_1024_768_60),
                ('1024x768@70Hz', self.est_timings_1024_768_70),
                ('1024x768@75Hz', self.est_timings_1024_768_75),
                ('1280x1024@75Hz', self.est_timings_1280_1024_75)]

    def populate_timings_from_edid_parser(self, edid):
        for item in edid['Standard_Timings']:
            data = edid['Standard_Timings'][item]
            id = re.search("^Identification_(\d+)$", item, re.IGNORECASE)

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
                raise Exception('Invalid aspect ratio can not be parsed.')

            timing = StandardTiming(identification=id.group(1),
                                    horizontal_active=data['Horizontal_active'],
                                    vertical_active=data['Vertical_active'],
                                    refresh_rate=data['Refresh_Rate'],
                                    aspect_ratio=aspect_ratio)

            self.standardtiming_set.add(timing)

        for item in edid['Descriptors']:
            data = edid['Descriptors'][item]
            id = re.search("^Timing_Descriptor_(\d+)$", item, re.IGNORECASE)
            if not id:
                #Not timing descriptor
                break

            timing = DetailedTiming(identification=id.group(1),
                                    pixel_clock=data['Pixel_clock'],
                                    horizontal_active=data['Horizontal_Active'],
                                    horizontal_blanking=data['Horizontal_Blanking'],
                                    horizontal_sync_offset=data['Horizontal_Sync_Offset'],
                                    horizontal_sync_pulse_width=data['Horizontal_Sync_Pulse_Width'],
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
                                    flags_sync_scheme=data['Flags']['Sync_Scheme'])

            if timing.flags_sync_scheme == DetailedTiming.Sync_Scheme.Digital_Separate:
                timing.flags_horizontal_polarity = data['Flags']['Horizontal_Polarity']
                timing.flags_vertical_polarity = data['Flags']['Vertical_Polarity']
            else:
                timing.flags_serrate = data['Flags']['Serrate']

                if timing.flags_sync_scheme == DetailedTiming.Sync_Scheme.Digital_Composite:
                    timing.flags_composite_polarity = data['Flags']['Composite_Polarity']
                else:
                    timing.flags_sync_on_RGB = data['Flags']['Sync_On_RGB']

            self.detailedtiming_set.add(timing)

        if 'Monitor_Range_Limits_Descriptor' in edid['Descriptors']:
            self.monitor_range_limits = True
            data = edid['Descriptors']['Monitor_Range_Limits_Descriptor']

            self.mrl_min_horizontal_rate = data['Min_Horizontal_rate']
            self.mrl_max_horizontal_rate = data['Max_Horizontal_rate']
            self.mrl_min_vertical_rate = data['Min_Vertical_rate']
            self.mrl_max_vertical_rate = data['Max_Vertical_rate']
            self.mrl_max_pixel_clock = data['Max_Supported_Pixel_Clock']
            self.mrl_secondary_GTF_curve_supported = data['Secondary_GTF_curve_supported']

            if self.mrl_secondary_GTF_curve_supported:
                self.mrl_secondary_GTF_start_frequency = data['Secondary_GTF']['start_frequency']
                self.mrl_secondary_GTF_C = data['Secondary_GTF']['C']
                self.mrl_secondary_GTF_M = data['Secondary_GTF']['M']
                self.mrl_secondary_GTF_K = data['Secondary_GTF']['K']
                self.mrl_secondary_GTF_J = data['Secondary_GTF']['J']
        else:
            self.monitor_range_limits = False

        self.status = self.STATUS_TIMINGS_ADDED

    def get_absolute_url(self):
        return reverse('edid-detail', kwargs={'pk': self.pk})

    def __unicode__(self):
        return "%s %s" % (self.manufacturer.name, self.monitor_name)

class Timing(models.Model):
    EDID = models.ForeignKey(EDID)

    #Identification
    identification = models.IntegerField()

    class Meta:
        abstract = True
        ordering = ['identification']

class StandardTiming(Timing):
    #Horizontal active, 256-2288 pixels
    horizontal_active = models.IntegerField()
    #Vertical active, pixels
    vertical_active = models.IntegerField()
    #Refresh rate, 60-123 Hz
    refresh_rate = models.IntegerField()

    ASPECT_RATIO_1_1 = 0
    ASPECT_RATIO_16_10 = 1
    ASPECT_RATIO_4_3 = 2
    ASPECT_RATIO_5_4 = 3
    ASPECT_RATIO_16_9 = 4
    ASPECT_RATIO_CHOICES = ((ASPECT_RATIO_1_1, '1:1'),
                            (ASPECT_RATIO_16_10, '16:10'),
                            (ASPECT_RATIO_4_3, '4:3'),
                            (ASPECT_RATIO_5_4, '5:4'),
                            (ASPECT_RATIO_16_9, '16:9'))
    aspect_ratio = models.SmallIntegerField(choices=ASPECT_RATIO_CHOICES)

    def __unicode__(self):
        return "%dx%d@%dHz" % (self.horizontal_active, self.vertical_active, self.refresh_rate)

class DetailedTiming(Timing):
    #Pixel clock in kHz
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

    Stereo_Mode = Display_Stereo_Mode
    STEREO_MODE_CHOICES = ((Stereo_Mode.Normal_display, ' Normal display, no stereo.'),
                            (Stereo_Mode.Field_sequential_right, ' Field sequential stereo, right image when stereo sync.'),
                            (Stereo_Mode.Field_sequential_left, ' Field sequential stereo, left image when stereo sync.'),
                            (Stereo_Mode.Interleaved_2_way_right, '2-way interleaved stereo, right image on even lines.'),
                            (Stereo_Mode.Interleaved_2_way_left, ' 2-way interleaved stereo, left image on even lines.'),
                            (Stereo_Mode.Interleaved_4_way, '4-way interleaved stereo.'),
                            (Stereo_Mode.Interleaved_side_by_side, ' Side-by-Side interleaved stereo.'))
    flags_stereo_mode = models.PositiveSmallIntegerField('stereo mode', choices=STEREO_MODE_CHOICES)

    Sync_Scheme = Timing_Sync_Scheme
    SYNC_SCHEME_CHOICES = ((Sync_Scheme.Analog_Composite, 'Analog Composite'),
                            (Sync_Scheme.Bipolar_Analog_Composite, 'Bipolar Analog Composite'),
                            (Sync_Scheme.Digital_Composite, 'Digital Composite'),
                            (Sync_Scheme.Digital_Separate, 'Digital Separate'))
    flags_sync_scheme = models.PositiveSmallIntegerField('sync scheme', choices=SYNC_SCHEME_CHOICES)

    #If flags_sync_scheme == Digital_Separate
    flags_horizontal_polarity = models.NullBooleanField('horizontal polarity')
    flags_vertical_polarity = models.NullBooleanField('vertical polarity')

    #If not flags_sync_scheme == Digital_Separate
    flags_serrate = models.NullBooleanField('serrate')

    #If flags_sync_scheme == Digital_Composite
    flags_composite_polarity = models.NullBooleanField('composite polarity')

    #If not flags_sync_scheme == Digital_Composite and not flags_sync_scheme == Digital_Separate
    flags_sync_on_RGB = models.NullBooleanField('sync on RGB')

    def __unicode__(self):
        return "%dx%d@%dHz" % (self.horizontal_active, self.vertical_active, self.pixel_clock / 1000)
