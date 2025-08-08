from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from unittest import skip  # @skip("Временно отключен для самотестирования")

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    # Текст заметки понадобится в нескольких местах кода,
    # поэтому запишем его в атрибуты класса.
    NOTE_TEXT = 'Текст заметки'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')  # Неанон
        cls.reader = User.objects.create(username='Читатель простой')  # Анон
        cls.notes = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author,
            slug='test-slug',
        )
        # Адрес страницы с заметкой
        cls.url = reverse('notes:add')
        # Создаём пользователя и клиент, логинимся в клиенте.
        cls.user = User.objects.create(username='Мимо Крокодил')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        # Данные для POST-запроса при создании записи.
        cls.form_data = {
            'title': 'Тестовая заметка',
            'text': 'Просто текст',
            'slug': 'test-note'
        }

    # Анонимный пользователь не может оставлять записи.
    def test_anonymous_user_cant_create_note(self):
        notes_count_before = Note.objects.count()
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом комментария.   
        self.client.post(self.url, data=self.form_data)
        # Считаем количество записей.
        notes_count = Note.objects.count()
        # Ожидаем, что комментариев в базе нет - сравниваем с нулём.
        self.assertEqual(notes_count, notes_count_before)

    # Авторизованный пользователь может оставлять записи.
    def test_user_can_create_cnote(self):
        notes_count_before = Note.objects.count()
        # Совершаем запрос через авторизованный клиент.
        response = self.auth_client.post(self.url, data=self.form_data)
        # Проверка редиректа на страницу успеха
        self.assertRedirects(response, reverse('notes:success'))
        # Считаем количество записей.
        notes_count = Note.objects.count()
        # Убеждаемся, что есть одна запись.
        self.assertEqual(notes_count, notes_count_before +1)
        # Получаем объект записи из базы.
        # Проверка атрибутов
        note = Note.objects.get(slug='test-note')
        self.assertEqual(note.author, self.user)
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])


class TestNoteEditDelete(TestCase):
    # Тексты для комментариев не нужно дополнительно создавать
    # (в отличие от объектов в БД), им не нужны ссылки на self или cls,
    # поэтому их можно перечислить просто в атрибутах класса.
    NOTE_TEXT = 'Текст комментария'
    NEW_NOTE_TEXT = 'Обновлённый комментарий'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Лев Толстой')  # Неанон
        cls.reader = User.objects.create(username='Читатель простой')  # Анон
        # Создаём запись в БД.
        cls.notes = Note.objects.create(
            title='Заголовок',
            text=cls.NOTE_TEXT,
            author=cls.author,
            slug='test-slug',
        )
        # Формируем адрес блока с записями, который понадобится для тестов.
        cls.notes_success_url = reverse('notes:success')  # Адрес успеха.
        cls.notes_list_url = reverse('notes:list')  # Адрес списка записей.
        # Создаём клиент для пользователя-автора.
        cls.author_client = Client()
        # "Логиним" пользователя в клиенте.
        cls.author_client.force_login(cls.author)
        # Делаем всё то же самое для пользователя-читателя.
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        # URL для редактирования записи.
        cls.edit_url = reverse('notes:edit', args=(cls.notes.slug,))
        # URL для удаления записи.
        cls.delete_url = reverse('notes:delete', args=(cls.notes.slug,))
        # Формируем данные для POST-запроса по обновлению комментария.
        cls.form_data = {
            'title': cls.notes.title,
            'text': cls.NEW_NOTE_TEXT,
            'slug': cls.notes.slug
        }

    def test_author_can_delete_note(self):
        # От имени автора записи отправляем DELETE-запрос на удаление.
        response = self.author_client.delete(self.delete_url)
        # Проверяем, что редирект привёл к успеху.
        self.assertRedirects(response, self.notes_success_url)
        # Заодно проверим статус-коды ответов.
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        # Считаем количество записей в системе.
        comments_count = Note.objects.count()
        # Ожидаем ноль комментариев в системе.
        self.assertEqual(comments_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        # Выполняем запрос на удаление от пользователя-читателя.
        response = self.reader_client.delete(self.delete_url)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что комментарий по-прежнему на месте.
        comments_count = Note.objects.count()
        self.assertEqual(comments_count, 1)

    def test_author_can_edit_note(self):
        # Выполняем запрос на редактирование от имени автора записи.
        response = self.author_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что сработал редирект.
        self.assertRedirects(response, self.notes_success_url)
        # Обновляем объект записи.
        self.notes.refresh_from_db()
        # Проверяем, что текст записи соответствует обновленному.
        self.assertEqual(self.notes.text, self.NEW_NOTE_TEXT)

    def test_user_cant_edit_note_of_another_user(self):
        # Выполняем запрос на редактирование от имени другого пользователя.
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем объект записи.
        self.notes.refresh_from_db()
        # Проверяем, что текст остался тем же, что и был.
        self.assertEqual(self.notes.text, self.NOTE_TEXT)
