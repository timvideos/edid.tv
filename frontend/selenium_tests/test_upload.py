from tempfile import NamedTemporaryFile

from django.db import transaction

from frontend.models import Manufacturer

from base import SeleniumTestCase


class UploadSeleniumTestCase(SeleniumTestCase):
    def setUp(self):
        super(UploadSeleniumTestCase, self).setUp()

        with transaction.commit_on_success():
            Manufacturer.objects.bulk_create([
                Manufacturer(name_id='TSB', name='Toshiba'),
                Manufacturer(name_id='UNK', name='Unknown'),
            ])

    def create_temp_file(self, edid_binary):
        edid_file = NamedTemporaryFile(delete=False)
        edid_file.write(edid_binary)
        edid_file.flush()
        edid_file.seek(0)

        return edid_file

    def test_valid(self):
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
        edid_file = self.create_temp_file(edid_binary)
        edid_file.close()

        self.browser.get("%s/edid/upload/binary" % self.live_server_url)

        self.browser.find_element_by_id('id_edid_file')\
                    .send_keys(edid_file.name)

        # Submit upload form
        self.browser.find_element_by_id('upload-id-upload').submit()

        # Check we got redirected to EDID detail page
        self.assertEqual(self.browser.current_url,
                         "%s/edid/1/" % self.live_server_url)
