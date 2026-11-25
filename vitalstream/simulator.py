"""Bedside-device simulator: streams realistic vitals for several patients."""
import argparse
import random
import socket
import time
from datetime import datetime

from . import config, protocol


class Patient:
    """Random-walk vitals around a per-patient baseline, with occasional episodes."""

    def __init__(self, pid: str):
        self.pid = pid
        self.temp = random.uniform(36.4, 37.2)
        self.hr = random.uniform(65, 85)
        self.rr = random.uniform(13, 17)
        self.sys = random.uniform(105, 125)
        self.dia = random.uniform(65, 80)

    def step(self) -> dict:
        drift = lambda v, s, lo, hi: min(hi, max(lo, v + random.gauss(0, s)))
        self.temp = drift(self.temp, 0.05, 35.5, 40.0)
        self.hr = drift(self.hr, 1.5, 40, 160)
        self.rr = drift(self.rr, 0.4, 8, 30)
        self.sys = drift(self.sys, 1.5, 80, 180)
        self.dia = drift(self.dia, 1.0, 50, 110)
        if random.random() < 0.01:  # rare tachycardic episode
            self.hr += random.uniform(20, 35)
        return {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "temperature": round(self.temp, 1),
            "heart_rate": round(self.hr),
            "respiration_rate": round(self.rr),
            "systolic_bp": round(self.sys),
            "diastolic_bp": round(self.dia),
        }


def run(n_patients: int, interval: float) -> None:
    patients = [Patient(f"P{1000 + i}") for i in range(n_patients)]
    with socket.create_connection((config.SERVER_HOST, config.SERVER_PORT)) as sock:
        print(f"Streaming {n_patients} patients to {config.SERVER_HOST}:{config.SERVER_PORT} (Ctrl+C to stop)")
        while True:
            for p in patients:
                protocol.send(sock, {"type": "vitals", "patient_id": p.pid, "reading": p.step()})
                protocol.recv(sock)  # ack
            time.sleep(interval)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="VitalStream bedside device simulator")
    ap.add_argument("-n", "--patients", type=int, default=5)
    ap.add_argument("-i", "--interval", type=float, default=1.0, help="seconds between samples")
    args = ap.parse_args()
    run(args.patients, args.interval)
