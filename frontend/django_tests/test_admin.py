from django.test import TestCase

from frontend.django_tests.base import EDIDTestMixin
from frontend.models import EDID


class EDIDUpdateFormTestCase(EDIDTestMixin, TestCase):
    def test_private_edid_is_listed(self):
        self.edid.status = self.edid.STATUS_PRIVATE
        self.edid.save()

        self._login(superuser=True)
        response = self.client.get('/admin/frontend/edid/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
                            '<a href="/admin/frontend/edid/1/change/">')
