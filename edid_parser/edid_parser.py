"""
EDID Parser for timvideos's HDMI2USB's EDID.tv website!


http://en.wikipedia.org/wiki/Extended_display_identification_data
http://read.pudn.com/downloads110/ebook/456020/E-EDID%20Standard.pdf
"""
# C0103: Invalid name
# R0201: Method could be a function (no-self-use)
# R0914: Too many local variables
# pylint: disable-msg=C0103,R0201,R0914

import struct


class DisplayType(object):
    Monochrome = 0b00
    RGB = 0b01
    Non_RGB = 0b10
    Undefined = 0b11


class ColorBitDepth(object):
    Undefined = 0b000
    Depth_6_bit = 0b001
    Depth_8_bit = 0b010
    Depth_10_bit = 0b011
    Depth_12_bit = 0b100
    Depth_14_bit = 0b101
    Depth_16_bit = 0b110


class DigitalVideoInterface(object):
    Undefined = 0b0000
    DVI = 0b0001
    HDMI_A = 0b0010
    HDMI_B = 0b0011
    MDDI = 0b0100
    DisplayPort = 0b0101


class DisplayStereoMode(object):
    Normal_display = 0b000
    Field_sequential_right = 0b010
    Field_sequential_left = 0b100
    Interleaved_2_way_right = 0b011
    Interleaved_2_way_left = 0b101
    Interleaved_4_way = 0b110
    Interleaved_side_by_side = 0b111


class TimingSyncScheme(object):
    Analog_Composite = 0b00
    Bipolar_Analog_Composite = 0b01
    Digital_Composite = 0b10
    Digital_Separate = 0b11


class CVTSupportDefinitionPreferredAspectRatio(object):
    AR_4_3 = 0b000
    AR_16_9 = 0b001
    AR_16_10 = 0b010
    AR_5_4 = 0b011
    AR_15_9 = 0b100


