""" EDID Parser for timvideos's HDMI2USB's EDID database website!


http://en.wikipedia.org/wiki/Extended_display_identification_data
http://read.pudn.com/downloads110/ebook/456020/E-EDID%20Standard.pdf
"""

import struct

class Display_Type:
    Monochrome = 0b00
    RGB_color = 0b01
    Non_RGB_color = 0b10
    Undefined = 0b11

class EDID_Parser(object):
    def __init__(self, bin_data=None):
        """
        Preparing settings

        """

        self.data = {}

        if bin_data:
            self.parse_all(bin_data)


    def parse_all(self, bin_data):
        edid = self.parse_binary(bin_data)

        self.checksum(edid)
        self.parse_header(edid[8:20])
        self.data['Basic_display_parameters'] = self.parse_basic_display(edid[20:25])
        self.data['Filter_Chromaticity'] = self.parse_chromaticity(edid[25:35])
        self.data['Established_Timings'] = self.parse_established_timings(edid[35:38])
        self.data['Standard_Timings'] = self.parse_standard_timings(edid[38:54])
        self.data['Descriptors'] = self.parse_descriptors(edid[54:125])


    def parse_binary(self, bin_data):
        """Converts string to list of bytes, supports first 128 bytes only

        bin_data is a string of bytes"""

        if len(bin_data) < 128:
            raise EDIDParsingError("Binary file is smaller than 128 bytes.")

        return struct.unpack("b" * 128, bin_data[:128])


    def checksum(self, edid):
        """Checks EDID header and checksum

        edid is a list of bytes"""

        #Check EDID header
        if not [x & 0xff for x in edid[0:8]] == [0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x00]:
            raise EDIDParsingError("Input is not an EDID file.")

        #Check EDID checksum
        if not sum(bytearray([chr(x & 0xff) for x in edid])) % 256 == 0:
            raise EDIDParsingError("Checksum is currupt.")

        self.data['Extension_Flag'] = edid[126]


    def parse_header(self, edid):
        """Parses "Vendor / Product Identification" and "EDID Structure Version / Revision"

        edid is list of bytes 8 (08h) to 19 (13h)"""

        #ID Manufacturer Name: edid[8:10]
        if (edid[0] >> 7 == 0):
            first = (edid[0] & 0b01111100) >> 2
            second = ((edid[0] & 0b00000011) << 3) + ((edid[1] & 0b11100000) >> 5)
            third = edid[1] & 0b00011111

            self.data['ID_Manufacturer_Name'] = chr(first + 64) + chr(second + 64) + chr(third + 64)
        else:
            raise EDIDParsingError("ID Manufacturer Name field is currupt.")


        #ID Product Code: edid[12:10]
        self.data['ID_Product_Code'] = "%02x%02x" % (edid[3], edid[2])

        #ID Serial Number: edid[12:16]
        self.data['ID_Serial_Number'] = edid[4] + (edid[5] << 8) + (edid[6] << 16) + (edid[7] << 24)

        #Week of manufacture and Year of manufacture: edid[16:17]
        self.data['Week_of_manufacture'] = edid[8] & 0xff
        self.data['Year_of_manufacture'] = edid[9] + 1990

        #EDID version and revision: edid[18:19]
        if (edid[10], edid[11]) in [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 0)]:
            self.data['EDID_version'] = edid[10]
            self.data['EDID_revision'] = edid[11]
        else:
            raise EDIDParsingError("EDID version and revision %d.%d are invalid." % (edid[10], edid[11]))


    def parse_basic_display(self, edid):
        """Parses "Basic Display Parameters / Features"

        edid is list of bytes 20 (14h) to 24 (18h)"""

        new_data = {}

        new_data['Video_Input'] = edid[0] >> 7
        #Analog Input
        if new_data['Video_Input'] == 0:
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
        #Digital Input
        else:
            #If True: Interface is signal compatible with VESA DFP 1.x TMDS CRGB,
            # 1 pixel / clock, up to 8 bits / color MSB aligned, DE active high
            new_data['Video_Input_DFP_1'] = edid[0] & 0b00000001

        #If either or both bytes are set to zero, then the system shall make no assumptions regarding the display size.
        # e.g. A projection display may be of indeterminate size.
        new_data['Max_Horizontal_Image_Size'] = edid[1]
        new_data['Max_Vertical_Image_Size'] = edid[2]

        if edid[3] == 0xFF:
            new_data['Display_Gamma'] = None
        else:
            new_data['Display_Gamma'] = float(edid[3] + 100) / 100

        new_data['Feature_Support'] = {'Standby': (edid[4] & 0b10000000) >> 7,
                            'Suspend': (edid[4] & 0b01000000) >> 6,
                            'Active-off': (edid[4] & 0b00100000) >> 5,
                            'Display_Type': (edid[4] & 0b00011000) >> 3,
                            'Standard-sRGB': (edid[4] & 0b00000100) >> 2,
                            'Preferred_Timing_Mode': (edid[4] & 0b00000010) >> 1,
                            'Default_GTF': edid[4] & 0b00000001}

