import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from http import HTTPStatus
from ..models import Group, Post, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
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
        cls.comment = Comment.objects.create(
            post=cls.post,
            text='Тестовый комментарий',
            author=cls.author,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.author)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(
            PostCreateFormTests.not_author)

    def test_create_new_post_by_authorized_user(self):
        """Проверка возможности создания нового поста авторизованным
        пользователем со страницы создания поста."""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
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
        form_data = {
            'text': 'Любой текст',
            'group': PostCreateFormTests.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=PostCreateFormTests.author,
                group=form_data['group'],
                image='posts/small.gif',
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_create_new_post_without_group(self):
        """Проверка возможности создания нового поста без указания группы со
        страницы создания поста."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Любой текст',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=PostCreateFormTests.author,
                group=None,
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_create_new_post_by_not_authorized_user(self):
        """Проверка возможности создания нового поста неавторизованным
        пользователем со страницы создания поста."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Любой текст',
            'group': PostCreateFormTests.group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_post_edit_by_authorized_user(self):
        """Проверка возможности изменения поста авторизованным пользователем
        со страницы редактирования поста."""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small_2.gif',
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
        form_data = {
            'text': 'Отредактированный текст',
            'group': PostCreateFormTests.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                id=PostCreateFormTests.post.id,
                text=form_data['text'],
                author=PostCreateFormTests.author,
                group=form_data['group'],
                image='posts/small_2.gif',
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_post_edit_by_not_authorized_user(self):
        """Проверка возможности изменения поста неавторизованным пользователем
        со страницы редактирования поста."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный текст',
            'group': PostCreateFormTests.group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostCreateFormTests.post.id}),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                text=PostCreateFormTests.post.text,
                author=PostCreateFormTests.author,
                group=PostCreateFormTests.post.group,
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_post_edit_by_not_author(self):
        """Проверка возможности изменения поста другим авторизованным
        пользователем со страницы редактирования поста."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный текст',
            'group': PostCreateFormTests.group.id,
        }
        response = self.authorized_client_not_author.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostCreateFormTests.post.id}),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                text=PostCreateFormTests.post.text,
                author=PostCreateFormTests.author,
                group=PostCreateFormTests.post.group,
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_post_edit_without_group_change(self):
        """Проверка возможности изменения поста без изменения группы со
        страницы редактирования поста."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный текст',
            'group': PostCreateFormTests.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostCreateFormTests.post.id}),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=PostCreateFormTests.author,
                group=PostCreateFormTests.group.id,
            ).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_create_new_comment_by_authorized_user(self):
        """Проверка возможности создания нового комментария авторизованным
        пользователем со страницы поста."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Любой комментарий',
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostCreateFormTests.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
                post=PostCreateFormTests.post,
                author=PostCreateFormTests.author,
            ).exists()
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)

    def test_create_new_comment_by_not_authorized_user(self):
        """Проверка возможности создания нового комментария неавторизованным
        пользователем со страницы поста."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Любой комментарий',
        }
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostCreateFormTests.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count)

    def test_new_comment_is_on_post_detail_page(self):
        """Проверка появления комментария на странице поста."""
        response = self.guest_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': PostCreateFormTests.post.id})
        )
        test_comment_text = 'Тестовый комментарий'
        response_comment_text = response.context['comments'][0].text
        self.assertEqual(test_comment_text, response_comment_text)
