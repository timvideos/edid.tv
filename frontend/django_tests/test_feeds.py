import base64
from xml.etree import ElementTree as ET

from django.core.urlresolvers import reverse
from django.test import TestCase

from edid_parser.edid_parser import EDID_Parser

from frontend.django_tests.base import EDIDTestMixin
from frontend.models import EDID


class FeedTestMixin(object):
    def setUp(self):
        super(FeedTestMixin, self).setUp()

        # Add another EDID
        edid_binary = "\x00\xFF\xFF\xFF\xFF\xFF\xFF\x00\x04\x72\xA1\xAD\xDE" \
                      "\xF7\x50\x83\x23\x12\x01\x03\x08\x2F\x1E\x78\xEA\xDE" \
                      "\x95\xA3\x54\x4C\x99\x26\x0F\x50\x54\xBF\xEF\x90\xA9" \
                      "\x40\x71\x4F\x81\x40\x8B\xC0\x95\x00\x95\x0F\x90\x40" \
                      "\x01\x01\x21\x39\x90\x30\x62\x1A\x27\x40\x68\xB0\x36" \
                      "\x00\xDA\x28\x11\x00\x00\x19\x00\x00\x00\xFD\x00\x38" \
                      "\x4D\x1F\x54\x11\x00\x0A\x20\x20\x20\x20\x20\x20\x00" \
                      "\x00\x00\xFF\x00\x4C\x41\x31\x30\x43\x30\x34\x31\x34" \
                      "\x30\x33\x30\x0A\x00\x00\x00\xFC\x00\x41\x4C\x32\x32" \
                      "\x31\x36\x57\x0A\x20\x20\x20\x20\x20\x00\x52"

        # Parse EDID file
        edid_data = EDID_Parser(edid_binary).data
        # Encode in base64
        edid_base64 = base64.b64encode(edid_binary)

        # Create EDID entry
        edid_object = EDID.create(file_base64=edid_base64,
                                  edid_data=edid_data)
        edid_object.save()
        edid_object.populate_timings_from_edid_parser(edid_data)
        edid_object.save()

        self.edid_2 = edid_object

        # Update first EDID
        self.edid.est_timings_720_400_70 = True
        self.edid.save()

    def test_items(self):
        response = self.client.get(self.feed_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'],
                         'application/rss+xml; charset=utf-8')

        rss_elem = ET.fromstring(response.content)

        self.assertEqual(rss_elem.tag, "rss")
        self.assertEqual(rss_elem.attrib, {"version": "2.0"})

        channel_elem = rss_elem.find("channel")

        title_elem = channel_elem.find("title")
        self.assertEqual(title_elem.text, "EDID.tv")

        items = rss_elem.findall("./channel/item")

        return items, channel_elem


class UploadedEDIDsFeedTestCase(FeedTestMixin, EDIDTestMixin, TestCase):
    def feed_url(self):
        return reverse('uploaded-feed')

    def test_items(self):
        items, channel_elem = super(UploadedEDIDsFeedTestCase, self) \
            .test_items()

        # EDID 1 is listed second
        self.assertEqual(
            items[1].find("link").text,
            "%sedid/%d/" % (channel_elem.find("link").text, self.edid.pk)
        )
        # EDID 2 is listed first
        self.assertEqual(
            items[0].find("link").text,
            "%sedid/%d/" % (channel_elem.find("link").text, self.edid_2.pk)
        )


class UpdatedEDIDsFeedTestCase(FeedTestMixin, EDIDTestMixin, TestCase):
    def feed_url(self):
        return reverse('updated-feed')

    def test_items(self):
        items, channel_elem = super(UpdatedEDIDsFeedTestCase, self) \
            .test_items()

        # Updated EDID 1 is listed first
        self.assertEqual(
            items[0].find("link").text,
            "%sedid/%d/" % (channel_elem.find("link").text, self.edid.pk)
        )
        # EDID 2 is listed second
        self.assertEqual(
            items[1].find("link").text,
            "%sedid/%d/" % (channel_elem.find("link").text, self.edid_2.pk)
        )
