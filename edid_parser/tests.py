import unittest
from edid_parser import EDID_Parser, EDIDParsingError, Display_Type, Display_Stereo_Mode, Timing_Sync_Scheme

class EDIDTest(unittest.TestCase):
    """Base class for EDID Parser tests."""

    def setUp(self):
        self.parser = EDID_Parser()
        #Assuming version 1.3 by default
        self.parser.data['EDID_version'] = 1
        self.parser.data['EDID_reversion'] = 3

class EDIDValidTest(EDIDTest):
    """EDID Parser tests with valid input."""

    def test_all(self):
        test_edid = "\x00\xFF\xFF\xFF\xFF\xFF\xFF\x00\x52\x62\x06\x02\x01\x01\x01\x01\xFF\x13\x01\x03\x80\x59\x32\x78\x0A\xF0\x9D\xA3\x55\x49\x9B\x26\x0F\x47\x4A\x21\x08\x00\x81\x80\x8B\xC0\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x02\x3A\x80\x18\x71\x38\x2D\x40\x58\x2C\x45\x00\x76\xF2\x31\x00\x00\x1E\x66\x21\x50\xB0\x51\x00\x1B\x30\x40\x70\x36\x00\x76\xF2\x31\x00\x00\x1E\x00\x00\x00\xFC\x00\x54\x4F\x53\x48\x49\x42\x41\x2D\x54\x56\x0A\x20\x20\x00\x00\x00\xFD\x00\x17\x3D\x0F\x44\x0F\x00\x0A\x20\x20\x20\x20\x20\x20\x01\x24"
        self.parser.parse_all(test_edid)

    def test_binary(self):
        test_edid = "\x00\xFF\xFF\xFF\xFF\xFF\xFF\x00\x52\x62\x06\x02\x01\x01\x01\x01\xFF\x13\x01\x03\x80\x59\x32\x78\x0A\xF0\x9D\xA3\x55\x49\x9B\x26\x0F\x47\x4A\x21\x08\x00\x81\x80\x8B\xC0\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01\x02\x3A\x80\x18\x71\x38\x2D\x40\x58\x2C\x45\x00\x76\xF2\x31\x00\x00\x1E\x66\x21\x50\xB0\x51\x00\x1B\x30\x40\x70\x36\x00\x76\xF2\x31\x00\x00\x1E\x00\x00\x00\xFC\x00\x54\x4F\x53\x48\x49\x42\x41\x2D\x54\x56\x0A\x20\x20\x00\x00\x00\xFD\x00\x17\x3D\x0F\x44\x0F\x00\x0A\x20\x20\x20\x20\x20\x20\x01\x24"
        self.parser.parse_binary(test_edid)

    def test_checksum(self):
        #Valid header and checksum
        test_edid = [0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x52, 0x62, 0x06, 0x02, 0x01, 0x01, 0x01, 0x01, 0xFF, 0x13, 0x01, 0x03, 0x80, 0x59, 0x32, 0x78, 0x0A, 0xF0, 0x9D, 0xA3, 0x55, 0x49, 0x9B, 0x26, 0x0F, 0x47, 0x4A, 0x21, 0x08, 0x00, 0x81, 0x80, 0x8B, 0xC0, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x02, 0x3A, 0x80, 0x18, 0x71, 0x38, 0x2D, 0x40, 0x58, 0x2C, 0x45, 0x00, 0x76, 0xF2, 0x31, 0x00, 0x00, 0x1E, 0x66, 0x21, 0x50, 0xB0, 0x51, 0x00, 0x1B, 0x30, 0x40, 0x70, 0x36, 0x00, 0x76, 0xF2, 0x31, 0x00, 0x00, 0x1E, 0x00, 0x00, 0x00, 0xFC, 0x00, 0x54, 0x4F, 0x53, 0x48, 0x49, 0x42, 0x41, 0x2D, 0x54, 0x56, 0x0A, 0x20, 0x20, 0x00, 0x00, 0x00, 0xFD, 0x00, 0x17, 0x3D, 0x0F, 0x44, 0x0F, 0x00, 0x0A, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0x01, 0x24]
        self.parser.checksum(test_edid)

        self.assertEqual(self.parser.data['Extension_Flag'], 1)

    def test_header(self):
        test_edid = [0x52, 0x62, 0x06, 0x02, 0x01, 0x01, 0x01, 0x01, 0xFF, 0x13, 0x01, 0x03]
        self.parser.parse_header(test_edid)

        self.assertEqual(self.parser.data['ID_Manufacturer_Name'], 'TSB')
        self.assertEqual(self.parser.data['ID_Product_Code'], '0206')
        self.assertEqual(self.parser.data['Week_of_manufacture'], 255)
        self.assertEqual(self.parser.data['Year_of_manufacture'], 2009)
        self.assertEqual(self.parser.data['ID_Serial_Number'], 16843009)
        self.assertEqual(self.parser.data['EDID_version'], 1)
        self.assertEqual(self.parser.data['EDID_revision'], 3)

    def test_basic_display(self):
        test_edid = [0b10000000, 0x59, 0x32, 0x78, 0b00001010]
        data = self.parser.parse_basic_display(test_edid)

        self.assertTrue(data['Video_Input'])
        self.assertFalse(data['Video_Input_DFP_1'])

        self.assertEqual(data['Max_Horizontal_Image_Size'], 89)
        self.assertEqual(data['Max_Vertical_Image_Size'], 50)

        self.assertEqual(data['Display_Gamma'], 2.2)

        self.assertFalse(data['Feature_Support']['Standby'])
        self.assertFalse(data['Feature_Support']['Suspend'])
        self.assertFalse(data['Feature_Support']['Active-off'])
        self.assertFalse(data['Feature_Support']['Standard-sRGB'])
        self.assertTrue(data['Feature_Support']['Preferred_Timing_Mode'])
        self.assertFalse(data['Feature_Support']['Default_GTF'])

        self.assertEqual(data['Feature_Support']['Display_Type'], Display_Type.RGB)

        test_edid = [0b01011111, 0x78, 0x44, 0x99, 0b11110111]
        data = self.parser.parse_basic_display(test_edid)

        self.assertFalse(data['Video_Input'])
        self.assertEqual(data['Signal_Level_Standard'], (1.000, 0.400))
        self.assertTrue(data['Blank-to-black_setup'])
        self.assertTrue(data['Separate_syncs'])
        self.assertTrue(data['Composite_sync'])
        self.assertTrue(data['Sync_on_green_video'])
        self.assertTrue(data['Vsync_serration'])

        self.assertEqual(data['Max_Horizontal_Image_Size'], 120)
        self.assertEqual(data['Max_Vertical_Image_Size'], 68)

        self.assertEqual(data['Display_Gamma'], 2.53)

        self.assertTrue(data['Feature_Support']['Standby'])
        self.assertTrue(data['Feature_Support']['Suspend'])
        self.assertTrue(data['Feature_Support']['Active-off'])
        self.assertTrue(data['Feature_Support']['Standard-sRGB'])
        self.assertTrue(data['Feature_Support']['Preferred_Timing_Mode'])
        self.assertTrue(data['Feature_Support']['Default_GTF'])

        self.assertEqual(data['Feature_Support']['Display_Type'], Display_Type.Non_RGB)

    def test_chromaticity(self):
        test_edid = [0xF0, 0x9D, 0xA3, 0x55, 0x49, 0x9B, 0x26, 0x0F, 0x47, 0x4A]
        data = self.parser.parse_chromaticity(test_edid)

        self.assertEqual(data['Red_x'], 0.640)
        self.assertEqual(data['Red_y'], 0.335)
        self.assertEqual(data['Green_x'], 0.285)
        self.assertEqual(data['Green_y'], 0.605)
        self.assertEqual(data['Blue_x'], 0.150)
        self.assertEqual(data['Blue_y'], 0.060)
        self.assertEqual(data['White_x'], 0.280)
        self.assertEqual(data['White_y'], 0.290)

    def test_chromaticity_calculater(self):
        self.assertEqual(self.parser.calculate_chromaticity(0b10011100, 0b01), 0.610)
        self.assertEqual(self.parser.calculate_chromaticity(0b01001110, 0b10), 0.307)
        self.assertEqual(self.parser.calculate_chromaticity(0b00100110, 0b10), 0.150)

    def test_established_timings(self):
        test_edid = [0b10101010, 0b10101010]
        data = self.parser.parse_established_timings(test_edid)

        self.assertTrue(data['720x400@70Hz'])
        self.assertFalse(data['720x400@88Hz'])
        self.assertTrue(data['640x480@60Hz'])
        self.assertFalse(data['640x480@67Hz'])
        self.assertTrue(data['640x480@72Hz'])
        self.assertFalse(data['640x480@75Hz'])
        self.assertTrue(data['800x600@56Hz'])
        self.assertFalse(data['800x600@60Hz'])

        self.assertTrue(data['800x600@72Hz'])
        self.assertFalse(data['800x600@75Hz'])
        self.assertTrue(data['832x624@75Hz'])
        self.assertFalse(data['1024x768@87Hz'])
        self.assertTrue(data['1024x768@60Hz'])
        self.assertFalse(data['1024x768@70Hz'])
        self.assertTrue(data['1024x768@75Hz'])
        self.assertFalse(data['1280x1024@75Hz'])

    def test_standard_timings(self):
        test_edid = [0x81, 0x3C, 0x45, 0x7C, 0x81, 0x80, 0x8B, 0xC0, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01]
        data = self.parser.parse_standard_timings(test_edid)

        self.assertEqual(len(data), 4)

        self.assertEqual(data['Identification_1']['Horizontal_active_pixels'], 1280)
        self.assertEqual(data['Identification_1']['Vertical_active_pixels'], 800)
        self.assertEqual(data['Identification_1']['Image_aspect_ratio'], (16, 10))
        self.assertEqual(data['Identification_1']['Refresh_Rate'], 120)

        self.assertEqual(data['Identification_2']['Horizontal_active_pixels'], 800)
        self.assertEqual(data['Identification_2']['Vertical_active_pixels'], 600)
        self.assertEqual(data['Identification_2']['Image_aspect_ratio'], (4, 3))
        self.assertEqual(data['Identification_2']['Refresh_Rate'], 120)

        self.assertEqual(data['Identification_3']['Horizontal_active_pixels'], 1280)
        self.assertEqual(data['Identification_3']['Vertical_active_pixels'], 1024)
        self.assertEqual(data['Identification_3']['Image_aspect_ratio'], (5, 4))
        self.assertEqual(data['Identification_3']['Refresh_Rate'], 60)

        self.assertEqual(data['Identification_4']['Horizontal_active_pixels'], 1360)
        self.assertEqual(data['Identification_4']['Vertical_active_pixels'], 765)
        self.assertEqual(data['Identification_4']['Image_aspect_ratio'], (16, 9))
        self.assertEqual(data['Identification_4']['Refresh_Rate'], 60)

        #Note: EDID structures prior to Version 1 Revision 3 defined the bit combination of 0 0
        # to indicate a 1:1 aspect ratio
        self.parser.data['EDID_version'] = 1
        self.parser.data['EDID_reversion'] = 2
        test_edid = [0x81, 0x3C, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01]
        data = self.parser.parse_standard_timings(test_edid)

        self.assertEqual(len(data), 1)

        self.assertEqual(data['Identification_1']['Horizontal_active_pixels'], 1280)
        self.assertEqual(data['Identification_1']['Vertical_active_pixels'], 1280)
        self.assertEqual(data['Identification_1']['Image_aspect_ratio'], (1, 1))
        self.assertEqual(data['Identification_1']['Refresh_Rate'], 120)

    def test_descriptors(self):
        test_edid = [0x02, 0x3A, 0x80, 0x18, 0x71, 0x38, 0x2D, 0x40, 0x58, 0x2C, 0x45, 0x00, 0x76, 0xF2, 0x31, 0x00, 0x00, 0x1E,
                     0x66, 0x21, 0x50, 0xB0, 0x51, 0x00, 0x1B, 0x30, 0x40, 0x70, 0x36, 0x00, 0x76, 0xF2, 0x31, 0x00, 0x00, 0x1E,
                     0x00, 0x00, 0x00, 0xFC, 0x00, 0x54, 0x4F, 0x53, 0x48, 0x49, 0x42, 0x41, 0x2D, 0x54, 0x56, 0x0A, 0x20, 0x20,
                     0x00, 0x00, 0x00, 0xFD, 0x00, 0x17, 0x3D, 0x0F, 0x44, 0x0F, 0x00, 0x0A, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20]
        data = self.parser.parse_descriptors(test_edid)

        self.assertIn('Timing_Descriptor_1', data)
        self.assertIn('Timing_Descriptor_2', data)
        self.assertIn('Monitor_Name', self.parser.data)
        self.assertIn('Monitor_Range_Limits_Descriptor', data)

    def test_timing_descriptor(self):
        pass
        test_edid = [0x02, 0x3A, 0x80, 0x18, 0x71, 0x38, 0x2D, 0x40, 0x58, 0x2C, 0x45, 0x00, 0x76, 0xF2, 0x31, 0x00, 0x00, 0x1E]
        data = self.parser.parse_timing_descriptor(test_edid)

        self.assertEqual(data['Pixel_clock'], 14850)

        self.assertEqual(data['Horizontal_Active'], 1920)
        self.assertEqual(data['Horizontal_Blanking'], 280)
        self.assertEqual(data['Horizontal_Sync_Offset'], 88)
        self.assertEqual(data['Horizontal_Sync_Pulse_Width'], 44)
        self.assertEqual(data['Horizontal_Image_Size'], 886)
        self.assertEqual(data['Horizontal_Border'], 0)

        self.assertEqual(data['Vertical_Active'], 1080)
        self.assertEqual(data['Vertical_Blanking'], 45)
        self.assertEqual(data['Vertical_Sync_Offset'], 4)
        self.assertEqual(data['Vertical_Sync_Pulse_Width'], 5)
        self.assertEqual(data['Vertical_Image_Size'], 498)
        self.assertEqual(data['Vertical_Border'], 0)

        self.assertFalse(data['Flags']['Interlaced'])
        self.assertEqual(data['Flags']['Stereo_Mode'], Display_Stereo_Mode.Normal_display)
        self.assertEqual(data['Flags']['Sync_Scheme'], Timing_Sync_Scheme.Digital_Separate)
        self.assertTrue(data['Flags']['Vertical_Polarity'])
        self.assertTrue(data['Flags']['Horizontal_Polarity'])

        test_edid = [0x66, 0x21, 0x50, 0xB0, 0x51, 0x00, 0x1B, 0x30, 0x40, 0x70, 0x36, 0x00, 0x76, 0xF2, 0x31, 0x00, 0x00, 0x1E]
        data = self.parser.parse_timing_descriptor(test_edid)

        self.assertEqual(data['Pixel_clock'], 8550)

        self.assertEqual(data['Horizontal_Active'], 1360)
        self.assertEqual(data['Horizontal_Blanking'], 432)
        self.assertEqual(data['Horizontal_Sync_Offset'], 64)
        self.assertEqual(data['Horizontal_Sync_Pulse_Width'], 112)
        self.assertEqual(data['Horizontal_Image_Size'], 886)
        self.assertEqual(data['Horizontal_Border'], 0)

        self.assertEqual(data['Vertical_Active'], 768)
        self.assertEqual(data['Vertical_Blanking'], 27)
        self.assertEqual(data['Vertical_Sync_Offset'], 3)
        self.assertEqual(data['Vertical_Sync_Pulse_Width'], 6)
        self.assertEqual(data['Vertical_Image_Size'], 498)
        self.assertEqual(data['Vertical_Border'], 0)

        self.assertFalse(data['Flags']['Interlaced'])
        self.assertEqual(data['Flags']['Stereo_Mode'], Display_Stereo_Mode.Normal_display)
        self.assertEqual(data['Flags']['Sync_Scheme'], Timing_Sync_Scheme.Digital_Separate)
        self.assertTrue(data['Flags']['Vertical_Polarity'])
        self.assertTrue(data['Flags']['Horizontal_Polarity'])

    def test_stereo_mode(self):
        self.assertEqual(self.parser.decode_stereo_mode(0, 0, 0), Display_Stereo_Mode.Normal_display)
        self.assertEqual(self.parser.decode_stereo_mode(0, 0, 1), Display_Stereo_Mode.Normal_display)
        self.assertEqual(self.parser.decode_stereo_mode(0, 1, 0), Display_Stereo_Mode.Field_sequential_right)
        self.assertEqual(self.parser.decode_stereo_mode(1, 0, 0), Display_Stereo_Mode.Field_sequential_left)
        self.assertEqual(self.parser.decode_stereo_mode(0, 1, 1), Display_Stereo_Mode.Interleaved_2_way_right)
        self.assertEqual(self.parser.decode_stereo_mode(1, 0, 1), Display_Stereo_Mode.Interleaved_2_way_left)
        self.assertEqual(self.parser.decode_stereo_mode(1, 1, 0), Display_Stereo_Mode.Interleaved_4_way)
        self.assertEqual(self.parser.decode_stereo_mode(1, 1, 1), Display_Stereo_Mode.Interleaved_side_by_side)

    def test_monitor_descriptor_text(self):
        test_edid = [0x54, 0x4F, 0x53, 0x48, 0x49, 0x42, 0x41, 0x2D, 0x54, 0x56, 0x0A, 0x20, 0x20]
        self.parser.parse_monitor_descriptor_text('test_TOSHIBA-TV', test_edid)

        self.assertEqual(self.parser.data['test_TOSHIBA-TV'], 'TOSHIBA-TV')

    def test_monitor_descriptor_range_limits(self):
        test_edid = [0x17, 0x3D, 0x0F, 0x44, 0x0F, 0x00, 0x0A, 0x20, 0x20, 0x20, 0x20, 0x20, 0x20]
        data = self.parser.parse_monitor_descriptor_range_limits(test_edid)

        self.assertEqual(data['Min_Vertical_rate'], 23)
        self.assertEqual(data['Max_Vertical_rate'], 61)

        self.assertEqual(data['Min_Horizontal_rate'], 15)
        self.assertEqual(data['Max_Horizontal_rate'], 68)

        self.assertEqual(data['Max_Supported_Pixel_Clock'], 150)

        self.assertFalse(data['Secondary_GTF_curve_supported'], data)

        test_edid = [0x3D, 0x17, 0x44, 0x0F, 0x44, 0x02, 0x0A, 0x55, 0x08, 0x80, 0xCB, 0xBC, 0xAD]
        data = self.parser.parse_monitor_descriptor_range_limits(test_edid)

        self.assertEqual(data['Min_Vertical_rate'], 61)
        self.assertEqual(data['Max_Vertical_rate'], 23)

        self.assertEqual(data['Min_Horizontal_rate'], 68)
        self.assertEqual(data['Max_Horizontal_rate'], 15)

        self.assertEqual(data['Max_Supported_Pixel_Clock'], 680)

        self.assertTrue(data['Secondary_GTF_curve_supported'], data)

        self.assertEqual(data['Secondary_GTF']['Start_frequency'], 170)
        self.assertEqual(data['Secondary_GTF']['C'], 4)
        self.assertEqual(data['Secondary_GTF']['M'], 32971)
        self.assertEqual(data['Secondary_GTF']['K'], 188)
        self.assertEqual(data['Secondary_GTF']['J'], 86.5)


