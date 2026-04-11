# Intelligent Traffic Control System 🚦

This project implements a hybrid intelligent traffic signal control system using real-time traffic data and optimization algorithms.

## 🚀 Technologies Used

- SUMO (Simulation of Urban Mobility)
- Python (TraCI API)
- Queue-Based Adaptive Control
- Particle Swarm Optimization (PSO)
- Genetic Algorithm (GA) *(optional tuning)*

---

## 🧠 Core Idea

The system dynamically controls traffic signals based on real-time congestion.

### 1. Queue-Based Control (Main Logic)
- Measures number of vehicles in each direction
- Gives priority to the direction with higher traffic
- Ensures efficient traffic flow

### 2. PSO (Optimization Layer)
- Optimizes the threshold for switching signals
- Reduces unnecessary signal switching
- Improves stability

### 3. GA (Optional Enhancement)
- Tunes sensitivity of decision making
- Provides fine adjustment to system behavior

---

## 📊 Features

- Real-time adaptive traffic control
- Baseline vs optimized comparison
- Reduced waiting time and congestion
- Improved traffic speed
- Modular experimental setup (easy to enable/disable algorithms)

---

## 📈 Results

| System | Performance |
|-------|------------|
| Baseline | Poor traffic flow |
| Queue-Based | Major improvement |
| Queue + PSO | Further optimization |
| Queue + PSO + GA | Slight refinement |

---

## ▶️ How to Run

```bash
python main.py --compare
