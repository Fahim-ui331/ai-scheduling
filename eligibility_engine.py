# eligibility_engine.py
from typing import Dict
from sqlalchemy.orm import Session
from data_models import Student, Course, Preference

def is_eligible(stu: Student) -> bool:
    return bool(stu.payment_cleared and stu.evaluation_done)

def passed_prereqs(stu_completed: set, target_course: Course) -> bool:
    return all(pr.id in stu_completed for pr in target_course.prerequisites)

def priority_weight(stu: Student) -> float:
    # High priority: CGPA >= 3.5 → +1.0 otherwise 0
    return 1.0 if stu.cgpa >= 3.5 else 0.0

def make_eligibility_snapshot(sess: Session) -> Dict[str, dict]:
    """Output: {student_id: {eligible:bool, priority:float}}"""
    result = {}
    for s in sess.query(Student).all():
        result[s.student_id] = {
            "eligible": is_eligible(s),
            "priority": priority_weight(s),
            "level": s.level,
            "dept": s.department
        }
    return result
