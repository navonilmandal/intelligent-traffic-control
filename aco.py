"""
aco.py — Ant Colony Optimization for Dynamic Vehicle Routing
============================================================
HOW ACO WORKS (plain English):
  Imagine ants searching for food. They leave pheromone trails as they walk.
  Other ants prefer trails with more pheromone. Over time, the shortest/best
  paths get the most pheromone, and bad routes fade out.

  Here:
  - "Ants" = vehicles on incoming roads
  - "Pheromone" = attractiveness of each route (starts equal)
  - "Heuristic" = current road conditions (less congestion = better)
  - Each update cycle: evaporate old pheromone + reinforce good routes
  - Vehicles approaching the junction get rerouted probabilistically
"""

import numpy as np
import traci
import traci.exceptions
from utils import EDGES_IN, EDGES_OUT, EDGE_CAPACITY

# ─── Route Definitions ───────────────────────────────────────────────────
# Format: "route_id" → (edge_list, entry_edge)
ROUTES = {
    # Vehicles coming from North
    "r_NS": (["N2C", "C2S"], "N2C"),
    "r_NE": (["N2C", "C2E"], "N2C"),
    "r_NW": (["N2C", "C2W"], "N2C"),
    # Vehicles coming from South
    "r_SN": (["S2C", "C2N"], "S2C"),
    "r_SE": (["S2C", "C2E"], "S2C"),
    "r_SW": (["S2C", "C2W"], "S2C"),
    # Vehicles coming from East
    "r_EN": (["E2C", "C2N"], "E2C"),
    "r_ES": (["E2C", "C2S"], "E2C"),
    "r_EW": (["E2C", "C2W"], "E2C"),
    # Vehicles coming from West
    "r_WN": (["W2C", "C2N"], "W2C"),
    "r_WS": (["W2C", "C2S"], "W2C"),
    "r_WE": (["W2C", "C2E"], "W2C"),
}

# Which routes are available from each entry edge
ROUTES_FROM = {
    "N2C": ["r_NS", "r_NE", "r_NW"],
    "S2C": ["r_SN", "r_SE", "r_SW"],
    "E2C": ["r_EN", "r_ES", "r_EW"],
    "W2C": ["r_WN", "r_WS", "r_WE"],
}


