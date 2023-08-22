from telegram_bot_calendar import DetailedTelegramCalendar

from database.database import User
from states.user_states import UserStates
from utils.set_bot_commands import set_default_commands
from config_data import config
from utils.dictionary import *
from geopy import Nominatim
from telebot import types
from datetime import *
from loader import *
import time as stime
import handlers
import keyboards
import requests
import json
import re

global user_id, chat_id


def get_city(message):
    global user_id, chat_id
    user_id = message.from_user.id
    chat_id = message.chat.id
    if message.text == "Главное меню" or message.text == "Назад":
        restart(message)
    bot.set_state(user_id=user_id, state=UserStates.language, chat_id=chat_id)
    bot.set_state(user_id=user_id, state=UserStates.currency, chat_id=chat_id)
    with bot.retrieve_data(user_id=user_id, chat_id=chat_id) as result:
        result['language'] = ['en_US', 'км']
        result['currency'] = ['USD', '$']
        querystring_loc = {"q": message.text, "locale": result['language'][0]}
    response = requests.request("GET", url_get_city, headers=headers, params=querystring_loc)
    while response.status_code != 200:
        stime.sleep(1)
        response = requests.request("GET", url_get_city, headers=headers, params=querystring_loc)
    date_locations = json.loads(response.text)
    dl_len = len(date_locations.get("sr"))
    if dl_len > 0:
        locations_and_id = create_town_list(date_locations, dl_len)
        markup = types.ReplyKeyboardMarkup()
        for i_dict in locations_and_id:
            markup.add(i_dict[1])
        bot.send_message(message.chat.id, "Выберите город из списка.", reply_markup=markup)
        bot.register_next_step_handler(message, get_id_and_city, locations_and_id)
    else:
        bot.send_message(message.chat.id, "По вашему запросу ничего не найдено",
                         bot.register_next_step_handler(restart(message)))


def create_town_list(list_, list_len):
    if list_len > 0:
        locations_and_id = []
        for i in range(list_len):
            try:
                locations_and_id.append((int(list_.get("sr")[i]['cityId']),
                                         str(list_.get("sr")[i]['hotelAddress']['city']),
                                         str(list_.get("sr")[i]['hierarchyInfo']['country']['isoCode2']),
                                         str(list_.get("sr")[i]['hierarchyInfo']['country']['isoCode3'])))
            except KeyError:
                try:
                    locations_and_id.append((int(list_.get("sr")[i]['cityId']),
                                             str(list_.get("sr")[i]["regionNames"]["fullName"]),
                                             str(list_.get("sr")[i]['hierarchyInfo']['country']['isoCode2']),
                                             str(list_.get("sr")[i]['hierarchyInfo']['country']['isoCode3'])))
                except KeyError:
                    try:
                        locations_and_id.append((int(list_.get("sr")[i]["essId"]["sourceId"]),
                                                 str(list_.get("sr")[i]["regionNames"]["fullName"]), str(
                            list_.get("sr")[i]['hierarchyInfo']['country']['isoCode2']), str(
                            list_.get("sr")[i]['hierarchyInfo']['country']['isoCode3'])))
                    except KeyError:
                        locations_and_id.append((int(list_.get("sr")[i]["essId"]["sourceId"]),
                                                 str(list_.get("sr")[i]["regionNames"]["fullName"]), str(
                            list_.get("sr")[i]['hierarchyInfo']['country']['isoCode3'])[:2], str(
                            list_.get("sr")[i]['hierarchyInfo']['country']['isoCode3'])))
    return locations_and_id


def get_id_and_city(message, locations_and_id):
    for i in range(len(locations_and_id)):
        if message.text == locations_and_id[i][1]:
            bot.set_state(message.from_user.id, UserStates.city_id, message.chat.id)
            bot.set_state(message.from_user.id, UserStates.country_iso_code2, message.chat.id)
            bot.set_state(message.from_user.id, UserStates.country_iso_code3, message.chat.id)
            with bot.retrieve_data(message.from_user.id, message.chat.id) as result:
                result['city_id'] = int(locations_and_id[i][0])
                result['country_iso_code2'] = str(locations_and_id[i][2])
                result['country_iso_code3'] = str(locations_and_id[i][3])
            break

    with bot.retrieve_data(user_id=user_id, chat_id=chat_id) as result:
        if result['city_id'] is not None:
            result['country'] = message.text
            if result['sort_order_distance'] is True:
                bot.send_message(message.chat.id, text=f'Искать в радиусе от (км):',
                                 reply_markup=types.ReplyKeyboardRemove())
                bot.register_next_step_handler(message, get_distance_from)
            elif result['sort_order_distance'] is False:
                bot.send_message(message.chat.id, text='Выберите дату заезда:',
                                 reply_markup=types.ReplyKeyboardRemove())
                check_in(message)
            else:
                bot.send_message(message.chat.id, text='<b>Ошибка!</b>', parse_mode='html')
                restart(message)
        elif message.text == 'Назад':
            bot.send_message(message.chat.id, 'Введите название города.', reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, get_city)
        elif message.text == 'Главное меню':
            restart(message)
        else:
            bot.send_message(message.chat.id, text='<b>Ошибка!</b>\nВыберите город из списка!', parse_mode='html')
            bot.register_next_step_handler(message, get_id_and_city, locations_and_id)


