from flask import Flask, request, jsonify
from database import SessionLocal, init_db
from models import UploadedFile, AnalysisResult
import pandas as pd
import json
import os
from pathlib import Path
from sqlalchemy.exc import SQLAlchemyError

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
    missing_filled = int(missing_filled)

    # Сохраняем в БД
    db = SessionLocal()
    try:
        uploaded_file = UploadedFile(
            filename=file.filename,
            file_type='csv' if file.filename.endswith('.csv') else 'xlsx',
            size=os.path.getsize(filepath)
        )
        db.add(uploaded_file)
        db.commit()
        db.refresh(uploaded_file)

        analysis_result = AnalysisResult(
            file_id=uploaded_file.id,
            mean=json.dumps(mean_val),
            median=json.dumps(median_val),
            correlation=corr,
            duplicates_removed=duplicates_removed,
            missing_filled=missing_filled
        )
        db.add(analysis_result)
        db.commit()

        return jsonify({
            "message": "Файл успешно загружен и проанализирован",
            "filename": filename,
            "file_id": uploaded_file.id,
            "analysis_summary": {
                "duplicates_removed": duplicates_removed,
                "missing_filled": missing_filled,
                "mean": mean_val,
                "median": median_val
            }
        }), 200
    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": f"Ошибка при сохранении в БД: {str(e)}"}), 500
    finally:
        db.close()

@app.route('/data/stats', methods=['GET'])
def get_stats():
    file_id = request.args.get('file_id')
    if not file_id:
        return jsonify({"error": "Не указан file_id"}), 400

    db = SessionLocal()
    try:
        result = db.query(AnalysisResult).filter_by(file_id=file_id).first()
        if not result:
            return jsonify({"error": "Результат анализа не найден"}), 404

        return jsonify({
            "file_id": file_id,
            "mean": json.loads(result.mean),
            "median": json.loads(result.median),
            "correlation": json.loads(result.correlation),
            "duplicates_removed": result.duplicates_removed,
            "missing_filled": result.missing_filled
        }), 200
    except SQLAlchemyError as e:
        return jsonify({"error": f"Ошибка при чтении из БД: {str(e)}"}), 500
    finally:
        db.close()

@app.route('/data/clean', methods=['GET'])
def clean_data():
    file_id = request.args.get('file_id')
    if not file_id:
        return jsonify({"error": "Не указан file_id"}), 400

    db = SessionLocal()
    try:
        result = db.query(AnalysisResult).filter_by(file_id=file_id).first()
        if not result:
            return jsonify({"error": "Результат анализа не найден"}), 404

        return jsonify({
            "message": "Данные уже очищены",
            "duplicates_removed": result.duplicates_removed,
            "missing_filled": result.missing_filled
        }), 200
    except SQLAlchemyError as e:
        return jsonify({"error": f"Ошибка при чтении из БД: {str(e)}"}), 500
    finally:
        db.close()

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)