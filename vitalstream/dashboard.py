"""Tkinter + Matplotlib clinician dashboard with live charts and alarm highlighting."""
import socket
import tkinter as tk
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from . import config, protocol

CHARTS = [
    ("temperature", "Body Temperature (°C)", "tab:red"),
    ("heart_rate", "Heart Rate (bpm)", "tab:blue"),
    ("respiration_rate", "Respiration Rate (/min)", "tab:green"),
    ("systolic_bp", "Systolic BP (mmHg)", "tab:purple"),
]


class Dashboard:
    REFRESH_MS = 1000

    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("VitalStream: Patient Monitor")
        root.geometry("1100x760")
        self.sock = socket.create_connection((config.SERVER_HOST, config.SERVER_PORT))
        self.patient_id: str | None = None

        bar = ttk.Frame(root, padding=8)
        bar.pack(fill=tk.X)
        ttk.Label(bar, text="Patient ID:").pack(side=tk.LEFT)
        self.pid_box = ttk.Combobox(bar, width=14, values=self._request({"type": "patients"}).get("patients", []))
        self.pid_box.pack(side=tk.LEFT, padx=6)
        ttk.Button(bar, text="Monitor", command=self.select_patient).pack(side=tk.LEFT)
        ttk.Button(bar, text="Refresh list", command=self.refresh_patients).pack(side=tk.LEFT, padx=6)
        self.status = ttk.Label(bar, text="Select a patient", font=("Segoe UI", 11, "bold"))
        self.status.pack(side=tk.RIGHT)

        self.latest = ttk.Label(root, text="", font=("Consolas", 11), padding=(10, 0))
        self.latest.pack(fill=tk.X)

        self.fig = Figure(figsize=(11, 6.5), dpi=100, tight_layout=True)
        self.axes = {key: self.fig.add_subplot(2, 2, i + 1) for i, (key, _, _) in enumerate(CHARTS)}
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.root.after(self.REFRESH_MS, self.refresh)

    def _request(self, msg: dict) -> dict:
        protocol.send(self.sock, msg)
        return protocol.recv(self.sock) or {}

    def refresh_patients(self):
        self.pid_box["values"] = self._request({"type": "patients"}).get("patients", [])

    def select_patient(self):
        pid = self.pid_box.get().strip()
        if not pid:
            messagebox.showinfo("VitalStream", "Please enter or choose a patient ID.")
            return
        self.patient_id = pid

    def refresh(self):
        if self.patient_id:
            history = self._request({"type": "query", "patient_id": self.patient_id, "limit": 120}).get("history", [])
            if history:
                self.draw(history)
            else:
                self.status.config(text=f"No data for {self.patient_id}", foreground="gray")
        self.root.after(self.REFRESH_MS, self.refresh)

    def draw(self, history: list[dict]):
        alarms = []
        x = list(range(len(history)))
        for key, title, color in CHARTS:
            ax = self.axes[key]
            ax.clear()
            y = [h[key] for h in history]
            lo, hi = config.NORMAL_RANGES[key]
            ax.axhspan(lo, hi, color="green", alpha=0.08)
            ax.plot(x, y, color=color, lw=1.6)
            ax.set_title(title, fontsize=10)
            ax.grid(alpha=0.3)
            if not lo <= y[-1] <= hi:
                alarms.append(title.split(" (")[0])
                ax.set_facecolor("#fff1f0")
        self.canvas.draw_idle()
        last = history[-1]
        self.latest.config(text=(f"{self.patient_id} @ {last['timestamp']}   "
                                 f"T {last['temperature']}°C   HR {last['heart_rate']}   RR {last['respiration_rate']}   "
                                 f"BP {last['systolic_bp']}/{last['diastolic_bp']}"))
        if alarms:
            self.status.config(text="ALARM: " + ", ".join(alarms), foreground="red")
        else:
            self.status.config(text="Stable", foreground="green")


if __name__ == "__main__":
    root = tk.Tk()
    Dashboard(root)
    root.mainloop()
