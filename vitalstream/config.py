"""Central configuration, overridable through environment variables."""
import os

SERVER_HOST = os.getenv("VS_SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("VS_SERVER_PORT", "12345"))
REDIS_HOST = os.getenv("VS_REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("VS_REDIS_PORT", "6379"))
HISTORY_LENGTH = int(os.getenv("VS_HISTORY_LENGTH", "300"))  # samples kept per patient

# Normal adult ranges used for alarm highlighting
NORMAL_RANGES = {
    "temperature": (36.1, 37.8),   # °C
    "heart_rate": (60, 100),       # bpm
    "respiration_rate": (12, 20),  # breaths/min
    "systolic_bp": (90, 140),      # mmHg
}
