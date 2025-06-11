import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import Flask, jsonify, request, send_file
import mysql.connector
import json
import base64
from datetime import datetime
import io
import uuid
from PIL import Image
from mysql.connector import errorcode

application = Flask(__name__)


# Функция для преобразования объектов datetime в строки
def datetime_converter(o):
    if isinstance(o, datetime):
        return o.strftime('%Y-%m-%d %H:%M:%S')


@application.route("/")
def hello():
    return "<h1 style='color:black'>Hello There!</h1>"


@application.route("/users")
def get_users():
    try:
        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",  # или адрес вашего сервера
            user="u2784859_rest",  # имя пользователя базы данных
            password="pass-wrd-for-rest",  # пароль пользователя базы данных
            database="u2784859_milenaoptbd"  # имя базы данных
        )

        # Выполнение запроса
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()

        # Преобразование в JSON
        users_json = json.dumps(users, indent=4, default=datetime_converter)

        # Закрытие соединения
        cursor.close()
        conn.close()

        return jsonify(users_json)
    except mysql.connector.Error as err:
        print(f"Ошибка при подключении к базе данных: {err}")
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        print(f"Произошла неизвестная ошибка: {e}")
        return jsonify({"error": str(e)}), 500


@application.route('/add_user', methods=['POST'])
def add_user():
    try:
        # Получаем данные из POST-запроса
        data = request.get_json()
        name = data['name']
        username = data['username']
        phone = data['phone']
        password = data['password']  # Здесь рекомендуется использовать хэширование паролей!

        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",  # или адрес вашего сервера
            user="u2784859_rest",  # имя пользователя базы данных
            password="pass-wrd-for-rest",  # пароль пользователя базы данных
            database="u2784859_milenaoptbd"  # имя базы данных
        )
        cursor = conn.cursor()

        # Выполнение запроса на вставку
        sql = "INSERT INTO users (name, username, phone, password) VALUES (%s, %s, %s, %s)"
        val = (name, username, phone, password)
        cursor.execute(sql, val)
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': 'Пользователь добавлен успешно'}), 201
    except mysql.connector.Error as err:
        print(f"Ошибка при добавлении пользователя: {err}")
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        print(f"Произошла неизвестная ошибка: {e}")
        return jsonify({'error': str(e)}), 500


@application.route('/add_promotion', methods=['POST'])
def add_promotion():
    try:
        # Получаем данные из POST-запроса
        data = request.get_json()

        # Проверка на наличие всех необходимых данных
        if not all(k in data for k in ("start", "end", "name", "description", "image")):
            return jsonify({'error': 'Не все необходимые данные переданы'}), 400

        start = data['start']
        end = data['end']
        name = data['name']
        description = data['description']
        image_base64 = data['image']

        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",
            user="u2784859_rest",
            password="pass-wrd-for-rest",
            database="u2784859_milenaoptbd"
        )
        cursor = conn.cursor()

        # Сначала вставляем данные промоции в таблицу Promotion
        promotion_sql = "INSERT INTO Promotion (start, end, name, description) VALUES (%s, %s, %s, %s)"
        promotion_val = (start, end, name, description)
        cursor.execute(promotion_sql, promotion_val)
        promotion_id = cursor.lastrowid  # Получаем ID вставленной записи промоции

        # Декодирование base64 изображения
        image_data = base64.b64decode(image_base64)

        # Вставка изображения в таблицу PromotionImages с привязкой к promotion_id
        image_sql = "INSERT INTO PromotionImages (promotion_id, image) VALUES (%s, %s)"
        image_val = (promotion_id, image_data)
        cursor.execute(image_sql, image_val)

        # Подтверждаем транзакцию
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': 'Промоция и изображение добавлены успешно', 'promotion_id': promotion_id}), 201

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            error_message = "Неправильное имя пользователя или пароль"
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            error_message = "База данных не существует"
        else:
            error_message = f"Ошибка при добавлении промоции: {err}"
        print(error_message)
        return jsonify({'error': error_message}), 500
    except Exception as e:
        print(f"Произошла неизвестная ошибка: {e}")
        return jsonify({'error': str(e)}), 500


