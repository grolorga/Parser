from PIL import Image
import io
import base64

def fix_base64_padding(encoded_string):
    # Если длина строки не кратна 4, добавляем необходимые символы =
    missing_padding = len(encoded_string) % 4
    if missing_padding:
        encoded_string += '=' * (4 - missing_padding)
    return encoded_string

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf8mb4')
    return encoded_string


def decode_base64_string_to_image(encoded_string, output_file):
    try:
        encoded_string = fix_base64_padding(encoded_string)
        decoded_bytes = base64.b64decode(encoded_string)

        if len(decoded_bytes) == 0:
            print("Decoded bytes are empty. Likely an issue with the Base64 string.")
            return

        image = Image.open(io.BytesIO(decoded_bytes))
        image.save(output_file)
        print(f"Image saved to '{output_file}'")

    except Exception as e:
        print("Failed to decode Base64 string or create image. Error:", str(e))


# Пример создания Base64 из изображения
encoded_string = encode_image_to_base64("C:/Users/Marat/Pictures/2.jpg")  # Замените на путь к вашему изображению
decode_base64_string_to_image(encoded_string, "venv/output_image.png")