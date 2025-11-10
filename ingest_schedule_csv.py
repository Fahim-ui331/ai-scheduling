# ingest_schedule_csv.py
"""
CSV -> ORM Seeder + (optional) RF training rows
Works with a single 'class_schedule_combined.csv' that may contain:
- course / section / time / room / faculty info
- semester info
- (optionally) student_id / student_name / cgpa / payment / evaluation / preferences

How to run:
    python ingest_schedule_csv.py --csv class_schedule_combined.csv --train-rf

If column names differ, adjust COLUMN_MAP below.
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List

from database import init_db, SessionLocal
from data_models import Student, Course, Section, Preference, Assignment  # Faculty optional if you add model
# from prediction_engine import train_rf  # uncomment if you want to train from this file

# --------- 1) Column mapping (fuzzy synonyms supported) ----------
# ডানের value গুলো হলো আমরা যেভাবে ব্যবহার করবো এমন "canonical" নাম।
COLUMN_MAP = {
    # Courses
    "course_id": ["course_id", "Course_ID", "course code", "CourseCode", "course"],
    "course_title": ["course_title", "Course", "Course_Title", "title", "Course Name"],
    "course_level": ["level", "CourseLevel", "course_level"],
    "credits": ["credits", "Credit", "credit"],

    # Sections / timing
    "section_code": ["section", "Section", "Sec", "section_code"],
    "day": ["day", "Day", "weekday"],
    "start_time": ["start_time", "Start", "start", "starttime", "time_from"],
    "end_time": ["end_time", "End", "end", "endtime", "time_to"],
    "room": ["room", "Room", "venue", "classroom"],
    "capacity": ["capacity", "Cap", "Seat", "seats"],

    # Faculty (optional)
    "faculty_name": ["faculty", "Faculty", "teacher", "instructor", "Teacher", "Instructor"],
    "faculty_code": ["faculty_code", "faculty_id", "teacher_id"],

    # Semester / term
    "semester": ["semester", "term", "Trimester", "Session"],

    # Students (optional; if present we’ll seed them too)
    "student_id": ["student_id", "Student_ID", "sid", "ID"],
    "student_name": ["name", "student_name", "Name"],
    "cgpa": ["cgpa", "GPA", "Cgpa"],
    "payment": ["payment_cleared", "Payment", "Payment_Status"],
    "evaluation": ["evaluation_done", "Evaluation", "Eval_Status"],
    "pref_sections": ["preferred_sections", "Preferred_Sections", "preference", "choice"],
    "time_pref": ["time_pref", "TimePref", "time_preference"],
}

def pick_col(df: pd.DataFrame, candidates: List[str]):
    cols = {c.lower(): c for c in df.columns}
    for key in candidates:
        k = key.lower()
        if k in cols:
            return cols[k]
    # contains search
    for key in candidates:
        for c in df.columns:
            if key.lower() in c.lower():
                return c
    return None

def canonicalize(df: pd.DataFrame) -> Dict[str, str]:
    mapping = {}
    for canon, cands in COLUMN_MAP.items():
        found = pick_col(df, cands)
        if found:
            mapping[canon] = found
    return mapping

def boolify(x):
    if pd.isna(x): return False
    if isinstance(x, (int,float)): return x != 0
    s = str(x).strip().lower()
    return s in ("1","true","yes","y","t","cleared","complete","completed","done")

def hhmm(s):
    # normalize times like 9:0 -> 09:00
    if pd.isna(s): return None
    s = str(s).strip()
    if len(s) == 4 and ":" in s:  # e.g., 9:00
        hh, mm = s.split(":")
        return f"{int(hh):02d}:{int(mm):02d}"
    if len(s) == 5 and s[2] == ":":
        return s
    # fallback for "900" / "0930"
    digits = "".join([c for c in s if c.isdigit()])
    if len(digits) == 3:
        return f"0{digits[0]}:{digits[1:]}"
    if len(digits) == 4:
        return f"{digits[:2]}:{digits[2:]}"
    return s

def seed_from_csv(csv_path: Path, train_rf: bool=False):
    init_db()
    sess = SessionLocal()

    df = pd.read_csv(csv_path)
    colmap = canonicalize(df)

    # --- sanity print ---
    print("Detected columns → canonical mapping:")
    for k,v in sorted(colmap.items()):
        print(f"  {k:>15}  <-  {v}")

    # --- Courses ---
    cid = colmap.get("course_id")
    ctitle = colmap.get("course_title")
    clevel = colmap.get("course_level")
    ccred = colmap.get("credits")

    # --- Sections / timetable ---
    s_code = colmap.get("section_code")
    s_day = colmap.get("day")
    s_start = colmap.get("start_time")
    s_end = colmap.get("end_time")
    s_room = colmap.get("room")
    s_cap = colmap.get("capacity")

    # --- Faculty (optional) ---
    f_name = colmap.get("faculty_name")
    f_code = colmap.get("faculty_code")

    # --- Semester (optional) ---
    sem_col = colmap.get("semester")

    # --- Student part (optional) ---
    stu_id = colmap.get("student_id")
    stu_name = colmap.get("student_name")
    stu_cgpa = colmap.get("cgpa")
    stu_pay = colmap.get("payment")
    stu_eval = colmap.get("evaluation")
    stu_pref = colmap.get("pref_sections")
    stu_tpref = colmap.get("time_pref")

    # ---------- Seed Courses ----------
    if cid:
        for _, r in df.drop_duplicates(subset=[cid]).iterrows():
            course = sess.get(Course, str(r[cid])) or Course(id=str(r[cid]))
            if ctitle: course.title = str(r[ctitle]) if not pd.isna(r[ctitle]) else ""
            if clevel: course.level = int(r[clevel]) if not pd.isna(r[clevel]) else 1
            if ccred:  course.credits = int(r[ccred]) if not pd.isna(r[ccred]) else 3
            sess.add(course)
        sess.commit()
        print(f"✔ Courses seeded: {sess.query(Course).count()}")

    # ---------- Seed Sections ----------
    if cid and s_code and s_day and s_start and s_end:
        sec_cols = [cid, s_code, s_day, s_start, s_end]
        extra = []
        if s_room: extra.append(s_room)
        if s_cap: extra.append(s_cap)
        subset_cols = list(dict.fromkeys(sec_cols + extra))
        sec_df = df.drop_duplicates(subset=subset_cols)
        for _, r in sec_df.iterrows():
            sec = Section(
                course_id=str(r[cid]),
                code=str(r[s_code]),
                day=str(r[s_day]),
                start_time=hhmm(r[s_start]),
                end_time=hhmm(r[s_end]),
                room=str(r[s_room]) if s_room and not pd.isna(r[s_room]) else "TBA",
                capacity=int(r[s_cap]) if s_cap and not pd.isna(r[s_cap]) else 40,
                faculty_id=None  # keep N/A; you can map if Faculty model exists
            )
            sess.add(sec)
        sess.commit()
        print(f"✔ Sections seeded: {sess.query(Section).count()}")

    # ---------- Seed Students (optional) ----------
    if stu_id:
        for _, r in df.drop_duplicates(subset=[stu_id]).iterrows():
            s = (
                sess.query(Student)
                .filter_by(student_id=str(r[stu_id]))
                .first()
            )
            if not s:
                s = Student(student_id=str(r[stu_id]))
            if stu_name and not pd.isna(r.get(stu_name, np.nan)):
                s.name = str(r[stu_name])
            if stu_cgpa and not pd.isna(r.get(stu_cgpa, np.nan)):
                s.cgpa = float(r[stu_cgpa])
            if stu_pay:
                s.payment_cleared = boolify(r.get(stu_pay, False))
            if stu_eval:
                s.evaluation_done = boolify(r.get(stu_eval, False))
            sess.add(s)
        sess.commit()
        print(f"✔ Students seeded: {sess.query(Student).count()}")

    # ---------- Seed Preferences (optional) ----------
    if stu_id and cid and (stu_pref or stu_tpref):
        # build map ext student_id -> internal pk
        smap = {s.student_id: s.id for s in sess.query(Student).all()}
        for _, r in df.drop_duplicates(subset=[stu_id, cid]).iterrows():
            sid = smap.get(str(r[stu_id]))
            if not sid: 
                continue
            pref = Preference(
                student_id=sid,
                course_id=str(r[cid]),
                preferred_sections=str(r[stu_pref]) if stu_pref and not pd.isna(r.get(stu_pref, np.nan)) else "",
                time_pref=str(r[stu_tpref]) if stu_tpref and not pd.isna(r.get(stu_tpref, np.nan)) else ""
            )
            sess.add(pref)
        sess.commit()
        print("✔ Preferences seeded.")

    # ---------- Optional RF training rows ----------
    if train_rf and sem_col and cid:
        # প্রতি (semester, course_id) এর enrollment ~ section capacity sum (approx)
        tmp = df.copy()
        tmp["_cap"] = df[s_cap] if s_cap in df.columns else 40
        hist = (
            tmp.groupby([sem_col, cid])["_cap"]
            .sum()
            .reset_index()
            .rename(columns={sem_col: "semester", cid: "course_id", "_cap": "enrollment"})
        )
        out = Path("rf_history_from_combined.csv")
        hist.to_csv(out, index=False)
        print(f"✔ RF history generated: {out.resolve()}")

    sess.close()
    print("✅ All done.")
    return True

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="class_schedule_combined.csv")
    ap.add_argument("--train-rf", action="store_true", help="also create rf_history_from_combined.csv")
    args = ap.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    seed_from_csv(csv_path, train_rf=args.train_rf)
