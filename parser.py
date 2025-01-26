import os
import requests
from bs4 import BeautifulSoup

# URL страницы (замени на нужную ссылку)
url = 'https://opt-milena.ru/product/rubashka_zhenskaya_belaya_so_shnurovkoy_i_volanami_len_r_r_42_44/'
#url = 'https://opt-milena.ru/product/zhenskiy-sportivnyy-kostyum-s-kapyushonom-zamok-flis-r-r-48-56/'
# Отправляем запрос на сервер
response = requests.get(url)

# Проверяем успешность запроса
if response.status_code == 200:
    # Парсим HTML с помощью BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Отладочный вывод HTML
    # print(soup.prettify())

    # Извлекаем название товара
    title = soup.find('h1', id='pagetitle')  # Проверьте правильность селектора
    if title:
        title = title.get_text(strip=True)
        print(f"Название: {title}")
    else:
        print("Название не найдено")

    # Папка для сохранения изображений
    save_folder = 'images'
    os.makedirs(save_folder, exist_ok=True)

    # Извлекаем все изображения
    image_tags = soup.find_all('img', class_='product-detail-gallery__picture')

    # Отладочный вывод всех тегов изображений
    for img in image_tags:
        print(img)

    # Собираем все ссылки на изображения
    image_urls = set()

    for img in image_tags:
        # Получаем URL изображения из атрибута data-src или src
        img_url = img.get('data-src') or img.get('src')

        # Обрабатываем URL, добавляя домен, если он отсутствует
        if img_url and img_url.startswith('/'):
            img_url = 'https://opt-milena.ru' + img_url

        # Добавляем URL в множество уникальных ссылок
        if img_url:
            image_urls.add(img_url)

    # Скачиваем и сохраняем уникальные изображения
    for idx, img_url in enumerate(image_urls):
        # Скачиваем изображение
        response = requests.get(img_url)

        # Определяем имя файла для сохранения
        file_extension = img_url.split('.')[-1]  # Получаем расширение файла
        file_name = f'image_{idx}.{file_extension}'
        file_path = os.path.join(save_folder, file_name)

        # Сохраняем изображение в файл
        with open(file_path, 'wb') as file:
            file.write(response.content)

        print(f'Сохранено изображение: {file_path}')

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
            print("Характеристики:")
            for k, v in characteristics.items():
                print(f"  {k}: {v}")
        else:
            print("Характеристики не найдены")
    else:
        print("Контейнер характеристик не найден")

    # Извлекаем цену за мелкий опт
    try:
        small_opt_price_block = soup.find('div', class_='price_group')
        if small_opt_price_block:
            small_opt_price = small_opt_price_block.find('div', class_='price').get_text(strip=True)
            print(f"Мелкий опт: {small_opt_price}")
        else:
            print("Блок цены за мелкий опт не найден")
    except AttributeError:
        print("Не удалось извлечь цену за мелкий опт")

    # Извлекаем цену за крупный опт
    try:
        large_opt_price_block = soup.find('div', class_='price_group min')
        if large_opt_price_block:
            large_opt_price = large_opt_price_block.find('div', class_='price').get_text(strip=True)
            print(f"Крупный опт: {large_opt_price}")
        else:
            print("Блок цены за крупный опт не найден")
    except AttributeError:
        print("Не удалось извлечь цену за крупный опт")

else:
    print(f"Ошибка при запросе страницы: {response.status_code}")