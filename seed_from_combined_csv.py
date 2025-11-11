# seed_from_combined_csv.py
import pandas as pd
from sqlalchemy.orm import Session
from database import init_db, SessionLocal
from data_models import Course, Section, Faculty

CSV_PATH = "class_schedule_combined.csv"


# ==================================================
# Helper: parse time safely
# ==================================================
def parse_time_range(time_str):
    if pd.isna(time_str):
        return None, None
    try:
        text = str(time_str).replace("python", "").replace("--", "-").strip()
        parts = [p.strip() for p in text.split('-')]
        if len(parts) >= 2:
            return parts[0], parts[1]
        elif len(parts) == 1:
            return parts[0], None
    except Exception:
        pass
    return None, None


# ==================================================
# Helper: load and clean CSV
# ==================================================
def load_and_clean_csv(path):
    df = pd.read_csv(path, header=1)
    df.columns = [str(c).strip().replace("\n", " ").replace("  ", " ") for c in df.columns]
    df.columns = [
        c.replace("C redit", "Credit")
        .replace("Course   Code", "Course Code")
        .replace("Faculty  Initial", "Faculty Initial")
        for c in df.columns
    ]
    df.columns = [c.title().strip() for c in df.columns]

    print("✅ Cleaned columns:", df.columns.tolist())

    if "Program" in df.columns:
        df = df[df["Program"] != "Program"]
    if "Course Code" in df.columns:
        df = df[df["Course Code"].notna()]

    print(f"✅ Loaded {len(df)} valid data rows\n")
    return df


# ==================================================
# Seeding logic
# ==================================================
def seed_from_combined(sess: Session):
    df = load_and_clean_csv(CSV_PATH)

    inserted_courses = 0
    inserted_faculty = 0
    updated_sections = 0
    inserted_sections = 0

    for _, row in df.iterrows():
        try:
            course_id = str(row.get("Course Code", "")).strip()
            if not course_id:
                continue
            course_title = str(row.get("Title", "")).strip()
            section_code = str(row.get("Section", "")).strip()
            faculty_name = str(row.get("Faculty Name", "")).strip()
            faculty_initial = str(row.get("Faculty Initial", "")).strip()
            credit_val = row.get("Credit", 3)
            try:
                credit = int(float(credit_val)) if not pd.isna(credit_val) else 3
            except:
                credit = 3

            # ----- Add or get course -----
            course = sess.get(Course, course_id)
            if not course:
                course = Course(id=course_id, title=course_title, level=1, credits=credit)
                sess.add(course)
                inserted_courses += 1

            # ----- Add or get faculty -----
            faculty = sess.query(Faculty).filter_by(name=faculty_name).first()
            if not faculty:
                faculty = Faculty(
                    code=faculty_initial or faculty_name[:3].upper(),
                    name=faculty_name,
                    max_load=3,
                    available=True,
                )
                sess.add(faculty)
                sess.flush()
                inserted_faculty += 1

            # ----- Handle section -----
            existing_section = (
                sess.query(Section)
                .filter_by(course_id=course_id, code=section_code)
                .first()
            )

            day1, time1, room1 = row.get("Day1"), row.get("Time1"), row.get("Room1")
            day2, time2, room2 = row.get("Day2"), row.get("Time2"), row.get("Room2")
            start1, end1 = parse_time_range(time1)
            start2, end2 = parse_time_range(time2)

            if existing_section:
                # If already exists, update it to include day2/time2 if empty
                if not existing_section.day and pd.notna(day1):
                    existing_section.day = str(day1).strip()
                    existing_section.start_time = start1
                    existing_section.end_time = end1
                if pd.notna(day2):
                    existing_section.day += f", {day2}"
                updated_sections += 1
            else:
                sec = Section(
                    course_id=course_id,
                    code=section_code,
                    day=str(day1).strip() if pd.notna(day1) else None,
                    start_time=start1,
                    end_time=end1,
                    room=str(room1).strip() if pd.notna(room1) else "TBA",
                    capacity=45,
                    faculty_id=faculty.id,
                )
                sess.add(sec)
                inserted_sections += 1

        except Exception as e:
            print(f"⚠️ Skipped a row ({course_id if 'course_id' in locals() else '?'}) — {e}")
            sess.rollback()
            continue

    sess.commit()
    print(f"🎓 Courses added: {inserted_courses}")
    print(f"👨‍🏫 Faculty added: {inserted_faculty}")
    print(f"📚 Sections inserted: {inserted_sections}")
    print(f"🔁 Sections updated: {updated_sections}")
    print("✅ Seeding complete!")


# ==================================================
# Entry Point
# ==================================================
if __name__ == "__main__":
    init_db()
    sess = SessionLocal()
    try:
        seed_from_combined(sess)
    except Exception as e:
        print("\n❌ Seeding failed:", e)
        sess.rollback()
    finally:
        sess.close()
