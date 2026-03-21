import socket
import logging
from common.utils import store_bets
from common.protocol_transfer import read_bet, send_ack, ProtocolError

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

        self._server_socket.settimeout(1)
        self.running = True
        self.client_sockets = []

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
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            bet = read_bet(client_sock)
            store_bets([bet])
            logging.info(
                "action: apuesta_almacenada | result: success | dni: %s | numero: %s",
                bet.document,
                bet.number
            )
            send_ack(client_sock)
        except (ProtocolError, OSError, ValueError) as e:
            logging.error(
                "action: handle_client | result: fail | error: %s",
                e
            )
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
