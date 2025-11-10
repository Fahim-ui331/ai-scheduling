# seed_from_csv.py
import pandas as pd
from sqlalchemy.orm import Session
from database import init_db, SessionLocal
from data_models import Student, Course, Section, Preference

# ---- CSV schema expectations (columns) ----
# students.csv: student_id,name,cgpa,payment_cleared,evaluation_done,level,department
# courses.csv:  course_id,title,level,credits
# sections.csv: course_id,code,day,start_time,end_time,room,capacity,faculty_code(optional)
# faculty.csv:  code,name,max_load,available
# prefs.csv:    student_id,course_id,preferred_sections,time_pref
# history.csv:  semester,course_id,enrollment  (RF training)

def boolify(x):
    if isinstance(x, str):
        return x.strip().lower() in ("1","true","yes","y","t")
    return bool(x)

def load_students(sess: Session, csv_path: str):
    df = pd.read_csv(csv_path)
    for _, r in df.iterrows():
        st = sess.query(Student).filter_by(student_id=str(r["student_id"])).first()
        if not st:
            st = Student(student_id=str(r["student_id"]))
        st.name = r.get("name","")
        st.cgpa = float(r.get("cgpa",0))
        st.payment_cleared = boolify(r.get("payment_cleared", False))
        st.evaluation_done = boolify(r.get("evaluation_done", False))
        st.level = int(r.get("level",1))
        st.department = r.get("department","CSE")
        sess.add(st)

def load_courses(sess: Session, csv_path: str):
    df = pd.read_csv(csv_path)
    for _, r in df.iterrows():
        c = sess.get(Course, str(r["course_id"])) or Course(id=str(r["course_id"]))
        c.title = r.get("title","")
        c.level = int(r.get("level",1))
        c.credits = int(r.get("credits",3))
        sess.add(c)

def load_sections(sess: Session, csv_path: str):
    df = pd.read_csv(csv_path)
    for _, r in df.iterrows():
        sec = Section(
            course_id=str(r["course_id"]),
            code=str(r["code"]),
            day=str(r["day"]),
            start_time=str(r["start_time"]),
            end_time=str(r["end_time"]),
            room=str(r.get("room","TBA")),
            capacity=int(r.get("capacity",40))
        )
        sess.add(sec)

def load_preferences(sess: Session, csv_path: str):
    df = pd.read_csv(csv_path)
    # map external student_id → internal id
    stu_map = {s.student_id: s.id for s in sess.query(Student).all()}
    for _, r in df.iterrows():
        sid = stu_map.get(str(r["student_id"]))
        if not sid: 
            continue
        pref = Preference(
            student_id=sid,
            course_id=str(r["course_id"]),
            preferred_sections=str(r.get("preferred_sections","")),
            time_pref=str(r.get("time_pref",""))
        )
        sess.add(pref)

def seed_all(
    students_csv=None, courses_csv=None, sections_csv=None, prefs_csv=None
):
    init_db()
    sess = SessionLocal()
    try:
        if students_csv:  load_students(sess, students_csv)
        if courses_csv:   load_courses(sess, courses_csv)
        if sections_csv:  load_sections(sess, sections_csv)
        if prefs_csv:     load_preferences(sess, prefs_csv)
        sess.commit()
        print("✅ Seeding complete.")
    except Exception as e:
        sess.rollback()
        print("❌ Seeding failed:", e)
        raise
    finally:
        sess.close()

if __name__ == "__main__":

    seed_all(
        students_csv="data/students.csv",
        courses_csv="app/static/courses.csv",
        sections_csv="data/sections.csv",
        prefs_csv="data/prefs.csv",
    )
