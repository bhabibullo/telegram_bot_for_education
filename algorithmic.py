import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

# Logging setup
logging.basicConfig(level=logging.INFO)

# Bot token
bot_token = "7585178811:AAHHYLDhH4QyHbmtWWX9gQiLC5R8Regt2VQ"  # Replace with your bot token

# Initialize the Bot and Dispatcher
bot = Bot(token=bot_token)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Define FSM states
class Form(StatesGroup):
    name = State()
    course = State()
    subcourse = State()
    day = State()
    time = State()
    phone_number = State()

# Courses and their channel IDs
courses = {
    "Ingliz tili": -1002289014372,
    "IT": -1002336411887,
    "Robototexnika": -1002297932865,
    "Matematika": -1002313828384,
}

# Subcourses for each course
subcourses = {
    "Ingliz tili": ["A1", "A2", "B1", "B2", "C1"],
    "IT": ["Frontend", "Backend", "0 Dan O`rganish"],
    "Robototexnika": ["Robot yasash"],
    "Matematika": [str(i) + " sinf" for i in range(1, 12)],
}

# Days of the week and available times
days_primary = ["Dushanba", "Chorshanba", "Juma"]
days_secondary = ["Seshanba", "Payshanba", "Shanba"]
times = ["9:00-11:00", "11:00-13:00", "14:00-16:00", "16:00-18:00"]

# Validate phone number format
async def validate_phone_number(phone_number: str) -> bool:
    if phone_number.startswith("+998"):
        return len(phone_number) == 13  # +998 and 9 digits
    elif len(phone_number) in [9, 7]:
        return True  # Accepting 9 or 7 digits
    return False

# Command handler for /start
@dp.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await state.set_state(Form.name)  # Set state to wait for name
    await message.answer("Ismingizni va familyangizni kiriting:")

# Handle name input
@dp.message(Form.name)
async def handle_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    course_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=course, callback_data=course)] for course in courses.keys()
    ])
    await message.answer("Qaysi kursni tanlaysiz?", reply_markup=course_keyboard)
    await state.set_state(Form.course)

# Handle course selection
@dp.callback_query(Form.course)
async def handle_course(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(course=callback_query.data)

    # Create subcourse keyboard based on selected course
    subcourse_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=subcourse, callback_data=subcourse)] for subcourse in subcourses[callback_query.data]
    ])
    await callback_query.message.answer("Qaysi kursni tanlaysiz?", reply_markup=subcourse_keyboard)
    await state.set_state(Form.subcourse)

# Handle subcourse selection
@dp.callback_query(Form.subcourse)
async def handle_subcourse(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(subcourse=callback_query.data)

    # Ask for day selection after subcourse selection
    day_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Dushanba, Chorshanba, Juma", callback_data="primary_days")],
        [InlineKeyboardButton(text="Seshanba, Payshanba, Shanba", callback_data="secondary_days")]
    ])
    await callback_query.message.answer("Kunni tanlang:", reply_markup=day_keyboard)
    await state.set_state(Form.day)  # Set state to day

# Handle day selection
@dp.callback_query(Form.day)
async def handle_day(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(day=callback_query.data)

    # Display time options with each time in a separate row
    time_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=time, callback_data=time)] for time in times  # Each time in a separate row
    ])
    await callback_query.message.answer("Vaqt tanlang:", reply_markup=time_keyboard)
    await state.set_state(Form.time)

# Handle time selection
@dp.callback_query(Form.time)
async def handle_time(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(time=callback_query.data)
    await callback_query.message.answer("Telefon raqamingizni kiriting:")
    await state.set_state(Form.phone_number)

# Handle phone number input
@dp.message(Form.phone_number)
async def handle_phone_number(message: types.Message, state: FSMContext):
    phone_number = message.text
    if await validate_phone_number(phone_number):
        # Prepend +998 if the number is in 9 or 7 digit format
        if len(phone_number) == 9:
            phone_number = f"+998{phone_number}"
        elif len(phone_number) == 7:
            phone_number = f"+998{phone_number[2:]}"

        data = await state.get_data()
        channel_id = courses.get(data['course'])

        if channel_id:
            try:
                await bot.send_message(channel_id, f"Ism: {data['name']}\n"
                                                    f"Kurs: {data['course']}\n"
                                                    f"Subkurs: {data['subcourse']}\n"
                                                    f"Kun: {data['day']}\n"
                                                    f"Vaqti: {data['time']}\n"
                                                    f"Telefon: {phone_number}")
                confirmation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Kurs tanlash", callback_data="restart")],
                    [InlineKeyboardButton(text="Biz haqimizda", callback_data="about")]
                ])
                await message.answer("Ma'lumotlaringiz qabul qilindi.", reply_markup=confirmation_keyboard)

                # Clear the state after submission
                await state.clear()
            except Exception as e:
                await message.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
                logging.error(f"Error while sending message: {e}")
    else:
        await message.answer("Iltimos, telefon raqamingizni to'g'ri formatda kiriting!")

# Handle restart and about options
@dp.callback_query(lambda c: c.data == "restart")
async def restart(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await start_command(callback_query.message, state)  # Restart the process

@dp.callback_query(lambda c: c.data == "about")
async def about(callback_query: types.CallbackQuery):
    about_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Filiallarimiz", callback_data="branches")],
        [InlineKeyboardButton(text="O'qituvchilar", callback_data="teachers")]
    ])
    await callback_query.message.answer("Biz haqimizda:", reply_markup=about_keyboard)
    await callback_query.answer()

# Handle branches and teachers options
@dp.callback_query(lambda c: c.data == "branches")
async def handle_branches(callback_query: types.CallbackQuery):
    branches_info = (
        "1. Samarqand shahar, Firdavsiy 1/5 (Infin Bank)\n"
        "2. Samarqand shahar, Sattepo 55-maktab\n"
        "3. Samarqand shahar, Vagzal 139 (Rich burger)"
    )
    await callback_query.message.answer(branches_info)
    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "teachers")
async def handle_teachers(callback_query: types.CallbackQuery):
    teachers_info = (
        "1. Salimov Sardor - IT (Microsoft Sertifikat)\n"
        "2. Alisherov Akramboy - Math (A Sertifikat)\n"
        "3. Qo'chqorov Zoir - Math (A+ Sertifikat)\n"
        "4. Hamrayeva Kumush - English (7.5 IELTS)"
    )
    await callback_query.message.answer(teachers_info)
    await callback_query.answer()


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
