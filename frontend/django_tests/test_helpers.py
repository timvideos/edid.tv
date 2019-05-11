import unittest
import os
from frontend.helpers.EDIDUploadFormCleaner import EDIDUploadFormCleaner


class EDIDUploadFormCleanerTest(unittest.TestCase):
    @staticmethod
    def _read_from_file(filename):
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        with open(os.path.join(data_dir, filename), 'r') as text_file:
            return text_file.read()

    def test_hex(self):
        for file in ['hex.log', 'hex2.log', 'hex3.log', 'hex4.log',
                     'hex5.log']:
            hex_text = self._read_from_file(file)
            edid = EDIDUploadFormCleaner.clean_hex(hex_text).lower()
            expected_edid = '00ffffffffffff004ca3415400000000' + \
                            '00130103902213780ac8959e57549226' + \
                            '0f505400000001010101010101010101' + \
                            '0101010101017d1e5618510016303020' + \
                            '250058c21000001a7d1e561651001630' + \
                            '3020250058c21000001a000000fe0053' + \
                            '414d53554e470a2020202020000000fe' + \
                            '004c544e313536415430325030390055'
            self.assertEqual(edid, expected_edid)

    def test_xrandr(self):
        xrandr_text = self._read_from_file('xrandr.log')
        edid_list = list(EDIDUploadFormCleaner.clean_xrandr(xrandr_text))
        expected_edid_list = [
            '00ffffffffffff004ca3415400000000' +
            '00130103902213780ac8959e57549226' +
            '0f505400000001010101010101010101' +
            '0101010101017d1e5618510016303020' +
            '250058c21000001a7d1e561651001630' +
            '3020250058c21000001a000000fe0053' +
            '414d53554e470a2020202020000000fe' +
            '004c544e313536415430325030390055'
        ]
        self.assertEqual(edid_list, expected_edid_list)

    def test_xrandr2(self):
        xrandr_text = self._read_from_file('xrandr2.log')
        edid_list = list(EDIDUploadFormCleaner.clean_xrandr(xrandr_text))
        expected_edid_list = [
            '00ffffffffffff000610c59c00000000' +
            '1c130103801d12780a00000000000000' +
            '00505400000001010101010101010101' +
            '010101010101521c008f50202e303020' +
            '36001eb3100000180000000100061020' +
            '00000000000000000a20000000fe004c' +
            '503133335758332d544c4134000000fe' +
            '00436f6c6f72204c43440a202020001d',

            '00ffffffffffff000469d323b74f0000' +
            '0e16010380351f782a6ea5a3544f9f26' +
            '115054bfef00714f8140818095008100' +
            '81c0b300d1c0023a801871382d40582c' +
            '450015382100001e000000ff0043344c' +
            '4d54463032303430370a000000fd0032' +
            '551c5311000a202020202020000000fc' +
            '00415355532056473233410a2020008f'
        ]
        self.assertEqual(edid_list, expected_edid_list)
