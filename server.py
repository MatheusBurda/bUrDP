import socket
import struct

from utils import calculate_md5, ACTION_STATUS, file_exists, SERVER_IP, SERVER_PORT
from FileTransmissionHandler import FileTransmissionHandler

class Server:

    def __init__(self, ip, port):

        print(f'binding server in {ip}:{port}')
        self.file_client_dict = {}
        self.ip = ip
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((ip, port))
        print("server is running")


    def parse_query(self, query:str):
        splitted_query = query.split(' ')

        if len(splitted_query) != 2:
            raise ValueError(f'BadRequestError: multiple arguments (expected 2, got {len(splitted_query)})')
        
        instruction, value = splitted_query
        instruction = instruction.upper()

        return instruction, value


    def request(self, query, client_address):
        instruction, value = self.parse_query(query)

        method = None
        if instruction == 'GET':
            method = self.handle_get_file
        elif instruction == 'ACK':
            method = self.handle_ack
        elif instruction == 'RSD':
            method = self.handle_resend
        else:
            raise ValueError(f'unknown request method "{instruction}"')
        
        return method(value, client_address)


    def handle_get_file(self, filename, client_address):

        if not file_exists(filename):
            raise FileNotFoundError(f'File {filename} does not exist')
        
        if client_address in self.file_client_dict.keys():
            # Explicitly delete object, so it closes the file that was open
            del self.file_client_dict[client_address]

        self.file_client_dict[client_address] = FileTransmissionHandler(filename, client_address)

        return self.file_client_dict[client_address].get_data_from_packet()
        

    def handle_ack(self, value, client_address):
        if client_address not in self.file_client_dict.keys():
            raise ValueError('File not open yet')
        value = int(value)
        wrong_ack = self.file_client_dict[client_address].ack(value)
        
        if wrong_ack:
            print(f'>>> wrong ack ({value}) retransmitting...')
        else:
            print(f'>>> ack {value}')

        return self.file_client_dict[client_address].get_data_from_packet()


    def handle_resend(self, value, client_address):
        value = int(value)
        print(f'>>> retransmitting ({value})')

        return self.file_client_dict[client_address].get_data_from_packet(value)


    def response(self, action_status, packet_id=0, data=''):
        # [action_status(2), packet_id (4), data_size (2), data(1000), checksum (16)]
        # 2    Bytes -> action_status
        # 4    Bytes -> packet_id (number of the packet transmited)
        # 1002 Bytes -> data (max data buffer size)
        # 16   Bytes -> checksum (md5 checksum hash)

        data_size = len(data)
        checksum = calculate_md5(data)

        res = struct.pack('>H', action_status)
        res += struct.pack('>I', packet_id)
        res += data
        res += checksum

        return res
    

    def run(self):
        while True:
            message, client_address = self.server_socket.recvfrom(1024)

            try:
                print(f'\n> request received from {client_address}:\n>> {self.parse_query(message.decode())}')
                packet_id, data = self.request(message.decode(), client_address)

                res = self.response(ACTION_STATUS["OK"], packet_id, data)

                self.server_socket.sendto(res, client_address)

            # Handles File not found
            except FileNotFoundError as e:
                data = bytes(str(e), encoding='utf-8')
                res = self.response(ACTION_STATUS["FILE_NOT_FOUND_ERROR"], data=data)
                self.server_socket.sendto(res, client_address)

            # Bad Request Error Handler
            except ValueError as e: 
                data = bytes(str(e), encoding='utf-8')
                print(f'BAD_REQUEST_ERROR: {data}')
                res = self.response(ACTION_STATUS["BAD_REQUEST_ERROR"], data=data)
                self.server_socket.sendto(res, client_address)

            # Handle End of file transmission
            except EOFError as e:
                data = bytes(str(e), encoding='utf-8')
                res = self.response(ACTION_STATUS["EOF"], data=data)
                self.server_socket.sendto(res, client_address)
                # Delete from client file list
                del self.file_client_dict[client_address]


if __name__ == "__main__":
    server = Server(SERVER_IP, SERVER_PORT)
    server.run()
