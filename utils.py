"""
utils.py — Shared utilities, constants, and metrics collector
=============================================================
Used by all other modules. Import what you need:
    from utils import MetricsCollector, EDGES_IN, TLS_ID, ...
"""

import json
import numpy as np
from collections import defaultdict

# ─── Network Constants ────────────────────────────────────────────────────
# These must match the edge IDs in edges.edg.xml

TLS_ID    = "C"                                    # Traffic light junction ID

EDGES_IN  = ["N2C", "S2C", "E2C", "W2C"]         # Roads approaching junction
EDGES_OUT = ["C2N", "C2S", "C2E", "C2W"]         # Roads leaving junction
ALL_EDGES = EDGES_IN + EDGES_OUT

# Lane IDs for each approach (3 lanes each, indexed 0–2)
NS_LANES  = [f"{e}_{i}" for e in ["N2C","S2C"] for i in range(3)]
EW_LANES  = [f"{e}_{i}" for e in ["E2C","W2C"] for i in range(3)]
ALL_LANES = NS_LANES + EW_LANES

# Approximate max vehicles per incoming edge (capacity estimate)
# Used to normalize congestion: 3 lanes × 300m / 7.5m spacing ≈ 120
EDGE_CAPACITY = 80   # conservative for congestion ratio


# ─── Metrics Collector ───────────────────────────────────────────────────

class MetricsCollector:
    """
    Collects and stores key simulation metrics at every update step.
    
    Usage:
        collector = MetricsCollector()
        metrics   = collector.collect(step, emergency_active=False)
        summary   = collector.get_summary()
        collector.save("my_run.json")
    """

    def __init__(self):
        # History lists — one entry per collected step
        self.history = {
            'step':             [],
            'total_vehicles':   [],
            'avg_waiting_time': [],
            'total_waiting':    [],
            'queue_length':     [],
            'avg_speed':        [],
            'emergency_active': [],
            'throughput':       [],   # vehicles that arrived this step
        }
        self.step_count = 0

    def collect(self, step, emergency_active=False):
        """
        Read current state from SUMO via TraCI and store metrics.
        Returns a dict of this step's metrics.
        """
        import traci

        # All vehicle IDs currently in the simulation
        try:
            vehicle_ids = traci.vehicle.getIDList()
        except Exception:
            vehicle_ids = []

        total_vehicles = len(vehicle_ids)

        # Waiting times and speeds per vehicle
        waiting_times = []
        speeds        = []
        for vid in vehicle_ids:
            try:
                waiting_times.append(traci.vehicle.getWaitingTime(vid))
                speeds.append(traci.vehicle.getSpeed(vid))
            except Exception:
                pass

        avg_waiting  = float(np.mean(waiting_times)) if waiting_times else 0.0
        total_waiting = sum(waiting_times)
        avg_speed    = float(np.mean(speeds))        if speeds        else 0.0

        # Queue = halting vehicles on all incoming edges
        queue = 0
        for edge in EDGES_IN:
            try:
                queue += traci.edge.getLastStepHaltingNumber(edge)
            except Exception:
                pass

        # Throughput = vehicles that completed their trip this step
        try:
            throughput = traci.simulation.getArrivedNumber()
        except Exception:
            throughput = 0

        # Build metrics dict
        metrics = {
            'step':             step,
            'total_vehicles':   total_vehicles,
            'avg_waiting_time': round(avg_waiting,  2),
            'total_waiting':    round(total_waiting, 2),
            'queue_length':     queue,
            'avg_speed':        round(avg_speed,    2),
            'emergency_active': int(emergency_active),
            'throughput':       throughput,
        }

        # Append to history
        for key, val in metrics.items():
            if key in self.history:
                self.history[key].append(val)

        self.step_count += 1
        return metrics

    def get_summary(self):
        """Aggregate statistics for the entire run."""
        h = self.history
        def safe_mean(lst): return round(float(np.mean(lst)), 2) if lst else 0.0
        def safe_max(lst):  return round(float(max(lst)),      2) if lst else 0.0

        return {
            'avg_waiting_time': safe_mean(h['avg_waiting_time']),
            'max_waiting_time': safe_max (h['avg_waiting_time']),
            'avg_queue_length': safe_mean(h['queue_length']),
            'max_queue_length': safe_max (h['queue_length']),
            'avg_speed':        safe_mean(h['avg_speed']),
            'total_throughput': int(sum(h['throughput'])),
            'steps_simulated':  self.step_count,
            'emergency_steps':  int(sum(h['emergency_active'])),
        }

    def save(self, filename):
        """Save full history + summary to a JSON file."""
        data = {
            'history': self.history,
            'summary': self.get_summary(),
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"[Utils] Metrics saved → {filename}")

    @staticmethod
    def load(filename):
        """Load a previously saved metrics JSON file."""
        with open(filename, 'r') as f:
            return json.load(f)


# ─── Helper Functions ─────────────────────────────────────────────────────

def get_edge_congestion():
    """
    Returns congestion ratio per incoming edge.
    0.0 = empty road, 1.0 = fully gridlocked.
    """
    import traci
    congestion = {}
    for edge in EDGES_IN:
        try:
            n = traci.edge.getLastStepVehicleNumber(edge)
            congestion[edge] = min(n / EDGE_CAPACITY, 1.0)
        except Exception:
            congestion[edge] = 0.0
    return congestion


def format_time(seconds):
    """Convert simulation seconds to MM:SS string."""
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"


def print_header():
    """Print the console table header."""
    print(f"\n{'Step':>6}  {'Time':>5}  {'Veh':>4}  "
          f"{'Wait(s)':>7}  {'Queue':>5}  {'Spd(m/s)':>8}  Note")
    print("─" * 65)


def print_row(step, metrics, note=""):
    """Print one row of the console metrics table."""
    print(
        f"{step:>6}  "
        f"{format_time(step):>5}  "
        f"{metrics['total_vehicles']:>4}  "
        f"{metrics['avg_waiting_time']:>7.1f}  "
        f"{metrics['queue_length']:>5}  "
        f"{metrics['avg_speed']:>8.2f}  "
        f"{note}"
    )