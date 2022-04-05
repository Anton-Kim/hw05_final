from django.test import TestCase, Client

from http import HTTPStatus


class StaticPagesURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_url_exists_at_desired_location(self):
        """Проверка доступности URL-адресов."""
        urls = (
            '/about/author/',
            '/about/tech/',
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_uses_correct_template(self):
        """Проверка шаблонов для URL-адресов."""
        url_templates_names = {
            '/about/author/': 'about/about_author.html',
            '/about/tech/': 'about/about_tech.html',
        }
        for url, template in url_templates_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
