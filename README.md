# Beam-Enhanced Time Shaping (BETS) for Industrial Wireless TSN Networks

This repository contains the complete implementation and simulation framework for **BETS**, a practical algorithm that jointly optimizes beamforming and intelligent scheduling to dramatically increase the capacity of Time-Sensitive Networking (TSN) traffic in industrial wireless networks.

## What is BETS?

BETS stands for **Beam-Enhanced Time Shaping**—a novel cross-layer framework that couples spatial multiplexing (via MIMO beamforming) with temporal scheduling (via TSN traffic shaping). Rather than treating MIMO link capacity as fixed or treating TSN scheduling independently, BETS simultaneously:

1. **Adapts beamweights** at base stations to maximize signal strength for critical streams
2. **Partitions available bandwidth** between uplink and downlink based on traffic demands  
3. **Optimizes frame schedules** to align with current channel conditions and network capacity

The result: Industrial networks can support **up to 130% more time-sensitive streams** while reducing transmission power by 10-15% compared to traditional approaches.

### The Problem BETS Solves

In Industry 4.0, wireless control loops and automation systems require:
- **Ultra-low latency** (milliseconds)
- **Guaranteed reliability** (deterministic delivery)
- **High capacity** to support many simultaneous streams

However, traditional TSN scheduling assumes **static, pre-configured link capacities**, while MIMO beamforming focuses on **maximizing throughput without latency constraints**. BETS bridges this gap by jointly optimizing both aspects within a single coherence interval.

---

## Key Features

### 🎯 Joint Optimization Framework
- **Network Demand**: Optimizes TSN frame scheduling and arrival times
- **Network Provision**: Adapts beamweights and bandwidth allocation based on channel conditions
- **Iterative Refinement**: Uses alternating optimization to refine all three components

### 📡 MIMO-Enabled Design  
- **Zero-Forcing Beamforming**: Eliminates inter-user interference for spatial multiplexing
- **Custom Power Allocation**: Distributes transmission power based on per-stream demands
- **Hybrid Architecture**: Supports both digital and analog beamforming

### 🔄 Intelligent Scheduling
- **Hop-aware Scheduler**: Optimizes per-link timing constraints
- **Coherence-Interval Based**: Operates within channel coherence windows for reliability
- **Greedy Satisfiability**: Prioritizes streams that are easiest to satisfy

### 📊 Comprehensive Simulation
- **Stochastic mmWave Channel Model**: Realistic LOS/NLOS/outage conditions
- **Industrial Environment Modeling**: 120m×80m×10m production hall with mobility
- **Scalability Testing**: Validated with 10-500 streams and varying network sizes

---

## How It Works

### The BETS Algorithm: Three-Phase Optimization

BETS operates on a **per-coherence-interval basis** (typically 10ms) and iterates through three optimization blocks:

#### Phase 1: Beamweight Optimization
- Determines which streams are satisfiable given current scheduling and bandwidth
- Greedily allocates transmission power to maximize satisfied streams
- Respects per-BS power budgets

#### Phase 2: Bandwidth Partitioning  
- Finds the optimal split between uplink and downlink bandwidth
- Computes "satisfiability ranges" for each stream
- Identifies the maximum overlapping interval that satisfies the most streams

#### Phase 3: Schedule Optimization
- Adjusts per-link arrival times and occupation durations
- Prioritizes streams with smallest bitrate gaps
- Ensures all temporal consistency and latency constraints are met

The algorithm repeats these phases until no further improvement is observed, typically converging in 2-3 iterations.

---

## Codebase Structure

