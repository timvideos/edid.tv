import base64

from django.urls import reverse
from django.test import TestCase

from edid_parser.edid_parser import EDIDParser

from frontend.django_tests.base import EDIDTestMixin
from frontend.feeds import UploadedEDIDsFeed, UpdatedEDIDsFeed
from frontend.models import EDID


class FeedTestMixin:
    def setUp(self):
        super(FeedTestMixin, self).setUp()

        # Add another EDID
        edid_binary = b'\x00\xFF\xFF\xFF\xFF\xFF\xFF\x00\x04\x72\xA1\xAD\xDE' \
                      b'\xF7\x50\x83\x23\x12\x01\x03\x08\x2F\x1E\x78\xEA\xDE' \
                      b'\x95\xA3\x54\x4C\x99\x26\x0F\x50\x54\xBF\xEF\x90\xA9' \
                      b'\x40\x71\x4F\x81\x40\x8B\xC0\x95\x00\x95\x0F\x90\x40' \
                      b'\x01\x01\x21\x39\x90\x30\x62\x1A\x27\x40\x68\xB0\x36' \
                      b'\x00\xDA\x28\x11\x00\x00\x19\x00\x00\x00\xFD\x00\x38' \
                      b'\x4D\x1F\x54\x11\x00\x0A\x20\x20\x20\x20\x20\x20\x00' \
                      b'\x00\x00\xFF\x00\x4C\x41\x31\x30\x43\x30\x34\x31\x34' \
                      b'\x30\x33\x30\x0A\x00\x00\x00\xFC\x00\x41\x4C\x32\x32' \
                      b'\x31\x36\x57\x0A\x20\x20\x20\x20\x20\x00\x52'

        # Parse EDID file
        edid_data = EDIDParser(edid_binary).data
        # Encode in base64
        edid_base64 = base64.b64encode(edid_binary)

        # Create EDID entry
        edid_object = EDID.create(file_base64=edid_base64,
                                  edid_data=edid_data)
        edid_object.save()
        edid_object.populate_timings_from_parser(edid_data)
        edid_object.save()

        self.edid_2 = edid_object

        # Update first EDID
        self.edid.est_timings_720_400_70 = True
        self.edid.save()

    def test_feed(self):
        response = self.client.get(self._feed_url())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'],
                         'application/rss+xml; charset=utf-8')


class UploadedEDIDsFeedTestCase(FeedTestMixin, EDIDTestMixin, TestCase):
    @staticmethod
    def _feed_url():
        return reverse('uploaded-feed')

    def test_items(self):
        # Get feed and check its URL
        feed = UploadedEDIDsFeed()
        self.assertEqual(feed.feed_url(), self._feed_url())

        # Get item and check their count
        items = list(feed.items())
        self.assertEqual(len(items), 2)

        # Check EDID 1 is listed second
        self.assertEqual(feed.item_link(items[1]),
                         self.edid.get_absolute_url())
        # Check EDID 2 is listed first
        self.assertEqual(feed.item_link(items[0]),
                         self.edid_2.get_absolute_url())


class UpdatedEDIDsFeedTestCase(FeedTestMixin, EDIDTestMixin, TestCase):
    @staticmethod
    def _feed_url():
        return reverse('updated-feed')

    def test_items(self):
        # Get feed and check its URL
        feed = UpdatedEDIDsFeed()
        self.assertEqual(feed.feed_url(), self._feed_url())

        # Get item and check their count
        items = list(feed.items())
        self.assertEqual(len(items), 2)

        # Check Updated EDID 1 is listed first
        self.assertEqual(feed.item_link(items[0]),
                         self.edid.get_absolute_url())
        # Check EDID 2 is listed second
        self.assertEqual(feed.item_link(items[1]),
                         self.edid_2.get_absolute_url())
