"""Length-prefixed JSON framing over TCP.

Each message is a 4-byte big-endian length header followed by a UTF-8 JSON body.
This avoids the message-boundary bugs of raw ``recv(1024)`` + ``json.loads``.
"""
import json
import socket
import struct

_HEADER = struct.Struct("!I")
MAX_MESSAGE_SIZE = 1 << 20  # 1 MiB


def encode(message: dict) -> bytes:
    body = json.dumps(message, separators=(",", ":")).encode("utf-8")
    return _HEADER.pack(len(body)) + body


def send(sock: socket.socket, message: dict) -> None:
    sock.sendall(encode(message))


def _recv_exact(sock: socket.socket, n: int) -> bytes | None:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)


def recv(sock: socket.socket) -> dict | None:
    header = _recv_exact(sock, _HEADER.size)
    if header is None:
        return None
    (length,) = _HEADER.unpack(header)
    if length > MAX_MESSAGE_SIZE:
        raise ValueError(f"message too large: {length} bytes")
    body = _recv_exact(sock, length)
    if body is None:
        return None
    return json.loads(body.decode("utf-8"))