```
pythonProject/
├── bets_enabler/                    # Core BETS algorithm
│   ├── bets_enabler.py             # Main BETS orchestrator
│   ├── objective_function.py        # Satisfaction evaluation
│   └── visualizer.py                # Performance visualization
│
├── beamforming/                     # Beamforming implementations
│   ├── digital_beamforming/
│   │   ├── zero_forcing.py         # Zero-forcing precoder design
│   │   └── beamweight_manager.py    # Power allocation per UE
│   └── analog_beamforming/
│       └── beam_sweeping.py         # Analog beam steering
│
├── environment/                     # Physical & channel modeling
│   ├── physical_environment.py      # 3D node placement & topology
│   ├── channel_model/
│   │   ├── channel_model.py         # mmWave stochastic model
│   │   ├── cluster.py               # Path cluster generation
│   │   └── path.py                  # Individual path modeling
│   ├── antenna_array/
│   │   └── URPA.py                  # Uniform Rectangular Planar Array
│   ├── mobility/                    # UE movement models
│   └── ofdm/
│       └── spectrum_manager.py      # UL/DL bandwidth split
│
├── traffic/                         # TSN & BE traffic models
│   ├── tst_stream.py               # TSN stream definition
│   ├── tst_frame.py                # TSN frame with timing
│   ├── frame.py                     # Generic frame structure
│   └── bet_generator.py             # Best-effort traffic
│
├── scheduler/                       # Scheduling algorithms
│   ├── hop_based_coherence_interval_aware_tst_scheduler.py
│   └── hop_based_tst_scheduler.py
│
├── nodes/                           # Network nodes
│   ├── bs.py                        # Base Station with arrays/managers
│   ├── ue.py                        # User Equipment
│   ├── node.py                      # Base node class
│   └── switch.py                    # Network switch
│
├── link/                            # Network links & queues
│   └── link.py                      # Wired/wireless link model
│
├── ue_selection/                    # UE selection & capacity calculation
│   ├── policies.py                  # Selection policies
│   ├── cumulative_data_rate.py     # Rate computation
│   ├── algorithms/                  # Selection algorithms
│   ├── cooperative/                 # Cooperative selection
│   └── non_cooperative/             # Non-cooperative selection
│
├── experiments/                     # Experiment runners
│   └── [various scenarios]/         # Pre-configured benchmarks
│
├── plotters/                        # Visualization
│   ├── batch_plotter.py
│   ├── graph_plotters.py
│   └── mobility_video.py
│
└── main.py                          # Example usage & entry point
```

---

## Architecture Overview

### System-Level Architecture

```
     ┌─────────────────────────────────────────────────────┐
     │          TSN Control Logic                          │
     │  (Streams, routes, QoS requirements)                │
     └─────────────┬───────────────────────────────────────┘
                   │
     ┌─────────────▼───────────────────────────────────────┐
     │          BETS Algorithm                             │
     │  ┌──────────────┬──────────────┬──────────────┐    │
     │  │  Beamweight  │  Bandwidth   │  Schedule    │    │
     │  │ Optimization │ Partitioning │ Optimization │    │
     │  └──────────────┴──────────────┴──────────────┘    │
     └─────────────┬───────────────────────────────────────┘
                   │
     ┌─────────────▼───────────────────────────────────────┐
     │       Physical Layer Control                        │
     │  ┌──────────────┬──────────────────────────────┐   │
     │  │ Beamforming  │  Spectrum Management         │   │
     │  │ • Weights    │  • UL/DL split              │   │
     │  │ • Precoding  │  • Guard band management    │   │
     │  └──────────────┴──────────────────────────────┘   │
     └─────────────┬───────────────────────────────────────┘
                   │
     ┌─────────────▼───────────────────────────────────────┐
     │          Channel Layer                              │
     │  ┌──────────────┬──────────────────────────────┐   │
     │  │ mmWave Model │  Path clustering            │   │
     │  │ SINR calc.   │  Antenna arrays             │   │
     │  └──────────────┴──────────────────────────────┘   │
     └─────────────┬───────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
   ┌────▼────┐          ┌────▼────┐
   │   BS    │    ...   │   BS    │
   │(w/URPA) │          │(w/URPA) │
   └────┬────┘          └────┬────┘
        │                    │
   ┌────▼────┐          ┌────▼────┐
   │   UE    │    ...   │   UE    │
   │(single  │          │(single  │
   │antenna) │          │antenna) │
   └─────────┘          └─────────┘
```

### Optimization Flow

