import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")

# ==================== КОНФИГУРАЦИЯ ====================
TOKEN = os.getenv("BOT_TOKEN")
print(f"Токен: {TOKEN}")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5063104298"))     
DATA_FILE = "schedule_data.json"

# Состояния для ConversationHandler
ADD_SUBJECT_DAY, ADD_SUBJECT_NAME = range(2)
DELETE_SUBJECT_DAY, DELETE_SUBJECT_NAME = range(2, 4)
EDIT_HOMEWORK_DAY, EDIT_HOMEWORK_SUBJECT, EDIT_HOMEWORK_TEXT = range(4, 7)

# ==================== РАБОТА С ДАННЫМИ ====================
def load_data():
    if not os.path.exists(DATA_FILE):
        default_data = {
            "schedule": {
                "Понедельник": [],
                "Вторник": [],
                "Среда": [],
                "Четверг": [],
                "Пятница": [],
                "Суббота": [],
                "Воскресенье": []
            },
            "homework": {}
        }
        save_data(default_data)
        return default_data
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==================== КЛАВИАТУРЫ ====================
def get_main_keyboard(user_id):
    keyboard = [["📅 Расписание"]]
    if user_id == ADMIN_ID:
        keyboard.append(["⚙️ Админ панель"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_days_keyboard():
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    keyboard = [[day] for day in days]
    keyboard.append(["🔙 На главную"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_keyboard():
    keyboard = [
        ["✏️ Добавить предмет"],
        ["🗑 Удалить предмет"],
        ["📝 Редактировать ДЗ"],
        ["🔙 На главную"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_subjects_keyboard(day):
    data = load_data()
    subjects = data["schedule"].get(day, [])
    keyboard = []
    for subject in subjects:
        keyboard.append([InlineKeyboardButton(subject, callback_data=f"hw_{day}_{subject}")])
    return InlineKeyboardMarkup(keyboard)

def get_cancel_keyboard():
    keyboard = [["❌ Отмена"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ==================== ХЭНДЛЕРЫ ====================
async def start(update: Update, context):
    await update.message.reply_text(
        f"👋 Привет! Я бот класса «10Б».\n\n"
        f"Нажми «📅 Расписание», выбери день, а затем предмет,\n"
        f"чтобы увидеть домашнее задание.",
        reply_markup=get_main_keyboard(update.effective_user.id)
    )

async def show_schedule(update: Update, context):
    await update.message.reply_text("📆 Выберите день недели:", reply_markup=get_days_keyboard())

async def show_subjects(update: Update, context):
    day = update.message.text
    data = load_data()
    subjects = data["schedule"].get(day, [])
    
    if not subjects:
        await update.message.reply_text(
            f"📭 На {day} пока нет предметов.",
            reply_markup=get_days_keyboard()
        )
        return
    
    await update.message.reply_text(
        f"📚 {day}\n\nВыберите предмет:",
        reply_markup=get_subjects_keyboard(day)
    )

async def show_homework(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    _, day, subject = query.data.split("_", 2)
    data = load_data()
    hw_key = f"{day}_{subject}"
    homework = data["homework"].get(hw_key, "📖 Домашнее задание не задано.")
    
    keyboard = [[InlineKeyboardButton("◀️ Назад к предметам", callback_data=f"back_{day}")]]
    await query.edit_message_text(
        f"📚 *{day}*\n📖 *Предмет:* {subject}\n\n📝 *Домашнее задание:*\n{homework}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def back_to_subjects(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    day = query.data.split("_")[1]
    await query.edit_message_text(
        f"📚 {day}\n\nВыберите предмет:",
        reply_markup=get_subjects_keyboard(day)
    )

async def admin_panel(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет прав.")
        return
    await update.message.reply_text("🔧 Админ панель:", reply_markup=get_admin_keyboard())

async def back_to_main(update: Update, context):
    await update.message.reply_text(
        "🏠 Главное меню:",
        reply_markup=get_main_keyboard(update.effective_user.id)
    )

# ==================== ДОБАВЛЕНИЕ ПРЕДМЕТА ====================
async def add_subject_start(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    await update.message.reply_text("Выберите день:", reply_markup=get_days_keyboard())
    return ADD_SUBJECT_DAY

async def add_subject_day(update: Update, context):
    context.user_data['day'] = update.message.text
    await update.message.reply_text("Введите название предмета:", reply_markup=get_cancel_keyboard())
    return ADD_SUBJECT_NAME

async def add_subject_name(update: Update, context):
    if update.message.text == "❌ Отмена":
        await update.message.reply_text("Отменено.", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    
    day = context.user_data['day']
    subject = update.message.text.strip()
    
    data = load_data()
    if subject not in data["schedule"][day]:
        data["schedule"][day].append(subject)
        save_data(data)
        await update.message.reply_text(f"✅ Предмет «{subject}» добавлен на {day}!")
    else:
        await update.message.reply_text(f"⚠️ Предмет уже есть на {day}.")
    
    await update.message.reply_text("Админ панель:", reply_markup=get_admin_keyboard())
    return ConversationHandler.END

# ==================== УДАЛЕНИЕ ПРЕДМЕТА ====================
async def delete_subject_start(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    await update.message.reply_text("Выберите день:", reply_markup=get_days_keyboard())
    return DELETE_SUBJECT_DAY

async def delete_subject_day(update: Update, context):
    day = update.message.text
    data = load_data()
    subjects = data["schedule"].get(day, [])
    
    if not subjects:
        await update.message.reply_text(f"На {day} нет предметов.", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    
    keyboard = [[f"🗑 {s}"] for s in subjects]
    keyboard.append(["❌ Отмена"])
    context.user_data['day'] = day
    await update.message.reply_text("Выберите предмет:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return DELETE_SUBJECT_NAME

async def delete_subject_name(update: Update, context):
    if update.message.text == "❌ Отмена":
        await update.message.reply_text("Отменено.", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    
    subject = update.message.text.replace("🗑 ", "")
    day = context.user_data['day']
    
    data = load_data()
    if subject in data["schedule"][day]:
        data["schedule"][day].remove(subject)
        hw_key = f"{day}_{subject}"
        if hw_key in data["homework"]:
            del data["homework"][hw_key]
        save_data(data)
        await update.message.reply_text(f"✅ Предмет «{subject}» удален!")
    else:
        await update.message.reply_text("Предмет не найден.")
    
    await update.message.reply_text("Админ панель:", reply_markup=get_admin_keyboard())
    return ConversationHandler.END

# ==================== РЕДАКТИРОВАНИЕ ДЗ ====================
async def edit_homework_start(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END
    await update.message.reply_text("Выберите день:", reply_markup=get_days_keyboard())
    return EDIT_HOMEWORK_DAY

async def edit_homework_day(update: Update, context):
    day = update.message.text
    data = load_data()
    subjects = data["schedule"].get(day, [])
    
    if not subjects:
        await update.message.reply_text(f"На {day} нет предметов.", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    
    keyboard = [[f"📖 {s}"] for s in subjects]
    keyboard.append(["❌ Отмена"])
    context.user_data['day'] = day
    await update.message.reply_text("Выберите предмет:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))
    return EDIT_HOMEWORK_SUBJECT

async def edit_homework_subject(update: Update, context):
    if update.message.text == "❌ Отмена":
        await update.message.reply_text("Отменено.", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    
    subject = update.message.text.replace("📖 ", "")
    context.user_data['subject'] = subject
    await update.message.reply_text("Введите домашнее задание:", reply_markup=get_cancel_keyboard())
    return EDIT_HOMEWORK_TEXT

async def edit_homework_text(update: Update, context):
    if update.message.text == "❌ Отмена":
        await update.message.reply_text("Отменено.", reply_markup=get_admin_keyboard())
        return ConversationHandler.END
    
    day = context.user_data['day']
    subject = context.user_data['subject']
    hw_text = update.message.text.strip()
    
    data = load_data()
    hw_key = f"{day}_{subject}"
    data["homework"][hw_key] = hw_text
    save_data(data)
    
    await update.message.reply_text(f"✅ ДЗ для «{subject}» сохранено!\n\n{hw_text}", reply_markup=get_admin_keyboard())
    return ConversationHandler.END

async def cancel(update: Update, context):
    await update.message.reply_text("Отменено.", reply_markup=get_admin_keyboard())
    return ConversationHandler.END

# ==================== ОСНОВНОЙ ЗАПУСК ====================
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text("📅 Расписание"), show_schedule))
    app.add_handler(MessageHandler(filters.Text("⚙️ Админ панель"), admin_panel))
    app.add_handler(MessageHandler(filters.Text("🔙 На главную"), back_to_main))
    app.add_handler(MessageHandler(filters.Text(["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]), show_subjects))
    
    app.add_handler(CallbackQueryHandler(show_homework, pattern="^hw_"))
    app.add_handler(CallbackQueryHandler(back_to_subjects, pattern="^back_"))
    
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Text("✏️ Добавить предмет"), add_subject_start),
            MessageHandler(filters.Text("🗑 Удалить предмет"), delete_subject_start),
            MessageHandler(filters.Text("📝 Редактировать ДЗ"), edit_homework_start),
        ],
        states={
            ADD_SUBJECT_DAY: [MessageHandler(filters.Text(["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]), add_subject_day)],
            ADD_SUBJECT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_subject_name)],
            DELETE_SUBJECT_DAY: [MessageHandler(filters.Text(["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]), delete_subject_day)],
            DELETE_SUBJECT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_subject_name)],
            EDIT_HOMEWORK_DAY: [MessageHandler(filters.Text(["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]), edit_homework_day)],
            EDIT_HOMEWORK_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_homework_subject)],
            EDIT_HOMEWORK_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_homework_text)],
        },
        fallbacks=[MessageHandler(filters.Text("❌ Отмена"), cancel)],
    )
    try:
        # ... все хэндлеры ...
        print("🤖 Бот запущен...")
        app.run_polling()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        input("Нажми Enter для выхода...")

if __name__ == "__main__":
    main()