class EDIDParser(object):
    def __init__(self, bin_data=None):
        """
        Preparing settings
        """

        self.data = {}
        self.bin_data = bin_data

        if self.bin_data:
            self.parse_all()

    def parse_all(self):
        edid = self.parse_binary()

        self.checksum(edid)
        self.parse_header(edid[8:20])
        self.data['Basic_display_parameters'] = \
            self.parse_basic_display(edid[20:25])
        self.data['Chromaticity'] = self.parse_chromaticity(edid[25:35])
        self.data['Established_Timings'] = \
            self.parse_established_timings(edid[35:38])
        self.data['Standard_Timings'] = \
            self.parse_standard_timings(edid[38:54])
        self.data['Descriptors'] = self.parse_descriptors(edid[54:126])

    def parse_binary(self):
        """
        Converts string to list of bytes, supports first 128 bytes only

        bin_data is a string of bytes
        """

        if len(self.bin_data) < 128:
            raise EDIDParsingError("Binary file is smaller than 128 bytes.")

        return struct.unpack("B" * 128, self.bin_data[:128])

    def checksum(self, edid):
        """
        Checks EDID header and checksum

        edid is a list of bytes
        """

        # Check EDID header
        if not [x for x in edid[0:8]] == [0x00, 0xff, 0xff, 0xff, 0xff, 0xff,
                                          0xff, 0x00]:
            raise EDIDParsingError("Input is not an EDID file.")

        # Check EDID checksum
        if not sum(bytearray([chr(x) for x in edid])) % 256 == 0:
            raise EDIDParsingError("Checksum is corrupt.")

        self.data['Extension_Flag'] = edid[126]

    def parse_header(self, edid):
        """
        Parses "Vendor / Product Identification" and
        "EDID Structure Version / Revision"

        edid is list of bytes 8 (08h) to 19 (13h)
        """

        # ID Manufacturer Name: edid[8:10]
        if edid[0] >> 7 == 0:
            first = (edid[0] & 0b01111100) >> 2
            second = ((edid[0] & 0b00000011) << 3) + \
                     ((edid[1] & 0b11100000) >> 5)
            third = edid[1] & 0b00011111

            self.data['ID_Manufacturer_Name'] = (chr(first + 64) +
                                                 chr(second + 64) +
                                                 chr(third + 64))
        else:
            raise EDIDParsingError("ID Manufacturer Name field is corrupt.")

        # ID Product Code: edid[12:10]
        self.data['ID_Product_Code'] = "%02x%02x" % (edid[3], edid[2])
        #TODO: v1.1 works this way?
        #self.data['ID_Product_Code'] = edid[2] + (edid[3] << 8)

        # ID Serial Number: edid[12:16]
        self.data['ID_Serial_Number'] = (
            edid[4] + (edid[5] << 8) + (edid[6] << 16) + (edid[7] << 24)
        )

        # Week of manufacture and Year of manufacture: edid[16:17]
        if edid[8] > 0x36 and edid[8] < 0xFF:
            raise EDIDParsingError("Week of manufacture (%d) is invalid." %
                                   (edid[8]))

        year = edid[9] + 1990
        if edid[8] == 0xff:
            self.data['Model_Year'] = year
        else:
            self.data['Week_of_manufacture'] = edid[8]
            self.data['Year_of_manufacture'] = year

        # EDID version and revision: edid[18:19]
        if (edid[10], edid[11]) in [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
                                    (2, 0)]:
            self.data['EDID_version'] = edid[10]
            self.data['EDID_revision'] = edid[11]
        else:
            raise EDIDParsingError("EDID version and revision %d.%d are"
                                   " invalid." % (edid[10], edid[11]))

    def parse_basic_display(self, edid):
        """
        Parses "Basic Display Parameters / Features"

        edid is list of bytes 20 (14h) to 24 (18h)
        """

        new_data = {}

        new_data['Feature_Support'] = {
            'Standby': (edid[4] & 0b10000000) >> 7,
            'Suspend': (edid[4] & 0b01000000) >> 6,
            'Active-off': (edid[4] & 0b00100000) >> 5,
            'Standard-sRGB': (edid[4] & 0b00000100) >> 2,
            'Preferred_Timing_Mode': (edid[4] & 0b00000010) >> 1,
        }

        new_data['Video_Input'] = edid[0] >> 7
        if new_data['Video_Input'] == 0:
            # Analog Input
            signal_level_standard = (edid[0] & 0b01100000) >> 5
            if signal_level_standard == 0b00:
                new_data['Signal_Level_Standard'] = (0.700, 0.300)
            elif signal_level_standard == 0b01:
                new_data['Signal_Level_Standard'] = (0.714, 0.286)
            elif signal_level_standard == 0b10:
                new_data['Signal_Level_Standard'] = (1.000, 0.400)
            elif signal_level_standard == 0b11:
                new_data['Signal_Level_Standard'] = (0.700, 0.000)

            new_data['Blank-to-black_setup'] = (edid[0] & 0b00010000) >> 4
            new_data['Separate_syncs'] = (edid[0] & 0b00001000) >> 3
            new_data['Composite_sync'] = (edid[0] & 0b00000100) >> 2
            new_data['Sync_on_green_video'] = (edid[0] & 0b00000010) >> 1
            new_data['Vsync_serration'] = edid[0] & 0b00000001
        else:
            # Digital Input
            if self.data['EDID_version'] == 1 \
                    and self.data['EDID_revision'] == 4:
                new_data['Color_Bit_Depth'] = (edid[0] & 0b01110000) >> 4
                new_data['Digital_Video_Interface'] = edid[0] & 0b00001111

                new_data['Feature_Support']['Color_Encoding_RGB444_Supported'] \
                    = True
                new_data['Feature_Support']['Color_Encoding_YCrCb444_Supported'] \
                    = (edid[4] & 0b00001000) != 0
                new_data['Feature_Support']['Color_Encoding_YCrCb422_Supported'] \
                    = (edid[4] & 0b00010000) != 0
            else:
                new_data['Video_Input_DFP_1'] = edid[0] & 0b00000001

        if self.data['EDID_version'] == 1 and self.data['EDID_revision'] == 4:
            if not (edid[1] == 0 and edid[2] == 0):
                if edid[1] == 0:
                    new_data['Aspect_Ratio'] = round(100.0 / (edid[2] + 99), 2)
                elif edid[2] == 0:
                    new_data['Aspect_Ratio'] = round((edid[1] + 99) / 100.0, 2)
                else:
                    new_data['Horizontal_Screen_Size'] = edid[1]
                    new_data['Vertical_Screen_Size'] = edid[2]

            new_data['Feature_Support']['Continuous_Frequency'] = \
                edid[4] & 0b00000001
        else:
            # If either or both bytes are set to zero, then the system shall
            # make no assumptions regarding the display size. e.g. A
            # projection display may be of indeterminate size.
            new_data['Max_Horizontal_Image_Size'] = edid[1]
            new_data['Max_Vertical_Image_Size'] = edid[2]

            new_data['Feature_Support']['Default_GTF'] = edid[4] & 0b00000001

        if (self.data['EDID_version'] == 1 and self.data['EDID_revision'] < 4) \
                or new_data['Video_Input'] == 0:
            new_data['Feature_Support']['Display_Type'] = \
                (edid[4] & 0b00011000) >> 3

        if edid[3] == 0xFF:
            new_data['Display_Gamma'] = None
        else:
            new_data['Display_Gamma'] = float(edid[3] + 100) / 100

