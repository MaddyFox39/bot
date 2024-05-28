from telebot import types
from datetime import datetime
from database import db_session, User, Habit, HabitEntry, DailyData, Session as db_Session
from bot_instance import bot
from report_generator import generate_pdf
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from  database  import  db_session,  User,  Habit,  HabitEntry,  DailyData,  Session
from  bot_instance  import  bot
from  report_generator  import  generate_pdf
DATABASE_URL = 'sqlite:///habits.db'
ADMIN_PASSWORD = "your_password"
ADMIN_CHAT_ID = 997979287  # Замени на chat_id администратора
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
session = Session()
db_session = session

class OnboardingHandler:
    def __init__(self, bot, user):
        self.bot = bot
        self.user = user
        self.step = 0
        self.messages = {
            'shy': [
                "Отлично! You are almost there.",
                "Твой пол?",
                "Твой возраст?",
                "Твой рост?",
                "В какой стране ты живешь?",
                "Твой город?",
                "Блеск! Завтра утром готовься к новой жизни!💪(картинка). Набери /menu для перехода в Главное меню"
            ],
            'sexy': [
                "Отлично! You are almost there.",
                "Твой пол?",
                "Твой возраст?",
                "Твой рост?",
                "В какой стране ты живешь?",
                "Твой город?",
                "Твой текущий вес?",
                "Твои замеры. Введи через запятую объем талии, бедер, ляжки",
                "Введи свою кастомную привычку, которую хочешь отслеживать",
                "Ты готов писать количество активных минут в день?",
                "Ты готов писать количество шагов в день?",
                "Супер, завтра утром мы начнем нашу работу. Набери /menu для перехода в Главное меню"
            ],
            'advanced': [
                "Отлично! You are almost there.",
                "Твой пол?",
                "Твой возраст?",
                "Твой рост?",
                "В какой стране ты живешь?",
                "Твой город?",
                "Твой текущий вес?",
                "Твои замеры. Введи через запятую объем талии, бедер, ляжки",
                "Введи свою кастомную привычку, которую хочешь отслеживать",
                "Ты готов писать количество активных минут в день?",
                "Ты готов писать количество шагов в день?",
                "Введи свой часовой пояс (например, Europe/Moscow):",
                "Супер, завтра утром мы начнем нашу работу. Набери /menu для перехода в Главное меню"
            ]
        }

    def get_keyboard(self):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('Назад'), types.KeyboardButton('Связаться с администратором'))
        return markup

    def start(self, chat_id):
        self.step = 1
        self.send_message(chat_id, self.messages[self.user.level][0])
        self.process_step(chat_id)

    def process_step(self, chat_id):
        if self.step < len(self.messages[self.user.level]):
            message = self.messages[self.user.level][self.step]
            if message == "Твой пол?":
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                markup.add('Мужской', 'Женский')
                self.send_message(chat_id, message, reply_markup=markup)
            elif message in ["Ты готов писать количество активных минут в день?",
                              "Ты готов писать количество шагов в день?"]:
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                markup.add('Да', 'Нет')
                self.send_message(chat_id, message, reply_markup=markup)
            else:
                self.send_message(chat_id, message)

            self.bot.register_next_step_handler_by_chat_id(chat_id, self.handle_response)
        else:
            self.step = 0  # Сбрасываем шаг
            self.send_message(chat_id, "Онбординг завершен. Добро пожаловать!")
            show_main_menu(chat_id)  # Вызываем show_main_menu

    def handle_response(self, message):
        chat_id = message.chat.id
        if message.text == 'Назад':
            self.step -= 1
            if self.step == 0:
                start_handler(message)  # Возвращаемся к самому началу
            else:
                self.process_step(chat_id)
        elif message.text == 'Связаться с администратором':
            self.send_message(chat_id, "Перенаправляем вас на администратора...")
            self.bot.send_message(ADMIN_CHAT_ID, f"Пользователь {chat_id} хочет связаться с администратором.")
        else:
            self.process_data(chat_id, message.text)
            self.step += 1
            self.process_step(chat_id)

    def send_message(self, chat_id, text, reply_markup=None):
        if reply_markup is None:
            reply_markup = self.get_keyboard()  # Добавлено self.
        self.bot.send_message(chat_id, text, reply_markup=reply_markup)

    def process_data(self, chat_id, data):
        if self.step == 1:  # Пол
            gender = data.lower()
            if gender in ['мужской', 'женский']:
                self.user.gender = gender
                db_session.commit()
            else:
                self.send_message(chat_id, "Пожалуйста, укажи свой пол, используя кнопки.")
                self.step -= 1
        elif self.step == 2:  # Возраст
            try:
                age = int(data)
                self.user.age = age
                db_session.commit()
            except ValueError:
                self.send_message(chat_id, "Пожалуйста, введи корректный возраст (число).")
                self.step -= 1
        elif self.step == 3:  # Рост
            try:
                height = int(data)
                self.user.height = height
                db_session.commit()
            except ValueError:
                self.send_message(chat_id, "Пожалуйста, введи корректный рост (число).")
                self.step -= 1
        elif self.step == 4:  # Страна
            self.user.country = data
            db_session.commit()
        elif self.step == 5:  # Город
            self.user.city = data
            db_session.commit()
        elif self.user.level == 'sexy' and self.step == 6: # Вес (только для Sexy)
            try:
                weight = float(data)
                self.user.weight = weight
                db_session.commit()
            except ValueError:
                self.send_message(chat_id, "Пожалуйста, введи корректный вес (число).")
                self.step -= 1
        elif self.user.level == 'sexy' and self.step == 7:  # Замеры (только для Sexy)
            try:
                measurements = [float(x.strip()) for x in data.split(',')]
                if len(measurements) != 3:
                    raise ValueError("Неверное количество замеров.")
                self.user.measurements = ",".join(str(x) for x in measurements)
                db_session.commit()
            except ValueError:
                self.send_message(chat_id, "Пожалуйста, введи три замера через запятую (например: 60,90,55).")
                self.step -= 1
        elif self.user.level == 'sexy' and self.step == 8:  # Кастомная привычка (только для Sexy)
            self.user.custom_habit = data
            db_session.commit()
        elif self.user.level == 'sexy' and self.step == 9:  # Активные минуты (только для Sexy)
            answer = data.lower()
            if answer == 'да':
                self.user.active_minutes_ready = True
            elif answer == 'нет':
                self.user.active_minutes_ready = False
            else:
                self.send_message(chat_id, "Пожалуйста, используй кнопки 'Да' или 'Нет'.")
                self.step -= 1
            db_session.commit()
        elif self.user.level == 'sexy' and self.step == 10:  # Шаги (только для Sexy)
            answer = data.lower()
            if answer == 'да':
                self.user.steps_ready = True
            elif answer == 'нет':
                self.user.steps_ready = False
            else:
                self.send_message(chat_id, "Пожалуйста, используй кнопки 'Да' или 'Нет'.")
                self.step -= 1
            db_session.commit()
        elif self.user.level == 'advanced' and self.step == 6:  # Вес (только для Advanced)
            try:
                weight = float(data)
                self.user.weight = weight
                db_session.commit()
            except ValueError:
                self.send_message(chat_id, "Пожалуйста, введи корректный вес (число).")
                self.step -= 1
        elif self.user.level == 'advanced' and self.step == 7:  # Замеры (только для Advanced)
            try:
                measurements = [float(x.strip()) for x in data.split(',')]
                if len(measurements) != 3:
                    raise ValueError("Неверное количество замеров.")
                self.user.measurements = ",".join(str(x) for x in measurements)
                db_session.commit()
            except ValueError:
                self.send_message(chat_id, "Пожалуйста, введи три замера через запятую (например: 60,90,55).")
                self.step -= 1
        elif self.user.level == 'advanced' and self.step == 8:  # Кастомная привычка (только для Advanced)
            self.user.custom_habit = data
            db_session.commit()
        elif self.user.level == 'advanced' and self.step == 9:  # Активные минуты (только для Advanced)
            answer = data.lower()
            if answer == 'да':
                self.user.active_minutes_ready = True
            elif answer == 'нет':
                self.user.active_minutes_ready = False
            else:
                self.send_message(chat_id, "Пожалуйста, используй кнопки 'Да' или 'Нет'.")
                self.step -= 1
            db_session.commit()
        elif self.user.level == 'advanced' and self.step == 10:  # Шаги (только для Advanced)
            answer = data.lower()
            if answer == 'да':
                self.user.steps_ready = True
            elif answer == 'нет':
                self.user.steps_ready = False
            else:
                self.send_message(chat_id, "Пожалуйста, используй кнопки 'Да' или 'Нет'.")
                self.step -= 1
            db_session.commit()
        elif self.user.level == 'advanced' and self.step == 11:  # Часовой пояс (только для Advanced)
            self.user.timezone = data
            db_session.commit()

def show_settings_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton('Бот: информация'),
        types.KeyboardButton('Настройки'),
        types.KeyboardButton('Изменить часовой пояс'),
        types.KeyboardButton('Тариф: информация'),
        types.KeyboardButton('Сменить тариф'),
        types.KeyboardButton('Отказаться от подписки'),
        types.KeyboardButton('Назад')
    )
    bot.send_message(chat_id, "Меню настроек:", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, process_settings_menu_choice)

