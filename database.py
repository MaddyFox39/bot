from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Date, Float
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from sqlalchemy import inspect

DATABASE_URL = 'sqlite:///habits.db'

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, unique=True)
    name = Column(String)
    reminder_time = Column(String)
    gender = Column(String)
    subscribed_to_newsletter = Column(Boolean, default=False)
    age = Column(Integer)
    height = Column(Float)
    country = Column(String)
    city = Column(String)
    level = Column(String)
    last_payment_date = Column(Date, nullable=True)
    last_payment_amount = Column(Float, nullable=True)
    subscribed_until = Column(Date, nullable=True)
    daily_reminders = Column(Boolean, default=True)
    newsletter = Column(Boolean, default=True)
    timezone = Column(String, default='UTC')
    custom_habit = Column(String)
    habits = relationship("Habit", back_populates="user")
    daily_data = relationship("DailyData", back_populates="user")
    custom_reminder_text = Column(String, nullable=True)

class Habit(Base):
    __tablename__ = 'habits'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="habits")
    entries = relationship("HabitEntry", back_populates="habit")

class HabitEntry(Base):
    __tablename__ = 'habit_entries'
    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey('habits.id'))
    date = Column(Date, default=datetime.utcnow)
    value = Column(String)
    habit = relationship("Habit", back_populates="entries")

class DailyData(Base):
    __tablename__ = 'daily_data'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="daily_data")
    date = Column(Date, default=datetime.utcnow)
    sleep_hours = Column(Float)
    weight = Column(Float)
    measurements = Column(String)
    food_photo = Column(String)  # Ссылка на загруженное фото
    mood_rating = Column(Integer)
    active_minutes = Column(Integer)
    steps = Column(Integer)
    goals_achieved = Column(Boolean)
    custom_habit_status = Column(Boolean)
    message_to_self = Column(String)

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()
db_session = session
def update_database():
    inspector = inspect(engine)
    if 'reminder_time' not in [column['name'] for column in inspector.get_columns('users')]:
        print("Обновление базы данных...")
        with engine.begin() as conn:
            conn.execute('ALTER TABLE users ADD COLUMN reminder_time VARCHAR(255)')
        print("База данных обновлена.")
Session = sessionmaker(bind=engine)
session = Session()















