# main_scheduler.py
import pandas as pd
from collections import defaultdict
from database import init_db, SessionLocal, get_all_students, get_all_sections
from eligibility_engine import make_eligibility_snapshot
from prediction_engine import load_rf, train_rf, predict_demand
from ga_optimizer import GAOptimizer
from constraint_solver import cp_refine_schedule
from data_models import Assignment, Preference, Section

def generate_schedule():
    init_db()
    sess = SessionLocal()

    students = get_all_students(sess)
    sections = get_all_sections(sess)

    # 1) Eligibility & priority
    snap = make_eligibility_snapshot(sess)
    eligible_students = [s for s in students if snap[s.student_id]["eligible"]]
    priomap = {s.student_id: snap[s.student_id]["priority"] for s in eligible_students}

    # 2) Load/Train RF and demand weights
    # এখানে demo হিসেবে dummy history বানাচ্ছি—তোমার historical table/CSV বসিয়ে দাও
    import pandas as pd
    hist = pd.DataFrame({
        "semester": ["Spring","Spring","Fall","Fall"]*5,
        "course_id": [sec.course_id for sec in sections[:20]],
        "enrollment": [min(45, sec.capacity) for sec in sections[:20]]
    })
    try:
        model = load_rf()
    except:
        model = train_rf(hist)
    upcoming = pd.DataFrame({"semester":["Spring"]*len(sections), "course_id":[s.course_id for s in sections]})
    demand_pred = predict_demand(model, upcoming)
    demand_weight = {sec.course_id: float(d) for sec, d in zip(sections, demand_pred)}

    # 3) Preferences map
    prefs = {p.student.student_id: p for p in sess.query(Preference).all()}

    # 4) GA
    ga = GAOptimizer(sections, prefs, priomap, demand_weight)
    ga_solution = ga.run(eligible_students)

    # 5) CP refine/validate
    repaired = cp_refine_schedule(eligible_students, sections, ga_solution)

    # 6) Save Assignments
    for stu in eligible_students:
        sec_id = repaired.get(stu.student_id)
        assign = Assignment(student=stu, section_id=sec_id, status="assigned" if sec_id else "not_assigned")
        sess.add(assign)
    sess.commit()
    sess.close()
    return repaired

# Targeted re-optimization for affected students
def run_dynamic_reoptimizer(affected_student_ids):
    sess = SessionLocal()
    students = [s for s in sess.query(Student).all() if s.student_id in affected_student_ids]
    sections = sess.query(Section).all()

    # simple: unassign their current sections first
    for a in sess.query(Assignment).all():
        if a.student.student_id in affected_student_ids:
            a.section_id = None
            a.status = "not_assigned"
    sess.commit()

    # reuse GA lightly with only affected students
    snap = make_eligibility_snapshot(sess)
    priomap = {s.student_id: snap[s.student_id]["priority"] for s in students}
    prefs = {p.student.student_id: p for p in sess.query(Preference).filter(Preference.student_id.in_([s.id for s in students]))}
    demand_weight = defaultdict(float)  # keep neutral

    from ga_optimizer import GAOptimizer
    ga = GAOptimizer(sections, prefs, priomap, demand_weight)
    sol = ga.run(students, generations=20, pop_size=20)
    repaired = cp_refine_schedule(students, sections, sol)

    for stu in students:
        sec_id = repaired.get(stu.student_id)
        a = Assignment(student=stu, section_id=sec_id, status="assigned" if sec_id else "not_assigned")
        sess.add(a)
    sess.commit()
    sess.close()
    return repaired