def show_upload_data_menu(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton('Вес', callback_data='upload_weight'),
        types.InlineKeyboardButton('Замеры', callback_data='upload_measurements'),
        types.InlineKeyboardButton('Фото еды', callback_data='upload_food_photo'),
        types.InlineKeyboardButton('Часы сна', callback_data='upload_sleep_hours')
    )
    markup.add(
        types.InlineKeyboardButton('Активные минуты', callback_data='upload_active_minutes'),
        types.InlineKeyboardButton('Шаги', callback_data='upload_steps'),
        types.InlineKeyboardButton('Отмена', callback_data='back_to_main')
    )
    bot.send_message(chat_id, "Загрузить данные:", reply_markup=markup)

def show_tariff_info_menu(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton('Вывод инфо: текущая подписка и срок действия', callback_data='show_tariff_info'),
        types.InlineKeyboardButton('Сменить тариф', callback_data='change_tariff')
    )
    markup.add(
        types.InlineKeyboardButton('Отказаться от подписки', callback_data='unsubscribe'),
        types.InlineKeyboardButton('Назад', callback_data='back_to_main')
    )
    bot.send_message(chat_id, "Информация о моем тарифе:", reply_markup=markup)
# --- Обработка команды /start и онбординга ---
def send_stats(message):
    chat_id = message.chat.id
    local_session = Session() # <-- Исправлено
    user = local_session.query(User).filter_by(chat_id=chat_id).first()
    if user:
        pdf_file = generate_pdf(user)
        with open(pdf_file, 'rb') as f:
            bot.send_document(chat_id, f)
    else:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")

@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    bot.send_message(chat_id,
                     "Привет! 👋  Я  бот  Hab  Hub,  твой  личный  помощник  в  достижении  целей! 💪 Введи /start для начала работы")
    if not user:
        user = User(chat_id=chat_id, reminder_time=None)
        db_session.add(user)
        db_session.commit()

        msg = bot.send_message(chat_id, "Как ты хочешь, чтобы мы к тебе обращались?")
        bot.register_next_step_handler(msg, get_name)
    else:
        bot.send_message(chat_id, f"Привет, {user.name}! Рад тебя видеть снова.")
        show_main_menu(chat_id)

def get_name(message):
    chat_id = message.chat.id
    if message.text == 'Назад':
        start_handler(message)  # Возвращаемся к самому началу
    elif message.text == 'Связаться с администратором':
        # Перенаправляем пользователя на чат с администратором
        bot.send_message(chat_id, "Перенаправляем вас на администратора...")
        bot.send_message(ADMIN_CHAT_ID, f"Пользователь {chat_id} хочет связаться с администратором.")
    else:
        name = message.text
        user = db_session.query(User).filter_by(chat_id=chat_id).first()
        user.name = name
        db_session.commit()

        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Shy', 'Sexy', 'Advanced')
        bot.send_message(chat_id, f"Добро пожаловать, {name}! Выбери уровень:", reply_markup=markup)
        bot.register_next_step_handler(message, get_level)

def get_level(message):
    chat_id = message.chat.id
    if message.text == 'Назад':
        get_name(message)  # Возвращаемся к выбору имени
    elif message.text == 'Связаться с администратором':
        # Перенаправляем пользователя на чат с администрацией
        bot.send_message(chat_id, "Перенаправляем вас на администратора...")
        bot.send_message(ADMIN_CHAT_ID, f"Пользователь {chat_id} хочет связаться с администратором.")
    else:
        level = message.text.lower()
        user = db_session.query(User).filter_by(chat_id=chat_id).first()

        if level in ['shy', 'sexy', 'advanced']:
            user.level = level
            db_session.commit()

            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('Принимаю', 'Не принимаю')
            bot.send_message(chat_id, "Перед началом работы, прими правила", reply_markup=markup)
            bot.register_next_step_handler(message, accept_rules)
        else:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('Shy', 'Sexy', 'Advanced')
            bot.send_message(chat_id, "Пожалуйста, выбери один из предложенных уровней:", reply_markup=markup)
            bot.register_next_step_handler(message, get_level)

def accept_rules(message):
    chat_id = message.chat.id
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    onboarding = None
    if message.text == 'Назад':
        get_level(message) # Возвращаемся к выбору уровня
    elif message.text == 'Связаться с администратором':
        bot.send_message(chat_id, "Перенаправляем вас на администратора...")
        bot.send_message(ADMIN_CHAT_ID, f"Пользователь {chat_id} хочет связаться с администратором.")
    elif message.text == "Принимаю":
        onboarding = OnboardingHandler(bot, user)
        onboarding.start(chat_id)
    else:
        bot.send_message(chat_id, "Для продолжения необходимо принять правила.",
                         reply_markup=onboarding.get_keyboard())

# --- Функции для главного меню ---
def show_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("Управление привычками"),
        types.KeyboardButton("Статистика"),
        types.KeyboardButton("Настройки")
    )
    bot.send_message(chat_id, "Главное меню:", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, process_main_menu_choice)

def process_main_menu_choice(message):
    chat_id = message.chat.id
    choice = message.text
    if choice == "Управление привычками":
        show_habits_menu(chat_id)
    elif choice == "Статистика":
        show_stats_menu(chat_id)
    elif choice == "Настройки":
        show_settings_menu(chat_id)
    else:
        bot.send_message(chat_id, "Неверный выбор. Попробуйте снова.")
        show_main_menu(chat_id)

def show_habits_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton('Просмотреть привычки'),
        types.KeyboardButton('Добавить привычку'),
        types.KeyboardButton('Редактировать привычку'),
        types.KeyboardButton('Удалить привычку')
    )
    markup.add(
        types.KeyboardButton('Назад')
    )
    bot.send_message(chat_id, "Меню привычек:", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, process_habits_menu_choice)

def process_habits_menu_choice(message):
    chat_id = message.chat.id
    choice = message.text
    if choice == "Просмотреть привычки":
        view_habits(chat_id)
    elif choice == "Добавить привычку":
        add_habit(chat_id)
    elif choice == "Редактировать привычку":
        edit_habit(chat_id)
    elif choice == "Удалить привычку":
        delete_habit(chat_id)
    elif choice == "Назад":
        show_admin_menu(chat_id)
    else:
        bot.send_message(chat_id, "Неверный выбор. Попробуйте снова.")
        show_habits_menu(chat_id)

def show_stats_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton('Просмотреть общую статистику'),
        types.KeyboardButton('Просмотреть статистику пользователя')
    )
    markup.add(
        types.KeyboardButton('Назад')
    )
    bot.send_message(chat_id, "Меню статистики:", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, process_stats_menu_choice)

def process_stats_menu_choice(message):
    chat_id = message.chat.id
    choice = message.text
    if choice == "Просмотреть общую статистику":
        view_general_stats(chat_id)
    elif choice == "Просмотреть статистику пользователя":
        view_user_stats(chat_id)
    elif choice == "Назад":
        show_main_menu(chat_id)
    else:
        bot.send_message(chat_id, "Неверный выбор. Попробуйте снова.")
        show_stats_menu(chat_id)

def process_settings_menu_choice(message):
    chat_id = message.chat.id
    choice = message.text
    if choice == "Бот: информация":
        info_handler(message)
    elif choice == "Настройки":
        communication_settings_handler(message)
    elif choice == "Изменить часовой пояс":
        change_timezone_handler(message)
    elif choice == "Тариф: информация":
        my_tariff_info_handler(message)
    elif choice == "Сменить тариф":
        change_tariff_handler(message)
    elif choice == "Отказаться от подписки":
        unsubscribe_handler(message)
    elif choice == "Назад":
        show_main_menu(chat_id)
    else:
        bot.send_message(chat_id, "Неверный выбор. Попробуйте снова.")
        show_settings_menu(chat_id)

# --- Функции для управления привычками ---
@bot.message_handler(func=lambda message: message.text == 'Добавить привычку')  # <- Новый декоратор
def add_habit_handler(message):
    chat_id = message.chat.id
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    if user:
        if user.level == 'basic' and len(user.habits) >= 1:
            bot.send_message(chat_id, "На базовом уровне можно отслеживать только одну привычку.")
        elif user.level == 'sexy' and len(user.habits) >= 5:
            bot.send_message(chat_id, "На уровне 'Секси' можно отслеживать до 5 привычек.")
        else:
            msg = bot.send_message(chat_id, "Введите название новой привычки:")
            bot.register_next_step_handler(msg, save_habit)
    else:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")

def save_habit(message):
    chat_id = message.chat.id
    habit_name = message.text
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    if user:
        habit = Habit(name=habit_name, user_id=user.id)
        db_session.add(habit)
        db_session.commit()
        bot.send_message(chat_id, f"Привычка '{habit_name}' добавлена.")
        show_main_menu(chat_id)
    else:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")


@bot.message_handler(func=lambda message: message.text == 'Записать привычку')
def record_habit_handler(message):
    chat_id = message.chat.id
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    if user:
        habits = db_session.query(Habit).filter_by(user_id=user.id).all()
        if habits:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            for habit in habits:
                markup.add(habit.name)
            msg = bot.send_message(chat_id, "Выберите привычку для записи:", reply_markup=markup)
            bot.register_next_step_handler(msg, get_habit_entry)
        else:
            bot.send_message(chat_id,
                             "У вас нет добавленных привычек. Сначала добавьте привычку с помощью команды /addhabit.")
    else:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")


def get_habit_entry(message):
    chat_id = message.chat.id
    habit_name = message.text
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    habit = db_session.query(Habit).filter_by(name=habit_name, user_id=user.id).first()
    if habit:
        msg = bot.send_message(chat_id, f"Введите запись для привычки '{habit_name}':")
        bot.register_next_step_handler(msg, save_habit_entry, habit)
    else:
        bot.send_message(chat_id, "Привычка не найдена. Пожалуйста, выберите привычку из списка.")


