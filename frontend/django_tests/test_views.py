from tempfile import TemporaryFile

from django.core.urlresolvers import reverse
from django.test import TestCase

from frontend.models import Manufacturer

class UploadingEDIDTests(TestCase):
    def setUp(self):
        Manufacturer.objects.bulk_create([
            Manufacturer(name_id='TSB', name='Toshiba'),
            Manufacturer(name_id='UNK', name='Unknown'),
        ])

    def create_temp_file(self, edid_binary):
        edid_file = TemporaryFile()
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

        # Upload the file again and check for redirection to EDID detail
        response = self.client.post(reverse('edid-upload'), {
            'name': 'edid.bin',
            'edid_file': edid_file
        })

        self.assertRedirects(response, reverse('edid-detail', kwargs={'pk': 1}))

        # Upload the file again and check error message
        edid_file.seek(0)
        response = self.client.post(reverse('edid-upload'), {
            'name': 'edid.bin',
            'edid_file': edid_file
        })

        self.assertFormError(response, 'form', 'edid_file',
                             'This file have been uploaded before.')

        edid_file.close()

    def test_invalid_size(self):
        edid_binary = "\x00\xFF\xFF\xFF\xFF\xFF\xFF\x00\x24"
        edid_file = self.create_temp_file(edid_binary)

        response = self.client.post(reverse('edid-upload'), {
            'name': 'edid.bin',
            'edid_file': edid_file
        })

        self.assertFormError(response, 'form', 'edid_file',
                             "'Binary file is smaller than 128 bytes.'")

        edid_file.close()

    def test_invalid_header(self):
        edid_binary = "\x00\xFF\xFF\x00\x00\xFF\xFF\x00\x52\x62\x06\x02\x01" \
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

        response = self.client.post(reverse('edid-upload'), {
            'name': 'edid.bin',
            'edid_file': edid_file
        })

        self.assertFormError(response, 'form', 'edid_file',
                             "'Input is not an EDID file.'")

        edid_file.close()

    def test_invalid_checksum(self):
        edid_binary = "\x00\xFF\xFF\xFF\xFF\xFF\xFF\x00\x52\x62\x06\x02\x01" \
                      "\x01\x01\x01\xFF\x13\x01\x03\x80\x59\x32\x78\x0A\xF0" \
                      "\x9D\xA3\x55\x49\x9B\x26\x0F\x47\x4A\x21\x08\x00\x81" \
                      "\x80\x8B\xC0\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01" \
                      "\x01\x01\x02\x3A\x80\x18\x71\x38\x2D\x40\x58\x2C\x45" \
                      "\x00\x76\xF2\x31\x00\x00\x1E\x66\x21\x50\xB0\x51\x00" \
                      "\x1B\x30\x40\x70\x36\x00\x76\xF2\x31\x00\x00\x1E\x00" \
                      "\x00\x00\xFC\x00\x54\x4F\x53\x48\x49\x42\x41\x2D\x54" \
                      "\x56\x0A\x20\x20\x00\x00\x00\xFD\x00\x17\x3D\x0F\x44" \
                      "\x0F\x00\x0A\x20\x20\x20\x20\x20\x20\x01\xFF"
        edid_file = self.create_temp_file(edid_binary)

        response = self.client.post(reverse('edid-upload'), {
            'name': 'edid.bin',
            'edid_file': edid_file
        })

        self.assertFormError(response, 'form', 'edid_file',
                             "'Checksum is corrupt.'")

        edid_file.close()

