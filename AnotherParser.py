import sys
import os
import base64
from io import BytesIO
import requests
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QTextEdit
from bs4 import BeautifulSoup
import json


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Загрузка продукта с сайта")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon('MilenaIcon.ico'))

        # Основной виджет и компоновка
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Поле ввода URL
        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Введите URL")
        self.layout.addWidget(self.url_input)

        # Кнопка отправки
        self.run_button = QPushButton("Получить и загрузить", self)
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
                title_tag = soup.find('h1', id='pagetitle')
                title = title_tag.get_text(strip=True) if title_tag else "Название не найдено"

                # Извлекаем артикул
                value_tag = soup.find('span', class_='article__value', itemprop='value')
                article = value_tag.get_text(strip=True) if value_tag else "Артикул не найден"

                # Извлекаем изображения
                image_tags = soup.find_all('img', class_='product-detail-gallery__picture')
                image_urls = set()
                base64_images = []
                for img in image_tags:
                    img_url = img.get('data-src') or img.get('src')
                    if img_url and img_url.startswith('/'):
                        img_url = 'https://opt-milena.ru' + img_url
                    if img_url:
                        image_urls.add(img_url)

                # Скачиваем изображения и преобразуем в base64
                for img_url in image_urls:
                    response = requests.get(img_url)
                    if response.status_code == 200:
                        image_base64 = base64.b64encode(response.content).decode('utf-8')
                        base64_images.append(image_base64)

                # Попытка найти таблицу с характеристиками
                table = soup.find('table', class_='props_list')

                characteristics = {}

                if table:
                    # Если таблица найдена, извлекаем данные из нее
                    rows = table.find_all('tr', class_='js-prop-replace')
                    for row in rows:
                        key_tag = row.find('span', class_='js-prop-title')
                        value_tag = row.find('span', class_='js-prop-value')
                        if key_tag and value_tag:
                            key = key_tag.get_text(strip=True)
                            value = value_tag.get_text(strip=True)
                            characteristics[key] = value
                else:
                    # Если таблицы нет, используем старый метод
                    char_container = soup.find('div', class_='product-chars')
                    if char_container:
                        char_items = char_container.find_all('div', class_='properties__item')
                        for item in char_items:
                            key = item.find('div', class_='properties__title')
                            value = item.find('div', class_='properties__value')
                            if key and value:
                                characteristics[key.get_text(strip=True)] = value.get_text(strip=True)

                # Извлекаем цены с обработкой возможных ошибок
                prices = []

                def parse_price(price_str):
                    try:
                        # Оставляем только цифры и убираем лишние символы
                        clean_price = price_str.replace('₽', '').replace(' ', '').split('/')[0]
                        return int(clean_price)
                    except ValueError:
                        return 0  # Возвращаем 0 или любое другое значение по умолчанию при ошибке

                small_opt_price_block = soup.find('div', class_='price_group')
                if small_opt_price_block:
                    small_opt_price = small_opt_price_block.find('div', class_='price').get_text(strip=True)
                    prices.append(
                        {"value": parse_price(small_opt_price), "currency": "RUB", "type": "wholesale_small"}
                    )

                large_opt_price_block = soup.find('div', class_='price_group min')
                if large_opt_price_block:
                    large_opt_price = large_opt_price_block.find('div', class_='price').get_text(strip=True)
                    prices.append(
                        {"value": parse_price(large_opt_price), "currency": "RUB", "type": "wholesale_large"}
                    )
                # Преобразование размеров в массив чисел и их преобразование в строки
                sizes = [str(int(size.strip())) for size in characteristics.get("Размер", "").split(',') if
                         size.strip().isdigit()]

                # Преобразуем данные в JSON формат
                product_data = {
                    "images": base64_images,  # Преобразуем множество в список для JSON
                    "name": title,
                    "priceLow": prices[0]["value"] if len(prices) > 0 else 0,
                    "priceHigh": prices[1]["value"] if len(prices) > 1 else 0,
                    "article": article,
                    "description": title,
                    "number": characteristics.get("Количество в упаковке", "0").replace(' шт', ''),
                    "country": characteristics.get("Страна", ""),
                    "type": "type",
                    "selectedOption": characteristics.get("Категория", ""),
                    "selectedSizes": sizes,
                    "selectedColors": [characteristics.get("Цвет", "В ассортименте")],
                    "selectedMaterials": [characteristics.get("Состав", "")],
                    "selectedSeasons": "",  # Возможно, будет пустым, поэтому список
                    "isNew": False,
                    "isHit": False
                }

                # Отображаем преобразованные данные
                self.result_area.setText(json.dumps(product_data, ensure_ascii=False, indent=4))

                # URL сервера, куда нужно отправить данные
                server_url = "https://rst-for-milenaopt.ru/add_product"  # Замените на ваш URL

                # Отправляем данные на сервер
                try:
                    headers = {'Content-Type': 'application/json'}
                    response = requests.post(server_url, json=product_data, headers=headers)
                    if response.status_code == 201:
                        self.result_area.append("\nДанные успешно отправлены на сервер.")
                    else:
                        self.result_area.append(
                            f"\nОшибка при отправке данных: {response.status_code} - {response.text}")
                except Exception as e:
                    self.result_area.append(f"\nОшибка при отправке на сервер: {str(e)}")

            else:
                self.result_area.setText(f"Ошибка при запросе страницы: {response.status_code}")

        except Exception as e:
            self.result_area.setText(f"Произошла ошибка: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
