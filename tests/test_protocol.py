import socket
import threading

from vitalstream import protocol


def test_roundtrip_over_socketpair():
    a, b = socket.socketpair()
    msg = {"type": "vitals", "patient_id": "P1000", "reading": {"heart_rate": 72}}
    threading.Thread(target=protocol.send, args=(a, msg)).start()
    assert protocol.recv(b) == msg
    a.close(); b.close()


def test_multiple_messages_keep_boundaries():
    a, b = socket.socketpair()
    msgs = [{"i": i, "pad": "x" * (i * 500)} for i in range(5)]
    a.sendall(b"".join(protocol.encode(m) for m in msgs))
    assert [protocol.recv(b) for _ in msgs] == msgs
    a.close(); b.close()


def test_closed_socket_returns_none():
    a, b = socket.socketpair()
    a.close()
    assert protocol.recv(b) is None
    b.close()
