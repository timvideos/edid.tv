import re


class EDIDUploadFormCleanerException(Exception):
    pass


class EDIDUploadFormCleaner:

    _hex_addresses = re.compile(r'0x[0-9A-Fa-f]+')
    _whitespaces = re.compile(r'\s')
    _non_hex = re.compile(r'[^0-9A-Fa-f]')

    @staticmethod
    def clean_hex(text):
        # Remove hex addresses, like 0x40
        text = EDIDUploadFormCleaner._hex_addresses.sub('', text)

        # Remove spaces, tabs and newlines
        text = EDIDUploadFormCleaner._whitespaces.sub('', text)

        # Check for non-hex digits
        if bool(EDIDUploadFormCleaner._non_hex.search(text)):
            raise EDIDUploadFormCleanerException(
                'Please remove all non-hex digits.'
            )

        # Convert hex to binary and add it to EDIDs list
        return text

    @staticmethod
    def clean_xrandr(text):
        inside_edid = False
        edid_hex = ''

        edid_pattern = re.compile(r'^\s*EDID:\s*$')
        hex_pattern = re.compile(r'^[0-9a-fA-F]+$')

        # Parse text line-by-line
        for line in text.splitlines():
            # If inside edid block
            if inside_edid:
                if hex_pattern.match(line.strip()):
                    edid_hex += line.strip()
                # edid block ended
                else:
                    inside_edid = False
                    # Convert hex to binary and add it to EDIDs list
                    yield edid_hex
            # Look for edid block
            elif edid_pattern.match(line):
                inside_edid = True
                edid_hex = ''
