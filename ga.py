"""
ga.py — Simple GA (Penalty Optimizer)
"""

import random

class SimpleGA:
    def __init__(self):
        self.population = [random.uniform(0.5, 2.0) for _ in range(6)]
        self.best = 1.0

    def evolve(self, queue):

        # fitness → smaller queue is better
        scored = [(p, queue * p) for p in self.population]
        scored.sort(key=lambda x: x[1])

        self.best = scored[0][0]

        # mutation (small change)
        new_population = []
        for p in self.population:
            new_p = p + random.uniform(-0.1, 0.1)
            new_p = max(0.5, min(2.0, new_p))
            new_population.append(new_p)

        self.population = new_population

    def get_penalty(self):
        return self.best