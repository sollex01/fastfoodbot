from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_all_categories, get_products_by_category, get_cart_products_for_delete

def generate_phone_button():
    return ReplyKeyboardMarkup([
        [KeyboardButton(text='Поделиться контактом', request_contact=True)]
    ], resize_keyboard=True)


def generate_main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton(text='✅ Сделать заказ')],
        [KeyboardButton(text='📃 История'), KeyboardButton(text='🛒 Корзина'), KeyboardButton(text='⚙ Настройки')]
    ], resize_keyboard=True)


def generate_category_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.row(
        InlineKeyboardButton(text='Всё наше меню', url='https://telegra.ph/Ofigennyj-Havchik-ot-gruppy-Vs-1000-04-16-2')
    )

    categories = get_all_categories()
    buttons = []
    for category in categories:
        btn = InlineKeyboardButton(text=category[1], callback_data=f'category_{category[0]}')
        buttons.append(btn)
    markup.add(*buttons)
    return markup


def generate_products_by_category(category_id):
    markup = InlineKeyboardMarkup(row_width=2)
    products = get_products_by_category(category_id)  # функция вернёт продукты по категории
    buttons = []
    for product in products:
        btn = InlineKeyboardButton(text=product[1], callback_data=f'product_{product[0]}')
        buttons.append(btn)
    markup.add(*buttons)

    markup.row(
        InlineKeyboardButton(text='🔙 Назад', callback_data='main_menu')
    )
    return markup




def generate_product_detail_menu(product_id, category_id):
    markup = InlineKeyboardMarkup(row_width=3)
    numbers = [i for i in range(1, 10)]
    buttons = []
    for number in numbers:
        btn = InlineKeyboardButton(text=str(number), callback_data=f'cart_{product_id}_{number}')
        buttons.append(btn)
    markup.add(*buttons)
    markup.row(
        InlineKeyboardButton(text='Назад', callback_data=f'back_{category_id}')
    )
    return markup




def generate_cart_menu(cart_id):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton(text='🚀 Оформить заказ', callback_data=f'order_{cart_id}')
    )

    cart_products = get_cart_products_for_delete(cart_id)  # функция возвращает список продуктов дял удаления
    for cart_product_id, product_name in cart_products:
        markup.row(
            InlineKeyboardButton(text=f'❌ {product_name}', callback_data=f'delete_{cart_product_id}')
        )

    return markup








