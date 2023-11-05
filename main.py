from aiogram import Dispatcher, executor, Bot
from aiogram.types import Message, CallbackQuery, LabeledPrice
from keyboards import *
from database import *
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

TOKEN = os.getenv('TOKEN')

PAYMENT_KEY = os.getenv('PAYMENT_KEY')

bot = Bot(TOKEN, parse_mode='HTML')

dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def command_start(message: Message):
    full_name = message.from_user.full_name
    await message.answer(f'Здравствуйте <b>{full_name}</b>/\nВас приветствует  Вкусняха бот')
    await register_user(message)


async def register_user(message: Message):
    chat_id = message.chat.id
    full_name = message.from_user.full_name
    user = first_select_user(chat_id)  # Данная функция будит проверять есть ли пользователь в базе
    if user:
        await message.answer('Авторизация прошла успешно')
        await show_main_menu(message)
    else:
        first_register_user(chat_id, full_name)  # Данная функция будит запускаться если пользователя нет в базе
        await message.answer('Для регистрации поделитесь контактом', reply_markup=generate_phone_button())


#  Функция для получения контакта и регистрации пользователя
@dp.message_handler(content_types=['contact'])
async def finish_register(message: Message):
    chat_id = message.chat.id
    phone = message.contact.phone_number
    print(phone)
    update_user_to_finish_register(chat_id, phone)  # функция для доп внесения данныйх пользователя
    await create_cart_for_user(message)  # Функция запускаеться для добавления карточки пользователю
    await message.answer('Регистрация прошла успешно')
    await show_main_menu(message)


async def create_cart_for_user(message: Message):
    chat_id = message.from_user.id
    print(chat_id)
    try:
        insert_to_cart(chat_id)
    except:
        pass


async def show_main_menu(message: Message):
    await message.answer('Выберите направление', reply_markup=generate_main_menu())


@dp.message_handler(lambda message: '✅ Сделать заказ' in message.text)
async def make_order(message: Message):
    await message.answer('Выберите категорию', reply_markup=generate_category_menu())


@dp.callback_query_handler(lambda call: 'category' in call.data)
async def show_products(call: CallbackQuery):
    chat_id = call.message.chat.id  # отлавливаем id тг в сигнале
    message_id = call.message.message_id  # получаю id самого сообщения
    _, category_id = call.data.split('_')
    category_id = int(category_id)
    await bot.edit_message_text('Выберите продукт', chat_id, message_id,
                                reply_markup=generate_products_by_category(category_id))


@dp.callback_query_handler(lambda call: 'main_menu' in call.data)
async def return_to_main_menu(call: CallbackQuery):
    chat_id = call.message.chat.id  # отлавливаем id тг в сигнале
    message_id = call.message.message_id
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                text='Выберите категорию',
                                reply_markup=generate_category_menu())


@dp.callback_query_handler(lambda call: 'product' in call.data)
async def show_detail_product(call: CallbackQuery):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    _, product_id = call.data.split('_')
    product_id = int(product_id)

    product = get_product_detail(product_id)
    print(product)
    await bot.delete_message(chat_id, message_id)
    with open(product[-1], mode='rb') as img:
        await bot.send_photo(chat_id=chat_id,
                             photo=img,
                             caption=f'''{product[2]}

Ингридиенты: {product[4]}

Цена: {product[3]} сумм''', reply_markup=generate_product_detail_menu(product_id=product_id, category_id=product[1]))


@dp.callback_query_handler(lambda call: 'back' in call.data)
async def return_to_category(call: CallbackQuery):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    _, category_id = call.data.split('_')
    await bot.delete_message(chat_id, message_id)
    await bot.send_message(chat_id, 'Выберите категорию', reply_markup=generate_products_by_category(category_id))


@dp.callback_query_handler(lambda call: 'cart' in call.data)
async def add_product_cart(call: CallbackQuery):
    chat_id = call.message.chat.id
    _, product_id, quantity = call.data.split('_')
    product_id, quantity = int(product_id), int(quantity)

    cart_id = get_user_cart_id(chat_id)  # функция для получения id карточки пользователя по тг id
    product = get_product_detail(product_id)  # функция которая возвращает информацию о продукте

    final_price = product[3] * quantity  # получаю стоимость за выбронное кол-во продукта

    if insert_or_update_cart_product(cart_id, product[2], quantity, final_price):
        await bot.answer_callback_query(call.id, 'Продукт успешно добавлен')
    else:
        await bot.answer_callback_query(call.id, 'Количество усзпешно изменено')


