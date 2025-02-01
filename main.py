import sys
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QPropertyAnimation, QRect, QEasingCurve
from PyQt5.QtGui import QFont, QColor
import g4f  # Библиотека для взаимодействия с GPT-4

# Устанавливаем политику цикла событий для Windows
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Класс для работы с потоками
class Worker(QObject):
    finished = pyqtSignal(str)  # Сигнал для передачи ответа от GPT-4

    def __init__(self, message):
        super().__init__()
        self.message = message

    def run(self):
        try:
            # Используем g4f для генерации ответа
            response = g4f.ChatCompletion.create(
                model="gpt-4o",  # Указываем модель GPT-4
                messages=[{"role": "user", "content": self.message}]
            )
            self.finished.emit(response)
        except Exception as e:
            print(f"Ошибка при генерации ответа: {e}")
            self.finished.emit("Извините, произошла ошибка при обработке вашего запроса.")

class ChatBot(QWidget):
    def __init__(self):
        super().__init__()
        self.is_dark_theme = True  # Текущая тема (по умолчанию темная)
        self.initUI()

    def initUI(self):
        # Настройка окна
        self.setWindowTitle('AIChat')
        self.setGeometry(100, 100, 500, 600)

        # Применение стилей (темная тема по умолчанию)
        self.apply_theme()

        # Создание виджетов
        self.chat_history = QTextEdit(self)
        self.chat_history.setReadOnly(True)
        self.chat_history.setFont(QFont("Arial", 12))

        self.user_input = QLineEdit(self)
        self.user_input.setPlaceholderText("Введите ваше сообщение...")
        self.user_input.returnPressed.connect(self.send_message)

        self.send_button = QPushButton('Отправить', self)
        self.send_button.clicked.connect(self.send_message)

        # Надпись "Бот думает..."
        self.thinking_label = QLabel("Бот думает...", self)
        self.thinking_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.thinking_label.hide()  # Скрываем надпись по умолчанию

        # Кнопка переключения темы
        self.theme_button = QPushButton('Светлая тема', self)
        self.theme_button.clicked.connect(self.toggle_theme)

        # Размещение виджетов
        layout = QVBoxLayout()
        layout.addWidget(QLabel("История чата:"))
        layout.addWidget(self.chat_history)

        # Горизонтальный layout для кнопки темы и надписи "Бот думает..."
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.theme_button)
        bottom_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        bottom_layout.addWidget(self.thinking_label)

        layout.addLayout(bottom_layout)
        layout.addWidget(QLabel("Ваше сообщение:"))
        layout.addWidget(self.user_input)
        layout.addWidget(self.send_button)

        self.setLayout(layout)

    def send_message(self):
        # Получаем текст от пользователя
        user_message = self.user_input.text()
        if user_message.strip() == "":
            return

        # Добавляем сообщение пользователя в историю
        self.add_message_to_chat(f"<b>Вы:</b> {user_message}", animate=True)
        self.user_input.clear()

        # Отключаем кнопку отправки, чтобы избежать множественных запросов
        self.send_button.setEnabled(False)

        # Показываем надпись "Бот думает..." с анимацией
        self.show_thinking_label()

        # Создаем и запускаем поток для выполнения запроса к GPT-4
        self.worker = Worker(user_message)
        self.worker.finished.connect(self.handle_response)
        threading.Thread(target=self.worker.run).start()

    def handle_response(self, response):
        # Добавляем ответ бота в историю
        self.add_message_to_chat(f"<b>Бот:</b> {response}", animate=True)

        # Включаем кнопку отправки обратно
        self.send_button.setEnabled(True)

        # Скрываем надпись "Бот думает..." с анимацией
        self.hide_thinking_label()

    def add_message_to_chat(self, message, animate=False):
        # Добавляем сообщение в историю чата
        if animate:
            # Анимация появления сообщения
            self.chat_history.append("")  # Добавляем пустую строку для анимации
            self.chat_history.moveCursor(self.chat_history.textCursor().End)
            self.chat_history.insertHtml(f"<div style='opacity: 0;'>{message}</div><br>")

            # Анимация плавного появления
            animation = QPropertyAnimation(self.chat_history.viewport(), b"geometry")
            animation.setDuration(500)  # Длительность анимации
            animation.setEasingCurve(QEasingCurve.OutQuad)
            animation.setStartValue(QRect(0, self.chat_history.height() - 50, self.chat_history.width(), 50))
            animation.setEndValue(QRect(0, self.chat_history.height(), self.chat_history.width(), 50))
            animation.start()
        else:
            self.chat_history.append(message)

        # Автоматическая прокрутка вниз
        self.chat_history.verticalScrollBar().setValue(self.chat_history.verticalScrollBar().maximum())

    def show_thinking_label(self):
        # Плавное появление надписи "Бот думает..."
        self.thinking_label.setStyleSheet("color: rgba(255, 255, 255, 0);")  # Начальная прозрачность
        self.thinking_label.show()

        self.animation = QPropertyAnimation(self.thinking_label, b"styleSheet")
        self.animation.setDuration(500)  # Длительность анимации
        self.animation.setStartValue("color: rgba(255, 255, 255, 0);")  # Начальная прозрачность
        self.animation.setEndValue("color: rgba(255, 255, 255, 255);")  # Конечная непрозрачность
        self.animation.start()

    def hide_thinking_label(self):
        # Плавное исчезновение надписи "Бот думает..."
        self.animation = QPropertyAnimation(self.thinking_label, b"styleSheet")
        self.animation.setDuration(500)  # Длительность анимации
        self.animation.setStartValue("color: rgba(255, 255, 255, 255);")  # Начальная непрозрачность
        self.animation.setEndValue("color: rgba(255, 255, 255, 0);")  # Конечная прозрачность
        self.animation.finished.connect(self.thinking_label.hide)  # Скрываем надпись после завершения анимации
        self.animation.start()

    def toggle_theme(self):
        # Переключение между светлой и темной темами
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()
        self.theme_button.setText("Темная тема" if self.is_dark_theme else "Светлая тема")

    def apply_theme(self):
        # Применение текущей темы
        if self.is_dark_theme:
            self.setStyleSheet("""
                QWidget {
                    background-color: #2E3440;
                    color: #D8DEE9;
                    font-family: 'Arial';
                    font-size: 14px;
                }
                QTextEdit {
                    background-color: #3B4252;
                    color: #ECEFF4;
                    border: 1px solid #4C566A;
                    border-radius: 10px;
                    padding: 10px;
                }
                QLineEdit {
                    background-color: #3B4252;
                    color: #ECEFF4;
                    border: 1px solid #4C566A;
                    border-radius: 10px;
                    padding: 10px;
                }
                QPushButton {
                    background-color: #5E81AC;
                    color: #ECEFF4;
                    border: none;
                    border-radius: 10px;
                    padding: 10px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #81A1C1;
                }
                QLabel {
                    color: #ECEFF4;
                    font-size: 16px;
                    font-weight: bold;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: #FFFFFF;
                    color: #000000;
                    font-family: 'Arial';
                    font-size: 14px;
                }
                QTextEdit {
                    background-color: #F0F0F0;
                    color: #000000;
                    border: 1px solid #CCCCCC;
                    border-radius: 10px;
                    padding: 10px;
                }
                QLineEdit {
                    background-color: #F0F0F0;
                    color: #000000;
                    border: 1px solid #CCCCCC;
                    border-radius: 10px;
                    padding: 10px;
                }
                QPushButton {
                    background-color: #0078D7;
                    color: #FFFFFF;
                    border: none;
                    border-radius: 10px;
                    padding: 10px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #005BB5;
                }
                QLabel {
                    color: #000000;
                    font-size: 16px;
                    font-weight: bold;
                }
            """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    chat_bot = ChatBot()
    chat_bot.show()
    sys.exit(app.exec_())