#        if not new_data['Feature_Support']['Preferred_Timing_Mode']:
#            if (self.data['EDID_version'] == 1 and
#                   self.data['EDID_revision'] >= 3) or
#                   self.data['EDID_version'] > 1:
#                #Warning
#                print 'Use of preferred timing mode is required by'
#                      'EDID Structure Version 1 Revision 3 and higher.'

        return new_data

    def parse_chromaticity(self, edid):
        """
        Parses "Chromaticity"

        edid is list of bytes 25 (19h) to 34 (22h)
        """

        # Extract low bits
        red_low_x = (edid[0] & 0b11000000) >> 6
        red_low_y = (edid[0] & 0b00110000) >> 4
        green_low_x = (edid[0] & 0b00001100) >> 2
        green_low_y = edid[0] & 0b00000011
        blue_low_x = (edid[1] & 0b11000000) >> 6
        blue_low_y = (edid[1] & 0b00110000) >> 4
        white_low_x = (edid[1] & 0b00001100) >> 2
        white_low_y = edid[1] & 0b00000011

        # Get the rest of the bits
        red_high_x = edid[2]
        red_high_y = edid[3]
        green_high_x = edid[4]
        green_high_y = edid[5]
        blue_high_x = edid[6]
        blue_high_y = edid[7]
        white_high_x = edid[8]
        white_high_y = edid[9]

        # Combine all bits and convert them to decimal fractions
        new_data = {
            'Red_x': self.calculate_chromaticity(red_high_x, red_low_x),
            'Red_y': self.calculate_chromaticity(red_high_y, red_low_y),
            'Green_x': self.calculate_chromaticity(green_high_x, green_low_x),
            'Green_y': self.calculate_chromaticity(green_high_y, green_low_y),
            'Blue_x': self.calculate_chromaticity(blue_high_x, blue_low_x),
            'Blue_y': self.calculate_chromaticity(blue_high_y, blue_low_y),
            'White_x': self.calculate_chromaticity(white_high_x, white_low_x),
            'White_y': self.calculate_chromaticity(white_high_y, white_low_y),
        }

        return new_data

    def calculate_chromaticity(self, high, low):
        return round(((high << 2) + low) / 2.0 ** 10, 3)

    def parse_established_timings(self, edid):
        """
        Parses "Established Timings"

        edid is list of bytes 35 (23h) to 37 (25h)
        """

        new_data = {}

        new_data['720x400@70Hz'] = (edid[0] & 0b10000000) >> 7
        new_data['720x400@88Hz'] = (edid[0] & 0b01000000) >> 6
        new_data['640x480@60Hz'] = (edid[0] & 0b00100000) >> 5
        new_data['640x480@67Hz'] = (edid[0] & 0b00010000) >> 4
        new_data['640x480@72Hz'] = (edid[0] & 0b00001000) >> 3
        new_data['640x480@75Hz'] = (edid[0] & 0b00000100) >> 2
        new_data['800x600@56Hz'] = (edid[0] & 0b00000010) >> 1
        new_data['800x600@60Hz'] = edid[0] & 0b00000001

        new_data['800x600@72Hz'] = (edid[1] & 0b10000000) >> 7
        new_data['800x600@75Hz'] = (edid[1] & 0b01000000) >> 6
        new_data['832x624@75Hz'] = (edid[1] & 0b00100000) >> 5
        new_data['1024x768@87Hz'] = (edid[1] & 0b00010000) >> 4
        new_data['1024x768@60Hz'] = (edid[1] & 0b00001000) >> 3
        new_data['1024x768@70Hz'] = (edid[1] & 0b00000100) >> 2
        new_data['1024x768@75Hz'] = (edid[1] & 0b00000010) >> 1
        new_data['1280x1024@75Hz'] = edid[1] & 0b00000001

        return new_data

    def parse_standard_timings(self, edid):
        """
        Parses "Standard Timing Identification"

        edid is list of bytes 38 (26h) to 53 (35h)
        """

        new_data = {}

        for i in range(0, 15, 2):
            # Check if the field is not unused (both bytes are 0b01)
            if edid[i] is not 0b01 and edid[i + 1] is not 0b01:
                timing = {
                    'Horizontal_active': ((edid[i] + 31) * 8),
                    'Refresh_Rate': (edid[i + 1] & 0b00111111) + 60,
                    'Image_aspect_ratio': (edid[i + 1] & 0b11000000) >> 6
                }

                if timing['Image_aspect_ratio'] == 0b00:
                    if (self.data['EDID_version'] <= 1) and \
                       (self.data['EDID_revision'] < 3):
                        timing['Image_aspect_ratio'] = (1, 1)
                    else:
                        timing['Image_aspect_ratio'] = (16, 10)
                elif timing['Image_aspect_ratio'] == 0b01:
                    timing['Image_aspect_ratio'] = (4, 3)
                elif timing['Image_aspect_ratio'] == 0b10:
                    timing['Image_aspect_ratio'] = (5, 4)
                elif timing['Image_aspect_ratio'] == 0b11:
                    timing['Image_aspect_ratio'] = (16, 9)

                timing['Vertical_active'] = (
                    (timing['Horizontal_active'] *
                     timing['Image_aspect_ratio'][1]) /
                    timing['Image_aspect_ratio'][0]
                )

                new_data['Identification_%d' % ((i / 2) + 1)] = timing

        return new_data

    def parse_descriptors(self, edid):
        """
        Parses "Descriptors"

        edid is list of bytes 54 (36h) to 125 (7Dh)
        """

        new_data = {}

        for i in range(0, 71, 18):
            if not (((edid[i] << 8) + edid[i + 1]) == 0x0000 and
                    edid[i + 2] == 0x00):
                new_data['Timing_Descriptor_%d' % ((i / 18) + 1)] = \
                    self.parse_timing_descriptor(edid[i:i + 18])
            else:
                tmp_edid = edid[i + 5:i + 18]
                if edid[i + 3] == 0xff:
                    self.parse_monitor_descriptor_text(
                        "Monitor_Serial_Number", tmp_edid)
                elif edid[i + 3] == 0xfe:
                    # TODO: Fix for multiple strings
                    # See "6.2  Example 2 - Legacy EDID example for reference"
                    # from "VESA Enhanced EDID Standard Release A, Rev.1"
                    self.parse_monitor_descriptor_text(
                        "Monitor_Data_String", tmp_edid)
                elif edid[i + 3] == 0xfd:
                    new_data["Monitor_Range_Limits_Descriptor"] = \
                        self.parse_monitor_descriptor_range_limits(tmp_edid)
                elif edid[i + 3] == 0xfc:
                    self.parse_monitor_descriptor_text(
                        "Monitor_Name", tmp_edid)
                elif edid[i + 3] == 0xfb:
                    new_data["Additional_Color_Point"] = \
                        "Not supported yet."
                elif edid[i + 3] == 0xfa:
                    new_data["Additional_Standard_Timing"] = \
                        "Not supported yet."

        return new_data

    def parse_timing_descriptor(self, edid):
        """
        Parses "Detailed Timing Descriptor"

        edid is list of 18 bytes
        """

        new_data = {}

        # Pixel clock in kHz
        new_data['Pixel_clock'] = ((edid[1] << 8) + edid[0]) * 10

        new_data['Horizontal_Active'] = (
            ((edid[4] & 0b11110000) << 4) + edid[2]
        )
        new_data['Horizontal_Blanking'] = (
            ((edid[4] & 0b00001111) << 8) + edid[3]
        )

        new_data['Vertical_Active'] = (
            ((edid[7] & 0b11110000) << 4) + edid[5]
        )
        new_data['Vertical_Blanking'] = (
            ((edid[7] & 0b00001111) << 8) + edid[6]
        )

        new_data['Horizontal_Sync_Offset'] = (
            ((edid[11] & 0b11000000) << 4) + edid[8]
        )
        new_data['Horizontal_Sync_Pulse_Width'] = (
            ((edid[11] & 0b00110000) << 8) + edid[9]
        )

        new_data['Vertical_Sync_Offset'] = (
            ((edid[11] & 0b00001100) << 4) + (edid[10] & 0b11110000) >> 4
        )
        new_data['Vertical_Sync_Pulse_Width'] = (
            ((edid[11] & 0b00000011) << 8) + (edid[10] & 0b00001111)
        )

        new_data['Horizontal_Image_Size'] = (
            ((edid[14] & 0b11110000) << 4) + edid[12]
        )
        new_data['Vertical_Image_Size'] = (
            ((edid[14] & 0b00001111) << 8) + edid[13]
        )

        new_data['Horizontal_Border'] = edid[15]
        new_data['Vertical_Border'] = edid[16]

        flags = {}

        flags['Interlaced'] = (edid[17] & 0b10000000) >> 7
        flags['Stereo_Mode'] = self.decode_stereo_mode(
            (edid[17] & 0b01000000) >> 6,
            (edid[17] & 0b00100000) >> 5,
            edid[17] & 0b00000001
        )
        flags['Sync_Scheme'] = (edid[17] & 0b00011000) >> 3

        bit_2 = (edid[17] & 0b00000100) >> 2
        bit_1 = (edid[17] & 0b00000010) >> 1

        if flags['Sync_Scheme'] == TimingSyncScheme.Digital_Separate:
            flags['Vertical_Polarity'] = bit_2
            flags['Horizontal_Polarity'] = bit_1
        else:
            flags['Serrate'] = bit_2

            if flags['Sync_Scheme'] == TimingSyncScheme.Digital_Composite:
                flags['Composite_Polarity'] = bit_1
            else:
                flags['Sync_On_RGB'] = bit_1

        new_data['Flags'] = flags

        return new_data

    def decode_stereo_mode(self, bit_6, bit_5, bit_0):
        """
        Decodes stereo mode bits.
        """

        if bit_6 == 0 and bit_5 == 0:
            stereo_mode = DisplayStereoMode.Normal_display
        elif bit_6 == 0 and bit_5 == 1 and bit_0 == 0:
            stereo_mode = DisplayStereoMode.Field_sequential_right
        elif bit_6 == 1 and bit_5 == 0 and bit_0 == 0:
            stereo_mode = DisplayStereoMode.Field_sequential_left
        elif bit_6 == 0 and bit_5 == 1 and bit_0 == 1:
            stereo_mode = DisplayStereoMode.Interleaved_2_way_right
        elif bit_6 == 1 and bit_5 == 0 and bit_0 == 1:
            stereo_mode = DisplayStereoMode.Interleaved_2_way_left
        elif bit_6 == 1 and bit_5 == 1 and bit_0 == 0:
            stereo_mode = DisplayStereoMode.Interleaved_4_way
        elif bit_6 == 1 and bit_5 == 1 and bit_0 == 1:
            stereo_mode = DisplayStereoMode.Interleaved_side_by_side

        return stereo_mode

    def parse_monitor_descriptor_text(self, name, edid):
        """
        Parses texts descriptor

        edid is list of bytes 5 (05h) to 18 (12h)
        """

        output = ""

        for index in range(0, 13):
            if edid[index] == 0x0a:
                break

            output += chr(edid[index])

        self.data[name] = output

    def parse_monitor_descriptor_range_limits(self, edid):
        """
        Parses monitor range limits descriptor

        edid is list of bytes 5 (05h) to 18 (12h)
        """

        new_data = {}

        new_data['Min_Vertical_rate'] = edid[0]
        new_data['Max_Vertical_rate'] = edid[1]

        new_data['Min_Horizontal_rate'] = edid[2]
        new_data['Max_Horizontal_rate'] = edid[3]

        new_data['Max_Supported_Pixel_Clock'] = edid[4] * 10

        new_data['Coordinated_Video_Timings_supported'] = False
        new_data['Secondary_GTF_curve_supported'] = False

        if edid[5] == 0x02:
            new_data['Secondary_GTF_curve_supported'] = True
            gtf = {}

            gtf['Start_frequency'] = edid[7] * 2
            gtf['C'] = float(edid[8]) / 2
            gtf['M'] = (edid[9] << 8) + edid[10]
            gtf['K'] = edid[11]
            gtf['J'] = float(edid[12]) / 2

            new_data['Secondary_GTF'] = gtf
        elif edid[5] == 0x04:
            new_data['Coordinated_Video_Timings_supported'] = True
            new_data['Max_Supported_Pixel_Clock'] -= (edid[7] >> 2) * 0.25
            new_data['Max_Active_Pixels_per_Line'] = (((edid[7] & 0b11) << 8) + edid[8]) * 8
            new_data['Aspect_Ratio_4:3_supported'] = \
                (edid[9] & 0b10000000) != 0
            new_data['Aspect_Ratio_16:9_supported'] = \
                (edid[9] & 0b01000000) != 0
            new_data['Aspect_Ratio_16:10_supported'] = \
                (edid[9] & 0b00100000) != 0
            new_data['Aspect_Ratio_5:4_supported'] = \
                (edid[9] & 0b00010000) != 0
            new_data['Aspect_Ratio_15:9_supported'] = \
                (edid[9] & 0b00001000) != 0
            new_data['Preferred_Aspect_Ratio'] = edid[10] >> 5
            new_data['CVT_Standard_Blanking_supported'] = \
                (edid[10] & 0b01000) != 0
            new_data['CVT_Reduced_Blanking_supported'] = \
                (edid[10] & 0b10000) != 0
            new_data['Horizontal_Shrink_supported'] = \
                (edid[11] & 0b10000000) != 0
            new_data['Horizontal_Stretch_supported'] = \
                (edid[11] & 0b01000000) != 0
            new_data['Vertical_Shrink_supported'] = \
                (edid[11] & 0b00100000) != 0
            new_data['Vertical_Stretch_supported'] = \
                (edid[11] & 0b00010000) != 0
            new_data['Preferred_Vertical_Refresh_Rate'] = edid[12]

        return new_data


class EDIDParsingError(Exception):
    def __init__(self, value):
        super(EDIDParsingError, self).__init__()

        self.value = value

    def __str__(self):
        return self.value


if __name__ == "__main__":
    import sys
    import pprint

    with open(sys.argv[1], 'rb') as edid_file:
        TEMP_EDID = EDIDParser(edid_file.read())

    print pprint.pprint(TEMP_EDID.data)