def save_habit_entry(message, habit):
    chat_id = message.chat.id
    entry_value = message.text
    entry = HabitEntry(habit_id=habit.id, value=entry_value, date=datetime.now())
    db_session.add(entry)
    db_session.commit()
    bot.send_message(chat_id, f"Запись для привычки '{habit.name}' добавлена.")
    show_main_menu(chat_id)


@bot.message_handler(commands=['stats'])
@bot.message_handler(func=lambda message: message.text == 'Статистика')
def get_stats_handler(message):
    chat_id = message.chat.id
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    if user:
        stats = f"Статистика для {user.name}:\n"
        for habit in user.habits:
            stats += f"\nПривычка: {habit.name}\n"
            entries = db_session.query(HabitEntry).filter_by(habit_id=habit.id).all()
            if entries:
                for entry in entries:
                    stats += f" - {entry.date.strftime('%Y-%m-%d')}: {entry.value}\n"
            else:
                stats += " Нет записей.\n"
        bot.send_message(chat_id, stats)
    else:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")


# --- Обработка напоминаний ---
@bot.message_handler(commands=['setreminder'])
@bot.message_handler(func=lambda message: message.text == 'Напоминания')  # <-  Добавь  декоратор
def set_reminder_handler(message):
    chat_id = message.chat.id
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    if user:
        bot.send_message(chat_id, "Введите время напоминания в формате ЧЧ:ММ (например, 09:00):")
        bot.register_next_step_handler(message, save_reminder_time)
    else:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")

def save_reminder_time(message):
    chat_id = message.chat.id

    reminder_time = message.text
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    if user:
        user.reminder_time = reminder_time  # <-- Обновляем атрибут reminder_time
        db_session.commit()
        bot.send_message(chat_id, f"Время напоминания установлено на {reminder_time}.")
        show_main_menu(chat_id)
    else:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")


# --- Обработка удаления привычки ---
@bot.message_handler(commands=['removehabit'])
def remove_habit_handler(message):
    chat_id = message.chat.id
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    if user:
        habits = db_session.query(Habit).filter_by(user_id=user.id).all()
        if habits:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            for habit in habits:
                markup.add(habit.name)
            msg = bot.send_message(chat_id, "Выберите привычку для удаления:", reply_markup=markup)
            bot.register_next_step_handler(msg, delete_habit)
        else:
            bot.send_message(chat_id, "У вас нет добавленных привычек.")
    else:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")


def delete_habit(message):
    chat_id = message.chat.id
    habit_name = message.text
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    habit = db_session.query(Habit).filter_by(name=habit_name, user_id=user.id).first()
    if habit:
        db_session.delete(habit)
        db_session.commit()
        bot.send_message(chat_id, f"Привычка '{habit_name}' удалена.")
        show_main_menu(chat_id)
    else:
        bot.send_message(chat_id, "Привычка не найдена.")


# --- Обработка загрузки изображений ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open(f"photos/{file_id}.jpg", 'wb') as new_file:
        new_file.write(downloaded_file)

    bot.send_message(chat_id, "Фото получено и сохранено.")


# --- Обработка рассылки сообщений ---
@bot.message_handler(commands=['broadcast'])
def broadcast_handler(message):
    chat_id = message.chat.id
    if is_admin(chat_id):
        msg = bot.send_message(chat_id, "Введите сообщение для рассылки:")
        bot.register_next_step_handler(msg, broadcast_message)
    else:
        bot.send_message(chat_id, "У вас нет прав для этой команды.")


def broadcast_message(message):
    text = message.text
    broadcast_message_to_all(text)


def broadcast_message_to_all(text):
    users = db_session.query(User).all()
    for user in users:
        try:
            bot.send_message(user.chat_id, text)
        except:
            print(f"Не удалось отправить сообщение пользователю {user.chat_id}")


def is_admin(chat_id):
    admin_ids = [997979287]  # список chat_id администраторов
    return chat_id in admin_ids


