# news/tests/test_routes.py
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note


# Получаем модель пользователя.
User = get_user_model()


class TestRoutes(TestCase):

    # Добавляем фикстуру с созданием первой новости:
    @classmethod
    def setUpTestData(cls):
        # Создаём двух пользователей с разными именами:
        cls.author = User.objects.create(username='Лев Толстой')
        cls.notes = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author,
            # Слаг обязательное поле модели Ноут, добавляем его в тесте.
            slug='test-slug',
        )

    def test_pages_availability(self):
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
