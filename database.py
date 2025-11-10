# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data_models import Base, Student, Course, Section, Preference, Assignment

# DB_URI = "mysql+mysqlclient://user:password@localhost/class_scheduler"
# PostgreSQL হলে:
# DB_URI = "postgresql+psycopg2://user:password@localhost/class_scheduler"
DB_URI = "sqlite:///ai_schedule.db"   

engine = create_engine(DB_URI, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    Base.metadata.create_all(engine)

# Utility data accessors (query helpers)
def get_all_students(sess):
    return sess.query(Student).all()

def get_all_sections(sess):
    return sess.query(Section).all()

def get_student_preferences(sess, student_ids=None):
    q = sess.query(Preference)
    if student_ids:
        q = q.filter(Preference.student_id.in_(student_ids))
    return q.all()
