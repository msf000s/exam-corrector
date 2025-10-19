from flask import Flask, request, jsonify, send_from_directory
import os
import json
from datetime import datetime
import traceback

app = Flask(__name__, static_folder='static')

# التأكد من وجود المجلدات
os.makedirs('static', exist_ok=True)

# ⚙️ تحميل الإجابات الصحيحة
def load_answer_key():
    try:
        if os.path.exists('answer_key.json'):
            with open('answer_key.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('answers', [])
    except:
        pass
    return ['B', 'C', 'A', 'D', 'B', 'A', 'C', 'D', 'A', 'B']

def save_answer_key(answers):
    """حفظ الإجابات الصحيحة في ملف"""
    try:
        with open('answer_key.json', 'w', encoding='utf-8') as f:
            json.dump({'answers': answers, 'updated': datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ خطأ في حفظ الإجابات: {e}")

ANSWER_KEY = load_answer_key()

@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/api/health', methods=['GET'])
def health_check():
    """فحص حالة الخادم"""
    return jsonify({
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "answer_key_count": len(ANSWER_KEY),
        "python_version": "3.10.8"
    })

@app.route('/api/answer_key', methods=['GET', 'POST'])
def handle_answer_key():
    """إدارة الإجابات الصحيحة"""
    global ANSWER_KEY
    
    if request.method == 'GET':
        return jsonify({
            "answers": ANSWER_KEY,
            "count": len(ANSWER_KEY)
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            new_answers = data.get('answers', [])
            
            if new_answers:
                ANSWER_KEY = new_answers
                save_answer_key(new_answers)
                
                return jsonify({
                    "success": True,
                    "message": f"تم تحديث {len(ANSWER_KEY)} إجابة صحيحة",
                    "answers": ANSWER_KEY
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "لم يتم تقديم إجابات صحيحة"
                }), 400
                
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"خطأ في تحديث الإجابات: {str(e)}"
            }), 500

@app.route('/api/correct', methods=['POST'])
def correct():
    """تصحيح ورقة الإجابة (نسخة مبسطة للاختبار)"""
    try:
        print("🚀 بدء عملية التصحيح...")
        
        # الحصول على المعلمات
        num_questions = request.form.get('num_questions', default=len(ANSWER_KEY), type=int)
        
        # التحقق من وجود الملف
        if 'image' not in request.files:
            return jsonify({"error": "لم يتم تقديم صورة"}), 400
            
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "لم يتم اختيار ملف"}), 400
        
        print(f"📁 معالجة الصورة: {file.filename}")
        
        # في هذه النسخة المبسطة، نستخدم OpenCV إذا كان متاحاً
        try:
            import cv2
            import numpy as np
            import imutils
            
            # قراءة الصورة
            nparr = np.frombuffer(file.read(), np.uint8)
            original_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if original_img is None:
                return jsonify({"error": "فشل في قراءة الصورة"}), 400
            
            print(f"📐 أبعاد الصورة: {original_img.shape}")
            
            # محاكاة عملية التصحيح
            student_answers = simulate_correction(num_questions)
            
        except ImportError:
            print("⚠️ OpenCV غير متاح، استخدام المحاكاة")
            student_answers = simulate_correction(num_questions)
        
        # حساب النتائج
        correct_count = sum(1 for s, c in zip(student_answers, ANSWER_KEY[:num_questions]) if s == c)
        wrong_count = num_questions - correct_count
        percentage = round((correct_count / num_questions) * 100) if num_questions > 0 else 0
        
        print(f"📊 النتائج: {correct_count} صحيحة، {wrong_count} خاطئة، {percentage}%")
        
        # تحضير الاستجابة
        response = {
            "success": True,
            "answers": student_answers,
            "correct_count": correct_count,
            "wrong_count": wrong_count,
            "percentage": percentage,
            "total_questions": num_questions,
            "timestamp": datetime.now().isoformat(),
            "note": "هذه نسخة مبسطة للتجربة"
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ خطأ في التصحيح: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"خطأ في معالجة الصورة: {str(e)}"
        }), 500

def simulate_correction(num_questions):
    """محاكاة عملية التصحيح (للاختبار فقط)"""
    import random
    options = ['A', 'B', 'C', 'D', 'فراغ']
    
    # إنشاء إجابات تحاكي النمط الحقيقي (ليست عشوائية تماماً)
    answers = []
    for i in range(num_questions):
        # محاكاة أن معظم الطلاب يجيبون بشكل صحيح على بعض الأسئلة
        if i < len(ANSWER_KEY) and random.random() > 0.3:  # 70% إجابة صحيحة
            answers.append(ANSWER_KEY[i])
        else:
            # 30% إجابة خاطئة أو فارغة
            if random.random() > 0.2:  # 80% إجابة خاطئة
                wrong_options = [opt for opt in options if opt != ANSWER_KEY[i] and opt != 'فراغ']
                answers.append(random.choice(wrong_options))
            else:  # 20% إجابة فارغة
                answers.append('فراغ')
    
    return answers

# إصلاح مشكلة CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    
    print(f"🚀 بدء تشغيل تطبيق تصحيح الاختبارات...")
    print(f"📊 عدد الإجابات الصحيحة: {len(ANSWER_KEY)}")
    print(f"🐍 إصدار Python: 3.10.8")
    print(f"🌐 الخادم يعمل على: http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=False)