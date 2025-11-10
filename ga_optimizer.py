# ga_optimizer.py
import random
from typing import Dict, List
from data_models import Student, Section, Preference

class GAOptimizer:
    def __init__(self, sections: List[Section], preferences: Dict[str, Preference],
                 priomap: Dict[str, float], demand_weight: Dict[str, float]):
        """
        sections: all available sections for a single course or full catalog
        preferences: {student_id: Preference}
        priomap: {student_id: priority_weight}
        demand_weight: {course_id: predicted_demand}
        """
        self.sections = sections
        self.preferences = preferences
        self.priomap = priomap
        self.demand_weight = demand_weight
        self.section_ids = [s.id for s in sections]

    def random_individual(self, students: List[Student]) -> Dict[str, int | None]:
        # mapping student_id -> section_id (or None)
        indiv = {}
        for s in students:
            if self.priomap.get(s.student_id, 0) < 0 and random.random() < 0.3:
                indiv[s.student_id] = None
            else:
                indiv[s.student_id] = random.choice(self.section_ids)
        return indiv

    def fitness(self, indiv: Dict[str, int], students: List[Student]) -> float:
        score = 0.0
        # preference match + priority + time-of-day soft penalty (8:00)
        sec_by_id = {s.id: s for s in self.sections}
        for s in students:
            sec_id = indiv.get(s.student_id)
            if not sec_id: 
                continue
            sec = sec_by_id[sec_id]
            pref = self.preferences.get(s.student_id)
            # section preference bonus
            if pref:
                preferred = set([x.strip() for x in (pref.preferred_sections or "").split(",") if x.strip()])
                if sec.code in preferred:
                    score += 2.0
                # time-of-day penalty: avoid 08:00
                if pref.time_pref == "avoid_08" and sec.start_time == "08:00":
                    score -= 1.0
            # priority boost
            score += 3.0 * self.priomap.get(s.student_id, 0.0)
            # demand weighting: popular courses get light bonus
            score += 0.1 * self.demand_weight.get(sec.course_id, 0.0)
        return score

    def crossover(self, p1: Dict[str,int], p2: Dict[str,int]) -> Dict[str,int]:
        child = {}
        keys = list(p1.keys())
        cut = random.randint(1, len(keys)-1)
        for k in keys[:cut]: child[k] = p1[k]
        for k in keys[cut:]: child[k] = p2[k]
        return child

    def mutate(self, indiv: Dict[str,int], rate=0.1):
        for k in list(indiv.keys()):
            if random.random() < rate:
                indiv[k] = random.choice(self.section_ids)

    def run(self, students: List[Student], generations=60, pop_size=30):
        population = [self.random_individual(students) for _ in range(pop_size)]
        for _ in range(generations):
            population.sort(key=lambda ind: self.fitness(ind, students), reverse=True)
            next_gen = population[:2]  # elitism
            while len(next_gen) < pop_size:
                p1, p2 = random.sample(population[:10], 2)
                child = self.crossover(p1, p2)
                self.mutate(child, 0.15)
                next_gen.append(child)
            population = next_gen
        best = max(population, key=lambda ind: self.fitness(ind, students))
        return best
