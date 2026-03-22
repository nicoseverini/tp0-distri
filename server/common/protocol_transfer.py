import socket
from common.utils import Bet

class ProtocolError(Exception):
    pass


class ClientDisconnected(Exception):
    """Raised when a client closes the socket before sending any data."""
    pass

def recv_line(sock: socket.socket) -> str:
    data = b''

    while b'\n' not in data:
        chunk = sock.recv(1024)
        if not chunk:
            if not data:
                raise ClientDisconnected("client closed connection before sending data")
            raise ProtocolError("incomplete bet format")
        data += chunk

    return data.decode()

def read_batch(sock: socket.socket):
    line = recv_line(sock)
    bets = []
    lines = line.strip().split("\n")

    for l in lines:
        parts = l.strip().split(",")

        if len(parts) != 6:
            raise ProtocolError("invalid bet format")

        bet = Bet(
            parts[0],
            parts[1],
            parts[2],
            parts[3],
            parts[4],
            parts[5]
        )
        bets.append(bet)

    return bets

def send_ack(sock: socket.socket):
    sock.sendall(b"OK\n")

def send_error(sock: socket.socket):
    sock.sendall(b"ERROR\n")