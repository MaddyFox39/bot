from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from datetime import datetime, timedelta
from database import db_session, User, DailyData, Habit, HabitEntry, Session
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.ticker import MaxNLocator
from bot_instance import bot

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT

# Регистрация шрифта DejaVuSans
pdfmetrics.registerFont(TTFont('DejaVuSans', 'fonts/DejaVuSans.ttf'))
styles = getSampleStyleSheet()

# Определение нового стиля с использованием шрифта DejaVuSans
custom_style = ParagraphStyle(
    name='DejaVuStyle',
    parent=styles['Normal'],
    fontName='DejaVuSans',
    fontSize=10,
    leading=12,
    alignment=TA_LEFT
)

def generate_pdf(user):
    filename = f"stats_{user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    story = []

    # Информация о пользователе
    story.append(Paragraph(f"Статистика за неделю для {user.name}", custom_style))
    story.append(Paragraph(f"Уровень: {user.level}", custom_style))
    story.append(Paragraph(f"Часовой пояс: {user.timezone}", custom_style))

    # Период отчета
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    story.append(Paragraph(f"Период отчета: {week_ago} - {today}", custom_style))

    # Генерация графиков
    generate_general_chart(user, week_ago, story)
    generate_additional_charts(user, week_ago, story)

    # Вывод данных о привычках
    habits = db_session.query(Habit).filter_by(user_id=user.id).all()
    for habit in habits:
        story.append(Paragraph(f"Привычка: {habit.name}", custom_style))
        entries = db_session.query(HabitEntry).filter_by(habit_id=habit.id).all()
        for entry in entries:
            story.append(Paragraph(f"{entry.date.strftime('%Y-%m-%d')}: {entry.value}", custom_style))

    doc.build(story)
    return filename

def generate_general_chart(user, week_ago, story):
    data = db_session.query(DailyData).filter(
        DailyData.user_id == user.id, DailyData.date >= week_ago
    ).all()

    if data:
        dates = [d.date for d in data]
        weights = [d.weight if d.weight is not None else 0 for d in data]
        sleep_hours = [d.sleep_hours if d.sleep_hours is not None else 0 for d in data]

        # Проверка данных
        if not dates or len(dates) != len(weights) or len(dates) != len(sleep_hours):
            print(f"Invalid data: dates={dates}, weights={weights}, sleep_hours={sleep_hours}")
            return

        fig, ax1 = plt.subplots(figsize=(10, 6))

        try:
            # Вес (левая ось Y)
            ax1.plot(dates, weights, 'b-', marker='o', label='Вес')
            ax1.set_xlabel('Дата', fontsize=12)
            ax1.set_ylabel('Вес (кг)', fontsize=12, color='b')
            ax1.tick_params('y', colors='b')
            ax1.tick_params(axis='x', rotation=45)
            ax1.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
            ax1.xaxis.set_major_locator(MaxNLocator(integer=True))

            # Сон (правая ось Y)
            ax2 = ax1.twinx()
            ax2.plot(dates, sleep_hours, 'r-', marker='s', label='Сон', alpha=0.7)
            ax2.set_ylabel('Часы сна', fontsize=12, color='r')
            ax2.tick_params('y', colors='r')

            # Стилизация
            plt.title('Вес и сон за неделю', fontsize=14)
            ax1.grid(True, which='both', linestyle='--', linewidth=0.5)
            fig.tight_layout()

            # Легенда
            fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))

            # Сохраняем график в файл
            chart_filename = f"general_chart_{user.id}.png"
            plt.savefig(chart_filename, bbox_inches='tight')

            # Добавляем график в PDF-отчет
            story.append(Image(chart_filename, width=6 * inch, height=4 * inch))
        except Exception as e:
            print(f"Error generating general chart: {e}")
        finally:
            plt.close()

