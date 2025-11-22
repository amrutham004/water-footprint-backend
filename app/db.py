# app/db.py
from sqlmodel import SQLModel, create_engine, Session
from .models import Reading
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./water_footprint.db")
# SQLite: disable same_thread for FastAPI dev server single-process concurrency
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)