class ACORouter:
    """
    Ant Colony Optimization router.

    Call every N steps:
      aco.update_pheromones()   ← evaporate + reinforce
      aco.apply_routes()        ← reroute approaching vehicles
    """

    def __init__(self,
                 evaporation_rate: float = 0.08,
                 alpha:            float = 1.0,
                 beta:             float = 2.5,
                 initial_pheromone: float = 1.0):
        """
        evaporation_rate: how fast pheromone fades each cycle (0–1)
        alpha:  pheromone importance (higher → follow pheromone more)
        beta:   heuristic importance (higher → avoid congestion more)
        """
        self.rho   = evaporation_rate
        self.alpha = alpha
        self.beta  = beta

        # Pheromone table: each route starts with equal pheromone
        self.pheromone = {rid: initial_pheromone for rid in ROUTES}

        # Set of vehicle IDs we've already rerouted this trip
        # (prevents us from rerouting the same vehicle repeatedly)
        self._rerouted: set = set()

        # Statistics
        self.total_reroutes   = 0
        self.pheromone_log    = []   # for tracking convergence

        print(f"[ACO] Ready — {len(ROUTES)} routes, "
              f"ρ={evaporation_rate}, α={alpha}, β={beta}")

    # ── Private helpers ──────────────────────────────────────────────────

    def _edge_congestion(self, edge_id: str) -> float:
        """Congestion on a single edge: 0.0 (empty) → 1.0 (full)."""
        try:
            n = traci.edge.getLastStepVehicleNumber(edge_id)
            return min(n / EDGE_CAPACITY, 1.0)
        except Exception:
            return 0.0

    def _route_congestion(self, edge_list: list) -> float:
        """Average congestion across all edges in a route."""
        if not edge_list:
            return 0.0
        scores = [self._edge_congestion(e) for e in edge_list]
        return float(np.mean(scores))

    def _heuristic(self, route_id: str) -> float:
        """
        Heuristic desirability: higher = better choice.
        Based on inverse congestion: clear road → high heuristic.
        """
        edges, _ = ROUTES[route_id]
        cong = self._route_congestion(edges)
        return 1.0 / (1.0 + cong * 5.0)   # amplify congestion sensitivity

    def _select_route(self, candidates: list) -> str | None:
        """
        ACO probability selection.

        P(route_i) = (τ_i^α × η_i^β) / Σ(τ_j^α × η_j^β)

        where τ = pheromone, η = heuristic (1/congestion)
        """
        if not candidates:
            return None

        scores = []
        for rid in candidates:
            tau = max(self.pheromone[rid], 1e-6)     # pheromone (τ)
            eta = self._heuristic(rid)                # heuristic (η)
            score = (tau ** self.alpha) * (eta ** self.beta)
            scores.append(score)

        total = sum(scores)
        if total < 1e-9:
            # All routes equally awful → uniform random
            return str(np.random.choice(candidates))

        probs = [s / total for s in scores]
        chosen = np.random.choice(candidates, p=probs)
        return str(chosen)

    # ── Public API ───────────────────────────────────────────────────────

    def update_pheromones(self):
        """
        Update pheromone values for all routes.

        Step 1 — Evaporation: τ ← τ × (1 – ρ)
                 Simulates pheromone fading over time.

        Step 2 — Reinforcement: τ ← τ + Δτ
                 Less congested routes receive more new pheromone.
                 Δτ = (1 – congestion)   → ranges from 0 (gridlock) to 1 (empty)
        """
        for rid, (edges, _) in ROUTES.items():
            # Step 1: Evaporation
            self.pheromone[rid] *= (1.0 - self.rho)

            # Step 2: Reinforcement (reward = inverse of congestion)
            cong = self._route_congestion(edges)
            delta_tau = max(0.0, 1.0 - cong)
            self.pheromone[rid] += delta_tau

            # Clamp to sensible range to prevent overflow
            self.pheromone[rid] = max(0.05, min(15.0, self.pheromone[rid]))

        # Log average pheromone for dashboard
        avg_ph = float(np.mean(list(self.pheromone.values())))
        self.pheromone_log.append(round(avg_ph, 3))

    def apply_routes(self):
        """
        For every vehicle currently on an INCOMING edge (approaching the
        junction), probabilistically assign the best route using ACO.

        We only reroute each vehicle once per trip to avoid conflict.
        Ambulances are excluded (they follow emergency priority logic).
        """
        try:
            vehicle_ids = traci.vehicle.getIDList()
        except Exception:
            return

        for vid in vehicle_ids:
            # Skip ambulances — they have their own routing
            if "ambulance" in vid.lower():
                continue

            # Skip already-rerouted vehicles
            if vid in self._rerouted:
                continue

            try:
                current_edge = traci.vehicle.getRoadID(vid)

                # Only act on vehicles approaching the junction
                if current_edge not in ROUTES_FROM:
                    continue

                candidates = ROUTES_FROM[current_edge]
                chosen     = self._select_route(candidates)

                if chosen is None:
                    continue

                edge_list, _ = ROUTES[chosen]
                traci.vehicle.setRoute(vid, edge_list)

                # Mark as rerouted so we don't touch it again
                self._rerouted.add(vid)
                self.total_reroutes += 1

            except traci.exceptions.TraCIException:
                pass  # Vehicle may have left between the IDList call and now

        # Housekeeping: remove departed vehicles from the rerouted set
        try:
            active = set(traci.vehicle.getIDList())
            self._rerouted &= active
        except Exception:
            pass

    def get_stats(self) -> dict:
        """Return current pheromone levels and routing stats."""
        return {
            'total_reroutes': self.total_reroutes,
            'avg_pheromone':  round(float(np.mean(list(self.pheromone.values()))), 3),
            'best_route':     max(self.pheromone, key=self.pheromone.get),
            'worst_route':    min(self.pheromone, key=self.pheromone.get),
        }