def get_distance_from(message):
    if message.text == "Главное меню":
        restart(message)
    elif message.text == "Назад":
        bot.send_message(message.chat.id, text='Введите название города:', reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_city)
    elif check_from_to(message=message, func_name=get_distance_from.__name__):
        with bot.retrieve_data(message.from_user.id, message.chat.id) as result:
            result['min_distance'] = int(message.text)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            bot.send_message(message.chat.id, text=f'Искать в радиусе до (км):',
                             reply_markup=markup)
            bot.register_next_step_handler(message, get_distance_to)
    else:
        bot.register_next_step_handler(message, get_distance_from)


def get_distance_to(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as result:
        if message.text == 'Главное меню':
            restart(message)
        elif message.text == 'Назад':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            bot.send_message(message.chat.id, text=f'Искать в радиусе от (км):',
                             reply_markup=markup)
            bot.register_next_step_handler(message, get_distance_from)
        elif check_from_to(message=message, func_name=get_distance_to.__name__):
            result['max_distance'] = int(message.text)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            bot.send_message(message.chat.id, text=f'Искать в стоимости за ночь от ($):',
                             reply_markup=markup)
            bot.register_next_step_handler(message, get_price_from)
        else:
            bot.register_next_step_handler(message, get_distance_to)


def get_price_from(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as result:
        if message.text == 'Главное меню':
            restart(message)
        elif message.text == 'Назад':
            bot.send_message(message.chat.id, text=f'Искать в радиусе до (км):')
            bot.register_next_step_handler(message, get_distance_to)
        elif check_from_to(message=message, func_name=get_price_from.__name__):
            result['min_price'] = int(message.text)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            bot.send_message(message.chat.id, text=f'Искать в стоимости за ночь до ($):',
                             reply_markup=markup)
            bot.register_next_step_handler(message, get_price_to)
        else:
            bot.register_next_step_handler(message, get_price_from)


def get_price_to(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as result:
        if message.text == 'Главное меню':
            restart(message)
        elif message.text == 'Назад':
            bot.send_message(message.chat.id, text=f'Искать в стоимости за ночь от ({result["currency"][0]}):',
                             reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, get_price_from)
        elif check_from_to(message=message, func_name=get_price_to.__name__):
            result['max_price'] = int(message.text)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            bot.send_message(message.chat.id, text=f'Выберите дату заезда:', reply_markup=markup)
            check_in(message)
        else:
            bot.register_next_step_handler(message, get_price_to)


def check_in(message):
    if message.text == 'Главное меню':
        restart(message)
    elif message.text == 'Назад':
        bot.register_next_step_handler(message, get_price_to)

    calendar, step = DetailedTelegramCalendar(calendar_id=1, min_date=date.today(), locale='ru').build()

    bot.send_message(message.chat.id,
                     f"Выберите {my_calendar[step]}",
                     reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def cal1(call):
    res, key, step = DetailedTelegramCalendar(min_date=date.today(),
                                              locale='ru', calendar_id=1).process(call.data)
    if not res and key:
        bot.edit_message_text(f"Выберите {my_calendar[step]}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif res:
        bot.edit_message_text(f"Дата заезда: {res}.",
                              call.message.chat.id,
                              call.message.message_id)
        global user_id, chat_id
        bot.send_message(call.message.chat.id, text='Выберите дату выезда:')
        bot.set_state(user_id=user_id, state=UserStates.check_in, chat_id=chat_id)
        with bot.retrieve_data(user_id=user_id, chat_id=chat_id) as result:
            result['check_in'] = res
        check_out(call.message)


def check_out(message):
    if message.text == 'Главное меню':
        restart(message)
    elif message.text == 'Назад':
        bot.register_next_step_handler(message, check_in)

    global user_id, chat_id
    with bot.retrieve_data(user_id=user_id, chat_id=chat_id) as result:
        calendar, step = DetailedTelegramCalendar(
            calendar_id=2, min_date=result['check_in'] + timedelta(days=1), locale='ru').build()
        bot.send_message(message.chat.id,
                         f"Выберите {my_calendar[step]}",
                         reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def cal2(call):
    global user_id, chat_id
    bot.set_state(user_id=user_id, state=UserStates.check_out, chat_id=chat_id)
    with bot.retrieve_data(user_id=user_id, chat_id=chat_id) as result:
        res, key, step = DetailedTelegramCalendar(min_date=result['check_in'] + timedelta(days=1),
                                                  locale='ru', calendar_id=2).process(call.data)
        if not res and key:
            bot.edit_message_text(f"Выберите {my_calendar[step]}",
                                  call.message.chat.id,
                                  call.message.message_id,
                                  reply_markup=key)
        elif res:
            bot.edit_message_text(f"Дата выезда: {res}.",
                                  call.message.chat.id,
                                  call.message.message_id)
            result['check_out'] = res
            bot.send_message(call.message.chat.id, text='Сколько отелей показать(max 10)?')
            bot.register_next_step_handler(call.message, get_count_hotel)


def get_count_hotel(message):
    if message.text == 'Главное меню':
        restart(message)
    elif message.text == 'Назад':
        bot.register_next_step_handler(message, check_out)
    elif int(message.text) > 0:
        count_hotel = int(message.text)
        if count_hotel >= 10:
            count_hotel = 10

        bot.set_state(message.from_user.id, UserStates.count_hotel, message.chat.id)
        bot.set_state(message.from_user.id, UserStates.page_size, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as result:
            result['count_hotel'] = count_hotel
            result['page_size'] = int(count_hotel)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        key_yes = types.KeyboardButton(text='Да')
        key_no = types.KeyboardButton(text='Нет')
        markup.add(key_yes, key_no)
        bot.send_message(message.chat.id, text='Результат поиска показать с фото?', reply_markup=markup)
        bot.register_next_step_handler(message, get_photo)


def get_photo(message):
    bot.set_state(message.from_user.id, UserStates.flag_photos, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as result:
        if message.text == 'Главное меню':
            restart(message)
        elif message.text == 'Назад':
            bot.register_next_step_handler(message, get_count_hotel)
        elif message.text.lower() == 'да':
            result['flag_photos'] = True
            bot.send_message(message.from_user.id, 'Сколько фото показать(max 10)?',
                             reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(message, get_count_photo)
        elif message.text.lower() == 'нет':
            result['flag_photos'] = False
            get_result(message)
        else:
            bot.send_message(message.chat.id, text='<b>Ошибка!</b>\nНе верная команда!', parse_mode='html')
            bot.register_next_step_handler(message, get_count_hotel)


def get_count_photo(message):
    if message.text == 'Главное меню':
        restart(message)
    elif message.text == 'Назад':
        bot.register_next_step_handler(message, get_photo)

    elif int(message.text) > 0:
        count_photo = int(message.text)
        if count_photo >= 10:
            count_photo: int = 10
        bot.set_state(message.from_user.id, UserStates.count_photos, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as result:
            result['count_photos'] = int(count_photo)
        get_result(message)
    else:
        bot.send_message(message.chat.id, '<b>Ошибка!</b>\nВведите число от 1 до 10:',
                         parse_mode='html')
        bot.register_next_step_handler(message, get_count_photo)


def check_from_to(message, func_name):
    bot.set_state(message.from_user.id, UserStates.name_key_dick, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as result:
        name_key_dick = func_name[4:]
        if func_name.startswith('get_distance'):
            word_check = 'Радиус'
        else:
            word_check = 'Стоимость за ночь'
        if func_name.endswith('from'):
            from_flag = True
            from_to = 'от'
        else:
            from_flag = False
            from_to = 'до'
        try:
            message_convector = int(message.text)
            try:
                if message_convector >= 0:
                    mess = f'<b>Ошибка!!</b>\n{word_check} поиска "до" не может быть меньше чем "от"\nВведите {word_check.lower()} {from_to} которого искать еще раз'
                    if from_flag is False and name_key_dick.startswith('distance') and message_convector < result[
                        'min_distance']:
                        bot.send_message(message.chat.id, text=mess, parse_mode='html')
                        raise IndexError
                    elif from_flag is False and name_key_dick.startswith('price') and message_convector < result[
                        'min_price']:
                        bot.send_message(message.chat.id, text=mess, parse_mode='html')
                        raise IndexError

                    result['name_key_dick'] = message_convector
                    return True
                else:
                    bot.send_message(message.chat.id,
                                     text=f'<b>Ошибка!!</b>\n{word_check} поиска не может быть меньше 0\nВведите '
                                          f'{word_check.lower()} {from_to} которого искать еще раз', parse_mode='html')
                    raise IndexError
            except IndexError:
                return False
        except ValueError:
            bot.send_message(message.chat.id, text=f'<b>Ошибка!!</b>\n{word_check} поиска должен быть числом\n'
                                                   f'Введите {word_check.lower()} {from_to} '
                                                   f'которого искать еще раз:', parse_mode='html')
            return False


def get_result(message):
    if message.text == 'Главное меню':
        restart(message)
    elif message.text == 'Назад':
        bot.register_next_step_handler(message, get_count_photo)
    bot.send_message(message.chat.id, text=f'<u>Подождите, идет загрузка...</u>',
                     reply_markup=types.ReplyKeyboardRemove(), parse_mode='html')
    response_meta = requests.request("GET", url_meta, headers=headers)
    while response_meta.status_code != 200:
        stime.sleep(1)
        response_meta = requests.request("GET", url_meta, headers=headers)
    meta_data = json.loads(response_meta.text)
    try:
        bot.set_state(message.from_user.id, UserStates.eapid, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as result:
            result['eapid'] = int(meta_data.get(result['country_iso_code2'])['EAPID'])
    except TypeError:
        bot.send_message(message.chat.id, text='Ничего не найдено.')
        restart(message)
    try:
        bot.set_state(message.from_user.id, UserStates.site_id, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as result:
            result['site_id'] = int(meta_data.get(result['country_iso_code2'])["siteId"])
    except TypeError:
        bot.send_message(message.chat.id, text='Ничего не найдено.')
        restart(message)
    bot.set_state(message.from_user.id, UserStates.res_size, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as result:
        if result['sort_order_distance'] is True:
            result['res_size'] = 200
        else:
            result['res_size'] = int(result['count_hotel'])
    with bot.retrieve_data(message.from_user.id, message.chat.id) as result:
        try:
            payload_hotels = {
                "currency": "USD",
                "eapid": result['eapid'],
                "locale": "en_US",
                "siteId": result['site_id'],
                "destination": {"regionId": str(result['city_id'])},
                "checkInDate": {
                    "day": int(str(result['check_in']).split("-")[2]),
                    "month": int(str(result['check_in']).split("-")[1]),
                    "year": int(str(result['check_in']).split("-")[0])
                },
                "checkOutDate": {
                    "day": int(str(result['check_out']).split("-")[2]),
                    "month": int(str(result['check_out']).split("-")[1]),
                    "year": int(str(result['check_out']).split("-")[0])
                },
                "rooms": [{"adults": 1}],
                "resultsStartingIndex": 0,
                "resultsSize": 200,
                "sort": result['res_size'],
                "filters": {"price": {
                    "min": int(result['min_price']),
                    "max": int(result['max_price'])
                }}
            }
        except KeyError:
            payload_hotels = {
                "currency": "USD",
                "eapid": result['eapid'],
                "locale": "en_US",
                "siteId": result['site_id'],
                "destination": {"regionId": str(result['city_id'])},
                "checkInDate": {
                    "day": int(str(result['check_in']).split("-")[2]),
                    "month": int(str(result['check_in']).split("-")[1]),
                    "year": int(str(result['check_in']).split("-")[0])
                },
                "checkOutDate": {
                    "day": int(str(result['check_out']).split("-")[2]),
                    "month": int(str(result['check_out']).split("-")[1]),
                    "year": int(str(result['check_out']).split("-")[0])
                },
                "rooms": [{"adults": 1}],
                "resultsStartingIndex": 0,
                "resultsSize": 200,
                "sort": result['res_size']
            }
    response_price = requests.request("POST", url_price, json=payload_hotels, headers=headers)
    while response_price.status_code != 200:
        stime.sleep(1)
        response_price = requests.request("POST", url_price, json=payload_hotels, headers=headers)
    date_price = json.loads(response_price.text)

    if date_price.get("data") is None:
        bot.send_message(message.chat.id, text='Ничего не найдено.')
        restart(message)
    else:
        try:
            if len(date_price.get("data")["propertySearch"]["properties"]) == 0:
                bot.send_message(message.chat.id, text='Ничего не найдено.')
                restart(message)
        except KeyError:
            bot.send_message(message.chat.id, text='Ничего не найдено.')
            restart(message)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as result:
            timedelta_ = int(str(result['check_out'] - result['check_in']).split()[0])
    finish_result = get_hotels_list(message, date_price, timedelta_)
    send_result(finish_result, message)
    date_command: datetime.date = datetime.now().replace(microsecond=0).strftime("%H:%M:%S %d.%m.%Y")
    hotel_str = str([finish_result[i]["name"] for i in range(len(finish_result))])
    user = User(telegram_id=user_id, command=result['command'], date_command=date_command, hotel_list=hotel_str)
    user.save()
    restart(message)


def get_hotels_list(message, date_price, timedelta_):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as result:
        finish_result = []
        for i in range(len(date_price.get("data")["propertySearch"]["properties"])):
            res = date_price.get("data")["propertySearch"]["properties"][i]
            distance = int(float(res["destinationInfo"]["distanceFromDestination"]["value"]) * 1.61)
            if result['sort_order_distance'] is False or (
                    result['sort_order_distance'] is True and result['max_distance'] > distance > result[
                'min_distance']):
                hotel_id = res["id"]
                name = res["name"]
                latitude = float(res["mapMarker"]["latLong"]["latitude"])
                longitude = float(res["mapMarker"]["latLong"]["longitude"])
                address = Nominatim(user_agent="GetLoc").reverse(f"{latitude}, {longitude}")
                price = re.findall(r"\d+", str(res["price"]["displayMessages"]))
                price = min([int(price[i]) if int(price[i]) != timedelta_ and int(price[i]) > 0 else 9999999 for i in
                             range(len(price))])
                hotel_rating = res["reviews"]["score"]
                currency = currencies[0]
                for cur in currencies:
                    if cur in str(res["price"]["displayMessages"]):
                        currency = cur
                finish_result.append(
                    {"hotel_id": hotel_id, "name": name, "address": address, "distance": distance, "price": price,
                     "hotel_rating": hotel_rating, "currency": currency})
            if len(finish_result) == result['count_hotel']:
                break
            stime.sleep(1)
        return finish_result


def send_result(finish_result, message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as result:
        for i in range(len(finish_result)):
            message_str = 'Отель: {hotel_name}\n' \
                          'Адрес: {hotel_address}\n' \
                          'Рейтинг: {hotel_rating}\n' \
                          'Удаленность от центра: {hotel_distance} км\n' \
                          'Цена за ночь: {price}'.format(
                hotel_name=finish_result[i].get("name"),
                hotel_address=finish_result[i].get("address"),
                hotel_rating=finish_result[i].get("hotel_rating"),
                hotel_distance=finish_result[i].get("distance"),
                price=str(finish_result[i].get("currency")) + str(finish_result[i].get("price")))
            try:
                if result['flag_photos'] is True:
                    payload_images = {
                        "currency": "USD",
                        "eapid": 1,
                        "locale": "en_US",
                        "siteId": 300000001,
                        "propertyId": str(finish_result[i].get("hotel_id"))
                    }
                    response_image = requests.request("POST", url_images, json=payload_images, headers=headers_image)
                    while response_image.status_code != 200:
                        response_image = requests.request("POST", url_images, json=payload_images, headers=headers_image)
                    image_data = json.loads(response_image.text)
                    images_data = image_data["data"]["propertyInfo"]["propertyGallery"]["images"]
                    images = [types.InputMediaPhoto(images_data[j]["image"]["url"]) for j in range(result['count_photos'])]
                    images[0] = types.InputMediaPhoto(images_data[0]["image"]["url"], caption=message_str)
                    bot.send_media_group(message.from_user.id, media=images)
                    stime.sleep(3)
            except KeyError:
                bot.send_message(message.from_user.id, message_str)
                stime.sleep(3)


def restart(message):
    bot.delete_state(user_id=user_id, chat_id=chat_id)
    bot.send_message(message.from_user.id, "Я вновь помогу вам подобрать лучший отель!")
    from keyboards.inline.keyboard import start_keyboard
    bot.send_message(message.from_user.id, "Выберите, что вас интересует", reply_markup=start_keyboard())


if __name__ == '__main__':
    set_default_commands(bot)
    bot.infinity_polling()
