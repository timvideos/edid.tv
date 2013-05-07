""" EDID Parser for timvideos's HDMI2USB's EDID database website!


http://en.wikipedia.org/wiki/Extended_display_identification_data
http://read.pudn.com/downloads110/ebook/456020/E-EDID%20Standard.pdf
"""

import struct

class EDID_Parser(object):
    edid = None
    data = {}

    def __init__(self, bin_data):
        """
        Preparing settings

        """

        self.edid = struct.unpack("b" * 128, bin_data)

        if sum(bytearray([chr(x & 0xff) for x in self.edid])) % 256 == 0:
            print "Checksum passed!"
        else:
            print "Currupt EDID file!"

        self.parse_header()
        self.data['Basic_display_parameters'] = self.parse_basic_display()
        self.data['Filter_Chromaticity'] = self.parse_chromaticity()
        self.data['Established_Timings'] = self.parse_established_timings()
        self.data['Standard_Timings'] = self.parse_standard_timings()
        self.data['Descriptors'] = self.parse_descriptors()


    def parse_header(self):
        #Check EDID header
        if [x & 0xff for x in self.edid[0:8]] == [0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x00]:
            print "This is indeed EDID file!"
        else:
            print "Header is currupt!"

        #ID Manufacturer Name: edid[8:10]
        if (self.edid[8] >> 7 == 0):
            first = (self.edid[8] & 0b01111100) >> 2
            second = ((self.edid[8] & 0b00000011) << 3) + ((self.edid[9] & 0b11100000) >> 5)
            third = self.edid[9] & 0b00011111

            self.data['ID_Manufacturer_Name'] = chr(first + 64) + chr(second + 64) + chr(third + 64)
        else:
            print "ID Manufacturer Name field is currupt!"


        #ID Product Code: edid[10:12]
        self.data['ID_Product_Code'] = "%02x%02x" % (self.edid[11], self.edid[10])

        #ID Serial Number: edid[12:16]
        self.data['ID_Serial_Number'] = self.edid[12] + (self.edid[13] << 8) + (self.edid[14] << 16) + (self.edid[15] << 24)

        self.data['Week_of_manufacture'] = self.edid[16] & 0xff
        self.data['Year_of_manufacture'] = self.edid[17] + 1990
        self.data['EDID_version'] = self.edid[18]
        self.data['EDID_revision'] = self.edid[19]
        self.data['Extension_Flag'] = self.edid[126]


    def parse_basic_display(self):
        new_data = {}

        new_data['Video_Input'] = (self.edid[20] & 0xff) >> 7
        if new_data['Video_Input'] == 0:
            new_data['Signal_Level_Standard'] = ((self.edid[20] & 0xff) & 0b01100000) >> 5
            if (new_data['Signal_Level_Standard'] == 0b00):
                new_data['Signal_Level_Standard'] = (0.700, 0.300)
            elif (new_data['Signal_Level_Standard'] == 0b01):
                new_data['Signal_Level_Standard'] = (0.714, 0.286)
            elif (new_data['Signal_Level_Standard'] == 0b10):
                new_data['Signal_Level_Standard'] = (1.000, 0.400)
            elif (new_data['Signal_Level_Standard'] == 0b11):
                new_data['Signal_Level_Standard'] = (0.700, 0.000)

            new_data['Blank-to-black_setup'] = ((self.edid[20] & 0xff) & 0b00010000) >> 4
            new_data['Separate_syncs'] = ((self.edid[20] & 0xff) & 0b00001000) >> 3
            new_data['Composite_sync'] = ((self.edid[20] & 0xff) & 0b00000100) >> 2
            new_data['Sync_on_green'] = ((self.edid[20] & 0xff) & 0b00000010) >> 1
            new_data['Vsync_serration'] = (self.edid[20] & 0xff) & 0b00000001
        else:
            new_data['Video_Input_DFP_1'] = (self.edid[20] & 0xff) & 0b00000001

        new_data['Max_Horizontal_Image_Size'] = self.edid[21]
        new_data['Max_Vertical_Image_Size'] = self.edid[22]
        new_data['Display_Gamma'] = float(self.edid[23] + 100) / 100

        new_data['Feature_Support'] = {'Standby': ((self.edid[24] & 0xff) & 0b10000000) >> 7,
                                    'Suspend': ((self.edid[24] & 0xff) & 0b01000000) >> 6,
                                    'Active-off': ((self.edid[24] & 0xff) & 0b00100000) >> 5,
                                    'Display Type': ((self.edid[24] & 0xff) & 0b00011000) >> 3,
                                    'Standard-sRGB': ((self.edid[24] & 0xff) & 0b00000100) >> 2,
                                    'Preferred_Timing_Mode': ((self.edid[24] & 0xff) & 0b00000010) >> 1,
                                    'Default_GTF': (self.edid[24] & 0xff) & 0b00000001}
        #Note that "Display Type" have multiple choices, should be handled by the website

        return new_data


    def parse_chromaticity(self):
        new_data = {}

        #Extract low bits
        Red_low_x = ((self.edid[25] & 0xff) & 0b11000000) >> 6
        Red_low_y = ((self.edid[25] & 0xff) & 0b00110000) >> 4
        Green_low_x = ((self.edid[25] & 0xff) & 0b00001100) >> 2
        Green_low_y = (self.edid[25] & 0xff) & 0b00000011
        Blue_low_x = ((self.edid[26] & 0xff) & 0b11000000) >> 6
        Blue_low_y = ((self.edid[26] & 0xff) & 0b00110000) >> 4
        White_low_x = ((self.edid[26] & 0xff) & 0b00001100) >> 2
        White_low_y = (self.edid[26] & 0xff) & 0b00000011

        #Get the rest of the bits
        Red_high_x = self.edid[27] & 0xff
        Red_high_y = self.edid[28] & 0xff
        Green_high_x = self.edid[29] & 0xff
        Green_high_y = self.edid[30] & 0xff
        Blue_high_x = self.edid[31] & 0xff
        Blue_high_y = self.edid[32] & 0xff
        White_high_x = self.edid[33] & 0xff
        White_high_y = self.edid[34] & 0xff

        #Combine all bits and convert them to decimal fractions
        new_data['Red_x'] = ((Red_high_x << 2) + Red_low_x) / 2.**(10)
        new_data['Red_y'] = ((Red_high_y << 2) + Red_low_y) / 2.**(10)
        new_data['Green_x'] = ((Green_high_x << 2) + Green_low_x) / 2.**(10)
        new_data['Green_y'] = ((Green_high_y << 2) + Green_low_y) / 2.**(10)
        new_data['Blue_x'] = ((Blue_high_x << 2) + Blue_low_x) / 2.**(10)
        new_data['Blue_y'] = ((Blue_high_y << 2) + Blue_low_y) / 2.**(10)
        new_data['White_x'] = ((White_high_x << 2) + White_low_x) / 2.**(10)
        new_data['White_y'] = ((White_high_y << 2) + White_low_y) / 2.**(10)

        return new_data


    def parse_established_timings(self):
        new_data = {}

        new_data['720x400@70Hz'] = ((self.edid[35] & 0xff) & 0b10000000) >> 7
        new_data['720x400@88Hz'] = ((self.edid[35] & 0xff) & 0b01000000) >> 6
        new_data['640x480@60Hz'] = ((self.edid[35] & 0xff) & 0b00100000) >> 5
        new_data['640x480@67Hz'] = ((self.edid[35] & 0xff) & 0b00010000) >> 4
        new_data['640x480@72Hz'] = ((self.edid[35] & 0xff) & 0b00001000) >> 3
        new_data['640x480@75Hz'] = ((self.edid[35] & 0xff) & 0b00000100) >> 2
        new_data['800x600@56Hz'] = ((self.edid[35] & 0xff) & 0b00000010) >> 1
        new_data['800x600@60Hz'] = (self.edid[35] & 0xff) & 0b00000001

        new_data['800x600@72Hz'] = ((self.edid[36] & 0xff) & 0b10000000) >> 7
        new_data['800x600@75Hz'] = ((self.edid[36] & 0xff) & 0b01000000) >> 6
        new_data['832x624@75Hz'] = ((self.edid[36] & 0xff) & 0b00100000) >> 5
        new_data['1024x768@87Hz'] = ((self.edid[36] & 0xff) & 0b00010000) >> 4
        new_data['1024x768@60Hz'] = ((self.edid[36] & 0xff) & 0b00001000) >> 3
        new_data['1024x768@70Hz'] = ((self.edid[36] & 0xff) & 0b00000100) >> 2
        new_data['1024x768@75Hz'] = ((self.edid[36] & 0xff) & 0b00000010) >> 1
        new_data['1280x1024@75Hz'] = (self.edid[36] & 0xff) & 0b00000001

        new_data['1152x870@75Hz'] = ((self.edid[37] & 0xff) & 0b10000000) >> 7

        return new_data


    def parse_standard_timings(self):
        new_data = {}

        #Note: EDID structures prior to Version 1 Revision 3 defined the bit combination of 0 0 to indicate a 1:1 aspect ratio

        for i in range(38, 53, 2):
            #Check if the field is not unused (value 01)
            if (self.edid[i] & 0xff) is not 0b01:
                id = {}
                id['X_Resolution'] = (((self.edid[i] & 0xff) + 31) * 8)

                #Y Resolution should be calculated using the aspect ratio below
                #Shouldn't we do that here?

                id['Image_Aspect_ratio'] = ((self.edid[i + 1] & 0xff) & 0b11000000) >> 6
