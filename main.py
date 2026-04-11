"""
main.py — FINAL HYBRID (Queue + PSO + GA)
Safe, stable, experimental version
"""

import os
import sys
import argparse

# ── SUMO SETUP ─────────────────────────────────────
_sumo_home = os.environ.get("SUMO_HOME", "")
if _sumo_home:
    _tools = os.path.join(_sumo_home, "tools")
    if _tools not in sys.path:
        sys.path.insert(0, _tools)

import traci

from utils import MetricsCollector, TLS_ID
from dashboard import Dashboard, plot_comparison
from pso import PSOThreshold
from ga import SimpleGA


# ───────────────────────────────────────────────────
CONFIG_FILE = "my_config.sumocfg"
MAX_STEPS   = 800
USE_GUI     = True

DASHBOARD_INTERVAL = 15
PRINT_INTERVAL     = 60

BASELINE_NS = 30


# ───────────────────────────────────────────────────
def start_sumo(mode):
    binary = "sumo-gui" if USE_GUI else "sumo"

    cmd = [
        binary,
        "-c", CONFIG_FILE,
        "--start",
        "--quit-on-end",
        "--no-warnings", "true",
    ]

    if USE_GUI:
        cmd += ["--delay", "20"]

    print(f"\n[STARTING SUMO - {mode.upper()} MODE]")
    traci.start(cmd)


# ───────────────────────────────────────────────────
def run(mode="optimized"):
    start_sumo(mode)

    collector = MetricsCollector()
    dash = Dashboard(mode)

    # AI modules
    pso = PSOThreshold() if mode == "optimized" else None
    ga  = SimpleGA() if mode == "optimized" else None

    threshold = 10
    penalty   = 1.0

    step = 0

    # Edge groups
    edges_NS = ["N2C", "S2C"]
    edges_EW = ["E2C", "W2C"]

    def get_queue(edges):
        return sum(traci.edge.getLastStepVehicleNumber(e) for e in edges)

    while step < MAX_STEPS:
        traci.simulationStep()

        # ─── COLLECT METRICS FIRST ─────────────────
        metrics = collector.collect(step)

        # ─── BASELINE MODE ─────────────────────────
        if mode == "baseline":
            traci.trafficlight.setPhaseDuration(TLS_ID, BASELINE_NS)

        # ─── OPTIMIZED MODE ────────────────────────
        if mode == "optimized":

            if step % 10 == 0:

                q_ns = get_queue(edges_NS)
                q_ew = get_queue(edges_EW)

                # 🔥 PSO UPDATE
                try:
                    pso.update(
                        metrics["avg_waiting_time"],
                        metrics["queue_length"],
                        metrics["avg_speed"]
                    )
                    threshold = pso.get_threshold()
                except Exception as e:
                    print("[PSO ERROR]", e)
                    threshold = 10

                # 🔥 GA UPDATE
                try:
                    ga.evolve(metrics["queue_length"])
                    penalty = ga.get_penalty()
                except Exception as e:
                    print("[GA ERROR]", e)
                    penalty = 1.0

                # 🔥 FINAL CONTROL LOGIC
                if q_ns > q_ew + threshold * penalty:
                    traci.trafficlight.setPhase(TLS_ID, 0)  # NS green

                elif q_ew > q_ns + threshold * penalty:
                    traci.trafficlight.setPhase(TLS_ID, 2)  # EW green

        # ─── DASHBOARD ─────────────────────────────
        if step % DASHBOARD_INTERVAL == 0:
            dash.update(metrics)

        # ─── LOGGING ───────────────────────────────
        if step % PRINT_INTERVAL == 0:
            print(
                f"[Step {step}] "
                f"Wait={metrics['avg_waiting_time']:.2f}s | "
                f"Queue={metrics['queue_length']:.0f} | "
                f"Speed={metrics['avg_speed']:.2f} | "
                f"T={threshold:.2f} | P={penalty:.2f}"
            )

        step += 1

    # ─── END ──────────────────────────────────────
    summary = collector.get_summary()
    dash.finalize(summary)

    traci.close()
    return summary


# ───────────────────────────────────────────────────
def run_comparison():
    print("\n=== BASELINE ===")
    baseline = run("baseline")

    print("\n=== OPTIMIZED (PSO + GA) ===")
    optimized = run("optimized")

    plot_comparison(baseline, optimized)


# ───────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--mode", choices=["baseline", "optimized"])
    parser.add_argument("--compare", action="store_true")
    parser.add_argument("--no-gui", action="store_true")

    args = parser.parse_args()

    if args.no_gui:
        USE_GUI = False

    if args.compare:
        run_comparison()
    else:
        run(args.mode or "optimized")