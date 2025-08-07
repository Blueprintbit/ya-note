# news/tests/test_routes.py
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from unittest import skip  # @skip("Временно отключен для самотестирования")

from notes.models import Note


# Получаем модель пользователя.
User = get_user_model()


class TestRoutes(TestCase):

    # Добавляем фикстуру с созданием первой записи и двух пользователей:
    @classmethod
    def setUpTestData(cls):
        # Создаём двух пользователей неанон и анон с разными именами:
        cls.author = User.objects.create(username='Лев Толстой')  # Неанон
        cls.reader = User.objects.create(username='Читатель простой')  # Анон
        cls.notes = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author,
            # Слаг обязательное поле модели Заметка, добавляем его в тесте.
            slug='test-slug',
        )

    # Проверяем доступность авторизованному пользователю главной страницы,
    # списка записей, отдельной записи, регистрации, входа в учетку:
    def test_pages_availability_for_author(self):
        self.client.force_login(self.author)
        # Создаём набор тестовых данных - кортеж кортежей.
        # Каждый вложенный кортеж содержит два элемента:
        # имя пути и позиционные аргументы для функции reverse().
        urls = (
            # Путь для главной страницы не принимает
            # никаких позиционных аргументов,
            # поэтому вторым параметром ставим None.
            ('notes:home', None),
            # Путь для страницы заметки
            # принимает в качестве позиционного аргумента
            # слаг записи; передаём его в кортеже.
            ('notes:detail', ('test-slug',)),
            ('notes:list', None),
            ('users:login', None),
            ('users:signup', None),
        )
        # Итерируемся по внешнему кортежу
        # и распаковываем содержимое вложенных кортежей:
        for name, args in urls:
            with self.subTest(name=name):
                # Передаём имя и позиционный аргумент в reverse()
                # и получаем адрес страницы для GET-запроса:
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверяем доступность анонимному пользователю главной страницы,
    # регистрации, входа в учетку:
    def test_pages_availability_for_reader(self):
        self.client.force_login(self.reader)
        # Создаём набор тестовых данных - кортеж кортежей.
        # Каждый вложенный кортеж содержит два элемента:
        # имя пути и позиционные аргументы для функции reverse().
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:signup', None),
        )
        # Итерируемся по внешнему кортежу
        # и распаковываем содержимое вложенных кортежей:
        for name, args in urls:
            with self.subTest(name=name):
                # Передаём имя и позиционный аргумент в reverse()
                # и получаем адрес страницы для GET-запроса:
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверяем доступность редактирования и удаления записи.
    def test_availability_for_notes_detail_edit_delete(self):
        # При обращении к страницам редактирования и удаления комментария
        users_statuses = (
            (self.author, HTTPStatus.OK),  # автор записи получает OK,
            (self.reader, HTTPStatus.NOT_FOUND),  # анон получает NOT_FOUND.
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for name in (
                'notes:edit',
                'notes:delete',
                'notes:detail'
            ):
                with self.subTest(user=user, name=name):       
                    url = reverse(name, args=(self.notes.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    # Проверяем редирект анона.
    def test_redirect_for_anonymous_client(self):
        # Сохраняем адрес страницы логина:
        login_url = reverse('users:login')
        # В цикле перебираем имена страниц, с которых ожидаем редирект:
        for name in ('notes:edit', 'notes:delete', 'notes:detail'):
            with self.subTest(name=name):
                # Получаем адрес страницы редактирования или удаления записи:
                url = reverse(name, args=(self.notes.slug,))
                # Получаем ожидаемый адрес страницы логина,
                # на который будет перенаправлен пользователь.
                # Учитываем, что в адресе будет параметр next,
                # в котором передаётся
                # адрес страницы, с которой пользователь был переадресован.
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                # Проверяем, что редирект приведёт именно на указанную ссылку.
                self.assertRedirects(response, redirect_url)