@dp.message_handler(regexp='🛒 Корзина')
async def show_cart(message: Message, edit_message: bool = False):
    chat_id = message.chat.id
    cart_id = get_user_cart_id(chat_id)

    try:
        update_total_product_price(cart_id)  # Функция для добавления и сумирования общей стоимости и кол-во продуктов

    except Exception as e:
        print(e)
        await message.answer('Корзина не доступна. Обратитесь в тех поддержку')
        return

    cart_products = get_cart_products(cart_id)  # Функция для получения Названия продукта, кол-во, стоимость
    total_products, total_price = get_total_product_price(cart_id)  # Получ общ стоимость и кол-во продуктов

    text = 'Ваша корзина: \n\n'
    i = 0
    for product_name, quantity, final_price in cart_products:
        i += 1
        text += f'''{i}. {product_name}
Количество: {quantity}
Общая стоимость: {final_price}\n\n'''

    text += f'''Общее количестов продуктов: {total_products}
Общая стоимость заказа {total_price}'''

    print(edit_message)

    if edit_message:
        await bot.edit_message_text(text, chat_id, message.message_id, reply_markup=generate_cart_menu(cart_id))
    else:
        await bot.send_message(chat_id, text, reply_markup=generate_cart_menu(cart_id))


@dp.callback_query_handler(lambda call: 'delete' in call.data)
async def delete_cart_product(call: CallbackQuery):
    _, cart_product_id = call.data.split('_')
    message = call.message
    cart_product_id = int(cart_product_id)

    delete_cart_product_from_database(cart_product_id)

    await bot.answer_callback_query(call.id, text='Продукт успешно удалён')
    await show_cart(message, edit_message=True)


@dp.callback_query_handler(lambda call: 'order' in call.data)
async def create_order(call: CallbackQuery):
    chat_id = call.message.chat.id

    time_now = datetime.now().strftime('%H:%M')
    data = datetime.now().strftime('%d.%m.%Y')

    _, cart_id = call.data.split('_')
    cart_id = int(cart_id)

    cart_products = get_cart_products(cart_id)  # Функция для получения Названия продукта, кол-во, стоимость
    total_products, total_price = get_total_product_price(cart_id)  # Получ общ стоимость и кол-во продуктов

    text = 'Ваша корзина: \n\n'
    i = 0
    for product_name, quantity, final_price in cart_products:
        i += 1
        text += f'''{i}. {product_name}
    Количество: {quantity}
    Общая стоимость: {final_price}\n\n'''

    text += f'''Общее количестов продуктов: {total_products}
    Общая стоимость заказа {total_price}'''

    # Метод для выполнения оплаты
    await bot.send_invoice(
        chat_id=chat_id,
        title=f'Заказ №{cart_id}',
        description=text,
        payload='bot-defined invoice payload',
        provider_token=PAYMENT_KEY,
        currency='UZS',
        prices=[
            LabeledPrice(label='Общая стоимость', amount=int(total_price * 100)),
            LabeledPrice(label='Доставка', amount=1000000)
        ],
        start_parameter='start_parameter'
    )


@dp.pre_checkout_query_handler(lambda query: True)
async def checkout(pre_checkout_query):
    await bot.answer_pre_checkout_query(pre_checkout_query.id,
                                        ok=True,
                                        error_message='Проверьте баланс карты')


@dp.message_handler(content_types=['successful_payment'])
async def get_payment(message):
    chat_id = message.chat.id
    cart_id = get_user_cart_id(chat_id)
    await bot.send_message(chat_id, 'Ура оплата прошла успешно. Мы вас кинули')
    drop_cart_products_default(cart_id)


@dp.message_handler(regexp='📃 История')
async def get_history(message: Message):
    full_name = message.from_user.full_name
    await bot.send_message(message.chat.id, f'Время заказа: 04-05-2023\n'
                                            f'Дата заказа: 20:06:10.2323343\n'
                                            f'Имя заказчика: {full_name}\n'
                                            f'Количество: 9\n'
                                            f'Общая стоимость: 252000')


executor.start_polling(dp)