```
Coherence Interval T_c
│
├─ Channel Estimation Phase (T_est)
│  └─ Acquire CSI via uplink pilots
│
└─ Data Transmission Phase (T_trn) 
   │
   └─ Run BETS Algorithm:
      │
      ├─ [Iteration 1]
      │  ├─ Beamweight Opt: Greedy stream selection
      │  ├─ Bandwidth Opt: Maximum overlapping interval
      │  ├─ Schedule Opt: Per-link arrival times
      │  └─ Evaluate improvement
      │
      ├─ [Iteration 2]
      │  ├─ Refine with new beamweights
      │  ├─ Adjust bandwidth split
      │  ├─ Reschedule frames
      │  └─ Check convergence
      │
      └─ [Terminate] 
         └─ Apply final configuration to transmit frames
```

---

## Metrics & Evaluation

### Primary Metric: Stream Satisfaction
A stream is **satisfied** if all of its frames meet:
- ✅ **Bitrate constraint**: `frame_size / link_occupation_time ≤ link_capacity`
- ✅ **Temporal constraint**: Frame arrives at each hop sequentially
- ✅ **Latency constraint**: Total end-to-end latency ≤ stream's latency tolerance

### Key Performance Indicators
- **Satisfied Stream Count**: Number of streams meeting all constraints
- **Power Efficiency**: Average transmission power utilization (10-15% lower than TAS)
- **Scalability**: Performance under varying stream counts (10→500) and network sizes
- **Convergence Speed**: Iterations until algorithm terminates (typically 2-3)

### Comparison Benchmarks
- **TAS (FDMA)**: Traditional TSN scheduler without beamforming (baseline)
- **TAS (BF)**: TSN scheduler with equal-weight beamforming
- **BETS**: Proposed joint optimization (our contribution)

---

## Getting Started

### Prerequisites

- **Programming Language:** Python 3.8+
- **Dependencies:**
  - `numpy` for numerical computations
  - `scipy` for optimization routines
  - `matplotlib` for visualization
  - `pandas` (optional) for structured data handling
  - `pytest` (optional) for testing

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/bets-simulator.git
   cd bets-simulator
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Setting Up Your Simulation Environment

### Quick Start with main.py

The `main.py` file provides a complete example of how to set up and run BETS simulations. Here's what happens:

```python
# 1. Configure simulation parameters
BS_COUNT = 4                          # Number of base stations
UE_COUNT = 32                         # Number of user equipment
TOTAL_BANDWIDTH = 5000                # Total available bandwidth (Kbps)
COHERENCE_INTERVAL_DURATION_MS = 10   # Channel coherence duration (ms)
STREAM_COUNT = 150                    # Number of TSN streams to schedule

# 2. Set up the physical environment
environment = PhysicalEnvironment()
environment.evenly_spread_switches_over_the_ceiling(1, 0.3, 1, 1)
environment.evenly_spread_bs_over_the_ceiling(BS_COUNT, 0.3, BS_ROW, BS_COLUMN)
environment.randomly_spread_ue_over_ue_plane(UE_COUNT, 1)
environment.connect_ues_to_closest_bs()

# 3. Generate TSN streams with random parameters
streams = generate_streams(environment, STREAM_COUNT)

# 4. Initialize BETS enabler
enabler = setup_bets_enabler(environment, streams)

# 5. Run the BETS algorithm
enabler.run_bets_optimization()
```

### Creating a Custom Simulation

To create your own simulation:

#### Step 1: Define the Physical Environment
```python
from pythonProject.environment.physical_environment import PhysicalEnvironment

# Create environment with custom dimensions (x, y, z in meters)
env = PhysicalEnvironment(x_dimension=120, y_dimension=80, z_dimension=10)

# Add base stations (on ceiling, facing downward)
env.evenly_spread_bs_over_the_ceiling(
    bs_count=4,
    antenna_height=0.3,      # Height from ceiling
    row_count=2,
    column_count=2,
    total_bandwidth=5000,    # MHz
    guard_band=50            # MHz
)

# Add user equipment (on ground plane)
env.randomly_spread_ue_over_ue_plane(ue_count=32, seed=42)

# Establish connectivity
env.connect_ues_to_closest_bs()
```

#### Step 2: Define TSN Streams
```python
from pythonProject.traffic.tst_stream import Stream

streams = []
for i in range(num_streams):
    stream = Stream(
        name=f"Stream_{i}",
        periodic_cycle=5,           # ms - time between frames
        frame_payload=3000,         # bits
        latency_tolerance=5,        # ms - max end-to-end delay
        jitter_tolerance=0.5,       # ms
        reliability=99,             # percentage
        source=source_ue,
        destination=dest_ue,
        start_time=0
    )
    streams.append(stream)
```