def generate_additional_charts(user, week_ago, story):
    data = db_session.query(DailyData).filter(
        DailyData.user_id == user.id, DailyData.date >= week_ago
    ).all()

    if data:
        dates = [d.date for d in data]
        active_minutes = [d.active_minutes if d.active_minutes is not None else 0 for d in data]
        steps = [d.steps if d.steps is not None else 0 for d in data]
        measurements = [
            [float(x) for x in d.measurements.split(',')] if d.measurements else [0, 0, 0] for d in data
        ]
        waist = [m[0] for m in measurements]
        hips = [m[1] for m in measurements]
        thighs = [m[2] for m in measurements]
        goals_achieved = [d.goals_achieved if d.goals_achieved is not None else 0 for d in data]

        # Проверка данных
        if not dates or len(dates) != len(active_minutes) or len(dates) != len(steps):
            print(f"Invalid data: dates={dates}, active_minutes={active_minutes}, steps={steps}")
            return

        # Генерация линейных графиков
        generate_line_chart('Активные минуты за неделю', dates, active_minutes, 'Активные минуты', 'active_minutes_chart.png', story)
        generate_line_chart('Шаги за неделю', dates, steps, 'Шаги', 'steps_chart.png', story)

        # Генерация столбчатых диаграмм
        generate_bar_chart('Талия за неделю', dates, waist, 'Талия (см)', 'waist_chart.png', story)
        generate_bar_chart('Бедра за неделю', dates, hips, 'Бедра (см)', 'hips_chart.png', story)
        generate_bar_chart('Бедра за неделю', dates, thighs, 'Бедра (см)', 'thighs_chart.png', story)

        # Генерация круговых диаграмм
        generate_pie_chart('Достижения целей за неделю', goals_achieved, 'goals_achieved_chart.png', story)

def generate_line_chart(title, x_data, y_data, y_label, filename, story):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x_data, y_data, marker='o')
    ax.set_xlabel('Дата', fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)
    plt.title(title, fontsize=14)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax.tick_params(axis='x', rotation=45)
    ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    try:
        # Сохраняем график в файл
        plt.tight_layout()
        plt.savefig(filename, bbox_inches='tight')

        # Добавляем график в PDF-отчет
        story.append(Image(filename, width=6 * inch, height=4 * inch))
    except Exception as e:
        print(f"Error generating line chart {title}: {e}")
    finally:
        plt.close()

def generate_bar_chart(title, x_data, y_data, y_label, filename, story):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x_data, y_data, color='skyblue')
    ax.set_xlabel('Дата', fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)
    plt.title(title, fontsize=14)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax.tick_params(axis='x', rotation=45)
    ax.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    try:
        # Сохраняем график в файл
        plt.tight_layout()
        plt.savefig(filename, bbox_inches='tight')

        # Добавляем график в PDF-отчет
        story.append(Image(filename, width=6 * inch, height=4 * inch))
    except Exception as e:
        print(f"Error generating bar chart {title}: {e}")
    finally:
        plt.close()

def generate_pie_chart(title, data, filename, story):
    labels = 'Достигнуто', 'Не достигнуто'
    sizes = [sum(data), len(data) - sum(data)]
    colors = ['lightgreen', 'lightcoral']
    explode = (0.1, 0)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
           shadow=True, startangle=140)
    plt.title(title, fontsize=14)

    try:
        # Сохраняем график в файл
        plt.tight_layout()
        plt.savefig(filename, bbox_inches='tight')

        # Добавляем график в PDF-отчет
        story.append(Image(filename, width=4 * inch, height=4 * inch))
    except Exception as e:
        print(f"Error generating pie chart {title}: {e}")
    finally:
        plt.close()

def send_stats(message):
    chat_id = message.chat.id
    local_session = Session()
    user = local_session.query(User).filter_by(chat_id=chat_id).first()
    if user:
        pdf_file = generate_pdf(user)
        with open(pdf_file, 'rb') as f:
            bot.send_document(chat_id, f)
    else:
        bot.send_message(chat_id, "Сначала зарегистрируйтесь с помощью команды /start.")
