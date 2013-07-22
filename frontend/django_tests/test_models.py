from django.test import TestCase

from frontend.django_tests.base import EDIDTestMixin
from frontend.models import EDID, Manufacturer


### EDID Tests
class EDIDTestCase(EDIDTestMixin, TestCase):
    def test_manufacturer(self):
        manufacturer = Manufacturer.objects.get(name_id='TSB')

        self.assertEqual(self.edid.manufacturer, manufacturer)

    def test_status(self):
        self.assertEqual(self.edid.status, EDID.STATUS_TIMINGS_ADDED)

    def test_version(self):
        self.assertEqual(self.edid.version, EDID.VERSION_1_3)

    def test_private(self):
        # Check we have 1 non-private EDID
        self.assertEqual(EDID.objects.count(), 1)
        # Change status to private
        EDID.objects.filter(pk=1).update(status=EDID.STATUS_PRIVATE)
        # Check we have 0 non-private EDID
        self.assertEqual(EDID.objects.count(), 0)

    def test_est_timings(self):
        est_timings = self.edid.get_est_timings()

        # Check we have 3 established timings
        self.assertEqual(
            len([timing for timing in est_timings if timing['supported']]),
            3
        )

    def test_timings(self):
        self.assertEqual(self.edid.standardtiming_set.count(), 2)
        self.assertEqual(self.edid.detailedtiming_set.count(), 2)


### Timing Tests
class TimingTestMixin(object):
    def setUp(self):
        super(TimingTestMixin, self).setUp()

        self.timings_set = self._get_timings_set()

    def test_delete_timing(self):
        # Check we have two standard timings
        self.assertEqual(self.timings_set.count(), 2)
        # Get first timing
        timing_1 = self.timings_set.get(EDID=self.edid, identification=1)
        # Get second timing pk
        timing_2_pk = self.timings_set.get(EDID=self.edid, identification=2).pk
        # Delete first timing
        timing_1.delete()
        # Check we have 1 standard timings
        self.assertEqual(self.timings_set.count(), 1)
        # Get second timing by its pk
        timing_2 = self.timings_set.get(pk=timing_2_pk)
        # Check timing_2 have been moved up
        self.assertEqual(timing_2.identification, 1)


class StandardTimingTestCase(TimingTestMixin, EDIDTestMixin, TestCase):
    def _get_timings_set(self):
        return self.edid.standardtiming_set


class DetailedTimingTestCase(TimingTestMixin, EDIDTestMixin, TestCase):
    def _get_timings_set(self):
        return self.edid.detailedtiming_set

