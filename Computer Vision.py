
import os
import base64
from io import BytesIO
from PIL import Image
import google.generativeai as genai


os.environ["GEMINI_API_KEY"] = "AIzaSyBqmRouG7ExZh-IFRgdxt4OFn3cBJll8nM"

# تهيئة الموديل
model = genai.GenerativeModel('gemini-1.5-flash')


def analyze_food_image(image_path: str) -> str:
    """
    يحلل صورة طعام باستخدام Google Gemini API
    ويعطي تقدير للسعرات الحرارية + نصائح غذائية.
    """
    # فتح الصورة كـ bytes
    with open(image_path, "rb") as image_file:
        image_bytes = image_file.read()

    # تحويل Base64
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    # إعداد المحتوى
    contents = [
        {
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": encoded_image
            }
        },
        {
            "text": (
                "You are a certified nutritionist. Carefully analyze this food image. "
                "List each food item you see, estimate the calories for each item and the total calories. "
                "Include portion size estimates and any basic nutrition advice for a healthy diet. "
                "Respond in clear, concise language suitable for a user who wants to track their daily intake."
            )
        }
    ]

    # استدعاء Gemini
    response = model.generate_content(contents)

    # إرجاع النتيجة
    if hasattr(response, 'text'):
        return response.text.strip()
    else:
        return "❌ لم أستطع الحصول على نص من النموذج. تأكد من الصورة وحاول مرة أخرى."


if __name__ == "__main__":
    # تشغيل من التيرمنال
    image_path = input("ادخل مسار الصورة (مثال: food.jpg): ").strip()
    if not os.path.exists(image_path):
        print("❌ الملف غير موجود")
    else:
        result = analyze_food_image(image_path)
        print("\n===== نتيجة التحليل =====\n")
        print(result)
