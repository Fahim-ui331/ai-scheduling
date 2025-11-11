# seed_students.py
import random
from sqlalchemy.orm import Session
from database import init_db, SessionLocal
from data_models import Student

# ---------------------------------------------------------
# Generate Random Students for AI Schedule Generator
# ---------------------------------------------------------

DEPARTMENTS = ["CSE", "EEE", "BBA", "ENG"]
LEVELS = [1, 2, 3, 4]
NAMES = [
    "Aminul Islam", "Tasnima Rahman", "Fahim Ahmed", "Nazmul Hasan",
    "Rafiul Karim", "Sadia Jahan", "Nafisa Chowdhury", "Tanzim Hossain",
    "Mehedi Rahman", "Tasnim Noor", "Shahriar Kabir", "Anika Rahman",
    "Tanvir Alam", "Raisul Hasan", "Farhana Akter", "Sajid Mahmud"
]


def generate_students(num_students=30):
    """Generate random student data for testing."""
    students = []
    for i in range(1, num_students + 1):
        student_id = f"S{i:03d}"  # e.g., S001, S002
        name = random.choice(NAMES)
        cgpa = round(random.uniform(2.0, 4.0), 2)
        payment_cleared = random.random() > 0.2  # 80% cleared
        evaluation_done = random.random() > 0.1  # 90% done
        level = random.choice(LEVELS)
        department = random.choice(DEPARTMENTS)

        st = Student(
            student_id=student_id,
            name=name,
            cgpa=cgpa,
            payment_cleared=payment_cleared,
            evaluation_done=evaluation_done,
            level=level,
            department=department,
        )
        students.append(st)
    return students


def seed_students():
    """Insert generated students into database."""
    init_db()
    sess: Session = SessionLocal()
    try:
        students = generate_students(40)
        for st in students:
            sess.merge(st)  # merge prevents duplicate insertions
        sess.commit()
        print(f"✅ Successfully inserted {len(students)} students.")
    except Exception as e:
        sess.rollback()
        print(f"❌ Error seeding students: {e}")
    finally:
        sess.close()


if __name__ == "__main__":
    seed_students()
