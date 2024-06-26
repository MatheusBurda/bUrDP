import socket
import struct
import sys
import threading
import os

import utils
from utils import ActionStatus


class ServerInstance:

    # Mutex to prevent use of terminal
    mutex_terminal = threading.Lock()

    def __init__(self, client_socket, thread_n):
        self.client_socket = client_socket 
        self.thread_n = thread_n

    def request(self, query):
        status, _, data, _ = utils.parse_query(query)

        if status == ActionStatus.FILE_REQUEST:
            filename = data.decode('utf-8').split(' ')
            if len(filename) != 1:
                raise ValueError(f'BadRequestError: multiple arguments (expected 1, got {len(filename)})')
            self.handle_get_file(filename=filename[0])
            
        elif status == ActionStatus.END_CONNECTION:
            self.running = False

        elif status == ActionStatus.CHAT:
            self.handle_chat(data.decode('utf-8'))


    def handle_get_file(self, filename):

        data_path = os.path.join(os.path.dirname(__file__), 'data')
        full_file_path = os.path.join(data_path, filename)

        if not os.path.exists(full_file_path):
            raise FileNotFoundError(f'File {filename} does not exist')
        
        with self.mutex_terminal:
            print(f'({self.thread_n}) [file request]: {filename}')

        with open(full_file_path, 'rb') as file:
            packet = 0
            while (data := file.read(utils.DATA_SIZE)) is not None:

                if not data:
                    res = utils.data_pack(ActionStatus.EOF)
                    self.client_socket.sendall(res)
                    with self.mutex_terminal:
                        print(f'({self.thread_n}) [file uploaded]: {filename} containing {packet} packets!')
                    return
                
                self.client_socket.sendall(utils.data_pack(status=ActionStatus.FILE_PACKET, data=data, packet_id=packet))
                packet += 1

    
    def handle_chat(self, message):
        with self.mutex_terminal:
            print(f'({self.thread_n}) [chat]: {message}')    
        self.client_socket.sendall(utils.data_pack(status=ActionStatus.OK))


    def run(self):
        self.running = True
        
        while self.running:
            try:
                buffer = utils.read_buffer(self.client_socket)

                if buffer is None:
                    print('Buffer empty')
                    self.running = False
                    continue

                self.request(buffer)

            # Handles File not found
            except FileNotFoundError as e:
                data = bytes(str(e), encoding='utf-8')
                res = utils.data_pack(ActionStatus.FILE_NOT_FOUND_ERROR, data=data)
                self.client_socket.sendall(res)

            # Bad Request Error Handler
            except ValueError as e: 
                data = bytes(str(e), encoding='utf-8')
                res = utils.data_pack(ActionStatus.BAD_REQUEST_ERROR, data=data)
                self.client_socket.sendall(res)

            except ConnectionResetError:
                with self.mutex_terminal:
                    print(f'({self.thread_n}) connection closed')
                    self.running = False


def create_server_instance(client_socket, thread_n):
    global connections

    print(f"({thread_n}) Connected from {client_socket.getpeername()}")
    # Save the connection to broadcast later
    connections.append(client_socket)
    server = ServerInstance(client_socket, thread_n)
    server.run()

    connections.remove(client_socket)


def server_broadcast_thread():
    global connections
    while True:
        message = input('')
        message_encoded = message.encode('utf-8')
        request = utils.data_pack(status=ActionStatus.CHAT, data=message_encoded)

        for conn in connections:
            conn.sendall(request)


if __name__ == "__main__":

    host = utils.SERVER_HOST
    if len(sys.argv) > 1:
        host = sys.argv[1]

    port = utils.SERVER_PORT
    if len(sys.argv) > 2:
        port = int(sys.argv[2])

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    print(f"Server listening on {host}:{port}")

    connections = []

    n_threads = 0

    # Creates the broadcast input thread
    server_input = threading.Thread(target=server_broadcast_thread)
    server_input.daemon = True  
    server_input.start()

    while True:
        conn, addr = server.accept()
        # creates a thread for the connection
        client_handler = threading.Thread(target=create_server_instance, args=(conn, n_threads, ))
        # kills the thread when main process is shut down
        client_handler.daemon = True  
        client_handler.start()
        n_threads += 1