# --- Функции для опросов ---
def send_evening_poll_start(user_id):
    user = db_session.query(User).filter_by(id=user_id).first()
    if user:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Супер', 'Нормально', 'Могло быть лучше', 'Сомнительно', 'Совсем беда')
        bot.send_message(user.chat_id, f"{user.name}, как ты оцениваешь этот день по своему самочувствию?",
                         reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(user.chat_id, get_evening_poll_answer)

def send_subscription_reminder(user):  #  <- Передаем  объект  user
    if user.subscribed_until:
        days_until_subscription_end = (user.subscribed_until - datetime.now().date()).days
        if days_until_subscription_end <= 3:  # Напоминаем  за  3  дня
            bot.send_message(user.chat_id, f"Напоминание:  ваша  подписка  заканчивается  через  {days_until_subscription_end}  дней.")
def send_lunch_photo_reminder(user):  #  <- Передаем  объект  user
    if user.level in ['sexy', 'advanced']:
        bot.send_message(user.chat_id, "Небольшое напоминание: ты можешь загрузить фото своего обеда.")
def send_dinner_photo_reminder(user):  #  <- Передаем  объект  user
    if user.level in ['sexy', 'advanced']:
        bot.send_message(user.chat_id, "Небольшое напоминание: ты можешь загрузить фото своего ужина.")

def get_evening_poll_answer(message):
    chat_id = message.chat.id
    answer = message.text
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    if user:
        daily_data = db_session.query(DailyData).filter_by(user_id=user.id, date=datetime.now().date()).first()
        if not daily_data:
            daily_data = DailyData(user_id=user.id, date=datetime.now().date())
            db_session.add(daily_data)
        daily_data.mood_rating = answer
        db_session.commit()
    bot.send_message(chat_id, "Давай сверим цифры. Сколько активных минут было за день?")
    bot.register_next_step_handler_by_chat_id(chat_id, get_evening_poll_active_minutes)

def get_evening_poll_active_minutes(message):
    chat_id = message.chat.id
    try:
        active_minutes = int(message.text)
        user = db_session.query(User).filter_by(chat_id=chat_id).first()
        if user:
            daily_data = db_session.query(DailyData).filter_by(user_id=user.id, date=datetime.now().date()).first()
            if not daily_data:
                daily_data = DailyData(user_id=user.id, date=datetime.now().date())
                db_session.add(daily_data)
            daily_data.active_minutes = active_minutes
            db_session.commit()
        bot.send_message(chat_id, "Сколько шагов было за день?")
        bot.register_next_step_handler_by_chat_id(chat_id, get_evening_poll_steps)
    except ValueError:
        bot.send_message(chat_id, "Пожалуйста, введите корректное количество активных минут (число).")
        bot.register_next_step_handler_by_chat_id(chat_id, get_evening_poll_active_minutes)

def get_evening_poll_steps(message):
    chat_id = message.chat.id
    try:
        steps = int(message.text)
        user = db_session.query(User).filter_by(chat_id=chat_id).first()
        if user:
            daily_data = db_session.query(DailyData).filter_by(user_id=user.id, date=datetime.now().date()).first()
            if not daily_data:
                daily_data = DailyData(user_id=user.id, date=datetime.now().date())
                db_session.add(daily_data)
            daily_data.steps = steps
            db_session.commit()
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Все отлично', 'Попробую завтра')
        bot.send_message(chat_id, "Насколько ты справился со своими целями сегодня?", reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(chat_id, get_evening_poll_goals)
    except ValueError:
        bot.send_message(chat_id, "Пожалуйста, введите корректное количество шагов (число).")
        bot.register_next_step_handler_by_chat_id(chat_id, get_evening_poll_steps)
def get_evening_poll_goals(message):
    chat_id = message.chat.id
    answer = message.text
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    if user:
        daily_data = db_session.query(DailyData).filter_by(user_id=user.id, date=datetime.now().date()).first()
        if not daily_data:
            daily_data = DailyData(user_id=user.id, date=datetime.now().date())
            db_session.add(daily_data)
        daily_data.goals_achieved = answer == 'Все отлично'
        db_session.commit()
    if user.level in ['sexy', 'advanced']:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Да', 'Нет')
        bot.send_message(chat_id, f"Твоя привычка для отслеживания: {user.custom_habit}. Получилось сегодня?",
                         reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(chat_id, get_evening_poll_custom_habit)
    else:
        bot.send_message(chat_id, "Ты большой молодец сегодня. Тут можешь оставить себе послание на завтра.")
        bot.register_next_step_handler_by_chat_id(chat_id, get_evening_poll_message)

def get_evening_poll_custom_habit(message):
    chat_id = message.chat.id
    answer = message.text
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    if user:
        daily_data = db_session.query(DailyData).filter_by(user_id=user.id, date=datetime.now().date()).first()
        if not daily_data:
            daily_data = DailyData(user_id=user.id, date=datetime.now().date())
            db_session.add(daily_data)
        daily_data.custom_habit_status = answer == 'Да'
        db_session.commit()

    bot.send_message(chat_id, "Ты большой молодец сегодня. Тут можешь оставить себе послание на завтра.")
    bot.register_next_step_handler_by_chat_id(chat_id, get_evening_poll_message)
def get_morning_poll_answer(message):
    chat_id = message.chat.id
    answer = message.text
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    if user:
        daily_data = DailyData(user_id=user.id, mood_rating=answer, date=datetime.now())
        db_session.add(daily_data)
        db_session.commit()
    bot.send_message(chat_id, "Спасибо за ответ! Хорошего дня!")

def get_evening_poll_message(message):
    chat_id = message.chat.id
    message_text = message.text
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    if user:
        daily_data = db_session.query(DailyData).filter_by(user_id=user.id, date=datetime.now().date()).first()
        if not daily_data:
            daily_data = DailyData(user_id=user.id, date=datetime.now().date())
            db_session.add(daily_data)
        daily_data.message_to_self = message_text
        db_session.commit()
    bot.send_message(chat_id, "Спасибо за ответ! Хорошего вечера!")

def send_custom_reminder(user_id):
    user = db_session.query(User).filter_by(id=user_id).first()
    if user and user.custom_reminder_text:
        bot.send_message(user.chat_id, f"Напоминание: {user.custom_reminder_text}")

def send_morning_poll():  # Функция для утреннего опроса
    users = db_session.query(User).all()
    for user in users:
        bot.send_message(user.chat_id, "Доброе утро! Как ты себя чувствуешь?")


def send_afternoon_poll(user_id):
    user = db_session.query(User).filter_by(id=user_id).first()
    if user:
        bot.send_message(user.chat_id, "Как проходит твой день?")  #  Пока  без  вариантов  ответов

def send_evening_poll_start(user_id):
    user = db_session.query(User).filter_by(id=user_id).first()
    if user:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Супер', 'Нормально', 'Могло быть лучше', 'Сомнительно', 'Совсем беда')
        bot.send_message(user.chat_id, f"{user.name}, как ты оцениваешь этот день по своему самочувствию?", reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(user.chat_id, get_evening_poll_answer)

@bot.message_handler(func=lambda message: message.text == "Информация о боте")
def info_handler(message):
    chat_id = message.chat.id
    info_text = """
    Привет! Я бот HabHub, помогаю отслеживать привычки и достигать целей.

    Вот что я умею:
    - Отслеживать привычки
    - Отправлять напоминания
    - Проводить опросы
    - Собирать статистику
    - Генерировать PDF-отчеты

    У меня есть три уровня подписки:
    - Shy
    - Sexy
    - Advanced 
    """
    bot.send_message(chat_id, info_text)


@bot.message_handler(func=lambda message: message.text == "Настройки коммуникаций")
def communication_settings_handler(message):
    chat_id = message.chat.id
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    if user:
        markup = types.InlineKeyboardMarkup()
        daily_reminders_text = "Вкл" if user.daily_reminders else "Выкл"
        newsletter_text = "Вкл" if user.newsletter else "Выкл"
        markup.add(types.InlineKeyboardButton(f"Дневные напоминания: {daily_reminders_text}",
                                              callback_data="toggle_daily_reminders"))
        markup.add(types.InlineKeyboardButton(f"Рассылка: {newsletter_text}", callback_data="toggle_newsletter"))
        bot.send_message(chat_id, "Настройки коммуникаций:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")
    db_session.close()

@bot.callback_query_handler(func=lambda call: call.data == "toggle_daily_reminders")
def toggle_daily_reminders_handler(call):
    chat_id = call.message.chat.id
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    user.daily_reminders = not user.daily_reminders
    db_session.commit()
    daily_reminders_text = "Вкл" if user.daily_reminders else "Выкл"
    newsletter_text = "Вкл" if user.newsletter else "Выкл"
    new_markup = types.InlineKeyboardMarkup()
    new_markup.add(
        types.InlineKeyboardButton(f"Дневные напоминания: {daily_reminders_text}",
                                   callback_data="toggle_daily_reminders"))
    new_markup.add(types.InlineKeyboardButton(f"Рассылка: {newsletter_text}", callback_data="toggle_newsletter"))
    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=new_markup)


@bot.callback_query_handler(func=lambda call: call.data == "toggle_newsletter")
def toggle_newsletter_handler(call):
    chat_id = call.message.chat.id
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    user.newsletter = not user.newsletter
    db_session.commit()
    daily_reminders_text = "Вкл" if user.daily_reminders else "Выкл"
    newsletter_text = "Вкл" if user.newsletter else "Выкл"
    new_markup = types.InlineKeyboardMarkup()
    new_markup.add(
        types.InlineKeyboardButton(f"Дневные напоминания: {daily_reminders_text}",
                                   callback_data="toggle_daily_reminders"))
    new_markup.add(types.InlineKeyboardButton(f"Рассылка: {newsletter_text}", callback_data="toggle_newsletter"))
    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=new_markup)


@bot.message_handler(func=lambda message: message.text == "Сменить часовой пояс")
def change_timezone_handler(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Введите ваш часовой пояс (например, Europe/Moscow):")
    bot.register_next_step_handler(message, save_timezone)


def save_timezone(message):
    chat_id = message.chat.id
    timezone = message.text
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    if user:
        user.timezone = timezone
        db_session.commit()
        bot.send_message(chat_id, f"Часовой пояс изменен на {timezone}.")
    else:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")


@bot.message_handler(func=lambda message: message.text == "Информация о моем тарифе")
def my_tariff_info_handler(message):
    chat_id = message.chat.id
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    if user:
        bot.send_message(chat_id, f"Ваш текущий тариф: {user.level}. Информация о сроке действия пока недоступна.")
    else:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")


@bot.message_handler(func=lambda message: message.text == "Сменить тариф")
def change_tariff_handler(message):
    chat_id = message.chat.id
    # Здесь  нужно  реализовать  логику  смены  тарифа,  например:
    #  -  Предложить  пользователю  выбрать  новый  тариф.
    #  -  Произвести  оплату.
    #  -  Обновить  данные  пользователя  в  базе.
    bot.send_message(chat_id, "Функция смены тарифа пока недоступна.")


@bot.message_handler(func=lambda message: message.text == "Отказаться от подписки")
def unsubscribe_handler(message):
    chat_id = message.chat.id
    #  Здесь  нужно  реализовать  логику  отказа  от  подписки,  например:
    #  -  Подтвердить  отказ  у  пользователя.
    #  -  Отключить  платную  подписку.
    #  -  Обновить  данные  пользователя  в  базе.
    bot.send_message(chat_id, "Функция отказа от подписки пока недоступна.")


@bot.message_handler(func=lambda message: message.text == "Загрузить данные")
def upload_data_handler(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Выберите, какие данные вы хотите загрузить:", reply_markup=get_upload_data_keyboard())

def get_upload_data_keyboard():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("Вес", "Замеры", "Фото еды", "Часы сна", "Активные минуты", "Шаги", "Отмена")
    return markup

@bot.message_handler(func=lambda message: message.text in ["Вес", "Замеры", "Фото еды", "Часы сна", "Активные минуты", "Шаги", "Отмена"])
def process_upload_data_choice(message):
    chat_id = message.chat.id
    choice = message.text
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    if not user:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")
        return

    if choice == "Вес":
        bot.send_message(chat_id,"Введите ваш вес (в кг):")
        bot.register_next_step_handler(message, save_weight)
    elif choice == "Замеры":
        bot.send_message(chat_id, "Введите ваши замеры (талия, бедра, ляжка, в см) через запятую:")
        bot.register_next_step_handler(message, save_measurements)
    elif choice == "Фото еды":
        bot.send_message(chat_id, "Отправьте фото вашей еды:")
        bot.register_next_step_handler(message, save_food_photo)
    elif choice == "Часы сна":
        bot.send_message(chat_id, "Введите количество часов сна:")
        bot.register_next_step_handler(message, save_sleep_hours)
    elif choice == "Активные минуты":
        bot.send_message(chat_id, "Введите количество активных минут:")
        bot.register_next_step_handler(message, save_active_minutes)
    elif choice == "Шаги":
        bot.send_message(chat_id, "Введите количество шагов:")
        bot.register_next_step_handler(message, save_steps)
    elif choice == "Отмена":
        show_main_menu(chat_id)

def save_weight(message):
    chat_id = message.chat.id
    try:
        weight = float(message.text)
        local_db_session = db_Session()
        user = local_db_session.query(User).filter_by(chat_id=chat_id).first()
        if user:
            daily_data = DailyData(user_id=user.id, weight=weight, date=datetime.now())
            local_db_session.add(daily_data)
            local_db_session.commit()
            bot.send_message(chat_id, f"Ваш вес ({weight} кг) сохранен.")
            show_main_menu(chat_id)
        else:
            bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")
    except ValueError:
        bot.send_message(chat_id, "Пожалуйста, введите корректный вес (число).")
        bot.register_next_step_handler(message, save_weight)

def save_measurements(message):
    chat_id = message.chat.id
    try:
        measurements = [float(x.strip()) for x in message.text.split(',')]
        if len(measurements) != 3:
            raise ValueError("Неверное количество замеров.")
        local_db_session = db_Session()
        user = local_db_session.query(User).filter_by(chat_id=chat_id).first()
        if user:
            daily_data = DailyData(user_id=user.id, measurements=",".join(str(x) for x in measurements), date=datetime.now())
            local_db_session.add(daily_data)
            local_db_session.commit()
            bot.send_message(chat_id, f"Ваши замеры сохранены.")
            show_main_menu(chat_id)
        else:
            bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")
    except ValueError:
        bot.send_message(chat_id, "Пожалуйста, введи три замера через запятую (например: 60,90,55).")
        bot.register_next_step_handler(message, save_measurements)

def save_food_photo(message):
    chat_id = message.chat.id
    if message.photo:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(f"food_photos/{file_id}.jpg", "wb") as new_file:
            new_file.write(downloaded_file)
        local_db_session = db_Session()
        user = local_db_session.query(User).filter_by(chat_id=chat_id).first()
        if user:
            daily_data = DailyData(user_id=user.id, food_photo=f"{file_id}.jpg", date=datetime.now())
            local_db_session.add(daily_data)
            local_db_session.commit()
            bot.send_message(chat_id, "Фото еды сохранено.")
            show_main_menu(chat_id)
        else:
            bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")
    else:
        bot.send_message(chat_id, "Пожалуйста, отправьте фото.")
        bot.register_next_step_handler(message, save_food_photo)

def save_sleep_hours(message):
    chat_id = message.chat.id
    try:
        sleep_hours = float(message.text)
        local_db_session = db_Session()
        user = local_db_session.query(User).filter_by(chat_id=chat_id).first()
        if user:
            daily_data = DailyData(user_id=user.id, sleep_hours=sleep_hours, date=datetime.now())
            local_db_session.add(daily_data)
            local_db_session.commit()
            bot.send_message(chat_id, f"Количество часов сна ({sleep_hours}) сохранено.")
            show_main_menu(chat_id)
        else:
            bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")
    except ValueError:
        bot.send_message(chat_id, "Пожалуйста, введите корректное количество часов сна (число).")
        bot.register_next_step_handler(message, save_sleep_hours)

def save_active_minutes(message):
    chat_id = message.chat.id
    try:
        active_minutes = int(message.text)
        local_db_session = db_Session()
        user = local_db_session.query(User).filter_by(chat_id=chat_id).first()
        if user:
            daily_data = DailyData(user_id=user.id, active_minutes=active_minutes, date=datetime.now())
            local_db_session.add(daily_data)
            local_db_session.commit()
            bot.send_message(chat_id, f"Количество активных минут ({active_minutes}) сохранено.")
            show_main_menu(chat_id)
        else:
            bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")
    except ValueError:
        bot.send_message(chat_id, "Пожалуйста, введите корректное количество активных минут (число).")
        bot.register_next_step_handler(message, save_active_minutes)

def save_steps(message):
    chat_id = message.chat.id
    try:
        steps = int(message.text)
        local_db_session = db_Session()
        user = local_db_session.query(User).filter_by(chat_id=chat_id).first()
        if user:
            daily_data = DailyData(user_id=user.id, steps=steps, date=datetime.now())
            local_db_session.add(daily_data)
            local_db_session.commit()
            bot.send_message(chat_id, f"Количество шагов ({steps}) сохранено.")
            show_main_menu(chat_id)
        else:
            bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")
    except ValueError:
        bot.send_message(chat_id, "Пожалуйста, введите корректное количество шагов (число).")
        bot.register_next_step_handler(message, save_steps)

def get_upload_date(message):
    chat_id  =  message.chat.id
    try:
        date_str  =  message.text
        upload_date  =  datetime.strptime(date_str,  "%Y-%m-%d").date()
        local_db_session = db_Session()
        user  =  local_db_session.query(User).filter_by(chat_id=chat_id).first()
        if  user:
            daily_data  =  local_db_session.query(DailyData).filter_by(user_id=user.id,  date=upload_date).first()
            if  not  daily_data:
                daily_data  =  DailyData(user_id=user.id,  date=upload_date)
                local_db_session.add(daily_data)
                local_db_session.commit()
            bot.send_message(chat_id,  "Отправьте  фото  еды:")
            bot.register_next_step_handler(message,  get_food_photo,  daily_data)
        else:
            bot.send_message(chat_id,  "Сначала  зарегистрируйтесь  с  помощью  команды  /start.")
    except  ValueError:
        bot.send_message(chat_id,  "Неверный  формат  даты.  Используйте  ГГГГ-ММ-ДД.")
        bot.register_next_step_handler(message,  get_upload_date)

def get_food_photo(message,  daily_data):
    chat_id  =  message.chat.id
    if  message.photo:
        file_id  =  message.photo[-1].file_id
        file_info  =  bot.get_file(file_id)
        downloaded_file  =  bot.download_file(file_info.file_path)
        with  open(f"food_photos/{file_id}.jpg",  "wb")  as  new_file:
            new_file.write(downloaded_file)
        daily_data.food_photo  =  f"{file_id}.jpg"
        local_db_session = db_Session()
        local_db_session.commit()
        bot.send_message(chat_id,  "Введите  количество  активных  минут:")
        bot.register_next_step_handler(message,  get_active_minutes,  daily_data)
    else:
        bot.send_message(chat_id,  "Пожалуйста,  отправьте  фото.")
        bot.register_next_step_handler(message,  get_food_photo,  daily_data)

def get_active_minutes(message,  daily_data):
    chat_id  =  message.chat.id
    try:
        active_minutes  =  int(message.text)
        daily_data.active_minutes  =  active_minutes
        local_db_session = db_Session()
        local_db_session.commit()
        bot.send_message(chat_id,  "Введите  количество  часов  сна:")
        bot.register_next_step_handler(message,  get_sleep_hours,  daily_data)
    except  ValueError:
        bot.send_message(chat_id,  "Пожалуйста,  введите  число.")
        bot.register_next_step_handler(message,  get_active_minutes,  daily_data)

def get_sleep_hours(message,  daily_data):
    chat_id  =  message.chat.id
    try:
        sleep_hours  =  float(message.text)
        daily_data.sleep_hours  =  sleep_hours
        local_db_session = db_Session()
        local_db_session.commit()
        #  ... (продолжение  сбора  данных)  ...
        bot.send_message(chat_id,  "Данные  загружены!")
    except  ValueError:
        bot.send_message(chat_id,  "Пожалуйста,  введите  число.")
        bot.register_next_step_handler(message,  get_sleep_hours,  daily_data)

@bot.message_handler(func=lambda message: message.text == "Изменить кастомную привычку")
def change_custom_habit_handler(message):
    chat_id  =  message.chat.id
    bot.send_message(chat_id,  "Введите  новую  кастомную  привычку:")
    bot.register_next_step_handler(message,  save_custom_habit)

def save_custom_habit(message):
    chat_id  =  message.chat.id
    custom_habit  =  message.text
    local_db_session = db_Session()
    user  =  local_db_session.query(User).filter_by(chat_id=chat_id).first()
    if  user:
        user.custom_habit  =  custom_habit
        local_db_session.commit()
        bot.send_message(chat_id,  f"Кастомная  привычка  изменена  на:  {custom_habit}")
    else:
        bot.send_message(chat_id,  "Сначала  зарегистрируйтесь  с  помощью  команды  /start.")

@bot.message_handler(commands=['setcustomreminder'])
def set_custom_reminder_handler(message):
    chat_id  =  message.chat.id
    local_db_session = db_Session()
    user  =  local_db_session.query(User).filter_by(chat_id=chat_id).first()
    if  user:
        bot.send_message(chat_id,  "Введите  текст  вашего  кастомного  напоминания:")
        bot.register_next_step_handler(message,  save_custom_reminder_text)
    else:
        bot.send_message(chat_id,  "Сначала  зарегистрируйтесь  с  помощью  команды  /start.")

def save_custom_reminder_text(message):
    chat_id  =  message.chat.id
    local_db_session = db_Session()
    user  =  local_db_session.query(User).filter_by(chat_id=chat_id).first()
    user.custom_reminder_text  =  message.text
    local_db_session.commit()
    bot.send_message(chat_id,  f"Ваш  кастомный  текст  напоминания  установлен:  {message.text}")

@bot.message_handler(commands=['viewcustomreminder'])
def view_custom_reminder_handler(message):
    chat_id  =  message.chat.id
    local_db_session = db_Session()
    user  =  local_db_session.query(User).filter_by(chat_id=chat_id).first()
    if  user  and  user.custom_reminder_text:
        bot.send_message(chat_id,  f"Ваш  кастомный  текст  напоминания:  {user.custom_reminder_text}")
    else:
        bot.send_message(chat_id,  "У  вас  пока  нет  кастомного  напоминания.")

@bot.message_handler(func=lambda message: message.text == "Подключить коучей")
def connect_coaches_handler(message):
    chat_id = message.chat.id
    #  Здесь нужно  реализовать  логику  подключения  коучей,  например:
    #  -  Предложить  пользователю  выбрать  коуча  из  списка.
    #  -  Создать  отдельный  чат  с  коучем.
    bot.send_message(chat_id, "Функция подключения коучей пока недоступна.")


@bot.message_handler(commands=['getstats'])
def get_stats_handler(message):
    chat_id = message.chat.id
    user = db_session.query(User).filter_by(chat_id=chat_id).first()
    if user:
        try:
            #  Генерируем  PDF-отчет
            pdf_file = generate_pdf(user)

            #  Отправляем  отчет  пользователю
            with open(pdf_file, 'rb') as pdf:
                bot.send_document(chat_id, pdf)

        except Exception as e:
            print(f"Ошибка при генерации отчета: {e}")
            bot.send_message(chat_id, "Произошла ошибка при генерации отчета.")
    else:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")


@bot.message_handler(commands=['admin'])
def admin_command_handler(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "Введите пароль для доступа к админ панели:")
    bot.register_next_step_handler(msg, check_admin_password)


def check_admin_password(message):
    chat_id = message.chat.id
    if message.text == ADMIN_PASSWORD:
        show_admin_menu(chat_id)
    else:
        bot.send_message(chat_id, "Неверный пароль!")


def show_admin_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton('Пользователи'),
        types.KeyboardButton('Привычки'),
        types.KeyboardButton('Напоминания'),
        types.KeyboardButton('Опросы')
    )
    markup.add(
        types.KeyboardButton('Статистика'),
        types.KeyboardButton('Инфо сообщения'),
        types.KeyboardButton('Логи')
    )
    markup.add(
        types.KeyboardButton('Назад')
    )
    bot.send_message(chat_id, "Админ панель:", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, process_admin_menu_choice)


def process_admin_menu_choice(message):
    chat_id = message.chat.id
    choice = message.text
    if choice == "Пользователи":
        show_users_menu(chat_id)
    elif choice == "Привычки":
        show_habits_menu(chat_id)
    elif choice == "Напоминания":
        show_reminders_menu(chat_id)
    elif choice == "Опросы":
        show_polls_menu(chat_id)
    elif choice == "Статистика":
        show_stats_menu(chat_id)
    elif choice == "Инфо сообщения":
        show_info_messages_menu(chat_id)
    elif choice == "Логи":
        show_logs_menu(chat_id)
    elif choice == "Назад":
        show_main_menu(chat_id)
    else:
        if chat_id == ADMIN_CHAT_ID:
            check_admin_password(message)
        else:
            bot.send_message(chat_id, "Неверный выбор. Попробуйте снова.")
            show_admin_menu(chat_id)

def show_users_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton('Просмотреть пользователей'),
        types.KeyboardButton('Добавить пользователя'),
        types.KeyboardButton('Редактировать пользователя'),
        types.KeyboardButton('Удалить пользователя')
    )
    markup.add(
        types.KeyboardButton('Назад')
    )
    bot.send_message(chat_id, "Меню пользователей:", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, process_users_menu_choice)


def process_users_menu_choice(message):
    chat_id = message.chat.id
    choice = message.text
    if choice == "Просмотреть пользователей":
        view_users(chat_id)
    elif choice == "Добавить пользователя":
        add_user(chat_id)
    elif choice == "Редактировать пользователя":
        edit_user(chat_id)
    elif choice == "Удалить пользователя":
        delete_user(chat_id)
    elif choice == "Назад":
        show_admin_menu(chat_id)
    else:
        bot.send_message(chat_id, "Неверный выбор. Попробуйте снова.")
        show_users_menu(chat_id)


def view_users(chat_id):
    local_session = Session()
    users = local_session.query(User).all()
    if users:
        users_info = "Список пользователей:\n"
        for user in users:
            users_info += f"ID: {user.id}, Имя: {user.name}, Уровень: {user.level},  Часовой пояс: {user.timezone}\n"
        bot.send_message(chat_id, users_info)
    else:
        bot.send_message(chat_id, "Пользователей пока нет.")
    local_session.close()


def view_habits(chat_id):
    local_session = Session()
    habits = local_session.query(Habit).all()
    if habits:
        habits_info = "Список привычек:\n"
        for habit in habits:
            habits_info += f"ID: {habit.id}, Название: {habit.name}, Пользователь: {habit.user_id}\n"
        bot.send_message(chat_id, habits_info)
    else:
        bot.send_message(chat_id, "Привычек пока нет.")
    local_session.close()


def show_reminders_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton('Просмотреть напоминания'),
        types.KeyboardButton('Добавить напоминание'),
        types.KeyboardButton('Редактировать напоминание'),
        types.KeyboardButton('Удалить напоминание')
    )
    markup.add(
        types.KeyboardButton('Назад')
    )
    bot.send_message(chat_id, "Меню напоминаний:", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, process_reminders_menu_choice)


def process_reminders_menu_choice(message):
    chat_id = message.chat.id
    choice = message.text
    if choice == "Просмотреть напоминания":
        view_reminders(chat_id)
    elif choice == "Добавить напоминание":
        add_reminder(chat_id)
    elif choice == "Редактировать напоминание":
        edit_reminder(chat_id)
    elif choice == "Удалить напоминание":
        delete_reminder(chat_id)
    elif choice == "Назад":
        show_admin_menu(chat_id)
    else:
        bot.send_message(chat_id, "Неверный выбор. Попробуйте снова.")
        show_reminders_menu(chat_id)


def view_reminders(chat_id):
    local_session = Session()
    users = local_session.query(User).all()
    if users:
        reminders_info = "Список напоминаний:\n"
        for user in users:
            if user.reminder_time:
                reminders_info += f"Пользователь: {user.name}, Время: {user.reminder_time}\n"
        bot.send_message(chat_id, reminders_info)
    else:
        bot.send_message(chat_id, "Напоминаний пока нет.")
    local_session.close()


def show_polls_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton('Просмотреть опросы'),
        types.KeyboardButton('Добавить опрос'),
        types.KeyboardButton('Редактировать опрос'),
        types.KeyboardButton('Удалить опрос')
    )
    markup.add(
        types.KeyboardButton('Назад')
    )
    bot.send_message(chat_id, "Меню опросов:", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, process_polls_menu_choice)


