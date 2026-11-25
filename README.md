<div align="center">

# 🏥 VitalStream: Distributed Real-Time Patient Monitoring

**A client–server system that streams bedside vital signs over TCP, stores them in Redis and shows them on a live clinician dashboard with alarm detection.**

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Sockets](https://img.shields.io/badge/TCP_Sockets-555555?style=for-the-badge&logo=socketdotio&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)

</div>

---

## 📖 Overview

In an ICU, many bedside devices produce vital signs continuously, and clinicians need them in one place in real time. **VitalStream** models this as a small distributed system:

- **Device simulators** generate realistic, drifting vitals for many patients (temperature, heart rate, respiration rate and blood pressure), with occasional abnormal episodes.
- A **multi-threaded ingestion server** receives readings over TCP using a **length-prefixed JSON protocol**, then persists them in **Redis**.
- A **clinician dashboard** queries the server and plots each patient's recent trends, shading the normal ranges and raising **alarms** when a value falls outside them.

> This project started in the **Distributed Application Development** course (SBEN314, Cairo University). I later refactored it into a clean, tested, configurable package.

## 🏗️ Architecture

```
┌──────────────────┐   TCP · framed JSON   ┌────────────────────────┐   pipeline   ┌──────────────────────────┐
│ Device simulator │ ────── vitals ──────▶ │  Ingestion server      │ ───────────▶ │ Redis                    │
│ (N patients)     │ ◀────── ack ───────── │  thread per client     │              │ patient:{id}:latest (H)  │
└──────────────────┘                       │  vitals · query · list │ ◀─────────── │ patient:{id}:history (L) │
                                           └───────────▲────────────┘              │ patients (S) · pub/sub   │
┌──────────────────┐   query / patients               │                            └──────────────────────────┘
│ Clinician        │ ─────────────────────────────────┘
│ dashboard (Tk)   │  live charts + alarm banner
└──────────────────┘
```

### Design decisions
- **Message framing:** a 4-byte length header in front of each JSON body. This fixes the message-boundary bugs of naive `recv(1024)` code and is covered by unit tests.
- **Concurrency:** the server starts one thread per connection, so many devices and dashboards can be connected at once.
- **Data model:** the latest reading is a Redis **hash**, recent history is a **capped list** (`LTRIM` keeps memory bounded), and the patient registry is a **set**. Each update is also **published** on a `vitals` channel for future subscribers.
- **Atomic writes:** each update goes through a Redis **pipeline**, so the hash, list and set stay consistent.
- **Configuration:** everything is set through environment variables (`VS_SERVER_HOST`, `VS_REDIS_HOST`, …).

## 🔌 Protocol

| Request | Response |
|---|---|
| `{"type":"vitals","patient_id":"P1000","reading":{...}}` | `{"ok":true}` |
| `{"type":"query","patient_id":"P1000","limit":120}` | `{"ok":true,"history":[...]}` |
| `{"type":"patients"}` | `{"ok":true,"patients":["P1000",...]}` |

## 🚀 Getting Started

```bash
git clone https://github.com/Mohamedd-Ayyman/vitalstream-patient-monitoring.git
cd vitalstream-patient-monitoring
pip install -r requirements.txt
docker compose up -d                        # Redis

python -m vitalstream.server                # 1. start the ingestion server
python -m vitalstream.simulator -n 5        # 2. stream 5 simulated patients
python -m vitalstream.dashboard             # 3. open the dashboard and pick a patient
```

To run across machines (as in the original lab, which used VirtualBox VMs), set `VS_SERVER_HOST` to the server's IP address.

## 🧪 Tests

```bash
pytest -q
```

## 🗂️ Structure

```
vitalstream/
├── protocol.py    # length-prefixed JSON framing
├── server.py      # threaded TCP ingestion/query server
├── store.py       # Redis persistence (hash + capped list + set + pub/sub)
├── simulator.py   # multi-patient bedside device simulator
├── dashboard.py   # Tkinter/Matplotlib clinician dashboard
└── config.py      # env-driven settings & normal ranges
tests/             # protocol unit tests
```

## 👤 Author

**Mohamed Ayman** · [GitHub](https://github.com/Mohamedd-Ayyman) · [LinkedIn](https://linkedin.com/in/mohamed-ayman-8787b0269)
