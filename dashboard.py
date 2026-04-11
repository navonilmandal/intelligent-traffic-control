"""
dashboard.py — Real-time Matplotlib Dashboard + Comparison Plots
================================================================
Two main components:
  1. Dashboard class  → live updating plots during simulation
  2. plot_comparison() → side-by-side baseline vs optimized analysis
"""

import numpy as np
from collections import deque

# ─── Matplotlib backend setup ────────────────────────────────────────────
# Try TkAgg first (most common on Windows), fall back to default
import matplotlib
try:
    matplotlib.use('TkAgg')
except Exception:
    pass   # Use whatever backend is available

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# Dark theme colours
BG_DARK   = '#1a1a2e'
BG_PANEL  = '#16213e'
C_RED     = '#e94560'
C_GREEN   = '#4ecca3'
C_AMBER   = '#f5a623'
C_PURPLE  = '#9b59b6'
C_BLUE    = '#3498db'
C_WHITE   = '#e0e0e0'
C_GRAY    = '#555566'

WINDOW = 300   # Max data points in rolling window


class Dashboard:
    """
    Live matplotlib dashboard.

    Usage:
        dash = Dashboard(mode="optimized")
        dash.update(metrics, pso_timing=(30, 25))
        dash.finalize(summary)
    """

    def __init__(self, mode: str = "optimized"):
        self.mode = mode

        # Rolling data windows
        self.steps    = deque(maxlen=WINDOW)
        self.waiting  = deque(maxlen=WINDOW)
        self.queue    = deque(maxlen=WINDOW)
        self.vehicles = deque(maxlen=WINDOW)
        self.speed    = deque(maxlen=WINDOW)

        self._setup_figure()
        print(f"[Dashboard] Live window ready — mode: {mode.upper()}")

    def _setup_figure(self):
        """Create the figure and all subplots."""
        plt.ion()   # Non-blocking interactive mode

        self.fig = plt.figure(figsize=(14, 8), facecolor=BG_DARK)
        self.fig.suptitle(
            f"🚦 Hybrid Intelligent Traffic System  [{self.mode.upper()}]",
            color=C_WHITE, fontsize=13, fontweight='bold', y=0.98
        )

        gs = gridspec.GridSpec(2, 3, figure=self.fig,
                               hspace=0.45, wspace=0.35,
                               top=0.93, bottom=0.1)

        # ── Create axes ──────────────────────────────────────────────────
        self.ax_wait   = self.fig.add_subplot(gs[0, 0])
        self.ax_queue  = self.fig.add_subplot(gs[0, 1])
        self.ax_speed  = self.fig.add_subplot(gs[0, 2])
        self.ax_vehs   = self.fig.add_subplot(gs[1, 0])
        self.ax_bar    = self.fig.add_subplot(gs[1, 1])
        self.ax_status = self.fig.add_subplot(gs[1, 2])

        self._style_axes()

        # ── Lines for live plots ─────────────────────────────────────────
        self.ln_wait,  = self.ax_wait.plot([], [],  color=C_RED,    lw=2)
        self.ln_queue, = self.ax_queue.plot([], [], color=C_AMBER,  lw=2)
        self.ln_speed, = self.ax_speed.plot([], [], color=C_GREEN,  lw=2)
        self.ln_vehs,  = self.ax_vehs.plot([], [],  color=C_PURPLE, lw=2)

        # Labels
        self.ax_wait.set_title("Avg Waiting Time (s)",   color=C_WHITE, fontsize=10)
        self.ax_queue.set_title("Queue Length (veh)",    color=C_WHITE, fontsize=10)
        self.ax_speed.set_title("Avg Speed (m/s)",       color=C_WHITE, fontsize=10)
        self.ax_vehs.set_title("Active Vehicles",        color=C_WHITE, fontsize=10)
        self.ax_bar.set_title("Live Metric Snapshot",    color=C_WHITE, fontsize=10)
        self.ax_status.set_title("System Status",        color=C_WHITE, fontsize=10)

        for ax in [self.ax_wait, self.ax_queue, self.ax_speed, self.ax_vehs]:
            ax.set_xlabel("Step", color=C_WHITE, fontsize=8)

        # Status text box
        self.ax_status.axis('off')
        self.status_lines = self.ax_status.text(
            0.05, 0.95, "Initializing...",
            transform=self.ax_status.transAxes,
            va='top', ha='left', fontsize=9,
            color=C_WHITE, fontfamily='monospace',
            linespacing=1.8
        )

        # Emergency alert patch (hidden by default)
        self.em_patch = self.ax_status.add_patch(
            plt.Rectangle((0, 0), 1, 0.18, transform=self.ax_status.transAxes,
                          color=C_RED, alpha=0.0, zorder=5)
        )
        self.em_text = self.ax_status.text(
            0.5, 0.09, "",
            transform=self.ax_status.transAxes,
            ha='center', va='center', fontsize=10,
            color='white', fontweight='bold', zorder=6
        )

        plt.pause(0.1)

    def _style_axes(self):
        """Apply dark theme to all axes."""
        for ax in [self.ax_wait, self.ax_queue, self.ax_speed,
                   self.ax_vehs, self.ax_bar, self.ax_status]:
            ax.set_facecolor(BG_PANEL)
            ax.tick_params(colors=C_WHITE, labelsize=7)
            for spine in ax.spines.values():
                spine.set_edgecolor(C_GRAY)

    def _update_bar(self, metrics):
        """Update the snapshot bar chart."""
        self.ax_bar.cla()
        self.ax_bar.set_facecolor(BG_PANEL)
        self.ax_bar.set_title("Live Metric Snapshot", color=C_WHITE, fontsize=10)
        for spine in self.ax_bar.spines.values():
            spine.set_edgecolor(C_GRAY)

        labels  = ["Wait(s)", "Queue", "Speed\n(m/s)", "Vehs"]
        values  = [
            metrics['avg_waiting_time'],
            metrics['queue_length'],
            metrics['avg_speed'],
            metrics['total_vehicles'],
        ]
        colours = [C_RED, C_AMBER, C_GREEN, C_PURPLE]

        bars = self.ax_bar.bar(labels, values, color=colours, alpha=0.8, width=0.6)
        self.ax_bar.tick_params(colors=C_WHITE, labelsize=8)

        # Value labels on top of each bar
        for bar, val in zip(bars, values):
            self.ax_bar.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() * 1.02,
                f"{val:.1f}",
                ha='center', va='bottom',
                color=C_WHITE, fontsize=8
            )

    def update(self, metrics: dict,
               pso_timing: tuple = None,
               aco_stats:  dict  = None):
        """
        Update the dashboard with new data.
        Call every DASHBOARD_INTERVAL steps.
        """
        step = metrics['step']

        # Append to rolling windows
        self.steps.append(step)
        self.waiting.append(metrics['avg_waiting_time'])
        self.queue.append(metrics['queue_length'])
        self.vehicles.append(metrics['total_vehicles'])
        self.speed.append(metrics['avg_speed'])

        x = list(self.steps)

        # ── Update line plots ─────────────────────────────────────────────
        for ln, data in [
            (self.ln_wait,  self.waiting),
            (self.ln_queue, self.queue),
            (self.ln_speed, self.speed),
            (self.ln_vehs,  self.vehicles),
        ]:
            ln.set_data(x, list(data))

        # Auto-scale axes
        for ax, data in [
            (self.ax_wait,  self.waiting),
            (self.ax_queue, self.queue),
            (self.ax_speed, self.speed),
            (self.ax_vehs,  self.vehicles),
        ]:
            if x:
                ax.set_xlim(x[0], max(x[-1], x[0] + 50))
            if data:
                ymax = max(data) * 1.25
                ax.set_ylim(0, max(ymax, 1.0))

        # ── Emergency overlay ─────────────────────────────────────────────
        is_emergency = bool(metrics.get('emergency_active'))
        alpha_val    = 0.25 if is_emergency else 0.0
        self.em_patch.set_alpha(alpha_val)
        self.em_text.set_text("🚨 EMERGENCY OVERRIDE ACTIVE" if is_emergency else "")

        # ── Snapshot bar ──────────────────────────────────────────────────
        self._update_bar(metrics)

        # ── Status text ───────────────────────────────────────────────────
        mode_line = f"Mode   : {self.mode.upper()}"
        step_line = f"Step   : {step}"
        wait_line = f"Wait   : {metrics['avg_waiting_time']:.1f}s"
        q_line    = f"Queue  : {metrics['queue_length']} veh"
        spd_line  = f"Speed  : {metrics['avg_speed']:.2f} m/s"
        veh_line  = f"Active : {metrics['total_vehicles']} veh"

        pso_line = ""
        if pso_timing and pso_timing[0]:
            pso_line = f"PSO    : NS={pso_timing[0]}s EW={pso_timing[1]}s"

        aco_line = ""
        if aco_stats:
            aco_line = (f"ACO    : reroutes={aco_stats['total_reroutes']} "
                        f"best={aco_stats['best_route']}")

        em_line = "EMERG  : 🟢 OVERRIDE" if is_emergency else "EMERG  : Normal"

        status = "\n".join(filter(None, [
            mode_line, step_line, "─" * 22,
            wait_line, q_line, spd_line, veh_line,
            "─" * 22, pso_line, aco_line, em_line
        ]))
        self.status_lines.set_text(status)

        # ── Redraw ───────────────────────────────────────────────────────
        try:
            self.fig.canvas.draw_idle()
            plt.pause(0.001)
        except Exception:
            pass

    def show_emergency_alert(self, veh_id: str, step: int):
        """Flash emergency alert prominently."""
        self.em_patch.set_alpha(0.35)
        self.em_text.set_text(f"🚑 {veh_id} approaching junction! (step {step})")
        try:
            self.fig.canvas.draw_idle()
            plt.pause(0.05)
        except Exception:
            pass

    def finalize(self, summary: dict):
        """Show final summary when simulation ends."""
        try:
            self.em_text.set_text(
                f"✅ Done | Avg wait {summary['avg_waiting_time']}s "
                f"| {summary['total_throughput']} vehicles"
            )
            self.em_patch.set_alpha(0.15)
            self.em_patch.set_facecolor(C_GREEN)
            self.fig.canvas.draw_idle()
            plt.pause(1.0)
            plt.ioff()
        except Exception:
            pass


