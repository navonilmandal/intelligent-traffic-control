"""
pso.py — Improved PSO (Multi-objective, stable)
"""

import random

class Particle:
    def __init__(self):
        self.position = random.uniform(2, 20)   # threshold
        self.velocity = 0
        self.best_position = self.position
        self.best_score = float("inf")


class PSOThreshold:
    def __init__(self, num_particles=6):
        self.particles = [Particle() for _ in range(num_particles)]
        self.global_best = None
        self.global_score = float("inf")

    def update(self, wait, queue, speed):

        # 🔥 Multi-objective fitness
        score = (0.6 * wait) + (0.3 * queue) - (0.2 * speed)

        for p in self.particles:

            if score < p.best_score:
                p.best_score = score
                p.best_position = p.position

            if score < self.global_score:
                self.global_score = score
                self.global_best = p.position

        # update velocity & position
        for p in self.particles:

            inertia = 0.4
            c1 = 1.7
            c2 = 1.7

            r1, r2 = random.random(), random.random()

            p.velocity = (
                inertia * p.velocity
                + c1 * r1 * (p.best_position - p.position)
                + c2 * r2 * (self.global_best - p.position)
            )

            p.position += p.velocity

            # clamp threshold
            p.position = max(2, min(20, p.position))

    def get_threshold(self):
        return self.global_best if self.global_best else 10