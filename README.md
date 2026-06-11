<h1 align="center">TRINITY</h1>
<h3 align="center">A Decentralized Framework for Privacy-Preserving Intelligence Sharing in Smart City IoT Ecosystems</h3>
<h5 align="center">Research Project — <a href="https://linkedin.com/in/p1r3x">Pavan Raja · AM.SC.P2CSN24014</a> (2026)</h5>

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

## ➤ Table of Contents

<details open>
<summary>Expand</summary>

1. [Overview](#-overview)
2. [Key Features](#-key-features)
3. [Architecture](#-architecture)
4. [Technology Stack](#-technology-stack)
5. [Prerequisites](#prerequisites)
6. [Configuration](#-configuration)
7. [Dataset](#-dataset)
8. [Methodology](#-methodology)
9. [Security Features](#-security-features)
10. [Experimental Results](#-experimental-results)
11. [Threat Model](#-threat-model)

</details>

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

## ➤ Overview

Modern smart cities deploy billions of heterogeneous IoT sensors across transportation networks, energy grids, public safety systems, and industrial control infrastructure. Effective intrusion detection across these deployments demands access to rich, diverse network telemetry from all city nodes — yet aggregating such data violates data sovereignty principles, GDPR obligations, and domestic data protection mandates. **Centralized IDS architectures are fundamentally incompatible with this privacy reality.**

**TRINITY** resolves this contradiction with a three-layer privacy-preserving federated learning framework purpose-built for smart-city IoT intrusion detection. Three heterogeneous city nodes — a *Residential Smart City* (City A), a *Commercial Smart City* (City B), and an *Industrial Smart City* (City C) — collaboratively train a global threat detection model without ever sharing raw network telemetry.

The framework integrates three orthogonal privacy mechanisms into a single unified pipeline:

- **FedProx** federated learning with non-IID-aware proximal regularization
- **Rényi Differential Privacy (RDP)** via Opacus with per-sample gradient clipping and Gaussian noise injection (ε = 10.0, δ = 10⁻⁵)
- **CKKS homomorphic encryption** via TenSEAL ensuring the aggregation server never observes plaintext client updates

A fourth **Hyperledger Fabric blockchain auditability layer** anchors SHA-256 model hashes to an immutable ledger after every aggregation round, providing cryptographic model provenance for regulatory compliance.

Evaluated on the real **ToN_IoT network intrusion dataset** (183,580 samples, 9 attack subtypes) under a non-IID Dirichlet (α = 0.3) partition, TRINITY achieves **96.83% accuracy** and **0.9255 F1-score** under full privacy protection — representing a privacy overhead of only **1.42 percentage points** versus the unprotected FedAvg baseline. Blockchain audit latency adds approximately **0.3 seconds per round**.

> 📄 **Paper:** *TRINITY: A Privacy-Preserving Federated Learning Framework for Secure Smart-City IoT* — to be submitted

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

## ➤ Key Features

| Feature | Description |
|:---|:---|
| **Multi-Layer Privacy Stack** | Three orthogonal privacy mechanisms (FedProx + DP + CKKS) operate independently, so each layer can be enabled or disabled without interfering with the others. |
| **Non-IID Federated Learning** | FedProx proximal regularization (µ = 0.01) handles heterogeneous city-node distributions; Dirichlet (α = 0.3) partitioning simulates realistic residential, commercial, and industrial traffic profiles. |
| **Formal Differential Privacy** | Opacus PrivacyEngine with per-sample gradient clipping (C = 1.0) and Gaussian noise (σ = 1.1). Privacy budget tracked via tight RDP composition; ε = 10.0 at δ = 10⁻⁵ exhausted at round 12 of 50. |
| **CKKS Homomorphic Aggregation** | TenSEAL CKKS (poly_mod = 8192, 128-bit security) encrypts client weights before upload. The server aggregates entirely in ciphertext space — no plaintext client update is ever observed. |
| **Blockchain Model Provenance** | Hyperledger Fabric 2.5.4 with custom chaincode records SHA-256 model hashes on-ledger after every round. 50 genuine blockchain transactions produced per full experimental campaign. |
| **Minimal Utility Degradation** | Full privacy stack (DP + CKKS + Blockchain) incurs only 1.42% accuracy drop vs. the unprotected FedAvg baseline (96.83% vs. 98.25%). |
| **Five Configurable Experiments** | Ablation-style experimental suite (FedAvg → FedProx → +DP → +SMPC → Full TRINITY) enables systematic privacy-utility-latency characterisation. |
| **Real IoT Intrusion Dataset** | Evaluated on the real ToN_IoT network dataset (not synthetic), 9 attack subtypes, 183,580 samples, under principled non-IID partitioning. |
| **Production-Grade Infrastructure** | NVFLARE 2.4.1 provisioning with TLS certificates, mutual authentication, and per-participant cryptographic identities for all FL nodes. |
| **Adversarial Demo** | Standalone adversarial scenario script for demonstrating attack resilience. |

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

## ➤ Architecture

TRINITY implements a five-layer hierarchical system architecture. Each layer has a clearly defined security boundary and communicates with adjacent layers through well-specified interfaces.

![TRINITY Architecture](/docs/architecture.png)

> *Fig. 1 — TRINITY multi-layer privacy-preserving federated learning architecture integrating Differential Privacy, CKKS Secure Aggregation, and Hyperledger Fabric blockchain auditability for secure smart-city IoT intrusion detection.*

### Layer Description

**Layer 1 — Smart City IoT Client Layer**

Three federated learning clients represent distinct urban deployment profiles. Each city node runs a local IDS engine, maintains a non-IID local dataset, and executes `ThreatDetectorMLP` local training via FedProx.

- **City A (site-1):** Residential Smart City — 77.8% normal / 22.2% attack traffic. Devices: smart home sensors, IoT gateways, CCTV.
- **City B (site-2):** Commercial Smart City — 50.0% normal / 50.0% attack traffic. Devices: building IoT, commercial gateways.
- **City C (site-3):** Industrial Smart City — 20.0% normal / 80.0% attack traffic. Devices: PLC/SCADA, industrial IoT, CCTV.

**Layer 2 — Differential Privacy Layer (Opacus)**

Wraps each client's local training loop with per-sample gradient clipping (ℓ₂ norm, C = 1.0) and Gaussian noise injection (σ = 1.1). The RDP accountant tracks privacy budget consumption. Noisy gradients are produced before any network transmission.

**Layer 3 — CKKS Secure Aggregation Layer (TenSEAL)**

Client model weights or noisy gradients are encrypted using CKKS homomorphic encryption before upload. The FL orchestration server performs weighted aggregation entirely in ciphertext space via homomorphic addition. Only the decrypted aggregate is recovered — no individual client plaintext is ever accessible to the server.

**Layer 4 — FL Orchestration Server Layer (NVFLARE)**

Hosts the FedProx / FedAvg aggregation engine, global model manager, and scatter-gather workflow. Receives encrypted client updates, performs encrypted aggregation, decrypts only the global aggregate, and broadcasts the updated global model back to all clients.

**Layer 5 — Blockchain Auditability Layer (Hyperledger Fabric)**

After each aggregation round, a SHA-256 hash of the global model is committed to the Hyperledger Fabric permissioned ledger via the `RecordGlobalModel` chaincode function. Three peer organisations (CityAMSP, CityBMSP, CityCMSP) and one etcdraft orderer participate. The `VerifyModelHash` chaincode function enables any authorised party to verify model integrity at any point.

### Communication Flow

```
City Nodes (Local Training)
    │
    │  Noisy Gradients (DP applied locally)
    ▼
CKKS Encrypt (TenSEAL)
    │
    │  Ciphertexts only — no plaintext leaves the client
    ▼
FL Orchestration Server
    │
    │  Homomorphic Aggregation in Encrypted Space
    ▼
CKKS Decrypt (Aggregate Only)
    │
    ├──► Global Model Broadcast → City Nodes
    │
    └──► SHA-256 Hash → Hyperledger Fabric Ledger
```

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

## ➤ Technology Stack

| Layer | Technology | Version | Purpose |
|:---|:---|:---|:---|
| **FL Framework** | NVFLARE | 2.4.1 | Infrastructure provisioning, TLS, cryptographic identities, FL orchestration |
| **FL Algorithm** | FedProx / FedAvg | Custom | Non-IID-aware federated aggregation with proximal regularization |
| **Deep Learning** | PyTorch | 2.1.2+cu121 | ThreatDetectorMLP local training, GPU acceleration |
| **Differential Privacy** | Opacus | 1.4.0 | Per-sample gradient clipping, Gaussian noise injection, RDP accounting |
| **Homomorphic Encryption** | TenSEAL | 0.3.14 | CKKS scheme, encrypted weight aggregation |
| **Blockchain** | Hyperledger Fabric | 2.5.4 | Permissioned ledger, model hash provenance, chaincode (Go) |
| **Container Orchestration** | Docker / Compose | 29.1.3 | Multi-service deployment (Fabric peers, orderer, CA) |
| **Smart Contract Runtime** | Go | 1.20.14 | Hyperledger Fabric chaincode |
| **Blockchain SDK** | Node.js | 18.20.8 | Fabric Gateway SDK for hash submission |
| **Data Processing** | scikit-learn | — | LabelEncoder, StandardScaler, preprocessing pipeline |
| **Experiment Tracking** | JSON / CSV | — | Structured result logging across all 5 experimental configurations |
| **Visualisation** | matplotlib / seaborn | — | Convergence curves, confusion matrices, ROC curves, radar charts |
| **Operating System** | Ubuntu Server | 24.xx | Host environment |
| **GPU** | NVIDIA CUDA | 12.1 | Accelerated local training |
| **Language** | Python | 3.10.12 | All FL, DP, SMPC, and evaluation scripts |

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

## ➤ Prerequisites

| Requirement | Version | Notes |
|:---|:---|:---|
| Ubuntu | 22.04 / 24.xx | Tested on Ubuntu Server 24.xx |
| Python | 3.10.12 | Required for Opacus compatibility |
| CUDA | 12.1 | NVIDIA GPU strongly recommended; CPU fallback available |
| Docker | 29.1.3+ | Required for Hyperledger Fabric network |
| Docker Compose | v2+ | Fabric multi-service orchestration |
| Node.js | 18.20.8 | Fabric Gateway SDK |
| Go | 1.20.14 | Chaincode compilation |

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

## ➤ Configuration

### FL Hyperparameters (`project.yml`)

| Parameter | Value | Rationale |
|:---|:---|:---|
| FL Rounds (T) | 50 | Standard convergence window for non-IID FL |
| Local Epochs (E) | 5 | Balance communication/computation efficiency |
| Batch Size | 256 | Optimal for GPU utilisation and DP sampling rate |
| Learning Rate (η) | 1×10⁻³ | Adam optimizer default; stable across all configurations |
| FedProx µ | 0.01 | Conservative proximal coefficient; minimal but effective constraint |
| Aggregation | Weighted FedAvg | Proportional to each client's dataset size |
| Random Seed | 42 | Fixed for full reproducibility |

### Privacy Hyperparameters

| Parameter | Value | Justification |
|:---|:---|:---|
| Max Grad Norm (C) | 1.0 | Standard sensitivity bound for DP-FL |
| Noise Multiplier (σ) | 1.1 | Achieves ε ≈ 10.0 at δ = 10⁻⁵ over ~12 rounds |
| Target ε | 10.0 | Pragmatic privacy-utility operating point |
| Target δ | 10⁻⁵ | Strictly < 1/N for all client dataset sizes |
| Accountant | RDP (Opacus) | Tighter than classical (ε, δ)-DP composition |
| CKKS poly_mod | 8,192 | 128-bit security, 4,096 slots per ciphertext |
| CKKS scale | 2⁴⁰ | Sufficient precision for float32 weight ranges |

### NVFLARE Participant Configuration

The `fl_project/trinity_fl/prod_00/` directory contains ready-to-use NVFLARE startup configurations:

- `server/startup/fed_server.json` — FL server endpoint and TLS settings
- `site-{1,2,3}/startup/fed_client.json` — City node client configuration and server address
- `admin@trinity.local/startup/fed_admin.json` — Admin console configuration
- All participants include `rootCA.pem`, `client.crt`, and `client.key` for mutual TLS authentication

### Blockchain Configuration

The Hyperledger Fabric network is configured for three peer organisations representing the three city nodes:

- **CityAMSP** → `peer0.city_a.trinity.local`
- **CityBMSP** → `peer0.city_b.trinity.local`
- **CityCMSP** → `peer0.city_c.trinity.local`
- **Orderer** → `orderer.trinity.local` (etcdraft single-node; expand to 3+ for production)

The `cti_audit` chaincode is deployed in CCaaS mode and exposes two functions: `RecordGlobalModel` (idempotent per-round hash submission) and `VerifyModelHash` (integrity verification).

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

## ➤ Dataset

### ToN_IoT Network Intrusion Dataset

| Property | Value |
|:---|:---|
| **Source** | University of New South Wales (UNSW) Canberra — [ToN_IoT Datasets](https://research.unsw.edu.au/projects/toniot-datasets) |
| **Total Samples** | 183,580 (after deduplication and cleaning) |
| **Features** | 44 raw → 40 after preprocessing |
| **Attack Subtypes** | 9 (backdoor, DDoS, DoS, injection, password, ransomware, scanning, XSS, MitM) |
| **Normal Traffic** | 50,000 samples (27.2%) |
| **Attack Traffic** | 133,580 samples (72.8%) |
| **Dataset Type** | Real-world IoT network captures (not synthetic) |

### Class Distribution

| Class | Samples | Proportion |
|:---|:---|:---|
| Normal | 50,000 | 27.2% |
| Backdoor | 20,000 | 10.9% |
| DDoS | 20,000 | 10.9% |
| DoS | 20,000 | 10.9% |
| Injection | 20,000 | 10.9% |
| Password | 20,000 | 10.9% |
| Ransomware | 20,000 | 10.9% |
| Scanning | 20,000 | 10.9% |
| XSS | 20,000 | 10.9% |
| MitM | 1,043 | 0.6% |

The pronounced underrepresentation of the MitM class reflects real capture conditions and is **strictly preserved** in TRINITY's evaluation — no artificial class balancing is applied.

### Feature Engineering Pipeline

1. **Categorical Encoding:** 16 categorical features are label-encoded using scikit-learn's `LabelEncoder`, fitted on the training partition only.
2. **Numeric Normalisation:** 24 numeric features are standardised (zero mean, unit variance) using `StandardScaler` fitted on training data only, preventing data leakage.
3. **IP Address Removal:** `src_ip` and `dst_ip` dropped as session-specific identifiers that would constitute spurious features in cross-session evaluation.
4. **Final Dimensionality:** 40 features, matching the `ThreatDetectorMLP` input layer.

### Non-IID City Partitioning

TRINITY simulates realistic smart-city heterogeneity through a two-level partitioning scheme.

**Level 1 — Label Skew** (reflecting urban deployment profiles):

| Node | Samples | Normal% | Attack% | Train | Val | Test |
|:---|:---|:---|:---|:---|:---|:---|
| City A (site-1) | 53,973 | 77.8 | 22.2 | 37,781 | 8,096 | 8,096 |
| City B (site-2) | 60,000 | 50.0 | 50.0 | 42,000 | 9,000 | 9,000 |
| City C (site-3) | 60,000 | 20.0 | 80.0 | 42,000 | 9,000 | 9,000 |

**Level 2 — Attack Subtype Skew:** Within attack samples, subtype proportions are drawn from a Dirichlet distribution with concentration parameter α = 0.3.

**Non-IID Severity (KL Divergence):**

- D_KL(City_A ‖ City_B) = 2.026
- D_KL(City_A ‖ City_C) = **2.9344** — confirming substantially heterogeneous distributions
- D_KL(City_B ‖ City_C) = 4.702

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

## ➤ Methodology

### ThreatDetectorMLP Architecture

A four-layer fully connected network (52,674 parameters) designed for DP compatibility, edge efficiency, and FL suitability:

```
Input (40 features)
    │
    ├── Linear(40 → 256) → GroupNorm(32 groups) → ReLU → Dropout(0.3)
    │
    ├── Linear(256 → 128) → GroupNorm(16 groups) → ReLU → Dropout(0.3)
    │
    ├── Linear(128 → 64) → GroupNorm(8 groups) → ReLU → Dropout(0.3)
    │
    └── Linear(64 → 2) → Logits {Normal, Attack}
```

**Design rationale:**

- **GroupNorm instead of BatchNorm:** Opacus requires modules without cross-sample statistics aggregation. GroupNorm normalises within groups per sample, fully compatible with per-sample gradient isolation.
- **52,674 parameters (~206 KB float32):** Compact enough for IoT gateway deployment (Raspberry Pi 4) and efficient FL round communication.
- **He initialisation:** Applied to all linear layers for stable convergence across distributed nodes with limited local epochs.

### FedAvg Baseline

Standard weighted averaging of local model updates: the global model at round t+1 is the dataset-size-weighted average of all client models after E = 5 local epochs.

### FedProx Algorithm

Adds a proximal regularisation term to each client's local objective:

```
h_k(w; w^t) = F_k(w) + (µ/2) * ||w - w^t||²
```

where µ = 0.01 penalises local models that drift excessively from the global model, improving convergence stability under high non-IID conditions.

### Differential Privacy (Opacus)

For each mini-batch B during local training:

1. **Per-sample gradient computation:** Each sample's gradient is computed independently.
2. **Gradient clipping:** Each per-sample gradient is clipped to ℓ₂ norm ≤ C = 1.0.
3. **Gaussian noise injection:** Calibrated noise N(0, σ²C²I) is added to the clipped gradient sum.
4. **RDP accounting:** Privacy budget is tracked using Rényi DP composition for tight (ε, δ)-DP guarantees.

### CKKS Secure Aggregation (TenSEAL)

Client model weights (52,674 float32 parameters packed across ~14 ciphertexts) are encrypted using CKKS before transmission. The server performs weighted aggregation via homomorphic scalar multiplication and addition, then decrypts only the final aggregate — individual client updates remain ciphertext throughout.

**CKKS Parameters:** `poly_modulus_degree` = 8192, coefficient modulus = [60, 40, 40, 60] bits (200-bit total, ~128-bit security), global scale = 2⁴⁰.

### Five Experimental Configurations

| Exp. | Name | DP | SMPC | Blockchain | Description |
|:---|:---|:---:|:---:|:---:|:---|
| proj1 | FedAvg | ✗ | ✗ | ✗ | Unprotected FedAvg baseline |
| proj2 | FedProx | ✗ | ✗ | ✗ | Non-IID optimised, no privacy |
| proj3 | FedProx+DP | ✓ | ✗ | ✗ | Formal differential privacy only |
| proj4 | FedProx+SMPC | ✗ | ✓ | ✗ | Encrypted aggregation only |
| proj5 | Full TRINITY | ✓ | ✓ | ✓ | Complete privacy stack |

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

## ➤ Security Features

### Gradient-Level Privacy (Differential Privacy)

Opacus PrivacyEngine enforces formal (ε, δ)-DP guarantees at every local training step. Per-sample gradient clipping bounds sensitivity; Gaussian noise injection provides provable protection against gradient inversion attacks. The RDP accountant provides tighter privacy accounting than classical composition, enabling the ε = 10.0 budget to support 12 fully protected rounds before saturation.

### Aggregation-Level Privacy (CKKS Homomorphic Encryption)

TenSEAL CKKS encryption ensures the aggregation server is cryptographically incapable of observing any individual client's plaintext model weights. All arithmetic during aggregation is performed directly on packed ciphertext polynomial vectors. Security is grounded in the hardness of the Ring Learning With Errors (RLWE) problem under the configured 128-bit lattice parameters.

### Model Integrity (Blockchain Provenance)

After every FL aggregation round, a SHA-256 hash of the serialised global model is submitted to the Hyperledger Fabric ledger via the `RecordGlobalModel` chaincode. The function enforces **idempotency** — duplicate submissions for the same round are rejected, preventing replay attacks. The `VerifyModelHash` function enables any authorised city node to verify a received model's integrity before deploying it to a live IDS. A hash mismatch constitutes cryptographic proof of tampering.

### Authentication & Transport Security

NVFLARE provisions mutual TLS certificates for all participants (server, three city clients, admin). All FL communication is authenticated and encrypted at the transport layer. Hyperledger Fabric enforces MSP-based identity for all blockchain transactions.

### FedProx Poisoning Resistance

The proximal term (µ = 0.01) limits the ℓ₂-norm deviation of any client update from the global model, providing passive resistance to model poisoning. Per-sample gradient clipping (C = 1.0) further bounds the maximum injection magnitude a rogue client can introduce per round.

> ⚠️ **Note:** TRINITY does not implement explicit Byzantine-robust aggregation (e.g., Krum, FLTrust). Byzantine robustness is acknowledged as a limitation and is identified as future work.

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

## ➤ Experimental Results

### Summary Performance Table

| Experiment | Accuracy | Precision | Recall | F1-Score | Latency/Round | Privacy |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| **FedAvg (proj1)** | 98.25% | 0.9505 | 0.9717 | 0.9610 | 10.68 s | None |
| **FedProx (proj2)** | 98.16% | 0.9545 | 0.9672 | 0.9592 | 10.67 s | None |
| **FedProx+DP (proj3)** | 96.76% | 0.9382 | 0.9107 | 0.9242 | 23.79 s | DP |
| **FedProx+SMPC (proj4)** | **98.49%** | **0.9571** | **0.9754** | **0.9662** | 11.18 s | CKKS |
| **Full TRINITY (proj5)** | 96.83% | 0.9401 | 0.9113 | 0.9255 | 24.46 s | DP+CKKS |

### Privacy-Utility Tradeoff

```
Δ Accuracy  = 98.25% − 96.83% = 1.42%   (Full TRINITY vs. FedAvg baseline)
Δ F1-Score  = 0.9610 − 0.9255 = 0.0355
```

**Full privacy protection (DP + CKKS + Blockchain) costs only 1.42 percentage points of accuracy** — a practically compelling operating point for production-grade collaborative IoT threat intelligence.

### Latency Decomposition (Full TRINITY — proj5)

| Component | Latency (s) | % of Total |
|:---|:---:|:---:|
| FL Base (FedAvg) | 10.68 | 43.7% |
| DP Overhead | 13.11 | 53.6% |
| SMPC/CKKS Overhead | 0.51 | 2.1% |
| Blockchain Commit | **0.30** | **1.2%** |
| **Total (proj5)** | **24.46** | **100%** |

**Key observations:**

- **DP dominates latency** (53.6%) due to per-sample gradient tracking replacing batch-level parallelisation.
- **CKKS overhead is minimal** (2.1%) — approximate arithmetic on 52,674-parameter models is computationally lightweight.
- **Blockchain overhead is negligible** (1.2%) — asynchronous ledger commitment adds only 0.30 s/round.
- **SMPC unexpectedly improves accuracy** (+0.24% vs. FedProx alone) — CKKS approximate arithmetic introduces slight weight perturbations that act as a stabilising regulariser.

### Result Plots

All plots are available in `results/plots/`:

| Plot | File |
|:---|:---|
| Convergence curves (all 5 experiments) | `convergence_all_5_subplots.png` |
| Accuracy & F1 comparison bar chart | `accuracy_f1_comparison.png` |
| Performance metrics heatmap (5×4) | `metrics_heatmap.png` |
| Multi-dimensional radar chart | `radar_comparison.png` |
| Privacy-utility-latency tradeoff | `privacy_utility_tradeoff.png` |
| DP budget consumption per city | `dp_budget_per_city.png` |
| Latency breakdown (stacked bar) | `latency_breakdown.png` |
| ROC curves (all experiments) | `roc_all_experiments.png` |
| Confusion matrices (all 5 configs) | `cm_proj{1-5}_*.png` |
| KL divergence heatmap | `kl_divergence_heatmap.png` |
| Attack type distribution (real data) | `attack_type_real.png` |
| Full pipeline analysis (proj5) | `proj5_full_pipeline.png` |

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

## ➤ Threat Model

TRINITY assumes the **honest-but-curious (semi-honest) adversary model** — the standard assumption for establishing baseline security properties in multi-party optimisation. Participants follow the FL protocol faithfully but may attempt to extract private information from observed parameters.

| Attack | Description | TRINITY Mitigation |
|:---|:---|:---|
| **Gradient Inversion** | Adversary reconstructs training samples from raw gradient updates using deep leakage optimisation. | Per-sample gradient clipping + Gaussian noise injection. DP with ε = 10.0 formally bounds reconstruction advantage. |
| **Membership Inference** | Adversary queries the global model to determine if a specific network flow record appeared in a client's training set. | Local DP provides formal membership inference bound: Pr[success] ≤ e^ε · Pr[failure] + δ. |
| **Model Poisoning** | Malicious client submits crafted updates to implant a backdoor or degrade global accuracy. | FedProx proximal term limits client drift; per-sample clipping bounds injection magnitude (‖g‖₂ ≤ C = 1.0); blockchain enables post-hoc anomaly tracing. |
| **Model Integrity Tampering** | Adversary intercepts and replaces the global model between server aggregation and city IDS deployment. | SHA-256 hash committed to immutable Fabric ledger; `VerifyModelHash` chaincode provides cryptographic proof of tampering on mismatch. |
| **Eavesdropping (Communication Intercept)** | Network-level adversary intercepts client-to-server communications to recover plaintext model weights. | CKKS encryption ensures all transmissions are semantically secure ciphertexts; aggregation occurs in the encrypted domain; RLWE hardness renders brute-force decryption infeasible. |

**Out-of-scope (acknowledged limitations):**

- Byzantine-malicious clients (coordinated adversarial updates) — requires explicit Byzantine-robust aggregation (Krum, FLTrust, Bulyan), not currently implemented.
- Fully compromised aggregation server — threshold HE would be required to eliminate the trusted aggregator assumption.

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)
