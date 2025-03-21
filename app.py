import os
import logging
from flask import Flask, render_template, request, send_file, jsonify
from dotenv import load_dotenv
from gemini import call_gemini_api
from plantuml_generator import generate_plantuml_image
from uml_include_replacer import replace_includes  # 새 모듈 임포트

# .env 파일에서 환경변수를 로드합니다.
load_dotenv()

# 'Front' 폴더 내의 static 및 templates 경로 지정
static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Front', 'static')
template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Front', 'templates')

app = Flask(__name__, static_folder=static_folder, template_folder=template_folder)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

# 로깅 설정
logging.basicConfig(level=logging.INFO)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_diagram():
    """
    클라이언트에서 전달된 JSON 데이터({ "input": "..." })를 받아 Gemini API를 통해 PlantUML 코드를 생성한 후,
    포함(include) 지시문을 치환하고, Docker를 사용해 UML 다이어그램 이미지를 생성하여 반환합니다.
    """
    data = request.get_json()
    if not data or "input" not in data:
        logging.error("입력 데이터가 올바르지 않습니다: %s", data)
        return jsonify({"error": "입력 데이터가 올바르지 않습니다."}), 400

    user_input = data["input"]
    logging.info("Received prompt: %s", user_input)
    
    try:
        # 1. Gemini API 호출하여 PlantUML 코드 생성
        plantuml_code = call_gemini_api(user_input)
        logging.info("Generated PlantUML Code:\n%s", plantuml_code)

        # 1.5. UML 코드 내의 include 지시문 치환
        modified_code = replace_includes(plantuml_code)
        logging.info("Modified PlantUML Code:\n%s", modified_code)

        # 2. 수정된 PlantUML 코드를 이미지로 변환
        image_path = generate_plantuml_image(modified_code)
        logging.info("Generated image at path: %s", image_path)
        
        # 3. 생성된 이미지 파일을 클라이언트에 반환
        abs_image_path = os.path.abspath(image_path)
        return send_file(abs_image_path, mimetype="image/png")

    except Exception as e:
        logging.exception("Error generating diagram")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
