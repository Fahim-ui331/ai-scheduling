# constraint_solver.py
from typing import List, Dict
from ortools.sat.python import cp_model
from data_models import Section

# Simple time overlap checker
def overlaps(s1, s2) -> bool:
    if s1.day != s2.day: return False
    return not (s1.end_time <= s2.start_time or s2.end_time <= s1.start_time)

def cp_refine_schedule(students, sections, initial_assignments):
    """
    students: list of Student
    sections: list of Section
    initial_assignments: dict {student_id: section_id or None}
    Returns: dict repaired assignments
    """
    model = cp_model.CpModel()
    # Variables: x[s][sec] ∈ {0,1}
    x = {}
    for stu in students:
        x[stu.student_id] = {}
        for sec in sections:
            x[stu.student_id][sec.id] = model.NewBoolVar(f"x_{stu.student_id}_{sec.id}")

    # 1) Assign exactly one section for each student's requested course (or zero if not feasible)
    for stu in students:
        model.Add(sum(x[stu.student_id][sec.id] for sec in sections) <= 1)

    # 2) Capacity
    for sec in sections:
        model.Add(sum(x[stu.student_id][sec.id] for stu in students) <= sec.capacity)

    # 3) Faculty availability (faculty_id may be None → treat as unavailable)
    for sec in sections:
        if sec.faculty_id is None:
            for stu in students:
                model.Add(x[stu.student_id][sec.id] == 0)

    # 4) No time conflicts per student (single-course example keeps simple;
    #    multi-course would compare chosen sections pairwise)

    # Objective: keep close to initial assignments
    terms = []
    for stu in students:
        for sec in sections:
            prefer = 1 if initial_assignments.get(stu.student_id) == sec.id else 0
            terms.append(prefer * x[stu.student_id][sec.id])
    model.Maximize(sum(terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.Solve(model)

    result = {}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for stu in students:
            chosen = None
            for sec in sections:
                if solver.Value(x[stu.student_id][sec.id]) == 1:
                    chosen = sec.id
                    break
            result[stu.student_id] = chosen
    else:
        result = {stu.student_id: None for stu in students}
    return result
