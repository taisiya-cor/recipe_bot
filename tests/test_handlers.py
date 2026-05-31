import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, Chat, User as TGUser

from handlers.help import cmd_help
from keyboards.inline import get_categories_keyboard
from database.models import Category


@pytest.mark.asyncio
async def test_help_handler():
    """Тест обработчика команды /help на выдачу корректной справки"""

    # Создаем базовый мок для сообщения
    message_mock = MagicMock(spec=Message)
    message_mock.text = "💡 Помощь"

    # Имитируем структуры пользователя и чата
    message_mock.from_user = MagicMock(spec=TGUser)
    message_mock.chat = MagicMock(spec=Chat)

    # Делаем метод answer асинхронной корутиной
    async_answer = AsyncMock()
    message_mock.answer = async_answer

    # Передаем настроенный мок в наш реальный обработчик
    await cmd_help(message=message_mock)

    # Проверяем, что метод отправки ответа сработал ровно 1 раз
    async_answer.assert_called_once()

    # Извлекаем переданный ботом текст
    called_args, called_kwargs = async_answer.call_args
    sent_text = called_args[0]

    # ИСПРАВЛЕНО: Проверяем, что ключевые слова содержатся в отправленном тексте
    assert "Справка по боту" in sent_text
    assert called_kwargs.get("parse_mode") == "Markdown"


def test_categories_inline_keyboard_generation():
    """Тест корректной генерации инлайн-кнопок и callback_data для меню категорий"""

    # Создаем тестовый список категорий (объекты модели)
    mock_categories = [
        Category(id=1, name="🌅 Завтраки"),
        Category(id=2, name="🍜 Супы")
    ]

    # Вызываем нашу функцию генерации клавиатуры
    markup = get_categories_keyboard(mock_categories)

    # Проверяем, что разметка клавиатуры успешно создана
    assert markup is not None
    assert markup.inline_keyboard is not None

    # Проверяем структуру кнопок
    buttons_row = markup.inline_keyboard[0]  # Первая строка кнопок
    assert len(buttons_row) == 2  # Две кнопки в одном ряду (.adjust(2))

    # Проверяем текст и скрытые данные (callback_data) первой кнопки
    assert buttons_row[0].text == "🌅 Завтраки"
    assert buttons_row[0].callback_data == "category_1"

    # Проверяем вторую кнопку
    assert buttons_row[1].text == "🍜 Супы"
    assert buttons_row[1].callback_data == "category_2"