def process_polls_menu_choice(message):
    chat_id = message.chat.id
    choice = message.text
    if choice == "Просмотреть опросы":
        view_polls(chat_id)
    elif choice == "Добавить опрос":
        add_poll(chat_id)
    elif choice == "Редактировать опрос":
        edit_poll(chat_id)
    elif choice == "Удалить опрос":
        delete_poll(chat_id)
    elif choice == "Назад":
        show_admin_menu(chat_id)
    else:
        bot.send_message(chat_id, "Неверный выбор. Попробуйте снова.")
        show_polls_menu(chat_id)


def view_polls(chat_id):
    # Здесь нужно реализовать функцию для просмотра опросов
    # Например, вывести список всех опросов в базе данных.
    bot.send_message(chat_id, "Функция просмотра опросов пока недоступна.")
    show_polls_menu(chat_id)



def view_general_stats(chat_id):
    # Здесь нужно реализовать функцию для просмотра общей статистики.
    # Например, можно вывести среднее количество часов сна, активных минут, шагов
    # за определенный период времени для всех пользователей.
    bot.send_message(chat_id, "Функция просмотра общей статистики пока недоступна.")
    # show_stats_menu(chat_id) # Удаляем лишний вызов


def view_user_stats(chat_id):
    # Здесь нужно реализовать функцию для просмотра статистики пользователя.
    # Например, можно запросить ID пользователя и вывести его статистику
    # по весу, сну, замерам, активным минутам и шагам за определенный период времени.
    bot.send_message(chat_id, "Функция просмотра статистики пользователя пока недоступна.")
    # show_stats_menu(chat_id) # Удаляем лишний вызов


