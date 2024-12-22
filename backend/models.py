from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Message(Base):
    """消息模型."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), index=True)  # 学生ID
    content = Column(Text)  # 消息内容
    sender = Column(String(50))  # 发送者
    role = Column(String(20))  # user 或 assistant
    timestamp = Column(DateTime, default=datetime.now)  # 时间戳

class StudyRecord(Base):
    """学习记录模型."""
    __tablename__ = "study_records"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), index=True)  # 学生ID
    topic = Column(String(100))  # 学习主题
    content = Column(Text)  # 学习内容
    duration = Column(Integer)  # 学习时长（秒）
    score = Column(Integer)  # 学习得分
    timestamp = Column(DateTime, default=datetime.now)  # 时间戳
