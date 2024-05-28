from bot_instance import bot
from handlers import *
from scheduler import start_scheduler
from database import engine, Base, session, User
from sqlalchemy import Table, Column, String
import time

def update_database():
    from sqlalchemy import inspect, MetaData
    inspector = inspect(engine)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    if 'reminder_time' not in [column['name'] for column in inspector.get_columns('users')]:
        print("Обновление базы данных...")

        #  1.  Проверяем,  существует  ли  таблица  'users_new'
        if 'users_new' not in metadata.tables:
            #  1.1.  Создаем  новую  таблицу  с  добавленным  столбцом,  только  если  её  нет
            old_users_table = metadata.tables['users']
            new_users_table = Table('users_new', metadata,
                                    *(Column(c.name, c.type) for c in old_users_table.columns),
                                    Column('reminder_time', String))
            new_users_table.create(engine)

            #  2.  Копируем  данные  из  старой  таблицы  в  новую
            with engine.begin() as conn:
                for row in conn.execute(old_users_table.select()):
                    conn.execute(new_users_table.insert().values(row))

            #  3.  Переименовываем  новую  таблицу
            old_users_table.drop(engine)
            new_users_table = Table('users', metadata,
                                    *(Column(c.name, c.type) for c in new_users_table.columns))
            new_users_table.create(engine, checkfirst=True)

        print("База данных обновлена.")

if __name__ == "__main__":
    update_database()
    start_scheduler()
    bot.polling(none_stop=True)














