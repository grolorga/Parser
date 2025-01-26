import sys
import os
import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QTextEdit
from bs4 import BeautifulSoup


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Парсер данных с сайта")
        self.setGeometry(100, 100, 800, 600)

        # Основной виджет и компоновка
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Поле ввода URL
        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Введите URL")
        self.layout.addWidget(self.url_input)

        # Кнопка отправки
        self.run_button = QPushButton("Получить данные", self)
        self.run_button.clicked.connect(self.run_scraper)
        self.layout.addWidget(self.run_button)

        # Поле вывода результатов
        self.result_area = QTextEdit(self)
        self.result_area.setReadOnly(True)
        self.layout.addWidget(self.result_area)

    def run_scraper(self):
        url = self.url_input.text().strip()
        if not url:
            self.result_area.setText("Пожалуйста, введите URL")
            return

        self.result_area.setText("Обработка запроса...")
        QApplication.processEvents()  # Обновляем UI

        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Извлекаем название товара
                title = soup.find('h1', id='pagetitle')
                if title:
                    title = title.get_text(strip=True)
                    self.result_area.append(f"Название: {title}")
                else:
                    self.result_area.append("Название не найдено")

                # Извлекаем значение из span с классом "article__value" и атрибутом itemprop="value"
                value_tag = soup.find('span', class_='article__value', itemprop='value')
                if value_tag:
                    value = value_tag.get_text(strip=True)
                    print(f"Артикул: {value}")
                    self.result_area.append(f"Артикул : {value_tag}")
                else:
                    print("Значение не найдено")
                # Папка для сохранения изображений
                save_folder = 'images'
                os.makedirs(save_folder, exist_ok=True)

                # Извлекаем все изображения
                image_tags = soup.find_all('img', class_='product-detail-gallery__picture')

                # Собираем все ссылки на изображения
                image_urls = set()

                for img in image_tags:
                    img_url = img.get('data-src') or img.get('src')
                    if img_url and img_url.startswith('/'):
                        img_url = 'https://opt-milena.ru' + img_url
                    if img_url:
                        image_urls.add(img_url)

                # Скачиваем и сохраняем уникальные изображения
                for idx, img_url in enumerate(image_urls):
                    response = requests.get(img_url)
                    file_extension = img_url.split('.')[-1]
                    file_name = f'image_{idx}.{file_extension}'
                    file_path = os.path.join(save_folder, file_name)

                    with open(file_path, 'wb') as file:
                        file.write(response.content)
                    self.result_area.append(f'Сохранено изображение: {file_path}')

                # Извлекаем все характеристики
                characteristics = {}
                char_container = soup.find('div', class_='product-chars')
                if char_container:
                    char_items = char_container.find_all('div', class_='properties__item')
                    for item in char_items:
                        key = item.find('div', class_='properties__title')
                        value = item.find('div', class_='properties__value')
                        if key and value:
                            characteristics[key.get_text(strip=True)] = value.get_text(strip=True)
                    if characteristics:
                        self.result_area.append("Характеристики:")
                        for k, v in characteristics.items():
                            self.result_area.append(f"  {k}: {v}")
                    else:
                        self.result_area.append("Характеристики не найдены")
                else:
                    self.result_area.append("Контейнер характеристик не найден")

                # Извлекаем цену за мелкий и крупный опт
                try:
                    small_opt_price_block = soup.find('div', class_='price_group')
                    if small_opt_price_block:
                        small_opt_price = small_opt_price_block.find('div', class_='price').get_text(strip=True)
                        self.result_area.append(f"Мелкий опт: {small_opt_price}")
                    else:
                        self.result_area.append("Блок цены за мелкий опт не найден")
                except AttributeError:
                    self.result_area.append("Не удалось извлечь цену за мелкий опт")

                try:
                    large_opt_price_block = soup.find('div', class_='price_group min')
                    if large_opt_price_block:
                        large_opt_price = large_opt_price_block.find('div', class_='price').get_text(strip=True)
                        self.result_area.append(f"Крупный опт: {large_opt_price}")
                    else:
                        self.result_area.append("Блок цены за крупный опт не найден")
                except AttributeError:
                    self.result_area.append("Не удалось извлечь цену за крупный опт")

            else:
                self.result_area.setText(f"Ошибка при запросе страницы: {response.status_code}")

        except Exception as e:
            self.result_area.setText(f"Произошла ошибка: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
