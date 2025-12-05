from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class UploadedFile(Base):
    __tablename__ = 'uploaded_files'

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    size = Column(Integer)

class AnalysisResult(Base):
    __tablename__ = 'analysis_results'

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, nullable=False)
    mean = Column(Text)
    median = Column(Text)
    correlation = Column(Text)     
    duplicates_removed = Column(Integer)
    missing_filled = Column(Integer)
    analysis_date = Column(DateTime, default=datetime.utcnow)