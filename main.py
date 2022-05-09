import math
import time
from datetime import date

import psycopg2
import telebot
from telebot import types

token = '5352027586:AAEAzBTwljKVjvgj5eEHX6PRKTeLIx-j2ds'
bot = telebot.TeleBot(token)

conn = psycopg2.connect(
    database="timetable_db",
    user="postgres",
    password="12345",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

week_days = [
    'понедельник',
    'вторник',
    'среда',
    'четверг',
    'пятница'
]


def generate_keyboard():
    keyboard = types.ReplyKeyboardMarkup()
    monday_btn = types.KeyboardButton('Понедельник')
    tuesday_btn = types.KeyboardButton('Вторник')
    wednesday_btn = types.KeyboardButton('Среда')
    thursday_btn = types.KeyboardButton('Четверг')
    friday_btn = types.KeyboardButton('Пятница')

    cur_week_btn = types.KeyboardButton('Тек. неделя')
    next_week_btn = types.KeyboardButton('След. неделя')

    keyboard.row(monday_btn, tuesday_btn)
    keyboard.row(wednesday_btn, thursday_btn)
    keyboard.row(friday_btn)
    keyboard.row(cur_week_btn, next_week_btn)

    return keyboard


def get_week_is_upper():
    today = date.today().timetuple()
    today_day_in_year = today.tm_yday
    study_year = today.tm_year
    if today.tm_mon < 9:
        study_year = study_year - 1

    september_first = time.struct_time((study_year, 9, 1, 0, 0, 0, 0, 0, 0))
    first_week_monday_day_in_year = september_first.tm_yday - september_first.tm_wday

    today_since_first_week = today_day_in_year - first_week_monday_day_in_year

    total_study_weeks = math.ceil(float(today_since_first_week) / float(7))
    return total_study_weeks % 2 == 0


def convert_time(time_str):
    splitted = time_str.split(":")
    hour = float(splitted[0])
    minutes = float(splitted[1])
    hour += minutes / 60
    return hour


def get_day_timetable(day, week_is_upper, standalone=True):
    day_full = day
    if week_is_upper:
        day_full = day + '_верхняя'
    else:
        day_full = day + '_нижняя'

    cursor.execute("SELECT * FROM timetable.timetable WHERE day=\'%s\'" % str(day_full))
    subjects = list(cursor.fetchall())

    # sort subjects
    sorted_subjects = sorted(subjects, key=lambda x: convert_time(x[4]))
    message = ""
    if standalone:
        message += "Расписание на "
    else:
        message += "-----------\n"
    message += day.capitalize() + ":"
    for i, subject in enumerate(sorted_subjects):
        message += "\n\n" + subject[2] + " в " + subject[4] + ", ауд. " + subject[3]
        # get teacher
        cursor.execute('SELECT * FROM timetable.teachers WHERE subject=\'%s\'' % str(subject[2]))
        teachers = list(cursor.fetchall())
        if len(teachers) > 0:
            teacher = teachers[0]
            message += "\nпреп. " + teacher[1]

    return message


def get_week_timetable(week_is_upper):
    message = ""
    if get_week_is_upper() == week_is_upper:
        message += "Расписание на текущую неделю:"
    else:
        message += "Расписание на следующую неделю:"
    for day in week_days:
        str = get_day_timetable(day, week_is_upper, False)
        message += "\n" + str

    return message


@bot.message_handler(commands=['start'])
def start(message):
    keyboard = generate_keyboard()
    bot.send_message(message.chat.id, 'Привет! Я бот, показывающий расписание!', reply_markup=keyboard)


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id,"У меня есть удобная клавиатура, где всё просто и понятно", reply_markup=generate_keyboard())


@bot.message_handler(commands=['week'])
def week_command(message):
    if get_week_is_upper():
        bot.send_message(message.chat.id, "Сейчас верхняя неделя" )
    else:
        bot.send_message(message.chat.id, "Сейчас нижняя неделя")


@bot.message_handler(content_types=['text'])
def answer(message):
    if message.text.lower() in week_days:
        bot.send_message(message.chat.id, get_day_timetable(message.text.lower(), get_week_is_upper()))
    elif message.text.lower() == 'тек. неделя':
        bot.send_message(message.chat.id, get_week_timetable(get_week_is_upper()))
    elif message.text.lower() == 'след. неделя':
        bot.send_message(message.chat.id, get_week_timetable(not get_week_is_upper()))
    else:
        bot.send_message(message.chat.id, "Я не знаю такой команды((")


bot.polling(none_stop=True, interval=0)
