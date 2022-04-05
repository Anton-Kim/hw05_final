from django.test import TestCase, Client

from http import HTTPStatus

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.not_author = User.objects.create_user(username='not_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание тестовой группы',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.author)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(PostURLTests.not_author)

    def test_post_edit_url_redirect_anonymous(self):
        """Проверка кодов статусов на всех страницах для всех типов
        пользователей."""
        urls_user_types = {
            '/': {
                self.guest_client: HTTPStatus.OK,
                self.authorized_client: HTTPStatus.OK,
                self.authorized_client_not_author: HTTPStatus.OK
            },
            f'/group/{PostURLTests.group.slug}/': {
                self.guest_client: HTTPStatus.OK,
                self.authorized_client: HTTPStatus.OK,
                self.authorized_client_not_author: HTTPStatus.OK
            },
            '/profile/author/': {
                self.guest_client: HTTPStatus.OK,
                self.authorized_client: HTTPStatus.OK,
                self.authorized_client_not_author: HTTPStatus.OK
            },
            '/create/': {
                self.guest_client: HTTPStatus.FOUND,
                self.authorized_client: HTTPStatus.OK,
                self.authorized_client_not_author: HTTPStatus.OK
            },
            f'/posts/{PostURLTests.post.id}/': {
                self.guest_client: HTTPStatus.OK,
                self.authorized_client: HTTPStatus.OK,
                self.authorized_client_not_author: HTTPStatus.OK
            },
            f'/posts/{PostURLTests.post.id}/edit/': {
                self.guest_client: HTTPStatus.FOUND,
                self.authorized_client: HTTPStatus.OK,
                self.authorized_client_not_author: HTTPStatus.FOUND
            }
        }
        for url in urls_user_types:
            for user_type, status in urls_user_types[url].items():
                with self.subTest(url=url):
                    response = user_type.get(url)
                    self.assertEqual(response.status_code, status)

    def test_unexisting_page_url_at_desired_location(self):
        """Страница недоступна при запросе к несуществующему адресу"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            '/profile/author/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
            f'/posts/{PostURLTests.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/404/': 'core/404.html',
        }
        for url, template in url_templates_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
