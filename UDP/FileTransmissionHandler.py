import os
from utils import file_exists, DATA_SIZE


class FileTransmissionHandler:

    def __init__(self, filename, client_address):
        self.filename = filename
        self.client_addr = client_address
        self.cached_data_packets = []
        self.last_ack_received = -1

        if not file_exists(filename):
            raise FileNotFoundError(f'File {filename} does not exist')
        
        data_path = os.path.join(os.getcwd(), 'data')
        full_file_path = os.path.join(data_path, filename)

        self.file = open(full_file_path, 'rb')


    def ack(self, value):

        value = int(value)
        if value != self.last_ack_received + 1: # Packet not delivered
            return True

        self.last_ack_received = value

        return False
        
    
    def get_file_data(self):
        data = self.file.read(DATA_SIZE)
        
        if not data:
            raise EOFError('')

        self.cached_data_packets.append(data)

        return data


    def get_data_from_packet(self, packet_n=None):
        if not packet_n:
            packet_n = self.last_ack_received + 1      
        
        if packet_n >= len(self.cached_data_packets):
            return packet_n, self.get_file_data()

        return packet_n, self.cached_data_packets[packet_n]


    def __del__(self):
        if self.file:
            self.file.close()