#        if not new_data['Feature_Support']['Preferred_Timing_Mode']:
#            if (self.data['EDID_version'] == 1 and self.data['EDID_reversion'] >= 3) or self.data['EDID_version'] > 1:
#                #Warning
#                print "Use of preferred timing mode is required by EDID Structure Version 1 Revision 3 and higher."

        return new_data


    def parse_chromaticity(self, edid):
        """Parses "Chromaticity"

        edid is list of bytes 25 (19h) to 34 (22h)"""

        #Extract low bits
        Red_low_x = (edid[0] & 0b11000000) >> 6
        Red_low_y = (edid[0] & 0b00110000) >> 4
        Green_low_x = (edid[0] & 0b00001100) >> 2
        Green_low_y = edid[0] & 0b00000011
        Blue_low_x = (edid[1] & 0b11000000) >> 6
        Blue_low_y = (edid[1] & 0b00110000) >> 4
        White_low_x = (edid[1] & 0b00001100) >> 2
        White_low_y = edid[1] & 0b00000011

        #Get the rest of the bits
        Red_high_x = edid[2] & 0xff
        Red_high_y = edid[3] & 0xff
        Green_high_x = edid[4] & 0xff
        Green_high_y = edid[5] & 0xff
        Blue_high_x = edid[6] & 0xff
        Blue_high_y = edid[7] & 0xff
        White_high_x = edid[8] & 0xff
        White_high_y = edid[9] & 0xff

        #Combine all bits and convert them to decimal fractions
        new_data = {}
        new_data['Red_x'] = ((Red_high_x << 2) + Red_low_x) / 2.0**10
        new_data['Red_y'] = ((Red_high_y << 2) + Red_low_y) / 2.0**10
        new_data['Green_x'] = ((Green_high_x << 2) + Green_low_x) / 2.0**10
        new_data['Green_y'] = ((Green_high_y << 2) + Green_low_y) / 2.0**10
        new_data['Blue_x'] = ((Blue_high_x << 2) + Blue_low_x) / 2.0**10
        new_data['Blue_y'] = ((Blue_high_y << 2) + Blue_low_y) / 2.0**10
        new_data['White_x'] = ((White_high_x << 2) + White_low_x) / 2.0**10
        new_data['White_y'] = ((White_high_y << 2) + White_low_y) / 2.0**10

        return new_data


    def parse_established_timings(self, edid):
        """Parses "Established Timings"

        edid is list of bytes 35 (23h) to 37 (25h)"""

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
        """Parses "Standard Timing Identification"

        edid is list of bytes 38 (26h) to 53 (35h)"""

        new_data = {}

        for i in range(0, 15, 2):
            #Check if the field is not unused (both bytes are 0b01)
            if (edid[i] & 0xff) is not 0b01 and (edid[i + 1] & 0xff) is not 0b01:
                id = {}
                id['Horizontal_active_pixels'] = (((edid[i] & 0xff) + 31) * 8)
                id['Refresh_Rate'] = ((edid[i + 1] & 0xff) & 0b00111111) + 60

                id['Image_aspect_ratio'] = ((edid[i + 1] & 0xff) & 0b11000000) >> 6
                if id['Image_aspect_ratio'] == 0b00:
                    if (self.data['EDID_version'] <= 1) and (self.data['EDID_reversion'] < 3):
                        id['Image_aspect_ratio'] = (1, 1)
                    else:
                        id['Image_aspect_ratio'] = (16, 10)
                elif id['Image_aspect_ratio'] == 0b01:
                    id['Image_aspect_ratio'] = (4, 3)
                elif id['Image_aspect_ratio'] == 0b10:
                    id['Image_aspect_ratio'] = (5, 4)
                elif id['Image_aspect_ratio'] == 0b11:
                    id['Image_aspect_ratio'] = (16, 9)

                id['Vertical_active_pixels'] = ((id['Horizontal_active_pixels'] * id['Image_aspect_ratio'][1]) / id['Image_aspect_ratio'][0])

                new_data['Identification_%d' % ((i / 2) + 1)] = id

        return new_data


    def parse_descriptors(self, edid):
        """Parses "Standard Timing Identification"

        edid is list of bytes 54 (36h) to 125 (7Dh)"""

        new_data = {}

        for i in range(0, 71, 18):
            if not (((edid[i] & 0xff) << 8) + (edid[i + 1] & 0xff)) == 0x0000:
                new_data['Timing_Descriptor_%d' % ((i / 18) + 1)] = self.parse_timing_descriptor(edid[i:i + 18])
            else:
                tmp_edid = edid[i + 5:i + 18]
                if ((edid[i + 3] & 0xff) == 0xff):
                    self.parse_monitor_descriptor_text("Monitor_Serial_Number", tmp_edid)
                elif ((edid[i + 3] & 0xff) == 0xfe):
                    self.parse_monitor_descriptor_text("Data_String", tmp_edid)
                elif ((edid[i + 3] & 0xff) == 0xfd):
                    new_data["Monitor_Range_Limits_Descriptor"] = self.parse_monitor_descriptor_range_limits(tmp_edid)
                elif ((edid[i + 3] & 0xff) == 0xfc):
                    self.parse_monitor_descriptor_text("Monitor_Name", tmp_edid)
                elif ((edid[i + 3] & 0xff) == 0xfb):
                    print "Descriptor contains additional color point data, NOT supported yet."
                elif ((edid[i + 3] & 0xff) == 0xfa):
                    print "Descriptor contains additional Standard Timing Identifications, NOT supported yet."

        return new_data


    def parse_timing_descriptor(self, edid):
        """Parses "Detailed Timing Descriptor"

        edid is list of 18 bytes"""

        new_data = {}

        new_data['Pixel_clock'] = ((edid[1] & 0xff) << 8) + (edid[0] & 0xff)

        new_data['Horizontal_Active'] = ((edid[4] & 0b11110000) << 4) + (edid[2] & 0xff)
        new_data['Horizontal_Blanking'] = ((edid[4] & 0b00001111) << 8) + (edid[3] & 0xff)

        new_data['Vertical_Active'] = ((edid[7] & 0b11110000) << 4) + (edid[5] & 0xff)
        new_data['Vertical_Blanking'] = ((edid[7] & 0b00001111) << 8) + (edid[6] & 0xff)

        new_data['Horizontal_Sync_Offset'] = ((edid[11] & 0b11000000) << 4) + (edid[8] & 0xff)
        new_data['Horizontal_Sync_Pulse_Width'] = ((edid[11] & 0b00110000) << 8) + (edid[9] & 0xff)

        new_data['Vertical_Sync_Offset'] = ((edid[11] & 0b00001100) << 4)\
                                           + (edid[10] & 0b11110000) >> 4
        new_data['Vertical_Sync_Pulse_Width'] = ((edid[11] & 0b00000011) << 8)\
                                                + (edid[10] & 0b00001111)

        new_data['Horizontal_Image_Size'] = ((edid[14] & 0b11110000) << 4) + (edid[12] & 0xff)
        new_data['Vertical_Image_Size'] = ((edid[14] & 0b00001111) << 8) + (edid[13] & 0xff)

        new_data['Horizontal_Border'] = (edid[15] & 0xff)
        new_data['Vertical_Border'] = (edid[16] & 0xff)

        #TODO: Need rewrite to parse these deeply
        new_data['Flags'] = {'Interlaced': ((edid[17] & 0xff) & 0b10000000) >> 7,
                        'Stereo_Mode': ((edid[17] & 0xff) & 0b01100000) >> 5,
                        'Sync': ((edid[17] & 0xff) & 0b00011000) >> 3,
                        'Bit_2': ((edid[17] & 0xff) & 0b00000100) >> 2,
                        'Bit_1': ((edid[17] & 0xff) & 0b00000010) >> 1,
                        'Stereo_Mode_x': (edid[17] & 0xff) & 0b00000001}

        return new_data


    def parse_monitor_descriptor_text(self, name, edid):
        """Parses texts descriptor

        edid is list of bytes 5 (05h) to 18 (12h)"""

        output = ""

        for x in range(0, 13):
            if edid[x] == 0x0a:
                break

            output = output + chr(edid[x])

        self.data[name] = output

    def parse_monitor_descriptor_range_limits(self, edid):
        """Parses monitor range limits descriptor

        edid is list of bytes 5 (05h) to 18 (12h)"""

        new_data = {}

        new_data['Min_Vertical_rate'] = (edid[0] & 0xff)
        new_data['Max_Vertical_rate'] = (edid[1] & 0xff)

        new_data['Min_Horizontal_rate'] = (edid[2] & 0xff)
        new_data['Max_Horizontal_rate'] = (edid[3] & 0xff)

        new_data['Max_Supported_Pixel_Clock'] = (edid[4] & 0xff) * 10

        if ((edid[5] & 0xff) == 0x02):
            gtf = {}

            gtf['Start_frequency'] = (edid[7] & 0xff) * 2
            gtf['C'] = (edid[8] & 0xff) / 2
            gtf['M'] = (((edid[9] & 0xff) << 8) + (edid[10] & 0xff))
            gtf['K'] = (edid[11] & 0xff)
            gtf['J'] = (edid[12] & 0xff) / 2

            new_data['Generalized_Timing_Formula'] = gtf

        return new_data


class EDIDParsingError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


if __name__ == "__main__":
    import sys
    import pprint

    with open(sys.argv[1], 'rb') as file:
        bin_data = file.read()

    my_edid = EDID_Parser(bin_data)
    print pprint.pprint(my_edid.data)
