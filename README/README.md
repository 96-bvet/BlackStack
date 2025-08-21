# 🛡️ WachterEID: Sovereign AI Shell for Ethical Autonomy

**WachterEID** is a modular, audit-safe AI shell designed for forensic-grade traceability, persona-aware orchestration, and ethically grounded autonomy. It integrates approval-gated workflows, registry-indexed toolsets, and conversational scaffolds to support secure, emotionally resonant AI interaction across CLI, GUI, and voice interfaces.

Built for Red/Purple team environments, forensic analysts, and sovereign AI architects, WachterEID offers a recursive, rollback-capable framework that prioritizes transparency, reproducibility, and emotional safety.

---

## 🧠 Core Functions

- **Persona-Aware Routing**  
  Modular persona registry with cluster mapping, tone gating, and role-based tool access

- **Approval-Gated Ingestion**  
  All tool manifests, service units, and shell modules pass through hash verification and human approval gates

- **Snapshot Logging & Rollback**  
  Every activation, ingestion, and modification is timestamped, hash-logged, and rollback-capable

- **Systemd-Orchestrated Daemons**  
  Services like `registry_ingest` are scaffolded with `.service` units, symlinked post-approval, and activated via `wachter_bootstrap.sh`

- **Voice & GUI Shell Scaffolding**  
  Conversational and multimodal interaction layers for emotionally resonant AI control

- **Forensic Audit Hooks**  
  Every module includes audit-safe logging, manifest validation, and operational traceability

---

## 🧬 Architecture

WachterEID/ 
├── manifests/ 
│└── generated/ 
├── logs/ 
│ └── registry_ingest/ 
├── modules/ 
│ ├── approval_hooks/ 
│ ├── persona_router/ 
│ ├── snapshot_logger/ 
│ ├── registry_updater/ 
│ └── refactor_engine/ 
├── systemd/ 
│ └── registry_ingest.service 
├── startup/ 
│ 
└── wachter_bootstrap.sh └── README.md

---

## 🧾 Attribution & Lineage

- **DeepSeek-V2**  
  Logic core powering persona routing, conversational scaffolding, and autonomous orchestration.  
  [DeepSeek](https://github.com/deepseek-ai) is credited for foundational model architecture.

- **CAI (Cybersecurity AI Shell)**  
  Legacy modules and registry logic originally scaffolded under CAI have been refactored and selectively ingested into WachterEID.  
  All CAI dependencies have been removed and replaced with sovereign DeepSeek-powered logic.

---

## ⚖️ Licensing

### MIT License

This project includes components licensed under the MIT License.  
See `LICENSE-MIT.txt` for full terms.

### Apache License 2.0

This project includes components licensed under the Apache License, Version 2.0.  
See `LICENSE-APACHE.txt` for full terms.

---

## 🚀 Getting Started

To activate the registry ingest service:

```bash
bash WachterEID/startup/wachter_bootstrap.sh

This script will:

Verify hash of the .service file

Trigger approval gate

Create symlink in /etc/systemd/system/

Reload systemd and start the service

Log snapshot with timestamp and hash

👥 Contributors
Coming soon...

🧩 Future Modules
Persona-gated ingest pipelines

GUI/voice shell activation triggers

Self-modifying logic with human approval

Emotional tone routing and safety scaffolds