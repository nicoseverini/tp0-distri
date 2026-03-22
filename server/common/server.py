import os
import socket
import logging
from common.utils import store_bets, load_bets, has_won
from common.protocol_transfer import read_command, send_ack, send_error, send_winners, read_batch, ClientDisconnected

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

        self._server_socket.settimeout(1)
        self.running = True
        self.client_sockets = []

        self.done_clients = set()
        self.expected_clients = int(os.getenv("CLIENTS", "5"))
        self.draw_done = False
        self.winners_by_agency = {}
        self.pending_get_winners = []

    def graceful_shutdown(self, signum=None, frame=None):
        self.running = False

        if self._server_socket:
            try:
                self._server_socket.close()
                logging.info('action: close_fd | result: success | target: server_socket')
            except OSError as e:
                logging.error(f'action: close_fd | result: fail | target: server_socket | error: {e}')

        for client_socket in self.client_sockets:
            try:
                client_socket.close()
                logging.info('action: close_fd | result: success | target: client_socket')
            except OSError as e:
                logging.error(f'action: close_fd | result: fail | target: client_socket | error: {e}')

        logging.info('action: shutdown | result: success')


    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """
        while self.running:
            try:
                client_sock = self.__accept_new_connection()

                if client_sock:
                    self.client_sockets.append(client_sock)
                    self.__handle_client_connection(client_sock)

            except socket.timeout:
                continue

            except OSError as e:
                if not self.running:
                    break
                logging.error(f'action: accept_error | error: {e}')

    def __handle_client_connection(self, client_sock):
        bets = []

        try:
            command, agency, reader = read_command(client_sock)

            if command == "DONE":
                self.__handle_done(client_sock, agency)
            elif command == "GET_WINNERS":
                self.__handle_get_winners(client_sock, agency)
            elif command == "BATCH":
                self.__handle_batch(client_sock, reader)

        except ClientDisconnected:
            logging.info(
                "action: handle_client | result: success | event: client_disconnected"
            )
        except Exception:
            logging.error(
                "action: apuesta_recibida | result: fail | cantidad: %d",
                len(bets)
            )

            send_error(client_sock)
        finally:
            client_sock.close()
            logging.info(
                'action: close_fd | result: success | target: client_socket'
            )
            try:
                self.client_sockets.remove(client_sock)
            except ValueError:
                pass

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c

    def __handle_done(self, client_sock, agency_id):
        self.done_clients.add(agency_id)
        if not self.draw_done and len(self.done_clients) >= self.expected_clients:
            winners = {}

            for bet in load_bets():
                if has_won(bet):
                    winners.setdefault(
                        bet.agency,
                        []
                    ).append(bet.document)

            self.winners_by_agency = winners
            self.draw_done = True
            logging.info(
                "action: sorteo | result: success"
            )
            pending = self.pending_get_winners
            self.pending_get_winners = []
            for sock, agency in pending:
                docs = self.winners_by_agency.get(
                    agency,
                    []
                )
                send_winners(sock, len(docs))
                sock.close()

    def __handle_get_winners(self, client_sock, agency):
        if not self.draw_done:
            self.pending_get_winners.append(
                (client_sock, agency)
            )
            return
        docs = self.winners_by_agency.get(
            agency,
            []
        )
        send_winners(
            client_sock,
            len(docs)
        )

    def __handle_batch(self, client_sock, reader):
        bets = read_batch(reader)
        store_bets(bets)

        logging.info(
            "action: apuesta_recibida | result: success | cantidad: %d",
            len(bets)
        )

        send_ack(client_sock)

    def __calculate_winners(self):
        winners = []
        for bet in load_bets():
            if has_won(bet):
                winners.append(bet.document)

        return winners