@application.route('/delete_promotion/<int:promotion_id>', methods=['DELETE'])
def delete_promotion(promotion_id):
    try:
        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",  # или адрес вашего сервера
            user="u2784859_rest",  # имя пользователя базы данных
            password="pass-wrd-for-rest",  # пароль пользователя базы данных
            database="u2784859_milenaoptbd"  # имя базы данных
        )
        cursor = conn.cursor()

        # Выполнение SQL-запроса для удаления промоции
        cursor.execute("DELETE FROM Promotion WHERE id = %s", (promotion_id,))
        conn.commit()

        # Проверка, была ли удалена промоция
        if cursor.rowcount > 0:
            response = {'message': 'Промоция успешно удалена.'}
            status_code = 200
        else:
            response = {'message': 'Промоция не найдена.'}
            status_code = 404

        # Закрытие соединения
        cursor.close()
        conn.close()

        return jsonify(response), status_code

    except mysql.connector.Error as err:
        print(f"Ошибка при удалении промоции: {err}")
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        print(f"Произошла неизвестная ошибка: {e}")
        return jsonify({'error': str(e)}), 500


@application.route('/delete_promotion', methods=['DELETE'])
def delete_promotion():
    try:
        # Получаем данные из DELETE-запроса
        data = request.get_json()

        # Проверка на наличие необходимого поля "name"
        if 'name' not in data:
            return jsonify({'error': 'Не указано название акции'}), 400

        name = data['name']

        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",
            user="u2784859_rest",
            password="pass-wrd-for-rest",
            database="u2784859_milenaoptbd"
        )
        cursor = conn.cursor()

        # Сначала удаляем записи из таблицы PromotionImages, связанные с акцией
        image_sql = """
        DELETE FROM PromotionImages
        WHERE promotion_id = (SELECT id FROM Promotion WHERE name = %s)
        """
        cursor.execute(image_sql, (name,))

        # Удаляем запись из таблицы Promotion по названию
        promotion_sql = "DELETE FROM Promotion WHERE name = %s"
        cursor.execute(promotion_sql, (name,))

        # Подтверждаем транзакцию
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': 'Акция успешно удалена'}), 200

    except mysql.connector.Error as err:
        error_message = f"Ошибка при удалении акции: {err}"
        print(error_message)
        return jsonify({'error': error_message}), 500
    except Exception as e:
        print(f"Произошла неизвестная ошибка: {e}")
        return jsonify({'error': str(e)}), 500


@application.route('/check_promotion', methods=['POST'])
def check_promotion():
    data = request.get_json()
    promotion_name = data.get('promotion_name')

    if not promotion_name:
        return jsonify({'error': 'promotion_name is required.'}), 400

    try:
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",  # или адрес вашего сервера
            user="u2784859_rest",  # имя пользователя базы данных
            password="pass-wrd-for-rest",  # пароль пользователя базы данных
            database="u2784859_milenaoptbd"  # имя базы данных
        )
        cursor = conn.cursor()

        # Проверка существования промоции по имени
        cursor.execute("SELECT * FROM Promotion WHERE name = %s", (promotion_name,))
        promotion = cursor.fetchone()

        cursor.close()
        conn.close()

        if promotion:
            response = {'message': 'Промоция существует.', 'promotion': promotion}
            return jsonify(response), 200
        else:
            return jsonify({'message': 'Промоция не найдена.'}), 404

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500


def fix_base64_padding(encoded_string):
    # Если длина строки не кратна 4, добавляем необходимые символы =
    missing_padding = len(encoded_string) % 4
    if missing_padding:
        encoded_string += '=' * (4 - missing_padding)
    return encoded_string


