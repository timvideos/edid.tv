import base64

from django.contrib.auth import get_user_model

from edid_parser.edid_parser import EDID_Parser

from frontend.models import Manufacturer, EDID


class EDIDTestMixin(object):
    def setUp(self):
        super(EDIDTestMixin, self).setUp()

        Manufacturer.objects.bulk_create([
            Manufacturer(name_id='TSB', name='Toshiba'),
            Manufacturer(name_id='UNK', name='Unknown'),
        ])

        edid_binary = "\x00\xFF\xFF\xFF\xFF\xFF\xFF\x00\x52\x62\x06\x02\x01" \
                      "\x01\x01\x01\xFF\x13\x01\x03\x80\x59\x32\x78\x0A\xF0" \
                      "\x9D\xA3\x55\x49\x9B\x26\x0F\x47\x4A\x21\x08\x00\x81" \
                      "\x80\x8B\xC0\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01" \
                      "\x01\x01\x02\x3A\x80\x18\x71\x38\x2D\x40\x58\x2C\x45" \
                      "\x00\x76\xF2\x31\x00\x00\x1E\x66\x21\x50\xB0\x51\x00" \
                      "\x1B\x30\x40\x70\x36\x00\x76\xF2\x31\x00\x00\x1E\x00" \
                      "\x00\x00\xFC\x00\x54\x4F\x53\x48\x49\x42\x41\x2D\x54" \
                      "\x56\x0A\x20\x20\x00\x00\x00\xFD\x00\x17\x3D\x0F\x44" \
                      "\x0F\x00\x0A\x20\x20\x20\x20\x20\x20\x01\x24"

        # Parse EDID file
        edid_data = EDID_Parser(edid_binary).data
        # Encode in base64
        edid_base64 = base64.b64encode(edid_binary)

        # Create EDID entry
        edid_object = EDID()
        edid_object.file_base64 = edid_base64
        edid_object.populate_from_edid_parser(edid_data)
        edid_object.save()
        edid_object.populate_timings_from_edid_parser(edid_data)
        edid_object.save()

        self.edid = edid_object

    def _login(self, username='tester', password='test', superuser=False):
        """
        Creates user and login then returns the user.
        """

        if superuser:
            user = get_user_model().objects.create_superuser(username, '',
                                                             password)
        else:
            user = get_user_model().objects.create_user(username,
                                                        password=password)

        self.client.login(username=username, password=password)

        return user
