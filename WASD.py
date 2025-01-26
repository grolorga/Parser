import base64
import json
import re

import requests
from bs4 import BeautifulSoup


def generate_page_links(base_url, last_page_number):
    page_links = []
    for page_number in range(last_page_number, 0, -1):
        page_url = f"{base_url}?PAGEN_1={page_number}"
        page_links.append(page_url)
    return page_links


def all_links_from_page(page_url):
    links = []
    # Отправляем запрос на сервер
    response = requests.get(page_url)

    # Проверяем успешность запроса
    if response.status_code == 200:
        # Парсим HTML с помощью BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        # Поиск всех тегов <a> с классом "thumb"
        link_tags = soup.find_all('a', class_='thumb')
        # Извлечение всех ссылок на продукты
        product_links = [base_url + tag.get('href') for tag in link_tags if tag.get('href')]
        return product_links


def send_to_api(product_url):
    if not product_url:
        print("URL не указано")
        return

    print("Обработка запроса...")

    try:
        response = requests.get(product_url)
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
                "type": "Товары для бани",
                "selectedOption": characteristics.get("Категория", ""),
                "selectedSizes": sizes,
                "selectedColors": [characteristics.get("Цвет", "В ассортименте")],
                "selectedMaterials": [characteristics.get("Состав", "")],
                "selectedSeasons": "",  # Возможно, будет пустым, поэтому список
                "isNew": False,
                "isHit": False
            }

            # Отображаем преобразованные данные
            print(json.dumps(product_data, ensure_ascii=False, indent=4))

            # URL сервера, куда нужно отправить данные
            server_url = "https://rst-for-milenaopt.ru/add_product"  # Замените на ваш URL

            # Отправляем данные на сервер
            try:
                headers = {'Content-Type': 'application/json'}
                response = requests.post(server_url, json=product_data, headers=headers)
                if response.status_code == 201:
                    print("\nДанные успешно отправлены на сервер.")
                else:
                    print(
                        f"\nОшибка при отправке данных: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"\nОшибка при отправке на сервер: {str(e)}")

        else:
            print(f"Ошибка при запросе страницы: {response.status_code}")

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")


# URL страницы (замени на нужную ссылку)
#url = 'https://opt-milena.ru/product-category/muzhskaya-odezhda-krupnyj-opt/' мужская одежда готово
#url = 'https://opt-milena.ru/product-category/zhenskaya-odezhda-krupnyj-opt/'  Женская одежда готово
#url = 'https://opt-milena.ru/product-category/odezhda_premium_klassa/' # Одежда Premium готово
#url = 'https://opt-milena.ru/product-category/detskaya-odezhda-krupnyj-opt/' # Детская одежда готово

#url = 'https://opt-milena.ru/product-category/odezhda_po_razmeram/' Одежда по размерам готово
#url = 'https://opt-milena.ru/product-category/obuv/' # Обувь готово
#url = 'https://opt-milena.ru/product-category/tekstil-dlya-doma/'  Для дома готово
#url = 'https://opt-milena.ru/product-category/aksessuary/'  Аксессуары готово
#url = 'https://opt-milena.ru/product-category/otdykh-razvlecheniya/'  Отдых - Развлечения готово
#url = 'https://opt-milena.ru/product-category/kantselyarskie-tovary/'  Канцелярские товары готово
#url = 'https://opt-milena.ru/product-category/spetsodezhda/' Спецодежда готово
url = 'https://opt-milena.ru/product-category/tovary-dlya-bani/' #Товары для бани готово

# Базовый URL сайта (замените на реальный URL сайта)
base_url = "https://opt-milena.ru"
# Отправляем запрос на сервер
response = requests.get(url)
all_products=[]

# Проверяем успешность запроса
if response.status_code == 200:
    # Парсим HTML с помощью BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    link_pages = soup.find_all('a', class_='dark_link')
    pages_links = [base_url + page.get('href') for page in link_pages if page.get('href')]
    last_page_number = 1
    # Находим последний элемент <a> с классом 'dark_link' используя XPath
    last_link = soup.select_one('div.nums a.dark_link:last-child')
    if last_link:
        href = last_link.get('href')
        print("Последняя ссылка:", base_url + last_link.get('href'))
        # Регулярное выражение, чтобы найти все после PAGEN_1=
        match = re.search(r'PAGEN_1=(\d+)', href)
        if match:
            last_page_number = int(match.group(1))
            print("Последний номер страницы:", last_page_number)
            all_links = generate_page_links(url, last_page_number)
            i = 0
            for link in all_links:
                print(f"Зедсь в {i+1} раз")
                i+=1
                all_products.extend(all_links_from_page(link))
        else:
            print("Не удалось извлечь номер страницы")
    else:
        all_products.extend(all_links_from_page(url))
    for index, link in enumerate(all_products, start=1):
        print(f"Ссылка на товар {index}: {link}")
    itera = 1
    allLen = len(all_products)
    for prod_url in all_products:
        send_to_api(prod_url)
        print(f"Прогресс {itera}/{allLen}")
        itera += 1
