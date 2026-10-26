from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Replace 'postgres' if your username is different, and 'your_password' with your PostgreSQL password
DATABASE_URL = "postgresql+psycopg2://postgres:aakash123@localhost:5432/customer_chatbot_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()