from aiogram.client.session.aiohttp import AiohttpSession
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from googletrans import Translator
import pandas as pd
from datetime import datetime
from token_name import TOKEN
from api_key import NEWS_API_KEY
import os 
import asyncio
import requests


session = AiohttpSession()
session._connector_init = {'ssl': False}
bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()
translator = Translator()

news_topic = {
    "Технологии, IT, гаджеты, инновации": "technology",
    "Бизнес, экономика, финансы": "business",
    "Развлечения, шоу-бизнес, кино, музыка": "entertainment",
    "Наука, исследования, открытия": "science",
    "Политика, происшествия, события": "general",
    "Здравоохранение, медицина, эпидемии": "health",
    "Спорт, соревнования, трансферы": "sports"
}

def get_news(category, page=1):
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "language": "en",
        "category": category,
        "apiKey": NEWS_API_KEY,
        "page": page
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data.get("articles", [])[:5]

async def send_news(category: str, message: types.Message, state: FSMContext):
    await message.answer("Ищу новости по вашей категории...")
    articles = get_news(category)

    if not articles:
        await message.answer("Новости не найдены. Попробуйте позже.")
        return

    await state.update_data(category=category)

    for article in articles:
        try:
            title = article.get("title", "")
            description = article.get("description", "")
            url = article.get("url", "")

            translated_title = translator.translate(title, dest='ru').text if title else "Без заголовка"
            translated_description = translator.translate(description, dest='ru').text if description else "Описание отсутствует"

            text = f"{translated_title}\n\n{translated_description}\n{url}"
            await message.answer(text)
        except Exception as e:
            print(f"Ошибка при обработке новости: {e}")
            await message.answer("Ошибка при получении одной из новостей.")

def get_curs():
    try:
        url = "https://www.nbrb.by/api/exrates/rates/USD?parammode=2"
        response = requests.get(url)
        data = response.json()

        rate = data.get("Cur_OfficialRate")
        if rate:
            return f"Официальный курс USD к BYN: {rate:.4f}"
        else:
            return "Не удалось получить курс USD к BYN."

    except Exception as e:
        print(f"Ошибка при получении курса: {e}")
        return "Произошла ошибка при получении курса валют."

def get_weather(city="Minsk"):
    try:
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url)
        data = response.json()
        current = data["current_condition"][0]
        temp = current["temp_C"]
        desc = current["weatherDesc"][0]["value"]
        return f"Погода в {city.title()}: {temp}°C, {desc}"
    except Exception as e:
        print(f"Ошибка при получении погоды: {e}")
        return "Не удалось получить прогноз погоды."
def user_log(user_id, user_name, user_motion, api_name,api_answer):
    now = datetime.now()
    date_now = now.strftime("%Y-%m-%d")
    time_now = now.strftime("%H:%M:%S")
    log_file = "bot_log.csv"
    new_row = {
        "Unic_id" : user_id,
        "@TG_nik" : f"@{user_name}",
        "Motion" : user_motion,
        "API" : api_name,
        "Date" : date_now,
        "Time" : time_now, 
        "API_answer" : api_answer
    }
    df = pd.read_csv(log_file)
    df = pd.concat([df,pd.DataFrame([new_row])],ignore_index=True)
    df.to_csv(log_file, index = False)

class Form(StatesGroup):
    user_input = State()
    user_choise = State()
    news_category = State()

@dp.message(Command("start"))
async def start_function(message: types.Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Новости по всему миру")],
            [KeyboardButton(text="Прогноз погоды")],
            [KeyboardButton(text="Курс валют")]
        ],
        resize_keyboard=True
    )
    await message.answer("Привет, я UniversalBot! Что желаешь посмотреть?", reply_markup=keyboard)
    await state.set_state(Form.user_choise)

@dp.message(Form.user_choise)
async def first_user_choise(message: types.Message, state: FSMContext):
    user_text = message.text.lower()

    if user_text == "новости по всему миру":
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=key)] for key in news_topic.keys()] + [[KeyboardButton(text="Назад")]],
            resize_keyboard=True
        )
        await message.answer("Выберите раздел для просмотра новостей", reply_markup=keyboard)
        await state.set_state(Form.news_category)

    elif user_text == "прогноз погоды":
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Минск")],
                [KeyboardButton(text="Витебск")],
                [KeyboardButton(text="Гродно")],
                [KeyboardButton(text="Гомель")],
                [KeyboardButton(text="Брест")],
                [KeyboardButton(text="Могилёв")],
                [KeyboardButton(text="Назад")]
            ],
            resize_keyboard=True
        )
        await message.answer("Выберите город для прогноза погоды", reply_markup=keyboard)
        await state.set_state(Form.user_input)

    elif user_text == "курс валют":
        result = get_curs()
        await message.answer(result)
        user_log(message.from_user.id, message.from_user.username,"Курс валют", "wttr.in",result)

    else:
        await message.answer(f"Вы написали <<{user_text}>>, я не знаю такой команды")

@dp.message(Form.news_category)
async def news_category(message: types.Message, state: FSMContext):
    text = message.text.strip()

    if text.lower() == "назад":
        await start_function(message, state)
        return

    category = news_topic.get(text)
    if category:
        await send_news(category, message, state)
        user_log(message.from_user.id, message.from_user.username, "Новости по всему миру", "newsapi.org", text)

    else:
        await message.answer("Не удалось определить категорию. Попробуйте позже.")

@dp.message(Form.user_input)
async def weather_city(message: types.Message, state: FSMContext):
    city = message.text.lower()
    if city == "назад":
        await start_function(message, state)
        return

    await message.answer(get_weather(city))
    user_log(message.from_user.id, message.from_user.username,"Прогноз погоды", "wttr.in",get_weather(city))

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
