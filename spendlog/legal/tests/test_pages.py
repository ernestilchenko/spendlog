from django.test import TestCase
from django.urls import reverse


class LegalPagesTests(TestCase):
    def test_privacy_is_public(self):
        response = self.client.get(reverse('legal:privacy'))
        self.assertContains(response, 'Privacy policy')
        self.assertContains(response, 'Enable Banking')

    def test_terms_is_public(self):
        response = self.client.get(reverse('legal:terms'))
        self.assertContains(response, 'Terms of use')
        self.assertContains(response, 'never initiates payments')
