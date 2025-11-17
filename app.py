from flask import Flask, request, jsonify
from database import SessionLocal, init_db
import pandas as pd
import os
from pathlib import Path

app = Flask(__name__)

@app.route('/')
def home():
    return "Database initialized."

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Файл не найден"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Имя файла пустое"}), 400

    # Сохраняем файл
    filename = str(os.urandom(8).hex()) + Path(file.filename).suffix
    filepath = os.path.join('uploads', filename)
    os.makedirs('uploads', exist_ok=True)
    file.save(filepath)

    # Читаем файл
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(filepath)
        else:
            return jsonify({"error": "Поддерживается только CSV и Excel"}), 415
    except Exception as e:
        return jsonify({"error": f"Ошибка чтения файла: {str(e)}"}), 400

    # Анализируем данные
    mean_val = df.mean(numeric_only=True).to_dict()
    median_val = df.median(numeric_only=True).to_dict()
    corr = df.corr(numeric_only=True).round(3).to_json()

    # Очистка данных
    duplicates_before = len(df)
    df.drop_duplicates(inplace=True)
    duplicates_after = len(df)
    duplicates_removed = duplicates_before - duplicates_after

    # Заполнение пропусков
    missing_before = df.isnull().sum().sum()
    df.fillna(df.mean(numeric_only=True), inplace=True)
    missing_after = df.isnull().sum().sum()
    missing_filled = missing_before - missing_after

    # Сохраняем результаты
    db = SessionLocal()
    db.close()

    return jsonify({
        "message": "Файл успешно загружен",
        "filename": filename,
        "analysis_summary": {
            "duplicates_removed": duplicates_removed,
            "missing_filled": missing_filled,
            "mean": mean_val,
            "median": median_val
        }
    }), 200

@app.route('/data/stats', methods=['GET'])
def get_stats():
    file_id = request.args.get('file_id')
    if not file_id:
        return jsonify({"error": "Не указан file_id"}), 400

    # Здесь нужно получить данные из базы
    return jsonify({
        "file_id": file_id,
        "mean": {"sales": 1500.0},
        "median": {"sales": 1400.0},
        "correlation": '{"sales": {"price": 0.8}}',
        "duplicates_removed": 3,
        "missing_filled": 5
    }), 200

@app.route('/data/clean', methods=['GET'])
def clean_data():
    file_id = request.args.get('file_id')
    if not file_id:
        return jsonify({"error": "Не указан file_id"}), 400

    return jsonify({
        "message": "Данные уже очищены",
        "duplicates_removed": 3,
        "missing_filled": 5
    }), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)