class EDIDInvalidTest(EDIDTest):
    """EDID Parser tests with invalid input."""

    def test_binary(self):
        #Invalid length of edid bytes list
        test_edid = [0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x24]
        self.assertRaises(EDIDParsingError, self.parser.parse_binary, test_edid)

    def test_checksum(self):
        #Invalid header
        test_edid = [0x00, 0xff, 0xff, 0x00, 0x00, 0xff, 0xff, 0x00, 0xf0 , 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0x0f]
        self.assertRaises(EDIDParsingError, self.parser.checksum, test_edid)

        #Invalid checksum
        test_edid = [0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x00, 0xf0 , 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0xf0, 0x0f]
        self.assertRaises(EDIDParsingError, self.parser.checksum, test_edid)

    def test_header(self):
        #Invalid ID Manufacturer Name
        test_edid = [0xD2, 0x62, 0x06, 0x02, 0x01, 0x01, 0x01, 0x01, 0xFF, 0x13, 0x01, 0x03]
        self.assertRaises(EDIDParsingError, self.parser.parse_header, test_edid)

        #Invalid EDID version and revision
        test_edid = [0x52, 0x62, 0x06, 0x02, 0x01, 0x01, 0x01, 0x01, 0xFF, 0x13, 0x02, 0x03]
        self.assertRaises(EDIDParsingError, self.parser.parse_header, test_edid)

if __name__ == '__main__':
    unittest.main()