def show_info_messages_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton('Просмотреть инфо сообщения'),
        types.KeyboardButton('Добавить инфо сообщение'),
        types.KeyboardButton('Редактировать инфо сообщение'),
        types.KeyboardButton('Удалить инфо сообщение')
    )
    markup.add(
        types.KeyboardButton('Назад')
    )
    bot.send_message(chat_id, "Меню информационных сообщений:", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, process_info_messages_menu_choice)


def process_info_messages_menu_choice(message):
    chat_id = message.chat.id
    choice = message.text
    if choice == "Просмотреть инфо сообщения":
        view_info_messages(chat_id)
    elif choice == "Добавить инфо сообщение":
        add_info_message(chat_id)
    elif choice == "Редактировать инфо сообщение":
        edit_info_message(chat_id)
    elif choice == "Удалить инфо сообщение":
        delete_info_message(chat_id)
    elif choice == "Назад":
        show_admin_menu(chat_id)
    else:
        bot.send_message(chat_id, "Неверный выбор. Попробуйте снова.")
        show_info_messages_menu(chat_id)


def view_info_messages(chat_id):
    # Здесь нужно реализовать функцию для просмотра информационных сообщений
    # Например, вывести список всех информационных сообщений в базе данных.
    bot.send_message(chat_id, "Функция просмотра информационных сообщений пока недоступна.")
    # show_info_messages_menu(chat_id) # Удаляем лишний вызов


def show_logs_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton('Просмотреть логи'),
        types.KeyboardButton('Скачать логи')
    )
    markup.add(
        types.KeyboardButton('Назад')
    )
    bot.send_message(chat_id, "Меню логов:", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, process_logs_menu_choice)


def process_logs_menu_choice(message):
    chat_id = message.chat.id
    choice = message.text
    if choice == "Просмотреть логи":
        view_logs(chat_id)
    elif choice == "Скачать логи":
        download_logs(chat_id)
    elif choice == "Назад":
        show_admin_menu(chat_id)
    else:
        bot.send_message(chat_id, "Неверный выбор. Попробуйте снова.")
        show_logs_menu(chat_id)


def view_logs(chat_id):
    # Здесь нужно реализовать функцию для просмотра логов
    # Например, вывести список всех логов в базе данных.
    bot.send_message(chat_id, "Функция просмотра логов пока недоступна.")
    # show_logs_menu(chat_id) # Удаляем лишний вызов


def download_logs(chat_id):
    # Здесь нужно реализовать функцию для скачивания логов
    # Например, сформировать файл с логами и отправить его пользователю.
    bot.send_message(chat_id, "Функция скачивания логов пока недоступна.")
    # show_logs_menu(chat_id) # Удаляем лишний вызов


def add_user(chat_id):
    bot.send_message(chat_id, "Введите ID нового пользователя (например, 123456789):")
    bot.register_next_step_handler_by_chat_id(chat_id, get_new_user_id)


def get_new_user_id(message):
    chat_id = message.chat.id
    try:
        new_user_id = int(message.text)
        local_session = Session()
        user = local_session.query(User).filter_by(chat_id=new_user_id).first()
        if user:
            bot.send_message(chat_id, "Пользователь с таким ID уже существует!")
        else:
            bot.send_message(chat_id, "Введите имя нового пользователя:")
            bot.register_next_step_handler_by_chat_id(chat_id, get_new_user_name, new_user_id)
    except ValueError:
        bot.send_message(chat_id, "Неверный формат ID. Введите число.")
        add_user(chat_id)

