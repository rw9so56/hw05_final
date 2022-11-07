from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_page_accessible_by_name(self):
        """URL, генерируемые при помощи имен
        about:author и about:tech, доступны."""
        namespaces = [
            'about:author',
            'about:tech'
        ]
        for namespace in namespaces:
            with self.subTest(namespace=namespace):
                response = self.guest_client.get(reverse(namespace))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_page_uses_correct_template(self):
        """При запросе к about:author и about:tech
        применяется шаблон about/author.html и about/tech.html."""
        url_templates_names = {
            'about:author': 'about/author.html',
            'about:tech': 'about/tech.html',
        }
        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(reverse(address))
                self.assertTemplateUsed(response, template)