# ─── Comparison Plot ─────────────────────────────────────────────────────

def plot_comparison(baseline: dict, optimized: dict,
                    save_path: str = "comparison.png"):
    """
    Generate a comprehensive comparison chart.

    baseline, optimized: dicts from MetricsCollector.load()
                         { 'history': {...}, 'summary': {...} }
    """
    bh  = baseline['history']
    oh  = optimized['history']
    bs  = baseline['summary']
    os_ = optimized['summary']

    fig = plt.figure(figsize=(18, 10), facecolor=BG_DARK)
    fig.suptitle(
        "Performance Comparison: Fixed Timing (Baseline) vs ACO + PSO + Emergency Priority",
        color=C_WHITE, fontsize=14, fontweight='bold', y=0.98
    )

    gs = gridspec.GridSpec(3, 3, figure=fig,
                           hspace=0.5, wspace=0.35,
                           top=0.93, bottom=0.07)

    axes = {
        'wait':  fig.add_subplot(gs[0, 0]),
        'queue': fig.add_subplot(gs[0, 1]),
        'speed': fig.add_subplot(gs[0, 2]),
        'bar':   fig.add_subplot(gs[1, 0:2]),
        'pct':   fig.add_subplot(gs[1, 2]),
        'info':  fig.add_subplot(gs[2, :]),
    }

    for ax in axes.values():
        ax.set_facecolor(BG_PANEL)
        ax.tick_params(colors=C_WHITE, labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor(C_GRAY)

    bs_steps = bh['step']
    os_steps = oh['step']

    # ── Time-series plots ─────────────────────────────────────────────────
    def ts_plot(ax, b_data, o_data, title, ylabel):
        ax.plot(bs_steps, b_data, color=C_RED,   lw=1.5, label='Baseline', alpha=0.8)
        ax.plot(os_steps, o_data, color=C_GREEN,  lw=1.5, label='ACO+PSO',  alpha=0.8)
        ax.set_title(title, color=C_WHITE, fontsize=10)
        ax.set_xlabel("Step", color=C_WHITE, fontsize=8)
        ax.set_ylabel(ylabel, color=C_WHITE, fontsize=8)
        leg = ax.legend(fontsize=8, facecolor=BG_PANEL, labelcolor=C_WHITE)
        leg.get_frame().set_edgecolor(C_GRAY)

    ts_plot(axes['wait'],  bh['avg_waiting_time'], oh['avg_waiting_time'],
            "Average Waiting Time",   "seconds")
    ts_plot(axes['queue'], bh['queue_length'],      oh['queue_length'],
            "Queue Length",           "vehicles")
    ts_plot(axes['speed'], bh['avg_speed'],          oh['avg_speed'],
            "Average Speed",          "m/s")

    # ── Grouped bar chart ─────────────────────────────────────────────────
    metric_labels  = ['Avg Wait (s)', 'Avg Queue', 'Avg Speed (m/s)', 'Throughput (/10)']
    baseline_vals  = [bs['avg_waiting_time'], bs['avg_queue_length'],
                      bs['avg_speed'],         bs['total_throughput'] / 10]
    optimized_vals = [os_['avg_waiting_time'], os_['avg_queue_length'],
                      os_['avg_speed'],          os_['total_throughput'] / 10]

    x  = np.arange(len(metric_labels))
    w  = 0.35
    b1 = axes['bar'].bar(x - w/2, baseline_vals,  w, color=C_RED,   label='Baseline', alpha=0.85)
    b2 = axes['bar'].bar(x + w/2, optimized_vals, w, color=C_GREEN,  label='ACO+PSO',  alpha=0.85)

    for bar in list(b1) + list(b2):
        axes['bar'].text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.3,
            f"{bar.get_height():.1f}",
            ha='center', va='bottom', color=C_WHITE, fontsize=7
        )

    axes['bar'].set_xticks(x)
    axes['bar'].set_xticklabels(metric_labels)
    axes['bar'].set_title("Key Metrics Side-by-Side", color=C_WHITE, fontsize=10)
    leg2 = axes['bar'].legend(fontsize=8, facecolor=BG_PANEL, labelcolor=C_WHITE)
    leg2.get_frame().set_edgecolor(C_GRAY)

    # ── Improvement % chart ───────────────────────────────────────────────
    def pct_change(b_val, o_val, higher_better=False):
        if b_val == 0:
            return 0.0
        delta = (o_val - b_val) / b_val * 100.0
        return delta if higher_better else -delta   # flip so positive = improvement

    improvements = {
        'Waiting\nTime':  pct_change(bs['avg_waiting_time'], os_['avg_waiting_time']),
        'Queue\nLength':  pct_change(bs['avg_queue_length'],  os_['avg_queue_length']),
        'Avg\nSpeed':     pct_change(bs['avg_speed'],         os_['avg_speed'],         higher_better=True),
        'Through-\nput':  pct_change(bs['total_throughput'],  os_['total_throughput'],  higher_better=True),
    }

    colors = [C_GREEN if v >= 0 else C_RED for v in improvements.values()]
    pbars  = axes['pct'].bar(
        list(improvements.keys()),
        list(improvements.values()),
        color=colors, alpha=0.85, width=0.6
    )

    for bar, val in zip(pbars, improvements.values()):
        yoff = bar.get_height() + 0.5 if val >= 0 else bar.get_height() - 2.5
        axes['pct'].text(
            bar.get_x() + bar.get_width() / 2,
            yoff,
            f"{val:+.1f}%",
            ha='center', va='bottom', color=C_WHITE,
            fontsize=9, fontweight='bold'
        )

    axes['pct'].axhline(0, color=C_WHITE, lw=0.8, alpha=0.4)
    axes['pct'].set_title("% Improvement (ACO+PSO vs Baseline)",
                           color=C_WHITE, fontsize=10)
    axes['pct'].set_ylabel("% change (↑ = better)", color=C_WHITE, fontsize=8)

    # ── Summary text band ─────────────────────────────────────────────────
    axes['info'].axis('off')

    def row(label, b_val, o_val, unit="", higher_better=False):
        if b_val == 0:
            pct_str = "N/A"
            icon    = " "
        else:
            delta = (o_val - b_val) / b_val * 100.0
            if not higher_better:
                delta = -delta   # lower wait = improvement
            icon    = "▲" if delta > 0 else "▼"
            pct_str = f"{abs(delta):.1f}%"
        return (f"  {label:<22} {str(b_val)+unit:>12}  →  "
                f"{str(o_val)+unit:<12}  {icon} {pct_str}")

    lines = [
        "  FULL PERFORMANCE SUMMARY",
        "  " + "─" * 70,
        f"  {'Metric':<22} {'Baseline':>12}     {'ACO+PSO':<12}  Change",
        "  " + "─" * 70,
        row("Avg Waiting Time",   bs['avg_waiting_time'],  os_['avg_waiting_time'],  "s"),
        row("Max Waiting Time",   bs['max_waiting_time'],  os_['max_waiting_time'],  "s"),
        row("Avg Queue Length",   bs['avg_queue_length'],  os_['avg_queue_length'],  " veh"),
        row("Max Queue Length",   bs['max_queue_length'],  os_['max_queue_length'],  " veh"),
        row("Avg Speed",          bs['avg_speed'],          os_['avg_speed'],          " m/s", True),
        row("Total Throughput",   bs['total_throughput'],   os_['total_throughput'],   " veh", True),
        "  " + "─" * 70,
    ]

    axes['info'].text(
        0.01, 0.98, "\n".join(lines),
        transform=axes['info'].transAxes,
        va='top', ha='left',
        fontsize=9, fontfamily='monospace',
        color=C_WHITE, linespacing=1.5
    )

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    if save_path:
        plt.savefig(save_path, dpi=130, bbox_inches='tight',
                    facecolor=BG_DARK)
        print(f"\n[Dashboard] Comparison chart saved → {save_path}")

    plt.ioff()
    plt.show(block=True)