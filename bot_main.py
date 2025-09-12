from aiogram.client.session.aiohttp import AiohttpSession
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from googletrans import Translator
import asyncio
import requests
API_KEY = "018b1b70cbb24bedb5ba805080aa5e8d"
TOKEN = "8457923329:AAFOSxGcDY4wqKiihUias__T99VscvAPvFk"
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
def get_news(category, page = 1):
    news_url = "https://newsapi.org/v2/top-headlines"
    news_params = {
        "language": "en",
        "category": category,
        "apiKey": API_KEY,
        "page": page
    }
    news_response = requests.get(news_url,params = news_params)
    news_data = news_response.json()
    news_articles = news_data.get('articles',[])
    return news_articles[:5] if news_articles else []
async def send_news(category : str, message : types.Message,state :FSMContext):
    await message.answer("Ищу новости по вашей категории...")
    news_articles = get_news(category)
    if not news_articles:
        await message.answer("Новости не найденыю Попробуйте позже...")
    else:
        await state.update_data(category = category)
        for n in news_articles:
            news_title = n.get("title","")
            news_description = n.get("description","")
            news_url = n.get("url","")
            translate_news_title = translator.translate(news_title,dest='ru').text
            translate_description = translator.translate(news_description,dest ="ru").text
            text = f"{translate_news_title}\n\n{translate_description}\n{news_url}"
def get_curs(base="USD", target="EUR"):
    url = f"https://api.frankfurter.app/latest?from={base}&to={target}"
    response = requests.get(url)
    data = response.json()
    rate = data["rates"][target]
    print(f"Курс {base} к {target}: {rate}")
def get_weather(city="Minsk"):
    url = f"https://wttr.in/{city}?format=j1"
    response = requests.get(url)
    data = response.json()
    current = data["current_condition"][0]
    temp = current["temp_C"]
    desc = current["weatherDesc"][0]["value"]
    print(f"Погода в {city}: {temp}°C, {desc}")


class Form(StatesGroup):
    user_input = State()
    user_choise = State()
    news_category = State()
@dp.message(Command('start'))
async def start_function(message : types.Message, state : FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text = "Новости по всему миру")],
            [KeyboardButton(text = "Прогноз погоды")], 
            [KeyboardButton(text = "Курс валют")]
        ],
        resize_keyboard=True
    )
    await message.answer("Привет, я UniversalBot! Что желаешь посмотреть?",reply_markup=keyboard)
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
        curs = get_curs("USD","BYN")
        await message.answer(f"Курс USD в BYN: {curs}")
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
    else:
        await message.answer("Не удалось определить категорию. Попробуйте позже...")
@dp.message(Form.user_input)
async def weather_city(message: types.Message, state: FSMContext):
    city = message.text.lower()
    if city == "назад":
        await start_function(message, state)
        return

    weather = get_weather(city)
    await message.answer(weather)
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())