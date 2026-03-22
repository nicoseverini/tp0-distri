import socket
from common.utils import Bet

class ProtocolError(Exception):
    pass

class ClientDisconnected(Exception):
    pass

class SocketReader:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.buffer = b''
    
    def read_line(self) -> str:
        while b'\n' not in self.buffer:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    if not self.buffer:
                        raise ClientDisconnected("client closed connection before sending data")
                    raise ProtocolError("connection closed unexpectedly")
                self.buffer += chunk
            except socket.timeout:
                if not self.buffer:
                    raise ClientDisconnected("socket timeout before receiving data")
                raise ProtocolError("socket timeout while reading")

        newline_pos = self.buffer.index(b'\n')
        line = self.buffer[:newline_pos].decode('utf-8')
        self.buffer = self.buffer[newline_pos + 1:]
        return line


def read_command(sock):
    reader = SocketReader(sock)
    line = reader.read_line().strip()
    parts = line.split(",")

    if parts[0] in ("DONE", "GET_WINNERS"):
        command = parts[0]
        agency = int(parts[1]) if len(parts) > 1 else None
    else:
        command = "BATCH"
        agency = None
        reader.buffer = (line + "\n").encode("utf-8") + reader.buffer

    return command, agency, reader

def send_winners(sock: socket.socket, count: int):
    response = f"WINS,{count}\n"
    sock.sendall(response.encode())

def read_batch(reader: SocketReader):
    bets = []

    while True:
        line = reader.read_line().strip()
        if not line:
            continue
        if line == "END":
            break
        parts = line.split(",")
        if len(parts) != 6:
            raise ProtocolError(f"invalid bet format: expected 6 fields, got {len(parts)}")
        try:
            bet = Bet(
                parts[0].strip(),
                parts[1].strip(),
                parts[2].strip(),
                parts[3].strip(),
                parts[4].strip(),
                parts[5].strip()
            )
            bets.append(bet)
        except (ValueError, IndexError) as e:
            raise ProtocolError(f"error parsing bet: {e}")

    return bets

def send_ack(sock: socket.socket):
    sock.sendall(b"OK\n")

def send_error(sock: socket.socket):
    sock.sendall(b"ERROR\n")