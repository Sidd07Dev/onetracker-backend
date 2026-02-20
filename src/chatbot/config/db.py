from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URI = os.getenv("DB_URI")

engine = create_engine(DATABASE_URI)
SessionLocal = sessionmaker(autocommit = False,autoflush = False,bind = engine)

def get_db():
    db = SessionLocal()
    try:
       yield db
    except Exception as e:
        raise e
    finally:
        db.close()