@application.route('/all_promotions', methods=['GET'])
def get_all_promotions():
    try:
        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",  # или адрес вашего сервера
            user="u2784859_rest",  # имя пользователя базы данных
            password="pass-wrd-for-rest",  # пароль пользователя базы данных
            database="u2784859_milenaoptbd"  # имя базы данных
        )
        cursor = conn.cursor()

        # Выполнение запроса к базе данных
        cursor.execute("SELECT start, end, name, description, image FROM Promotion")
        promotions = cursor.fetchall()

        # Формирование результата
        result = []
        for promotion in promotions:
            result.append({
                "start": promotion[0],
                "end": promotion[1],
                "name": promotion[2],
                "description": promotion[3],
                "image": (base64.b64decode(promotion[4])).decode('utf-8')
            })

        # Закрытие соединения
        cursor.close()
        conn.close()

        # Возвращаем результат в формате JSON
        return jsonify(result), 200

    except mysql.connector.Error as err:
        print(f"Ошибка при получении промоций: {err}")
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        print(f"Произошла неизвестная ошибка: {e}")
        return jsonify({'error': str(e)}), 500


@application.route('/login', methods=['POST'])
def login():
    try:
        # Получаем данные из POST-запроса
        data = request.get_json()
        username = data['username']
        password = data['password']

        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",  # или адрес вашего сервера
            user="u2784859_rest",  # имя пользователя базы данных
            password="pass-wrd-for-rest",  # пароль пользователя базы данных
            database="u2784859_milenaoptbd"  # имя базы данных
        )
        cursor = conn.cursor()

        # Выполнение запроса на проверку пользователя
        sql = "SELECT * FROM users WHERE username = %s AND password = %s"
        val = (username, password)
        cursor.execute(sql, val)
        user = cursor.fetchone()

        if user:
            # Успешная авторизация
            return jsonify({'message': 'Авторизация успешна'}), 200
        else:
            return jsonify({'error': 'Неверный логин или пароль'}), 401

    except mysql.connector.Error as err:
        print(f"Ошибка при авторизации пользователя: {err}")
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        print(f"Произошла неизвестная ошибка: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


def compress_image(image_data: bytes, target_width: int, target_height: int) -> bytes:
    """
    Сжимает изображение до заданных размеров.
    :param image_data: Исходное изображение в формате байтов
    :param target_width: Ширина для сжатого изображения
    :param target_height: Высота для сжатого изображения
    :return: Сжатое изображение в формате байтов
    """
    image = Image.open(io.BytesIO(image_data))
    image = image.resize((target_width, target_height), Image.ANTIALIAS)

    output = io.BytesIO()
    image.save(output, format='JPEG', quality=85)
    return output.getvalue()


@application.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        data = request.json
        image_base64 = data.get('image')

        if not image_base64:
            return jsonify({'error': 'No image data provided'}), 400

        # Декодирование base64
        image_data = base64.b64decode(image_base64)

        # Сжатие изображения
        compressed_image_data = compress_image(image_data, 800, 600)  # Уменьшить до 800x600

        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",
            user="u2784859_rest",
            password="pass-wrd-for-rest",
            database="u2784859_milenaoptbd"
        )
        cursor = conn.cursor()

        sql = "INSERT INTO PromotionImages (image) VALUES (%s)"
        cursor.execute(sql, (compressed_image_data,))

        conn.commit()
        image_id = cursor.lastrowid

        cursor.close()
        conn.close()

        return jsonify({'id': image_id}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@application.route('/image/<image_id>', methods=['GET'])
def get_image(image_id):
    conn = mysql.connector.connect(
        host="server17.hosting.reg.ru",
        user="u2784859_rest",
        password="pass-wrd-for-rest",
        database="u2784859_milenaoptbd"
    )
    cursor = conn.cursor()

    cursor.execute("SELECT image FROM PromotionImages WHERE id = %s", (image_id,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result:
        image_data = result[0]
        return send_file(io.BytesIO(image_data), mimetype='image/jpg')
    else:
        return jsonify({'error': 'Image not found'}), 404


@application.route('/update_user', methods=['PUT'])
def update_user():
    try:
        # Получаем данные из PUT-запроса
        data = request.get_json()

        current_username = data.get('current_username')
        new_username = data.get('new_username')
        name = data.get('name')
        phone = data.get('phone')

        if not current_username:
            return jsonify({'error': 'Не указано текущее имя пользователя'}), 400

        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",
            user="u2784859_rest",
            password="pass-wrd-for-rest",
            database="u2784859_milenaoptbd"
        )
        cursor = conn.cursor()

        # Формируем SQL-запрос на обновление
        update_fields = []
        update_values = []

        if new_username:
            update_fields.append("username = %s")
            update_values.append(new_username)

        if name:
            update_fields.append("name = %s")
            update_values.append(name)

        if phone:
            update_fields.append("phone = %s")
            update_values.append(phone)

        if not update_fields:
            return jsonify({'error': 'Нет данных для обновления'}), 400

        update_values.append(current_username)
        sql = f"UPDATE users SET {', '.join(update_fields)} WHERE username = %s"

        cursor.execute(sql, tuple(update_values))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': 'Пользовательские данные обновлены успешно'}), 200
    except mysql.connector.Error as err:
        print(f"Ошибка при обновлении пользователя: {err}")
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        print(f"Произошла неизвестная ошибка: {e}"), 500


@application.route('/get_user_info', methods=['GET'])
def get_user_info():
    try:
        # Получаем параметр username из запроса
        username = request.args.get('username')

        if not username:
            return jsonify({'error': 'Имя пользователя не указано'}), 400

        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",
            user="u2784859_rest",
            password="pass-wrd-for-rest",
            database="u2784859_milenaoptbd"
        )
        cursor = conn.cursor()

        # Выполнение SQL-запроса для получения информации о пользователе
        sql = "SELECT name, username, phone, is_admin FROM users WHERE username = %s"
        cursor.execute(sql, (username,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            user_info = {
                'name': result[0],
                'username': result[1],
                'phone': result[2],
                'is_admin': result[3]
            }
            return jsonify(user_info), 200
        else:
            return jsonify({'error': 'Пользователь не найден'}), 404

    except mysql.connector.Error as err:
        print(f"Ошибка при получении информации о пользователе: {err}")
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        print(f"Произошла неизвестная ошибка: {e}")
        return jsonify({'error': str(e)}), 500


@application.route('/add_product', methods=['POST'])
def add_product():
    try:
        # Получаем данные из POST-запроса
        data = request.get_json()

        # Проверка на наличие всех необходимых данных
        required_fields = ["name", "priceLow", "priceHigh", "article", "description", "number",
                           "country", "type", "selectedOption", "selectedSizes", "selectedColors",
                           "selectedMaterials", "selectedSeasons", "isNew", "isHit", "images"]
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Не все необходимые данные переданы'}), 400

        # Извлекаем данные
        name = data['name']
        priceLow = data['priceLow']
        priceHigh = data['priceHigh']
        article = data['article']
        description = data['description']
        number = data['number']
        country = data['country']
        type_ = data['type']
        selectedOption = data['selectedOption']
        selectedSizes = ','.join(data['selectedSizes'])  # Преобразуем списки в строки
        selectedColors = ','.join(data['selectedColors'])
        selectedMaterials = ','.join(data['selectedMaterials'])
        selectedSeasons = ','.join(data['selectedSeasons'])
        isNew = data['isNew']
        isHit = data['isHit']
        images = data['images']

        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",
            user="u2784859_rest",
            password="pass-wrd-for-rest",
            database="u2784859_milenaoptbd"
        )
        cursor = conn.cursor()

        # Вставка данных продукта в таблицу Products
        product_sql = """
            INSERT INTO Products 
            (name, price_low, price_high, article, description, number, country, type, selected_option, 
             selected_sizes, selected_colors, selected_materials, selected_seasons, new, hit)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        product_val = (name, priceLow, priceHigh, article, description, number, country, type_,
                       selectedOption, selectedSizes, selectedColors, selectedMaterials, selectedSeasons, isNew, isHit)
        cursor.execute(product_sql, product_val)
        product_id = cursor.lastrowid  # Получаем ID вставленной записи продукта

        # Обработка изображений
        for image_base64 in images:
            try:
                # Декодируем и сжимаем изображение
                image_data = base64.b64decode(image_base64)
                compressed_image_data = compress_image(image_data, 1200, 1600)
            except Exception as e:
                print(f"Ошибка при декодировании изображения: {e}")
                return jsonify({'error': 'Ошибка при декодировании изображения'}), 400

            # Вставка изображения в таблицу ProductImages с привязкой к product_id
            image_sql = "INSERT INTO ProductImages (product_id, image) VALUES (%s, %s)"
            image_val = (product_id, compressed_image_data)
            cursor.execute(image_sql, image_val)

        # Подтверждаем транзакцию
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': 'Продукт и изображения добавлены успешно', 'product_id': product_id}), 201

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            error_message = "Неправильное имя пользователя или пароль"
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            error_message = "База данных не существует"
        else:
            error_message = f"Ошибка при добавлении продукта: {err}"
        print(error_message)
        return jsonify({'error': error_message}), 500
    except Exception as e:
        print(f"Произошла неизвестная ошибка: {e}")
        return jsonify({'error': str(e)}), 500


@application.route('/product_image/<int:image_id>', methods=['GET'])
def get_product_image(image_id):
    try:
        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",
            user="u2784859_rest",
            password="pass-wrd-for-rest",
            database="u2784859_milenaoptbd"
        )
        cursor = conn.cursor()

        # Выполнение запроса к базе данных
        cursor.execute("SELECT image FROM ProductImages WHERE id = %s", (image_id,))
        result = cursor.fetchone()

        # Закрытие соединения
        cursor.close()
        conn.close()

        if result:
            image_data = result[0]
            return send_file(io.BytesIO(image_data), mimetype='image/jpeg')
        else:
            return jsonify({'error': 'Image not found'}), 404

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({'error': 'Unexpected error'}), 500


@application.route('/products', methods=['GET'])
def get_all_products():
    try:
        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",
            user="u2784859_rest",
            password="pass-wrd-for-rest",
            database="u2784859_milenaoptbd"
        )
        cursor = conn.cursor()

        # Получение всех продуктов
        cursor.execute("""
            SELECT id, name, price_low, price_high, article, description, number, country, type,
                   selected_option, selected_sizes, selected_colors, selected_materials, selected_seasons, new, hit
            FROM Products
        """)
        products = cursor.fetchall()

        all_products = []

        # URL для получения изображений
        base_url = "https://rst-for-milenaopt.ru/product_image/"

        for product in products:
            product_id = product[0]
            product_data = {
                'id': product_id,
                'name': product[1],
                'priceLow': product[2],
                'priceHigh': product[3],
                'article': product[4],
                'description': product[5],
                'number': product[6],
                'country': product[7],
                'type': product[8],
                'selectedOption': product[9],
                'selectedSizes': product[10].split(',') if product[10] else [],
                'selectedColors': product[11].split(',') if product[11] else [],
                'selectedMaterials': product[12].split(',') if product[12] else [],
                'selectedSeasons': product[13].split(',') if product[13] else [],
                'isNew': product[14],
                'isHit': product[15]
            }

            # Получение изображений для текущего продукта
            cursor.execute("SELECT id FROM ProductImages WHERE product_id = %s", (product_id,))
            images = cursor.fetchall()

            # Формируем список URL-ов изображений
            image_urls = [base_url + str(image_id[0]) for image_id in images]
            product_data['images'] = image_urls

            all_products.append(product_data)

        cursor.close()
        conn.close()

        return jsonify(all_products)

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({'error': str(e)}), 500


@application.route('/get_product/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    try:
        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",
            user="u2784859_rest",
            password="pass-wrd-for-rest",
            database="u2784859_milenaoptbd"
        )
        cursor = conn.cursor()

        # Получение всех продуктов
        cursor.execute("""
            SELECT id, name, price_low, price_high, article, description, number, country, type,
                   selected_option, selected_sizes, selected_colors, selected_materials, selected_seasons, new, hit
            FROM Products WHERE id = %s
        """, (product_id,))
        product = cursor.fetchone()

        all_products = []

        # URL для получения изображений
        base_url = "https://rst-for-milenaopt.ru/product_image/"
        product_id = product[0]
        product_data = {
            'id': product_id,
            'name': product[1],
            'priceLow': product[2],
            'priceHigh': product[3],
            'article': product[4],
            'description': product[5],
            'number': product[6],
            'country': product[7],
            'type': product[8],
            'selectedOption': product[9],
            'selectedSizes': product[10].split(',') if product[10] else [],
            'selectedColors': product[11].split(',') if product[11] else [],
            'selectedMaterials': product[12].split(',') if product[12] else [],
            'selectedSeasons': product[13].split(',') if product[13] else [],
            'isNew': product[14],
            'isHit': product[15]
        }

        # Получение изображений для текущего продукта
        cursor.execute("SELECT id FROM ProductImages WHERE product_id = %s", (product_id,))
        images = cursor.fetchall()

        # Формируем список URL-ов изображений
        image_urls = [base_url + str(image_id[0]) for image_id in images]
        product_data['images'] = image_urls

        cursor.close()
        conn.close()

        return jsonify(product_data)

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({'error': str(e)}), 500


@application.route('/create_order', methods=['POST'])
def create_order():
    try:
        # Получаем данные из POST-запроса
        data = request.get_json()

        # Получаем данные из запроса
        name = data.get('name')
        phone = data.get('phone')
        login = data.get('login')
        product_ids = data.get('product_ids')  # Ожидаем строку с id через запятую
        amounts = data.get('amounts')          # Ожидаем строку с количествами через запятую
        type_ = data.get('type')
        selected_sum = data.get('selected_sum')
        final_price = data.get('final_price')
        status = data.get('status', 'создан')

        if not (name and phone and login and product_ids and amounts and type_ and selected_sum and final_price):
            return jsonify({'error': 'Некоторые поля отсутствуют'}), 400

        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",
            user="u2784859_rest",
            password="pass-wrd-for-rest",
            database="u2784859_milenaoptbd"
        )
        cursor = conn.cursor()

        # SQL-запрос для вставки нового заказа
        sql = """
        INSERT INTO orders (name, phone, login, product_ids, amounts, type, selected_sum, final_price, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (name, phone, login, product_ids, amounts, type_, selected_sum, final_price, status))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': 'Заказ создан успешно'}), 200
    except mysql.connector.Error as err:
        print(f"Ошибка при создании заказа: {err}")
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        print(f"Произошла неизвестная ошибка: {e}")
        return jsonify({'error': str(e)}), 500


@application.route('/get_orders_by_login', methods=['GET'])
def get_orders_by_login():
    try:
        # Получаем логин из параметров запроса
        login = request.args.get('login')
        if not login:
            return jsonify({'error': 'Логин не предоставлен'}), 400

        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",
            user="u2784859_rest",
            password="pass-wrd-for-rest",
            database="u2784859_milenaoptbd"
        )
        cursor = conn.cursor(dictionary=True)

        # SQL-запрос для получения всех заказов пользователя по логину
        sql = "SELECT * FROM orders WHERE login = %s"
        cursor.execute(sql, (login,))
        orders = cursor.fetchall()

        cursor.close()
        conn.close()

        if not orders:
            return jsonify({'message': 'Заказы не найдены для данного логина'}), 404

        return jsonify(orders), 200
    except mysql.connector.Error as err:
        print(f"Ошибка при получении заказов: {err}")
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        print(f"Произошла неизвестная ошибка: {e}")
        return jsonify({'error': str(e)}), 500


@application.route('/get_orders', methods=['GET'])
def get_orders_by_login():
    try:

        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",
            user="u2784859_rest",
            password="pass-wrd-for-rest",
            database="u2784859_milenaoptbd"
        )
        cursor = conn.cursor(dictionary=True)

        # SQL-запрос для получения всех заказов пользователя по логину
        sql = "SELECT * FROM orders WHERE status = 'создан'"
        cursor.execute(sql)
        orders = cursor.fetchall()

        cursor.close()
        conn.close()

        if not orders:
            return jsonify({'message': 'Заказы не найдены'}), 404

        return jsonify(orders), 200
    except mysql.connector.Error as err:
        print(f"Ошибка при получении заказов: {err}")
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        print(f"Произошла неизвестная ошибка: {e}")
        return jsonify({'error': str(e)}), 500


