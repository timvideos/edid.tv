
from django.db import models

class EDID(models.Model):
    #ID Manufacturer Name, full name assigned from PNP IDs list
    manufacturer_name = models.CharField(max_length=255, null=True)

    #ID Manufacturer Name, 3 characters
    manufacturer_name_id = models.CharField(max_length=3, null=True)

    #ID Product Code
    manufacturer_product_code = models.CharField(max_length=4, null=True)

    #ID Serial Number
    manufacturer_serial_number = models.IntegerField(null=True)

    #Monitor Name, from Monitor Descriptor Description (type 0xFC)
    monitor_name = models.CharField(max_length=13, null=True)

    #Monitor Serial Number, from Monitor Descriptor Description (type 0xFF)
    monitor_serial_number = models.IntegerField(null=True)

#Part of standard timings
#    Aspect_Ratio_16_10 = 0
#    Aspect_Ratio_4_3 = 1
#    Aspect_Ratio_5_4 = 2
#    Aspect_Ratio_16_9 = 3
#    Image_Aspect_Ratio = ((Aspect_Ratio_16_10, '16:10'),
#                            (Aspect_Ratio_4_3, '4:3'),
#                            (Aspect_Ratio_5_4, '5:4'),
#                            (Aspect_Ratio_16_9, '16:9'))
#    image_aspect_ratio = models.SmallIntegerField(max_length=1, choices=Image_Aspect_Ratio, default=Aspect_Ratio_16_10)

    def populate_from_edid_parser(self, edid):
        #self.manufacturer_name = edid['ID_Manufacturer_Name'] Parse from PNP IDs list
        self.manufacturer_name_id = edid['ID_Manufacturer_Name']

        self.manufacturer_product_code = edid['ID_Product_Code']
        self.manufacturer_serial_number = edid['ID_Serial_Number']

        if 'Monitor_Name' in edid:
            self.monitor_name = edid['Monitor_Name']

        if 'Monitor_Serial_Number' in edid:
            self.monitor_serial_number = edid['Monitor_Serial_Number']

    def __unicode__(self):
        #should be manufacturer_name NOT _id
        return "%s %s" % (self.manufacturer_name_id, self.monitor_name)
