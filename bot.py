from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import asyncio

from Constants import TOKEN  # Убедись, что TOKEN определён

ASK_DATE = 1
original_titles = {}
scheduler = AsyncIOScheduler()


# Склонение слова "день"
def get_day_word(n: int) -> str:
    if 11 <= n % 100 <= 14:
        return "дней"
    elif n % 10 == 1:
        return "день"
    elif 2 <= n % 10 <= 4:
        return "дня"
    else:
        return "дней"


# /count — запуск отсчёта
async def count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_chat.type in ['group', 'supergroup']:
        chat = update.effective_chat
        original_titles[chat.id] = chat.title
        await update.message.reply_text("Введите дату в формате ДД.ММ.ГГГГ (например, 30.04.2025):")
        return ASK_DATE
    else:
        await update.message.reply_text("Эта команда работает только в группах.")
        return ConversationHandler.END


# Обработка даты и запуск задачи
async def process_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.effective_chat.id
    date_str = update.message.text

    try:
        target_date = datetime.strptime(date_str, "%d.%m.%Y").date()
        today = datetime.today().date()
        delta_days = (target_date - today).days

        if delta_days < 0:
            await update.message.reply_text("Дата уже прошла. Попробуйте снова.")
            return ASK_DATE

        await update.message.reply_text(f"📅 Отсчёт до {date_str} запущен!")

        original_title = original_titles.get(chat_id)

        # Задача, которая будет запускаться ежедневно
        async def update_title():
            nonlocal delta_days
            if delta_days <= 0:
                final_title = f"{original_title} — Сегодня!"
                await context.bot.set_chat_title(chat_id=chat_id, title=final_title)
                await asyncio.sleep(5)
                await context.bot.set_chat_title(chat_id=chat_id, title=original_title)
                scheduler.remove_job(str(chat_id))
                return

            word = get_day_word(delta_days)
            new_title = f"{original_title} — Осталось {delta_days} {word}"
            try:
                await context.bot.set_chat_title(chat_id=chat_id, title=new_title)
            except Exception as e:
                print(f"Ошибка смены названия: {e}")
            delta_days -= 1

        # Добавляем задачу по расписанию
        scheduler.add_job(update_title, "cron", hour=9, minute=0, id=str(chat_id), replace_existing=True)

        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("❗ Неверный формат даты. Попробуйте снова (ДД.ММ.ГГГГ).")
        return ASK_DATE


# /stopcount — остановить задачу
async def stop_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    job_id = str(chat_id)
    job = scheduler.get_job(job_id)

    if job:
        job.remove()
        original_title = original_titles.get(chat_id)
        if original_title:
            try:
                await context.bot.set_chat_title(chat_id=chat_id, title=original_title)
            except Exception as e:
                print(f"Ошибка при возврате названия: {e}")
        await update.message.reply_text("⛔️ Отсчёт остановлен.")
    else:
        await update.message.reply_text("Нет активного отсчёта для этой беседы.")


# /cancel — отмена ввода даты
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Ввод даты отменён.")
    return ConversationHandler.END


# Запуск планировщика после старта бота
async def post_init(app):
    scheduler.start()


# Сборка и запуск приложения
app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("count", count)],
    states={
        ASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_date)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(conv_handler)
app.add_handler(CommandHandler("stopcount", stop_count))

app.run_polling()
