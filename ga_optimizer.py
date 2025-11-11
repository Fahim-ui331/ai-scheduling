# ga_optimizer.py
import random
from typing import Dict, List
from data_models import Student, Section, Preference


class GAOptimizer:
    def __init__(self, sections: List[Section], preferences: Dict[str, Preference],
                 priomap: Dict[str, float], demand_weight: Dict[str, float]):
        """
        Genetic Algorithm (GA) Optimizer for AI Class Scheduling.
        ----------------------------------------------------------
        sections: all available Section objects from DB
        preferences: {student_id: Preference}
        priomap: {student_id: priority weight (based on CGPA, payment, etc.)}
        demand_weight: {course_id: predicted demand (from Random Forest)}
        """
        self.sections = sections or []
        self.preferences = preferences or {}
        self.priomap = priomap or {}
        self.demand_weight = demand_weight or {}
        self.section_ids = [s.id for s in self.sections] if self.sections else []

    # ------------------------------------------------------
    # 1️⃣ Generate Random Individual (Chromosome)
    # ------------------------------------------------------
    def random_individual(self, students: List[Student]) -> Dict[str, int | None]:
        """Randomly assign each student to a section (or None)."""
        indiv = {}
        if not self.section_ids:
            return {s.student_id: None for s in students}  # no available sections

        for s in students:
            # lower-priority students have a small chance to be unassigned
            if self.priomap.get(s.student_id, 0) < 0 and random.random() < 0.3:
                indiv[s.student_id] = None
            else:
                indiv[s.student_id] = random.choice(self.section_ids)
        return indiv

    # ------------------------------------------------------
    # 2️⃣ Fitness Function
    # ------------------------------------------------------
    def fitness(self, indiv: Dict[str, int], students: List[Student]) -> float:
        """Evaluate how good a schedule is based on preferences & priorities."""
        if not indiv:
            return 0.0

        score = 0.0
        sec_by_id = {s.id: s for s in self.sections}

        for s in students:
            sec_id = indiv.get(s.student_id)
            if not sec_id or sec_id not in sec_by_id:
                continue
            sec = sec_by_id[sec_id]
            pref = self.preferences.get(s.student_id)

            # ---- Preference Matching Bonus ----
            if pref:
                preferred = set([x.strip() for x in (pref.preferred_sections or "").split(",") if x.strip()])
                if sec.code in preferred:
                    score += 2.0
                # Time penalty (avoid morning)
                if pref.time_pref == "avoid_08" and str(sec.start_time).startswith("08"):
                    score -= 1.0

            # ---- Student Priority Weight ----
            score += 3.0 * self.priomap.get(s.student_id, 0.0)

            # ---- Demand Weight Bonus ----
            score += 0.1 * self.demand_weight.get(sec.course_id, 0.0)

        return score

    # ------------------------------------------------------
    # 3️⃣ Crossover Operator
    # ------------------------------------------------------
    def crossover(self, p1: Dict[str, int], p2: Dict[str, int]) -> Dict[str, int]:
        """Combine two parent schedules into a child."""
        keys = list(p1.keys())
        if len(keys) < 2:
            return p1.copy()  # not enough genes to crossover safely

        child = {}
        cut = random.randint(1, len(keys) - 1)
        for k in keys[:cut]:
            child[k] = p1[k]
        for k in keys[cut:]:
            child[k] = p2[k]
        return child

    # ------------------------------------------------------
    # 4️⃣ Mutation Operator
    # ------------------------------------------------------
    def mutate(self, indiv: Dict[str, int], rate=0.1):
        """Randomly change a student's section assignment."""
        if not self.section_ids:
            return
        for k in list(indiv.keys()):
            if random.random() < rate:
                indiv[k] = random.choice(self.section_ids)

    # ------------------------------------------------------
    # 5️⃣ Run Genetic Algorithm
    # ------------------------------------------------------
    def run(self, students: List[Student], generations=60, pop_size=30):
        """
        Run the Genetic Algorithm evolution process.
        - Creates initial population
        - Applies selection, crossover, and mutation
        - Returns the best schedule (mapping of student → section_id)
        """
        if not students or not self.sections:
            print("⚠️ GA skipped — no students or sections found.")
            return {}

        # Initialize population
        population = [self.random_individual(students) for _ in range(pop_size)]

        for gen in range(generations):
            population.sort(key=lambda ind: self.fitness(ind, students), reverse=True)
            best_fit = self.fitness(population[0], students)
            print(f"Generation {gen+1}/{generations} — Best fitness: {best_fit:.2f}")

            next_gen = population[:2]  # elitism

            while len(next_gen) < pop_size:
                # pick two parents from top 10
                if len(population) < 2:
                    break
                p1, p2 = random.sample(population[:min(10, len(population))], 2)
                child = self.crossover(p1, p2)
                self.mutate(child, 0.15)
                next_gen.append(child)

            population = next_gen

        best = max(population, key=lambda ind: self.fitness(ind, students))
        print("✅ GA completed successfully.")
        return best
