"""Redis persistence layer for patient vitals."""
import json
import redis

from . import config


class VitalsStore:
    def __init__(self, client: "redis.Redis | None" = None):
        self.r = client or redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)

    @staticmethod
    def _latest_key(pid: str) -> str:
        return f"patient:{pid}:latest"

    @staticmethod
    def _history_key(pid: str) -> str:
        return f"patient:{pid}:history"

    def save(self, patient_id: str, reading: dict) -> None:
        """Store the latest reading (hash) and append to a capped history list."""
        pipe = self.r.pipeline()
        pipe.hset(self._latest_key(patient_id), mapping={k: str(v) for k, v in reading.items()})
        pipe.rpush(self._history_key(patient_id), json.dumps(reading))
        pipe.ltrim(self._history_key(patient_id), -config.HISTORY_LENGTH, -1)
        pipe.sadd("patients", patient_id)
        pipe.publish("vitals", json.dumps({"patient_id": patient_id, **reading}))
        pipe.execute()

    def latest(self, patient_id: str) -> dict:
        return self.r.hgetall(self._latest_key(patient_id))

    def history(self, patient_id: str, limit: int = 120) -> list[dict]:
        return [json.loads(x) for x in self.r.lrange(self._history_key(patient_id), -limit, -1)]

    def patients(self) -> list[str]:
        return sorted(self.r.smembers("patients"))
