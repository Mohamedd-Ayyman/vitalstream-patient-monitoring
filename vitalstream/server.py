"""Multi-threaded TCP ingestion & query server.

Message types
-------------
{"type": "vitals", "patient_id": str, "reading": {...}}   -> stored, reply {"ok": true}
{"type": "query",  "patient_id": str, "limit": int}       -> reply {"ok": true, "history": [...]}
{"type": "patients"}                                      -> reply {"ok": true, "patients": [...]}
"""
import logging
import socket
import threading

from . import config, protocol
from .store import VitalsStore

log = logging.getLogger("vitalstream.server")


def handle(conn: socket.socket, addr, store: VitalsStore) -> None:
    log.info("client connected: %s:%s", *addr)
    with conn:
        while True:
            try:
                msg = protocol.recv(conn)
            except (ValueError, ConnectionError) as exc:
                log.warning("bad message from %s: %s", addr, exc)
                break
            if msg is None:
                break
            kind = msg.get("type")
            try:
                if kind == "vitals":
                    store.save(str(msg["patient_id"]), msg["reading"])
                    protocol.send(conn, {"ok": True})
                elif kind == "query":
                    protocol.send(conn, {"ok": True, "history": store.history(str(msg["patient_id"]), int(msg.get("limit", 120)))})
                elif kind == "patients":
                    protocol.send(conn, {"ok": True, "patients": store.patients()})
                else:
                    protocol.send(conn, {"ok": False, "error": f"unknown type {kind!r}"})
            except (KeyError, TypeError) as exc:
                protocol.send(conn, {"ok": False, "error": f"malformed message: {exc}"})
    log.info("client disconnected: %s:%s", *addr)


def serve(host: str = config.SERVER_HOST, port: int = config.SERVER_PORT) -> None:
    store = VitalsStore()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen()
        log.info("VitalStream server listening on %s:%s", host, port)
        while True:
            conn, addr = srv.accept()
            threading.Thread(target=handle, args=(conn, addr, store), daemon=True).start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    serve()