#                if (id['Image_Aspect_ratio'] == 0b00):
#                    id['Image_Aspect_ratio'] = "16:10"
#                elif (id['Image_Aspect_ratio'] == 0b01):
#                    id['Image_Aspect_ratio'] = "4:3"
#                elif (id['Image_Aspect_ratio'] == 0b10):
#                    id['Image_Aspect_ratio'] = "5:4"
#                elif (id['Image_Aspect_ratio'] == 0b11):
#                    id['Image_Aspect_ratio'] = "16:9"

                id['Refresh_Rate'] = ((self.edid[i + 1] & 0xff) & 0b00111111) + 60

                new_data['Identification_%d' % (((i - 38) / 2) + 1)] = id

        return new_data


    def parse_descriptors(self):
        new_data = {}

        for i in range(54, 125, 18):#54, 125, 18
            if not (((self.edid[i] & 0xff) << 8) + (self.edid[i + 1] & 0xff)) == 0x0000:
                new_data['Timing_Descriptor_%d' % (((i - 54) / 18) + 1)] = self.parse_timing_descriptor(i)
            else:
                if ((self.edid[i + 3] & 0xff) == 0xff):
                    self.parse_monitor_descriptor_text("Monitor_Serial_Number", i)
                elif ((self.edid[i + 3] & 0xff) == 0xfe):
                    self.parse_monitor_descriptor_text("Data_String", i)
                elif ((self.edid[i + 3] & 0xff) == 0xfd):
                    new_data["Monitor_Range_Limits_Descriptor"] = self.parse_monitor_descriptor_range_limits(i)
                elif ((self.edid[i + 3] & 0xff) == 0xfc):
                    self.parse_monitor_descriptor_text("Monitor_Name", i)
                elif ((self.edid[i + 3] & 0xff) == 0xfb):
                    print "Descriptor contains additional color point data, NOT supported yet."
                elif ((self.edid[i + 3] & 0xff) == 0xfa):
                    print "Descriptor contains additional Standard Timing Identifications, NOT supported yet."

        return new_data


    def parse_timing_descriptor(self, i):
        new_data = {}

        new_data['Horizontal_Active'] = ((self.edid[i + 4] & 0b11110000) << 4) + (self.edid[i + 2] & 0xff)
        new_data['Horizontal_Blanking'] = ((self.edid[i + 4] & 0b00001111) << 8) + (self.edid[i + 3] & 0xff)

        new_data['Vertical_Active'] = ((self.edid[i + 7] & 0b11110000) << 4) + (self.edid[i + 5] & 0xff)
        new_data['Vertical_Blanking'] = ((self.edid[i + 7] & 0b00001111) << 8) + (self.edid[i + 6] & 0xff)

        new_data['Horizontal_Sync_Offset'] = ((self.edid[i + 11] & 0b11000000) << 4) + (self.edid[i + 8] & 0xff)
        new_data['Horizontal_Sync_Pulse_Width'] = ((self.edid[i + 11] & 0b00110000) << 8) + (self.edid[i + 9] & 0xff)

        new_data['Vertical_Sync_Offset'] = ((self.edid[i + 11] & 0b00001100) << 4) + (self.edid[i + 10] & 0b11110000) >> 4
        new_data['Vertical_Sync_Pulse_Width'] = ((self.edid[i + 11] & 0b00000011) << 8) + (self.edid[i + 10] & 0b00001111)

        new_data['Horizontal_Image_Size'] = ((self.edid[i + 14] & 0b11110000) << 4) + (self.edid[i + 12] & 0xff)
        new_data['Vertical_Image_Size'] = ((self.edid[i + 14] & 0b00001111) << 8) + (self.edid[i + 13] & 0xff)

        new_data['Horizontal_Border'] = (self.edid[i + 15] & 0xff)
        new_data['Vertical_Border'] = (self.edid[i + 16] & 0xff)

        #TODO: Need rewrite to parse these deeply
        new_data['Flags'] = {'Interlaced': ((self.edid[i + 17] & 0xff) & 0b10000000) >> 7,
                        'Stereo_Mode': ((self.edid[i + 17] & 0xff) & 0b01100000) >> 5,
                        'Sync': ((self.edid[i + 17] & 0xff) & 0b00011000) >> 3,
                        'Bit_2': ((self.edid[i + 17] & 0xff) & 0b00000100) >> 2,
                        'Bit_1': ((self.edid[i + 17] & 0xff) & 0b00000010) >> 1,
                        'Stereo_Mode_x': (self.edid[i + 17] & 0xff) & 0b00000001}

        return new_data


    def parse_monitor_descriptor_text(self, name, i):
        output = ""

        for x in range(5, 18):
            if self.edid[i + x] == 0x0a:
                break

            output = output + chr(self.edid[i + x])

        self.data[name] = output

    def parse_monitor_descriptor_range_limits(self, i):
        new_data = {}

        new_data['Min_Vertical_rate'] = (self.edid[i + 5] & 0xff)
        new_data['Max_Vertical_rate'] = (self.edid[i + 6] & 0xff)

        new_data['Min_Horizontal_rate'] = (self.edid[i + 7] & 0xff)
        new_data['Max_Horizontal_rate'] = (self.edid[i + 8] & 0xff)

        new_data['Max_Supported_Pixel_Clock'] = (self.edid[i + 9] & 0xff) * 10

        if ((self.edid[i + 10] & 0xff) == 0x02):
            gtf = {}

            gtf['Start_frequency'] = (self.edid[i + 12] & 0xff) * 2
            gtf['C'] = (self.edid[i + 13] & 0xff) / 2
            gtf['M'] = (((self.edid[i + 14] & 0xff) << 8) + (self.edid[i + 15] & 0xff))
            gtf['K'] = (self.edid[i + 16] & 0xff)
            gtf['J'] = (self.edid[i + 17] & 0xff) / 2

            new_data['Generalized_Timing_Formula'] = gtf

        return new_data



if __name__ == "__main__":
    import sys
    import pprint

    with open(sys.argv[1], 'rb') as file:
        bin_data = file.read()

    my_edid = EDID_Parser(bin_data)
    print pprint.pprint(my_edid.data)
