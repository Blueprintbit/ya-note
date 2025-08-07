from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from unittest import skip  # @skip("Временно отключен для самотестирования")

from notes.models import Note
from notes.forms import NoteForm


User = get_user_model()


class TestHomePage(TestCase):
    # Вынесем ссылку на список записей в атрибуты класса.
    LIST_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        # Создаём двух пользователей неанон и анон с разными именами:
        cls.author = User.objects.create(username='Лев Толстой')  # Неанон
        cls.reader = User.objects.create(username='Читатель простой')  # Анон
        cls.notes = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author,
            slug='test-slug',
        )

        all_notes = [
            Note(title='Note 1', text='Text 1', author=cls.author, slug='note-1'),
            Note(title='Note 2', text='Text 2', author=cls.reader, slug='note-2'),
        ]

        Note.objects.bulk_create(all_notes)

    # Проверяем сортировку
    def test_notes_list_order(self):
        self.client.force_login(self.author)
        response = self.client.get(self.LIST_URL)
        object_list = response.context['object_list']
        # Получаем id записей в том порядке, как они выведены на странице.
        all_idis = [notes.id for notes in object_list]
        # Сортируем полученный список.
        sorted_dates = sorted(all_idis)
        # Проверяем, что исходный список был отсортирован правильно.
        self.assertEqual(all_idis, sorted_dates)


class TestNoteCreatePage(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url_add = reverse('notes:add')
        cls.url_success = reverse('notes:success')
        cls.user = User.objects.create(username='Лев Толстой')  # Неанон

    # Проверка переадресации на страницу логина.
    def test_anonymous_user_cannot_see_form(self):
        response = self.client.get(self.url_add)
        # Для анонимного пользователя должен быть редирект на страницу логина:
        login_url = settings.LOGIN_URL
        self.assertRedirects(response, f'{login_url}?next={self.url_add}')

    # Проверка наличия формы у неанона.
    def test_authenticated_user_can_see_form(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url_add)
        # Проверим, что форма передана в контекст:
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], NoteForm)

    # Проверка переадресации на страницу успеха.
    def test_create_success(self):
        self.client.force_login(self.user)  # Авторизуем пользователя
        form_data = {
            'title': 'Тестовая заметка',
            'text': 'Просто текст',
            'slug': 'test-note'
        }
        response = self.client.post(self.url_add, data=form_data)
        # Проверим, что пользователь переадресован на страницу успеха
        self.assertRedirects(response, self.url_success)