def get_new_user_name(message, new_user_id):
    chat_id = message.chat.id
    name = message.text
    bot.send_message(chat_id, "Выберите уровень нового пользователя:")
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add('Shy', 'Sexy', 'Advanced')
    msg = bot.send_message(chat_id, "Выберите уровень:", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, get_new_user_level, new_user_id, name)

def get_new_user_level(message, new_user_id, name):
    chat_id = message.chat.id
    level = message.text.lower()
    if level in ['shy', 'sexy', 'advanced']:
        bot.send_message(chat_id, "Введите часовой пояс нового пользователя (например, Europe/Moscow):")
        bot.register_next_step_handler_by_chat_id(chat_id, get_new_user_timezone, new_user_id, name, level)
    else:
        bot.send_message(chat_id, "Неверный уровень. Выберите из списка.")
        get_new_user_level(message, new_user_id, name)


def get_new_user_timezone(message, new_user_id, name, level):
    chat_id = message.chat.id
    timezone = message.text
    local_session = Session()
    new_user = User(chat_id=new_user_id, name=name, level=level, timezone=timezone)
    local_session.add(new_user)
    local_session.commit()
    bot.send_message(chat_id, f"Пользователь {name} с ID {new_user_id} успешно добавлен!")
    show_users_menu(chat_id)

def edit_user(chat_id):
    bot.send_message(chat_id, "Введите ID пользователя, которого хотите редактировать:")
    bot.register_next_step_handler_by_chat_id(chat_id, get_user_id_for_edit)


def get_user_id_for_edit(message):
    chat_id = message.chat.id
    try:
        user_id = int(message.text)
        local_session = Session()
        user = local_session.query(User).filter_by(chat_id=user_id).first()
        if user:
            bot.send_message(chat_id, f"Пользователь {user.name} найден. Что хотите изменить?")
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add(
                types.KeyboardButton('Имя'),
                types.KeyboardButton('Уровень'),
                types.KeyboardButton('Часовой пояс')
            )
            markup.add(
                types.KeyboardButton('Назад')
            )
            msg = bot.send_message(chat_id, "Выберите поле для редактирования:", reply_markup=markup)
            bot.register_next_step_handler_by_chat_id(chat_id, get_edit_field, user)
        else:
            bot.send_message(chat_id, "Пользователь с таким ID не найден!")
    except ValueError:
        bot.send_message(chat_id, "Неверный формат ID. Введите число.")
        edit_user(chat_id)


