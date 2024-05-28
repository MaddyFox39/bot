from datetime import datetime, timedelta
from database import session, User, DailyData

#  Создаем  тестового  пользователя,  если  его  еще  нет
user = session.query(User).filter_by(chat_id=997979287).first()  #  Замени  123456789  на  свой  chat_id
if not user:
    user = User(chat_id=123456789, name="Тестовый  Пользователь", level="advanced",
                custom_habit="Читать  книги")
    session.add(user)
    session.commit()

#  Заполняем  базу  данных  тестовыми  данными  за  последнюю  неделю
today = datetime.now().date()
for i in range(7):
    date = today - timedelta(days=i)
    daily_data = DailyData(user_id=user.id, date=date, weight=70 + i * 0.5, sleep_hours=8 - i * 0.2,
                           measurements=f"80,{90 + i},{55 - i * 0.1}", active_minutes=60 + i * 5,
                           steps=10000 - i * 1000, goals_achieved=i % 2 == 0)
    session.add(daily_data)

session.commit()
print("База  данных  заполнена  тестовыми  данными!")