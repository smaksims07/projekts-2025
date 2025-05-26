import asyncio
import logging
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

API_TOKEN = '7551460968:AAHChxccU9cnFufSdeO5HMEm_J1XTMlPGEE'  

logging.basicConfig(level=logging.INFO)

# SQLite 
conn = sqlite3.connect('reminders.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL
)
''')
conn.commit()

# Инициализация бота и диспетчера 
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

scheduler = AsyncIOScheduler()

# Функция отправки напоминания 
async def send_reminder(user_id: int, text: str):
    try:
        await bot.send_message(user_id, f"🔔 Atgādinājums: {text}")
    except Exception as error:
        logging.error(f"Kļūda, sūtot ziņojumu: {error}")

# Добавляем задачу в APScheduler 
def schedule_reminder(reminder_id, user_id, text, date_str, time_str):
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    scheduler.add_job(
        send_reminder,
        trigger=DateTrigger(run_date=dt),
        args=(user_id, text),
        id=str(reminder_id),
        replace_existing=True
    )

# Загрузка напоминаний из базы при старте
def load_reminders():
    cursor.execute("SELECT id, user_id, text, date, time FROM reminders")
    rows = cursor.fetchall()
    for row in rows:
        schedule_reminder(*row)

# Валидация даты и времени
def validate_date_time(date_str: str, time_str: str) -> bool:
    try:
        datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        return True
    except ValueError:
        return False

# /start
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Cau! Esmu tavs atgādinājums.\n\n"
        "Komandas:\n"
        "/add YYYY-MM-DD HH:MM teksts — pievienot atgādinājumu\n"
        "/list — atgādinājumu sarakstu.\n"
        "/delete ID — izdzēst atgādinājumu pēc ID"
    )

# /add 
@dp.message(Command("add"))
async def add_handler(message: types.Message):
    parts = message.text.split(maxsplit=3)
    # Проверяем корректность введённых данных
    if len(parts) < 4:
        await message.answer("Nepareizs formāts. Izmantojiet:\n/add YYYY-MM-DD HH:MM teksts")
        return

    date_str, time_str, reminder_text = parts[1], parts[2], parts[3]

    if not validate_date_time(date_str, time_str):
        await message.answer("Nepareizs datuma vai laika formāts. Izmantojiet YYYY-MM-DD HH:MM")
        return

    # Вставляем в базу
    cursor.execute(
        "INSERT INTO reminders (user_id, text, date, time) VALUES (?, ?, ?, ?)",
        (message.from_user.id, reminder_text, date_str, time_str)
    )
    conn.commit()
    reminder_id = cursor.lastrowid

    # Запланировать отправку напоминания
    schedule_reminder(reminder_id, message.from_user.id, reminder_text, date_str, time_str)

    await message.answer("Ir pievienots atgādinājums!")

# /list 
@dp.message(Command("list"))
async def list_handler(message: types.Message):
    cursor.execute("SELECT id, date, time, text FROM reminders WHERE user_id = ?", (message.from_user.id,))
    reminders = cursor.fetchall()

    if not reminders:
        await message.answer("Jums nav nekādu atgādinājumi")
        return

    response_lines = ["Jūsu atgādinājumi:"]
    for reminder_id, date_str, time_str, text in reminders:
        response_lines.append(f"{reminder_id}. {date_str} {time_str} — {text}")

    await message.answer("\n".join(response_lines))

# /delete 
@dp.message(Command("delete"))
async def delete_handler(message: types.Message):
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Izmantojiet: /delete ID")
        return

    try:
        reminder_id = int(parts[1])
    except ValueError:
        await message.answer("ID jābūt skaitlim.")
        return

    cursor.execute("DELETE FROM reminders WHERE id = ? AND user_id = ?", (reminder_id, message.from_user.id))
    conn.commit()

    if cursor.rowcount == 0:
        await message.answer("Nav atrasts neviens atgādinājums ar šo ID.")
    else:
        # Удаляем задачу из планировщика, если есть
        try:
            scheduler.remove_job(str(reminder_id))
        except Exception:
            pass
        await message.answer("Izdzēsts atgādinājums.")

# Запуск 
async def main():
    load_reminders()
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
