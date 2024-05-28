import schedule
import time
from threading import Thread
from datetime import datetime, timedelta
from database import session, User
from bot_instance import bot
from report_generator import generate_pdf, send_stats
from collections import defaultdict
from  database  import  db_session,  User #  <-  Изменили  `session`  на  `db_session`
from  bot_instance  import  bot
from  report_generator  import  generate_pdf,  send_stats
from report_generator import generate_pdf, send_stats
def send_reminders(user):
    if user.daily_reminders:
        bot.send_message(user.chat_id, "Напоминание: не забудьте записать свои привычки!")

def send_newsletter():
    users = session.query(User).filter_by(subscribed_to_newsletter=True).all()
    for user in users:
        bot.send_message(user.chat_id, "Привет! Это ваша рассылка.")

def schedule_newsletter(user_id):
    user = session.query(User).get(user_id)
    if user:
        if user.subscribed_to_newsletter:
            # Планируем отправку рассылки, например, каждый понедельник в 9:00
            schedule.every().monday.at("09:00").do(send_newsletter)
            print(f"Пользователь {user_id} подписан на рассылку.")
        else:
            # Отписываем пользователя от рассылки
            for job in schedule.get_jobs():
                if job.job_func.__name__ == 'send_newsletter':
                    schedule.cancel_job(job)
            print(f"Пользователь {user_id} отписан от рассылки.")
def send_custom_reminder(user):
    if user.custom_reminder_text:
        bot.send_message(user.chat_id, f"Напоминание: {user.custom_reminder_text}")

def send_subscription_reminder(user):
    if user.subscribed_until:
        bot.send_message(user.chat_id, "Напоминание: ваша подписка скоро закончится!")

def send_lunch_photo_reminder(user):
    if user.level in ['sexy', 'advanced']:
        bot.send_message(user.chat_id, "Небольшое напоминание: ты можешь загрузить фото своего обеда")

def send_dinner_photo_reminder(user):
    if user.level in ['sexy', 'advanced']:
        bot.send_message(user.chat_id, "Небольшое напоминание: ты можешь загрузить фото своего ужина")

def send_morning_poll():
    users = session.query(User).all()
    for user in users:
        bot.send_message(user.chat_id, "Доброе утро! Как ты себя чувствуешь?")

def send_afternoon_poll():
    users = session.query(User).filter(User.level.in_(['sexy', 'advanced'])).all()
    for user in users:
        bot.send_message(user.chat_id, "Как проходит твой день?")

def send_evening_poll():
    users = session.query(User).all()
    for user in users:
        bot.send_message(user.chat_id, "Давай сверим цифры. Сколько активных минут было за день?")

def send_weekly_stats():
    users = session.query(User).filter(User.level == 'advanced').all()
    for user in users:
        try:
            send_stats(user.chat_id)
        except Exception as e:
            print(f"Ошибка при отправке статистики пользователю {user.chat_id}: {e}")

def schedule_checker():
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_scheduler():
    """Настраивает и запускает планировщик задач."""

    users = db_session.query(User).all() # <-- Изменено
    reminders = defaultdict(list)

    for user in users:
        if user.reminder_time:
            # Обрабатываем только одно время напоминания
            try:
                schedule.every().day.at(user.reminder_time).do(send_reminders, user)
                print(f"Ежедневное напоминание для пользователя {user.id} запланировано на {user.reminder_time}.")
            except Exception as e:
                print(f"Ошибка при планировании ежедневного напоминания для пользователя {user.id}: {e}")

        if user.subscribed_until:
            try:
                schedule.every().day.at("12:00").do(send_subscription_reminder, user)
                print(f"Напоминание о подписке для пользователя {user.id} запланировано.")
            except Exception as e:
                print(f"Ошибка при планировании напоминания о подписке для пользователя {user.id}: {e}")

        if user.level in ['sexy', 'advanced']:
            try:
                schedule.every().day.at("14:00").do(send_lunch_photo_reminder, user)
                schedule.every().day.at("18:00").do(send_dinner_photo_reminder, user)
                print(f"Напоминания о фото еды для пользователя {user.id} запланированы.")
            except Exception as e:
                print(f"Ошибка при планировании напоминаний о фото еды для пользователя {user.id}: {e}")

        # Если пользователь уже подписан на рассылку, планируем ее отправку
        if user.subscribed_to_newsletter:
            try:
                schedule_newsletter(user.id)
                print(f"Рассылка для пользователя {user.id} запланирована.")
            except Exception as e:
                print(f"Ошибка при планировании рассылки для пользователя {user.id}: {e}")

    # Настройка опросов
    try:
        schedule.every().day.at("09:00").do(send_morning_poll)
        schedule.every().day.at("15:00").do(send_afternoon_poll)
        schedule.every().day.at("18:00").do(send_evening_poll)
        print("Опросы запланированы.")
    except Exception as e:
        print(f"Ошибка при планировании опросов: {e}")

    # Настройка еженедельной статистики
    try:
        schedule.every().sunday.at("18:00").do(send_weekly_stats)
        print("Еженедельная статистика запланирована.")
    except Exception as e:
        print(f"Ошибка при планировании еженедельной статистики: {e}")

    # Запуск планировщика в отдельном потоке
    Thread(target=schedule_checker).start()
    print("Планировщик запущен.")