#### Step 3: Initialize and Run BETS
```python
from pythonProject.bets_enabler.bets_enabler import BETSEnabler

enabler = BETSEnabler(
    environment=env,
    streams=streams,
    bet_generator=None,  # Best-effort traffic generator (optional)
    channel_coherence_duration=10,  # ms
    channel_sensing_time=0.1,       # ms
    wireless_propagation_delay=0.01 # ms
)

# Run optimization for one coherence interval
satisfied_streams = enabler.run_bets_optimization()
print(f"Satisfied {len(satisfied_streams)} out of {len(streams)} streams")
```

### Understanding Configuration Parameters

| Parameter | Description | Typical Value |
|-----------|-------------|----------------|
| `COHERENCE_INTERVAL_DURATION_MS` | Time window for which CSI remains valid (high SNR) | 10 ms |
| `TOTAL_BANDWIDTH` | Available spectrum (OFDMA resource blocks) | 50 MHz |
| `GUARD_BAND` | Frequency separation between UL and DL | 50 MHz |
| `AIR_PROPAGATION_DELAY` | Wireless signal travel time | 0.01 ms |
| `WIRED_LINK_CONSTANT_DELAY` | Wired link processing/propagation | 0.04 ms |
| `BS_ANTENNA_COUNT` | Number of transceiving elements per BS (URPA) | 60 (12×5) |
| `BS_POWER_BUDGET` | Maximum transmit power per BS | 1 Watt |

---

## Detailed Architecture

### Core Components

#### 1. **Physical Environment (`environment/`)**
Manages the 3D spatial layout and connectivity:
- **`physical_environment.py`**: Main environment orchestrator
  - Node placement (BSs on ceiling, UEs on ground plane)
  - Link establishment and topology management
  - History tracking for mobility analysis
  
- **`connection_manager.py`**: Graph-based network model
  - UE-BS associations
  - Path routing between nodes
  - Link bitrate calculations

- **`antenna_array/URPA.py`**: Uniform Rectangular Planar Array
  - Antenna element positions
  - Steering vector computation
  - Gain patterns (UPA geometry)

- **`channel_model/`**: mmWave Propagation Modeling
  - Stochastic path generation (LOS/NLOS/Outage)
  - Path clustering
  - Complex gain modeling
  - SINR calculations

#### 2. **BETS Algorithm (`bets_enabler/`)**
The core optimization engine:
- **`bets_enabler.py`**: Main orchestrator
  - Iterative optimization loop
  - Convergence monitoring
  - Variable initialization

- **`objective_function.py`**: Stream satisfaction evaluation
  - Bitrate constraint checking
  - Latency constraint verification
  - Satisfaction counting

- **`visualizer.py`**: Algorithm behavior visualization
  - Beamweight allocation plots
  - Bandwidth usage charts
  - Stream satisfaction rates

#### 3. **Beamforming (`beamforming/`)**
- **`digital_beamforming/zero_forcing.py`**: Zero-Forcing Precoder
  - Null interference generation
  - Weighted power allocation per UE
  
- **`digital_beamforming/beamweight_manager.py`**: Power distribution
  - Tracks per-UE power allocation
  - Enforces power constraints
  - Computes achievable rates

- **`analog_beamforming/beam_sweeping.py`**: Codebook-based analog steering

#### 4. **Spectrum Management (`environment/ofdm/`)**
- **`spectrum_manager.py`**: Frequency partition controller
  - Uplink/downlink bandwidth allocation
  - Guard band management
  - Per-UE subcarrier assignment

#### 5. **Scheduling (`scheduler/`)**
- **`hop_based_coherence_interval_aware_tst_scheduler.py`**: Main scheduler
  - Per-link arrival time assignment
  - Frame occupation duration calculation
  - Temporal consistency enforcement

#### 6. **Traffic Modeling (`traffic/`)**
- **`tst_stream.py`**: TSN stream definition
  - Periodic generation parameters
  - Latency/reliability requirements
  