def get_edit_field(message, user):
    chat_id = message.chat.id
    field = message.text
    if field == "Имя":
        bot.send_message(chat_id, "Введите новое имя:")
        bot.register_next_step_handler_by_chat_id(chat_id, edit_user_name, user)
    elif field == "Уровень":
        bot.send_message(chat_id, "Выберите новый уровень:")
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Shy', 'Sexy', 'Advanced')
        msg = bot.send_message(chat_id, "Выберите уровень:", reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(chat_id, edit_user_level, user)
    elif field == "Часовой пояс":
        bot.send_message(chat_id, "Введите новый часовой пояс:")
        bot.register_next_step_handler_by_chat_id(chat_id, edit_user_timezone, user)
    elif field == "Назад":
        show_users_menu(chat_id)
    else:
        bot.send_message(chat_id, "Неверный выбор. Попробуйте снова.")
        get_edit_field(message, user)


def edit_user_name(message, user):
    chat_id = message.chat.id
    new_name = message.text
    local_session = Session()
    user.name = new_name
    local_session.commit()
    bot.send_message(chat_id, f"Имя пользователя {user.chat_id} изменено на {new_name}.")
    show_users_menu(chat_id)


def edit_user_level(message, user):
    chat_id = message.chat.id
    new_level = message.text.lower()
    if new_level in ['shy', 'sexy', 'advanced']:
        local_session = Session()
        user.level = new_level
        local_session.commit()
        bot.send_message(chat_id, f"Уровень пользователя {user.chat_id} изменен на {new_level}.")
        show_users_menu(chat_id)
    else:
        bot.send_message(chat_id, "Неверный уровень. Выберите из списка.")
        edit_user_level(message, user)


def edit_user_timezone(message, user):
    chat_id = message.chat.id
    new_timezone = message.text
    local_session = Session()
    user.timezone = new_timezone
    local_session.commit()
    bot.send_message(chat_id, f"Часовой пояс пользователя {user.chat_id} изменен на {new_timezone}.")
    show_users_menu(chat_id)


def delete_user(chat_id):
    bot.send_message(chat_id, "Введите ID пользователя, которого хотите удалить:")
    bot.register_next_step_handler_by_chat_id(chat_id, get_user_id_for_delete)


def get_user_id_for_delete(message):
    chat_id = message.chat.id
    try:
        user_id = int(message.text)
        local_session = Session()
        user = local_session.query(User).filter_by(chat_id=user_id).first()
        if user:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('Да', 'Нет')
            msg = bot.send_message(chat_id, f"Вы действительно хотите удалить пользователя {user.name} с ID {user_id}?", reply_markup=markup)
            bot.register_next_step_handler_by_chat_id(chat_id, confirm_delete_user, user)
        else:
            bot.send_message(chat_id, "Пользователь с таким ID не найден!")
    except ValueError:
        bot.send_message(chat_id, "Неверный формат ID. Введите число.")
        delete_user(chat_id)


def confirm_delete_user(message, user):
    chat_id = message.chat.id
    if message.text == "Да":
        local_session = Session()
        local_session.delete(user)
        local_session.commit()
        bot.send_message(chat_id, f"Пользователь {user.name} с ID {user.chat_id} удалён.")
    else:
        bot.send_message(chat_id, "Удаление отменено.")
    show_users_menu(chat_id)


def add_habit(chat_id):
    bot.send_message(chat_id, "Введите название новой привычки:")
    bot.register_next_step_handler_by_chat_id(chat_id, get_new_habit_name)

def get_new_habit_name(message):
    chat_id = message.chat.id
    habit_name = message.text
    bot.send_message(chat_id, "Введите ID пользователя, для которого хотите добавить привычку:")
    bot.register_next_step_handler_by_chat_id(chat_id, get_user_id_for_habit, habit_name)


def get_user_id_for_habit(message, habit_name):
    chat_id = message.chat.id
    try:
        user_id = int(message.text)
        local_session = Session()
        user = local_session.query(User).filter_by(chat_id=user_id).first()
        if user:
            new_habit = Habit(name=habit_name, user_id=user.id)
            local_session.add(new_habit)
            local_session.commit()
            bot.send_message(chat_id, f"Привычка '{habit_name}' успешно добавлена для пользователя {user.name}!")
        else:
            bot.send_message(chat_id, "Пользователь с таким ID не найден!")
    except ValueError:
        bot.send_message(chat_id, "Неверный формат ID. Введите число.")
        get_user_id_for_habit(message, habit_name)
    show_habits_menu(chat_id)


def edit_habit(chat_id):
    bot.send_message(chat_id, "Введите ID привычки, которую хотите редактировать:")
    bot.register_next_step_handler_by_chat_id(chat_id, get_habit_id_for_edit)


def get_habit_id_for_edit(message):
    chat_id = message.chat.id
    try:
        habit_id = int(message.text)
        local_session = Session()
        habit = local_session.query(Habit).filter_by(id=habit_id).first()
        if habit:
            bot.send_message(chat_id, f"Привычка '{habit.name}' найдена. Что хотите изменить?")
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add(
                types.KeyboardButton('Название'),
                types.KeyboardButton('Пользователь')
            )
            markup.add(
                types.KeyboardButton('Назад')
            )
            msg = bot.send_message(chat_id, "Выберите поле для редактирования:", reply_markup=markup)
            bot.register_next_step_handler_by_chat_id(chat_id, get_edit_habit_field, habit)
        else:
            bot.send_message(chat_id, "Привычка с таким ID не найдена!")
    except ValueError:
        bot.send_message(chat_id, "Неверный формат ID. Введите число.")
        edit_habit(chat_id)


def get_edit_habit_field(message, habit):
    chat_id = message.chat.id
    field = message.text
    if field == "Название":
        bot.send_message(chat_id, "Введите новое название:")
        bot.register_next_step_handler_by_chat_id(chat_id, edit_habit_name, habit)
    elif field == "Пользователь":
        bot.send_message(chat_id, "Введите ID нового пользователя:")
        bot.register_next_step_handler_by_chat_id(chat_id, edit_habit_user, habit)
    elif field == "Назад":
        show_habits_menu(chat_id)
    else:
        bot.send_message(chat_id, "Неверный выбор. Попробуйте снова.")
        get_edit_habit_field(message, habit)


def edit_habit_name(message, habit):
    chat_id = message.chat.id
    new_name = message.text
    local_session = Session()
    habit.name = new_name
    local_session.commit()
    bot.send_message(chat_id, f"Название привычки {habit.id} изменено на {new_name}.")
    show_habits_menu(chat_id)


def edit_habit_user(message, habit):
    chat_id = message.chat.id
    try:
        new_user_id = int(message.text)
        local_session = Session()
        user = local_session.query(User).filter_by(chat_id=new_user_id).first()
        if user:
            habit.user_id = user.id
            local_session.commit()
            bot.send_message(chat_id, f"Пользователь для привычки {habit.id} изменен на {user.name}.")
        else:
            bot.send_message(chat_id, "Пользователь с таким ID не найден!")
    except ValueError:
        bot.send_message(chat_id, "Неверный формат ID. Введите число.")
        edit_habit_user(message, habit)
    show_habits_menu(chat_id)


def delete_habit(chat_id):
    bot.send_message(chat_id, "Введите ID привычки, которую хотите удалить:")
    bot.register_next_step_handler_by_chat_id(chat_id, get_habit_id_for_delete)


def get_habit_id_for_delete(message):
    chat_id = message.chat.id
    try:
        habit_id = int(message.text)
        local_session = Session()
        habit = local_session.query(Habit).filter_by(id=habit_id).first()
        if habit:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('Да', 'Нет')
            msg = bot.send_message(chat_id, f"Вы действительно хотите удалить привычку '{habit.name}' с ID {habit_id}?", reply_markup=markup)
            bot.register_next_step_handler_by_chat_id(chat_id, confirm_delete_habit, habit)
        else:
            bot.send_message(chat_id, "Привычка с таким ID не найдена!")
    except ValueError:
        bot.send_message(chat_id, "Неверный формат ID. Введите число.")
        delete_habit(chat_id)


def confirm_delete_habit(message, habit):
    chat_id = message.chat.id
    if message.text == "Да":
        local_session = Session()
        local_session.delete(habit)
        local_session.commit()
        bot.send_message(chat_id, f"Привычка '{habit.name}' с ID {habit.id} удалён.")
    else:
        bot.send_message(chat_id, "Удаление отменено.")
    show_habits_menu(chat_id)


def add_reminder(chat_id):
    bot.send_message(chat_id, "Введите ID пользователя, для которого хотите добавить напоминание:")
    bot.register_next_step_handler_by_chat_id(chat_id, get_user_id_for_reminder)


def get_user_id_for_reminder(message):
    chat_id = message.chat.id
    try:
        user_id = int(message.text)
        local_session = Session()
        user = local_session.query(User).filter_by(chat_id=user_id).first()
        if user:
            bot.send_message(chat_id, "Введите время напоминания в формате ЧЧ:ММ (например, 09:00):")
            bot.register_next_step_handler_by_chat_id(chat_id, get_reminder_time, user)
        else:
            bot.send_message(chat_id, "Пользователь с таким ID не найден!")
    except ValueError:
        bot.send_message(chat_id, "Неверный формат ID. Введите число.")
        add_reminder(chat_id)


def get_reminder_time(message, user):
    chat_id = message.chat.id
    reminder_time = message.text
    user.reminder_time = reminder_time  # <-- Обновляем атрибут reminder_time
    db_session.commit()
    bot.send_message(chat_id, f"Время напоминания установлено на {reminder_time}.")
    show_reminders_menu(chat_id)

def edit_reminder(chat_id):
    bot.send_message(chat_id, "Введите ID пользователя, для которого хотите изменить напоминание:")
    bot.register_next_step_handler_by_chat_id(chat_id, get_user_id_for_edit_reminder)


def get_user_id_for_edit_reminder(message):
    chat_id = message.chat.id
    try:
        user_id = int(message.text)
        local_session = Session()
        user = local_session.query(User).filter_by(chat_id=user_id).first()
        if user:
            bot.send_message(chat_id, "Введите новое время напоминания в формате ЧЧ:ММ (например, 09:00):")
            bot.register_next_step_handler_by_chat_id(chat_id, get_new_reminder_time, user)
        else:
            bot.send_message(chat_id, "Пользователь с таким ID не найден!")
    except ValueError:
        bot.send_message(chat_id, "Неверный формат ID. Введите число.")
        edit_reminder(chat_id)


def get_new_reminder_time(message, user):
    chat_id = message.chat.id
    new_reminder_time = message.text
    user.reminder_time = new_reminder_time
    db_session.commit()
    bot.send_message(chat_id, f"Время напоминания изменено на {new_reminder_time}.")
    show_reminders_menu(chat_id)

def delete_reminder(chat_id):
    bot.send_message(chat_id, "Введите ID пользователя, для которого хотите удалить напоминание:")
    bot.register_next_step_handler_by_chat_id(chat_id, get_user_id_for_delete_reminder)


def get_user_id_for_delete_reminder(message):
    chat_id = message.chat.id
    try:
        user_id = int(message.text)
        local_session = Session()
        user = local_session.query(User).filter_by(chat_id=user_id).first()
        if user:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('Да', 'Нет')
            msg = bot.send_message(chat_id, f"Вы действительно хотите удалить напоминание у пользователя {user.name}?", reply_markup=markup)
            bot.register_next_step_handler_by_chat_id(chat_id, confirm_delete_reminder, user)
        else:
            bot.send_message(chat_id, "Пользователь с таким ID не найден!")
    except ValueError:
        bot.send_message(chat_id, "Неверный формат ID. Введите число.")
        delete_reminder(chat_id)


def confirm_delete_reminder(message, user):
    chat_id = message.chat.id
    if message.text == "Да":
        user.reminder_time = None
        db_session.commit()
        bot.send_message(chat_id, f"Напоминание у пользователя {user.name} удалено.")
    else:
        bot.send_message(chat_id, "Удаление отменено.")
    show_reminders_menu(chat_id)


def add_poll(chat_id):
    # Здесь нужно реализовать функцию для добавления опроса
    # Например, запросить у администратора вопрос и варианты ответов,
    # а затем сохранить опрос в базу данных.
    bot.send_message(chat_id, "Функция добавления опроса пока недоступна.")
    show_polls_menu(chat_id)


def get_poll_question(message):
    chat_id = message.chat.id
    question = message.text
    bot.send_message(chat_id, "Введите  варианты  ответов  через  запятую  (например,  Да,  Нет):")
    bot.register_next_step_handler_by_chat_id(chat_id, get_poll_options, question)


def get_poll_options(message, question):
    chat_id = message.chat.id
    options = message.text.split(',')
    options = [option.strip() for option in options]
    bot.send_message(chat_id, "Введите  время  публикации  опроса  в  формате  ЧЧ:ММ  (например,  10:00):")
    bot.register_next_step_handler_by_chat_id(chat_id, get_poll_time, question, options)


def get_poll_time(message, question, options):
    chat_id = message.chat.id
    poll_time = message.text
    #  Здесь  нужно  реализовать  сохранение  опроса  в  базу  данных
    #  и  запланировать  его  публикацию  на  заданное  время
    bot.send_message(chat_id, f"Опрос  '{question}'  успешно  добавлен  и  будет  опубликован  в  {poll_time}!")
    show_polls_menu(chat_id)


def edit_poll(chat_id):
    # Здесь нужно реализовать функцию для редактирования опроса
    # Например, запросить у администратора ID опроса, который нужно редактировать,
    # а затем запросить новые данные для опроса (вопрос, варианты ответов, время публикации)
    bot.send_message(chat_id, "Функция редактирования опроса пока недоступна.")
    show_polls_menu(chat_id)


def delete_poll(chat_id):
    # Здесь нужно реализовать функцию для удаления опроса
    # Например, запросить у администратора ID опроса, который нужно удалить.
    bot.send_message(chat_id, "Функция удаления опроса пока недоступна.")
    show_polls_menu(chat_id)

def add_info_message(chat_id):
    # Здесь нужно реализовать функцию для добавления информационного сообщения
    # Например, запросить у администратора текст сообщения и время отправки,
    # а затем сохранить сообщение в базу данных.
    bot.send_message(chat_id, "Функция добавления информационного сообщения пока недоступна.")
    # show_info_messages_menu(chat_id) # Удаляем лишний вызов


def get_info_message_text(message):
    chat_id = message.chat.id
    text = message.text
    bot.send_message(chat_id, "Введите  время  отправки  сообщения  в  формате  ЧЧ:ММ  (например,  10:00):")
    bot.register_next_step_handler_by_chat_id(chat_id, get_info_message_time, text)


def get_info_message_time(message, text):
    chat_id = message.chat.id
    time = message.text
    #  Здесь  нужно  реализовать  сохранение  информационного  сообщения  в  базу  данных
    #  и  запланировать  его  отправку  на  заданное  время
    bot.send_message(chat_id,
                     f"Информационное  сообщение  '{text}'  успешно  добавлен  и  будет  отправлено  в  {time}!")
    show_info_messages_menu(chat_id)


def edit_info_message(chat_id):
    # Здесь нужно реализовать функцию для редактирования информационного сообщения
    # Например, запросить у администратора ID сообщения, которое нужно редактировать,
    # а затем запросить новый текст сообщения и время отправки.
    bot.send_message(chat_id, "Функция редактирования информационного сообщения пока недоступна.")
    # show_info_messages_menu(chat_id) # Удаляем лишний вызов


def edit_info_message(chat_id):
    # Здесь нужно реализовать функцию для редактирования информационного сообщения
    # Например, запросить у администратора ID сообщения, которое нужно редактировать,
    # а затем запросить новый текст сообщения и время отправки.
    bot.send_message(chat_id, "Функция редактирования информационного сообщения пока недоступна.")
    # show_info_messages_menu(chat_id) # Удаляем лишний вызов

def delete_info_message(chat_id):
    # Здесь нужно реализовать функцию для удаления информационного сообщения
    # Например, запросить у администратора ID сообщения, которое нужно удалить.
    bot.send_message(chat_id, "Функция удаления информационного сообщения пока недоступна.")
    # show_info_messages_menu(chat_id) # Удаляем лишний вызов


@bot.message_handler(commands=['admin'])
def admin_command_handler(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "Введите пароль для доступа к админ панели:")
    bot.register_next_step_handler(msg, check_admin_password)

def check_admin_password(message):
    chat_id = message.chat.id
    if message.text == ADMIN_PASSWORD:
        show_admin_menu(chat_id)
    else:
        bot.send_message(chat_id, "Неверный пароль!")



