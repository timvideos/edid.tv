
from django.db import models

from edid_parser.edid_parser import Display_Type, Display_Stereo_Mode, Timing_Sync_Scheme

class EDID(models.Model):
    ### Header
    #ID Manufacturer Name, full name assigned from PNP IDs list
    manufacturer_name = models.CharField(max_length=255, blank=True)
    #ID Manufacturer Name, 3 characters
    manufacturer_name_id = models.CharField(max_length=3)
    #ID Product Code
    manufacturer_product_code = models.CharField(max_length=4, blank=True)
    #ID Serial Number, 32-bit
    manufacturer_serial_number = models.PositiveIntegerField(blank=True, null=True)
    #Week of manufacture, 1-53, 255==the year model
    week_of_manufacture = models.PositiveSmallIntegerField()
    #Year of manufacture, 1990-2245
    year_of_manufacture = models.PositiveSmallIntegerField()
    #EDID version
    EDID_version = models.IntegerField()
    #EDID revision
    EDID_revision = models.IntegerField()

    ###ASCII Text Descriptors
    #Monitor Name, from Monitor Descriptor Description (type 0xFC)
    monitor_name = models.CharField(max_length=13, blank=True)
    #Monitor Serial Number, from Monitor Descriptor Description (type 0xFF)
    monitor_serial_number = models.CharField(max_length=13, blank=True)
    #Monitor Data String, from Monitor Descriptor Description (type 0xFE)
    monitor_data_string = models.CharField(max_length=13, blank=True)

    ###bsp=Basic display parameters
    bsp_video_input = models.BooleanField()
    #Analog Input
    bsp_signal_level_standard_choices = ((0, '(0.700, 0.300)'),
                                        (1, '(0.714, 0.286)'),
                                        (2, '(1.000, 0.400)'),
                                        (3, '(0.700, 0.000)'))
    bsp_signal_level_standard = models.PositiveSmallIntegerField(choices=bsp_signal_level_standard_choices, blank=True, null=True)

    bsp_blank_to_black_setup = models.NullBooleanField()
    bsp_separate_syncs = models.NullBooleanField()
    bsp_composite_sync = models.NullBooleanField()
    bsp_sync_on_green_video = models.NullBooleanField()
    bsp_vsync_serration = models.NullBooleanField()
    #Digital Input
    bsp_video_input_DFP_1 = models.NullBooleanField()

    bsp_max_horizontal_image_size = models.IntegerField()
    bsp_max_vertical_image_size = models.IntegerField()
    bsp_display_gamma = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)

    bsp_feature_display_type_choices = ((Display_Type.Monochrome, 'Monochrome / grayscale display'),
                                        (Display_Type.RGB, 'RGB color display'),
                                        (Display_Type.Non_RGB, 'Non-RGB multicolor display'),
                                        (Display_Type.Undefined, 'Undefined'))

    bsp_feature_standby = models.BooleanField()
    bsp_feature_suspend = models.BooleanField()
    bsp_feature_active_off = models.BooleanField()
    bsp_feature_display_type = models.PositiveSmallIntegerField(choices=bsp_feature_display_type_choices)
    bsp_feature_standard_sRGB = models.BooleanField()
    bsp_feature_preferred_timing_mode = models.BooleanField()
    bsp_feature_default_GTF = models.BooleanField()

    ###chr=Chromaticity
    chr_red_x = models.DecimalField(max_digits=4, decimal_places=3)
    chr_red_y = models.DecimalField(max_digits=4, decimal_places=3)
    chr_green_x = models.DecimalField(max_digits=4, decimal_places=3)
    chr_green_y = models.DecimalField(max_digits=4, decimal_places=3)
    chr_blue_x = models.DecimalField(max_digits=4, decimal_places=3)
    chr_blue_y = models.DecimalField(max_digits=4, decimal_places=3)
    chr_white_x = models.DecimalField(max_digits=4, decimal_places=3)
    chr_white_y = models.DecimalField(max_digits=4, decimal_places=3)

    def populate_from_edid_parser(self, edid):
        ### Header
        #TODO: Parse from PNP IDs list
        self.manufacturer_name = edid['ID_Manufacturer_Name']
        self.manufacturer_name_id = edid['ID_Manufacturer_Name']

        self.manufacturer_product_code = edid['ID_Product_Code']
        self.manufacturer_serial_number = edid['ID_Serial_Number']

        self.week_of_manufacture = edid['Week_of_manufacture']
        self.year_of_manufacture = edid['Year_of_manufacture']

        self.EDID_version = edid['EDID_version']
        self.EDID_revision = edid['EDID_revision']

        ###ASCII Text Descriptors
        if 'Monitor_Name' in edid:
            self.monitor_name = edid['Monitor_Name']

        if 'Monitor_Serial_Number' in edid:
            self.monitor_serial_number = edid['Monitor_Serial_Number']

        if 'Monitor_Data_String' in edid:
            self.monitor_data_string = edid['Monitor_Data_String']

        ###Basic display parameters
        self.bsp_video_input = edid['Basic_display_parameters']['Video_Input']
        #Analog Input
        if not self.bsp_video_input:
            self.bsp_signal_level_standard = edid['Basic_display_parameters']['Signal_Level_Standard']
            self.bsp_blank_to_black_setup = edid['Basic_display_parameters']['Blank-to-black_setup']
            self.bsp_separate_syncs = edid['Basic_display_parameters']['Separate_syncs']
            self.bsp_composite_sync = edid['Basic_display_parameters']['Composite_sync']
            self.bsp_sync_on_green_video = edid['Basic_display_parameters']['Sync_on_green_video']
            self.bsp_vsync_serration = edid['Basic_display_parameters']['Vsync_serration']
        #Digital Input
        else:
            self.bsp_video_input_DFP_1 = edid['Basic_display_parameters']['Video_Input_DFP_1']

        self.bsp_max_horizontal_image_size = edid['Basic_display_parameters']['Max_Horizontal_Image_Size']
        self.bsp_max_vertical_image_size = edid['Basic_display_parameters']['Max_Vertical_Image_Size']
        self.bsp_display_gamma = edid['Basic_display_parameters']['Display_Gamma']

        self.bsp_feature_standby = edid['Basic_display_parameters']['Feature_Support']['Standby']
        self.bsp_feature_suspend = edid['Basic_display_parameters']['Feature_Support']['Suspend']
        self.bsp_feature_active_off = edid['Basic_display_parameters']['Feature_Support']['Active-off']
        self.bsp_feature_display_type = edid['Basic_display_parameters']['Feature_Support']['Display_Type']
        self.bsp_feature_standard_sRGB = edid['Basic_display_parameters']['Feature_Support']['Standard-sRGB']
        self.bsp_feature_preferred_timing_mode = edid['Basic_display_parameters']['Feature_Support']['Preferred_Timing_Mode']
        self.bsp_feature_default_GTF = edid['Basic_display_parameters']['Feature_Support']['Default_GTF']

        ###Chromaticity
        self.chr_red_x = edid['Chromaticity']['Red_x']
        self.chr_red_y = edid['Chromaticity']['Red_y']
        self.chr_green_x = edid['Chromaticity']['Green_x']
        self.chr_green_y = edid['Chromaticity']['Green_y']
        self.chr_blue_x = edid['Chromaticity']['Blue_x']
        self.chr_blue_y = edid['Chromaticity']['Blue_y']
        self.chr_white_x = edid['Chromaticity']['White_x']
        self.chr_white_y = edid['Chromaticity']['White_y']

    def __unicode__(self):
        #should be manufacturer_name NOT _id
        return "%s %s" % (self.manufacturer_name_id, self.monitor_name)