- **`tst_frame.py`**: Individual frame instance
  - Per-link scheduling info
  - Satisfaction status tracking

#### 7. **Link & Rate Calculation (`ue_selection/`, `link/`)**
- **`cumulative_data_rate.py`**: Bitrate computation
  - SINR-to-rate mapping (Shannon capacity)
  - Per-link capacity calculation
  
- **`link.py`**: Wired and wireless link modeling
  - Queue management
  - Delay calculation

### Data Flow

```
1. User Input
   ├── Network topology (BS/UE placement)
   ├── TSN stream requirements
   └── Channel realizations
         ↓
2. Environment Setup
   ├── Physical coordinate assignment
   ├── Antenna array configuration
   ├── Connection topology
   └── Channel matrix computation
         ↓
3. Variable Initialization
   ├── Equal beamweights (1/M per UE)
   ├── Symmetric UL/DL split (50/50)
   └── Equal time partition scheduling
         ↓
4. BETS Optimization Loop
   ├─→ Phase 1: Beamweight Optimization
   │   ├── Identify satisfiable streams
   │   ├── Greedy stream selection
   │   └── Power allocation update
   │
   ├─→ Phase 2: Bandwidth Partitioning
   │   ├── Compute UL/DL splitting ranges
   │   ├── Find maximum overlapping interval
   │   └── Update spectrum allocation
   │
   ├─→ Phase 3: Schedule Optimization
   │   ├── Identify bottleneck links
   │   ├── Minimize occupation times
   │   └── Update arrival times
   │
   └─→ Check Convergence
       └─ If improved, loop back to Phase 1
         ↓
5. Output
   ├── Final beamweights
   ├── Optimized schedule
   ├── Satisfied stream list
   └── Performance metrics
```

### Key Algorithms

#### Beamweight Optimization (Greedy Algorithm)
```
1. Initialize: p_{b,u} = 0 for all BSs b, UEs u
2. Identify initially satisfiable streams
3. While satisfiable streams remain:
   a. For each candidate stream r:
      - Calculate minimum required beamweights
      - Estimate impact: new satisfied - no longer satisfiable
   b. Select stream with maximum positive impact
   c. Update beamweights to satisfy that stream
   d. Remove satisfied streams from candidate list
4. Return optimized beamweights
```

#### Bandwidth Partitioning (Interval Overlap Algorithm)
```
1. For each BS:
   a. Compute satisfiability interval for each stream
      [w_dn_min, w_dn_max] for downlink allocation
   b. Find maximum overlapping interval (MOI)
      - Sort interval boundaries
      - Find largest sub-interval covered by all intervals
   c. Assign UL/DL bandwidth at MOI center
2. Recalculate satisfied streams based on new bandwidth
```

#### Schedule Optimization (Bitrate-Gap Greedy)
```
1. Sort unsatisfied streams by maximum bitrate gap
2. For each stream in sorted order:
   a. For each frame in the stream:
      - Compute required occupation time per link
        ∆ = frame_size / link_bitrate + overhead
      - Update arrival times using temporal consistency
      - Check if total latency ≤ stream deadline
   b. If all frames within deadline: mark stream satisfied
3. Return updated schedule
```

### Computational Complexity

- **Beamweight Opt:** O(|R|² · |f_rt|) where |R| = stream count, |f_rt| = avg path length
- **Bandwidth Part:** O(B · |R| log|R|) where B = BS count
- **Schedule Opt:** O(|R| · |F_r| · |f_rt|) where |F_r| = frames per stream
- **Total per iteration:** Polynomial time with fast convergence (2-3 iterations typical)

---

## Contributing

Contributions are welcome! If you have ideas for improving the simulator, such as additional channel models or more sophisticated scheduling heuristics:

1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature
   ```
3. Implement and test your feature.
4. Submit a pull request.

Please ensure that new code is well-documented and includes tests.

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

## Contact

Author & Researcher: Mohammadreza Heydarian  
Email: [Mohammadreza.Heydarian@ugent.be](mailto:Mohammadreza.Heydarian@ugent.be)  
LinkedIn: [mrheydarian](https://www.linkedin.com/in/mrheydarian)

---