@application.route('/update_order_status', methods=['POST'])
def update_order_status():
    try:
        # Получаем данные из POST-запроса
        data = request.get_json()
        order_id = data.get('id')
        new_status = data.get('status')

        if not (order_id and new_status):
            return jsonify({'error': 'Необходимо указать ID заказа и новый статус'}), 400

        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",
            user="u2784859_rest",
            password="pass-wrd-for-rest",
            database="u2784859_milenaoptbd"
        )
        cursor = conn.cursor()

        # SQL-запрос для обновления статуса заказа
        sql = "UPDATE orders SET status = %s WHERE id = %s"
        cursor.execute(sql, (new_status, order_id))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': 'Статус заказа обновлен успешно'}), 200
    except mysql.connector.Error as err:
        print(f"Ошибка при обновлении статуса заказа: {err}")
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        print(f"Произошла неизвестная ошибка: {e}")
        return jsonify({'error': str(e)}), 500


def send_order_email(order_data):
    # Шаблон HTML-письма
    html = """
    <html>
    <body>
        <h2>Новый заказ</h2>
        <p><b>Имя:</b> {name}</p>
        <p><b>Телефон:</b> {phone}</p>
        <p><b>Логин:</b> {login}</p>
        <h3>Товары:</h3>
        <ul>
        {% for product, amount in zip(product_ids, amounts) %}
            <li>{product} - {amount}</li>
        {% endfor %}
        </ul>
        <p><b>Итоговая сумма:</b> {final_price}</p>
    </body>
    </html>
    """
    sender_email = "FUTUREstudio.ru@yandex.ru"
    sender_password = "ldzobwdjgbrmedcv"
    recipient_email = "madara.lsog610@gmail.com"
    # Подготовка данных для шаблона
    products_with_amounts = order_data['product_ids'].split(','), order_data['amounts'].split(',')
    context = {
        'name': order_data['name'],
        'phone': order_data['phone'],
        # ... остальные поля ...
        'products_with_amounts': products_with_amounts,
        'final_price': order_data['final_price']
    }

    # Замена плейсхолдеров в шаблоне
    # Подготовка данных для шаблона
    message = MIMEText(
        f"Имя заказчика: {order_data['name']}\nНомер телефона: {order_data['phone']}\nКомментарий: {order_data['comment']}\nСумма: {order_data['final_price']}")
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = f"Новый заказ от {order_data['login']}"

    part1 = MIMEText(html.format(**context), 'html')
    message.attach(part1)

    # Отправка письма
    with smtplib.SMTP('smtp.yandex.ru', 587) as s:
        s.starttls()
        s.login(sender_email, sender_password)
        s.sendmail(sender_email, recipient_email, message.as_string())


@application.route('/delete_order', methods=['DELETE'])
def delete_order():
    try:
        # Получаем ID заказа из параметров запроса
        order_id = request.args.get('id')

        if not order_id:
            return jsonify({'error': 'ID заказа не предоставлен'}), 400

        # Подключение к базе данных
        conn = mysql.connector.connect(
            host="server17.hosting.reg.ru",
            user="u2784859_rest",
            password="pass-wrd-for-rest",
            database="u2784859_milenaoptbd"
        )
        cursor = conn.cursor()

        # SQL-запрос для удаления заказа
        sql = "DELETE FROM orders WHERE id = %s"
        cursor.execute(sql, (order_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'message': 'Заказ успешно удален'}), 200
    except mysql.connector.Error as err:
        print(f"Ошибка при удалении заказа: {err}")
        return jsonify({'error': str(err)}), 500
    except Exception as e:
        print(f"Произошла неизвестная ошибка: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    application.run(host='0.0.0.0')
