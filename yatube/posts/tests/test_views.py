from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Group, Post, User, Follow
from ..forms import PostForm


class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание тестовой группы',
        )
        cls.other_group = Group.objects.create(
            title='Другая тестовая группа',
            slug='other-test-slug',
            description='Описание другой тестовой группы',
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=(
                b'\x47\x49\x46\x38\x39\x61\x02\x00'
                b'\x01\x00\x80\x00\x00\x00\x00\x00'
                b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                b'\x0A\x00\x3B'
            ),
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group,
            image=cls.uploaded,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewTests.author)
        self.user = User.objects.create_user(username='Follow_tester')
        self.authorized_client_follower = Client()
        self.authorized_client_follower.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_names_pages = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                'slug': PostViewTests.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': 'author'}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': f'{PostViewTests.post.id}'
            }): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={
                'post_id': f'{PostViewTests.post.id}'
            }): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_names_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_posts_index_page_show_correct_context(self):
        """Проверка контекста страниц index.html, group_list.html,
        profile.html."""
        urls = (
            '/',
            f'/group/{PostViewTests.group.slug}/',
            f'/profile/{PostViewTests.author}/'
        )
        for url in urls:
            response = self.authorized_client.get(url)
            first_object = response.context['page_obj'][0]
            context_objects = {
                PostViewTests.post.text: first_object.text,
                PostViewTests.author: first_object.author,
                PostViewTests.group: first_object.group,
                PostViewTests.post.id: first_object.id,
                PostViewTests.post.image: first_object.image,
            }
            for reverse_name, response_name in context_objects.items():
                with self.subTest(reverse_name=reverse_name):
                    self.assertEqual(reverse_name, response_name)

    def test_post_detail_pages_show_correct_context(self):
        """Проверка контекста страницы post_detail.html."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': f'{PostViewTests.post.id}'})
        )
        self.assertEqual(response.context.get('post').text, 'Тестовый текст')
        self.assertEqual(response.context.get('post').author,
                         PostViewTests.author)
        self.assertEqual(response.context.get('post').group,
                         PostViewTests.group)
        self.assertEqual(response.context.get('post').id,
                         PostViewTests.post.id)
        self.assertEqual(response.context.get('post').image,
                         PostViewTests.post.image)

    def test_post_edit_page_show_correct_context(self):
        """Проверка контекста страницы редактирования поста."""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': f'{PostViewTests.post.id}'})
        )
        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)

    def test_post_create_page_show_correct_context(self):
        """Проверка контекста страницы создания поста."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)

    def test_post_create_new_appears_on_correct_pages(self):
        """Проверка появления нового поста на главной странице, на странице
        выбранной группы и в профиле пользователя."""
        exp_pages = [
            reverse('posts:index'),
            reverse(
                'posts:group_list', kwargs={'slug': PostViewTests.group.slug}),
            reverse(
                'posts:profile', kwargs={'username': PostViewTests.author})
        ]
        for page in exp_pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(PostViewTests.post,
                                 response.context['page_obj'][0])

    def test_post_not_contain_in_wrong_group(self):
        """При создании поста он не должен появляться в другой группе."""
        post = PostViewTests.post
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PostViewTests.other_group.slug})
        )
        self.assertNotIn(post, response.context['page_obj'].object_list)

    def test_cache_index_page_context(self):
        """Проверка работы кеша страницы index.html."""
        posts_count = Post.objects.count()
        response_cached = self.authorized_client.get('/')
        Post.objects.create(
            text='Не должен кешироваться',
            author=PostViewTests.author,
            group=PostViewTests.group,
        )
        response = self.authorized_client.get('/')
        self.assertEqual(response_cached.content, response.content)
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_correct_follow_and_unfollow(self):
        """Проверка возможности авторизованному пользователю подписываться на
        других пользователей и удалять их из подписок."""
        follow_count = Follow.objects.filter(
            user=self.user,
            author=self.author
        ).count()
        self.assertEqual(0, follow_count)
        self.authorized_client_follower.get(reverse(
            'posts:profile_follow',
            kwargs={'username': 'author'})
        )
        follow_count = Follow.objects.filter(
            user=self.user,
            author=self.author).count()
        self.assertEqual(1, follow_count)
        self.authorized_client_follower.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': 'author'})
        )
        follow_count = Follow.objects.filter(
            user=self.user,
            author=self.author).count()
        self.assertEqual(0, follow_count)

    def test_correct_follow_index_page_work(self):
        """Проверка появления новой записи пользователя в ленте тех, кто на
        него подписан и её отсутствия в ленте тех, кто не подписан."""
        Post.objects.create(
            text='Тестовый пост для подписчика',
            author=PostViewTests.author,
            group=PostViewTests.group,
        )
        response = self.authorized_client_follower.get(
            reverse('posts:follow_index'))
        posts_count = len(response.context['page_obj'])
        self.assertEqual(0, posts_count)
        self.authorized_client_follower.get(reverse(
            'posts:profile_follow',
            kwargs={'username': 'author'})
        )
        response = self.authorized_client_follower.get(
            reverse('posts:follow_index'))
        last_post = response.context['page_obj'][0].text
        self.assertEqual('Тестовый пост для подписчика', last_post)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание тестовой группы',
        )
        for _ in range(settings.POSTS_COUNT_FOR_PAGINATOR):
            cls.post = Post.objects.create(
                text='Тестовый текст',
                author=cls.author,
                group=cls.group,
            )

    def test_first_page_contains_ten_records(self):
        urls = ('posts:index', 'posts:group_list', 'posts:profile')
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(reverse('posts:index'))
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POSTS_PER_PAGE
                )

    def test_second_page_contains_three_records(self):
        urls = ('posts:index', 'posts:group_list', 'posts:profile')
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(reverse('posts:index') + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POSTS_COUNT_FOR_PAGINATOR
                    - settings.POSTS_PER_PAGE
                )
