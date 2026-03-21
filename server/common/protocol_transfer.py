import socket
from server.common.utils import Bet

class ProtocolError(Exception):
    pass

def recv_line(sock: socket.socket) -> str:
    data = b''

    while b'\n' not in data:
        chunk = sock.recv(1024)
        if not chunk:
            raise OSError("socket closed")
        data += chunk

    return data.decode()

def read_bet(sock: socket.socket) -> Bet:
    line = recv_line(sock)
    parts = line.strip().split(",")

    if len(parts) != 6:
        raise ProtocolError("invalid bet format")

    agency = parts[0]
    first_name = parts[1]
    last_name = parts[2]
    document = parts[3]
    birthdate = parts[4]
    number = parts[5]

    return Bet(
        agency,
        first_name,
        last_name,
        document,
        birthdate,
        number
    )

def send_ack(sock: socket.socket):
    sock.sendall(b"OK\n")