import sys
import subprocess
import threading
import os
from PyQt6 import uic
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QDialog,
    QHBoxLayout,
    QLabel,
    QFileDialog,
)
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QTextCursor, QPixmap, QFont
from PyQt6.QtCore import Qt


# Класс для захвата вывода консоли
class ConsoleOutput(QObject):
    text_written = pyqtSignal(str)

    def write(self, text):
        self.text_written.emit(text)

    def flush(self):
        pass


# Окно для отображения консоли
class ConsoleWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Консоль")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(
            """
            QTextEdit {
                background-color: #2b2b2b;
                color: #e0e0e0;
                border: 1px solid #3b3b3b;
                border-radius: 4px;
                padding: 5px;
                font-family: 'Consolas', 'Monospace';
            }
        """
        )
        layout.addWidget(self.text_edit)

        self.hide_button = QPushButton("Скрыть")
        self.hide_button.setStyleSheet(
            """
            QPushButton {
                background-color: #5c5c5c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6c6c6c;
            }
        """
        )
        self.hide_button.clicked.connect(self.hide)
        layout.addWidget(self.hide_button)

        self.setLayout(layout)
        self.setStyleSheet("background-color: #3c3c3c;")

    def append_text(self, text):
        self.text_edit.moveCursor(QTextCursor.MoveOperation.End)
        self.text_edit.insertPlainText(text)


# Главное окно
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_file = None
        uic.loadUi("main.ui", self)
        self.initUI()
        self.console_window = None
        self.process = None

    def initUI(self):
        self.setWindowTitle("DZ-slpit")
        self.setGeometry(100, 100, 800, 500)
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #f5f5f5;
            }
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """
        )

        # Создаем главный горизонтальный layout
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Левая панель с элементами управления
        left_widget = QWidget()
        left_widget.setStyleSheet(
            """
            QWidget {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """
        )
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)
        left_layout.setContentsMargins(15, 15, 15, 15)

        # Заголовок 1
        label1 = QLabel("1. Выберите файл (*pdf)")
        label1_font = QFont()
        label1_font.setBold(True)
        label1_font.setPointSize(12)
        label1.setFont(label1_font)
        label1.setStyleSheet("color: #e74c3c;")
        left_layout.addWidget(label1)

        # Кнопка выбора файла
        self.select_file_button = QPushButton("Выбрать файл")
        self.select_file_button.setStyleSheet(
            """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """
        )
        self.select_file_button.clicked.connect(self.select_file)
        left_layout.addWidget(self.select_file_button)

        # Метка для отображения выбранного файла
        self.file_label = QLabel("Вы выбрали: файл не выбран")
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet(
            """
            QLabel {
                background-color: #f9f9f9;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                color: #555;
            }
        """
        )
        left_layout.addWidget(self.file_label)

        # Заголовок 2
        label2 = QLabel("2. Нажмите кнопку")
        label2_font = QFont()
        label2_font.setBold(True)
        label2_font.setPointSize(12)
        label2.setFont(label2_font)
        label2.setStyleSheet("color: #e74c3c;")
        left_layout.addWidget(label2)

        # Кнопка старт
        self.start_button = QPushButton("Запустить обработку")
        self.start_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """
        )
        self.start_button.clicked.connect(self.start_program)
        self.start_button.setEnabled(False)  # Изначально неактивна
        left_layout.addWidget(self.start_button)

        # Примечания
        notes_label = QLabel(
            "Примечание: программа работает ТОЛЬКО с РТ по профильной математике от Школково \nАвтор: Roman P. ❤"
        )
        notes_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        notes_label.setWordWrap(True)
        left_layout.addWidget(notes_label)

        # Добавляем растягивающееся пространство внизу
        left_layout.addStretch()

        left_widget.setLayout(left_layout)

        # Правая панель с изображением
        right_widget = QWidget()
        right_widget.setStyleSheet(
            """
            QWidget {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """
        )
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(15, 15, 15, 15)

        # # Заголовок для правой панели
        # image_title = QLabel("Логотип")
        # image_title_font = QFont()
        # image_title_font.setBold(True)
        # image_title_font.setPointSize(12)
        # image_title.setFont(image_title_font)
        # image_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # image_title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        # right_layout.addWidget(image_title)

        # Изображение
        # image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(
            "border: 2px dashed #bdc3c7; border-radius: 8px; min-height: 300px;"
        )

        # # Загрузка изображения - используем относительный путь
        # try:
        #     # Получаем путь к директории скрипта
        #     script_dir = os.path.dirname(os.path.abspath(__file__))
        #     logo_path = os.path.join(script_dir, "img", "logo.png")

        #     # Проверяем существование файла
        #     if os.path.exists(logo_path):
        #         pixmap = QPixmap(logo_path)
        #         if not pixmap.isNull():
        #             # Масштабируем изображение
        #             pixmap = pixmap.scaled(
        #                 300,
        #                 300,
        #                 Qt.AspectRatioMode.KeepAspectRatio,
        #                 Qt.TransformationMode.SmoothTransformation,
        #             )
        #             image_label.setPixmap(pixmap)
        #         else:
        #             image_label.setText("Ошибка загрузки изображения\n(файл поврежден)")
        #             image_label.setStyleSheet(
        #                 "border: 2px dashed #bdc3c7; border-radius: 8px; color: #e74c3c;"
        #             )
        #     else:
        #         image_label.setText(f"Изображение не найдено\n\n{logo_path}")
        #         image_label.setStyleSheet(
        #             "border: 2px dashed #bdc3c7; border-radius: 8px; color: #7f8c8d;"
        #         )
        # except Exception as e:
        #     image_label.setText(f"Ошибка: {str(e)}")
        #     image_label.setStyleSheet(
        #         "border: 2px dashed #bdc3c7; border-radius: 8px; color: #e74c3c;"
        #     )

        right_layout.addWidget(self.image_label)

        # Добавляем растягивающееся пространство
        right_layout.addStretch()

        right_widget.setLayout(right_layout)

        # Добавляем левую и правую панели в главный layout
        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(right_widget, 1)

        # Устанавливаем главный layout
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def select_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Выберите PDF файл", "", "PDF Files (*.pdf)"
        )
        if file_name:
            self.selected_file = file_name
            self.file_label.setText(f"Вы выбрали: {file_name.split('/')[-1]}")
            self.start_button.setEnabled(True)  # Активируем кнопку старт

    def start_program(self):
        self.console_window = ConsoleWindow()
        self.console_window.show()

        thread = threading.Thread(target=self.run_program)
        thread.daemon = True
        thread.start()

    def run_program(self):
        # Перенаправляем вывод консоли
        original_stdout = sys.stdout
        console_output = ConsoleOutput()
        console_output.text_written.connect(self.console_window.append_text)
        sys.stdout = console_output

        try:
            from prog import split_pdf_by_keyword

            input_pdf = self.selected_file
            output_directory = "output-dzSPLIT"  # Директория для сохранения файлов
            word_sp = "Задача"

            split_pdf_by_keyword(
                input_path=input_pdf, output_dir=output_directory, word=word_sp
            )
        except Exception as e:
            print(f"Ошибка: {str(e)}")
        finally:
            sys.stdout = original_stdout


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
