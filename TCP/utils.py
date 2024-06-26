from enum import Enum, EnumMeta
import os
import hashlib
import struct

################## Defines ##################
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 7777
DATA_SIZE = 1000


class ValueMeta(EnumMeta):
    def __getattribute__(cls, name):
        value = super().__getattribute__(name)
        if isinstance(value, cls):
            value = value.value
        return value

class ActionStatus(Enum, metaclass=ValueMeta):
    OK = 0xFF
    END_CONNECTION = 0xFA
    BAD_REQUEST_ERROR = 0xFC
    CHAT = 0xC0
    FILE_NOT_FOUND_ERROR = 0x80
    FILE_REQUEST = 0x81
    FILE_PACKET = 0x82
    EOF = 0x83

#############################################

def calculate_md5(data):
    if type(data) is str:
        data = bytes(data, 'utf-8')
    md5 = hashlib.md5()
    md5.update(data)
    return md5.digest()


def is_md5_checksum_valid(data, checksum):
    new_hash = calculate_md5(data)
    return checksum == new_hash


def file_exists(filename):
    data_path = os.path.join(os.getcwd(), 'data')

    if '..' in filename:
        raise FileNotFoundError(filename)
    
    full_file_path = os.path.join(data_path, filename)
    return os.path.exists(full_file_path)


def get_bytes_as_string(byte_string):
    return ''.join('\\x{:02x}'.format(letter) for letter in byte_string)


def data_pack(status, packet_id=0, data=b''):
    # [action_status(2), packet_id (4), data(1002), checksum (16)]
    # 2    Bytes -> buffer_size
    # 2    Bytes -> action_status
    # 4    Bytes -> packet_id (number of the packet transmited)
    # 1000 Bytes -> data (max data buffer size)
    # 16   Bytes -> checksum (md5 checksum hash)

    checksum = calculate_md5(data)
    status_binary = struct.pack('>H', status)
    packet_id_binary = struct.pack('>I', packet_id)
    buffer_size = len(checksum) + len(status_binary) + len(packet_id_binary) + len(data)

    res = struct.pack('>H', buffer_size)
    res += status_binary
    res += packet_id_binary
    assert len(data) <= DATA_SIZE, 'Data bigger than DATA_SIZE max value'
    res += data
    res += checksum

    return res

# returns in order the tupple (status, packet_id, data, check_sum)
def parse_query(buffer):
    if len(buffer) < 22:
        return None, None, None, None
    
    # [ActionStatus(2), packet_id (4), data(1000), checksum (16)] 
    status = struct.unpack('>H', buffer[:2])[0]
    packet_id = int(struct.unpack('>I', buffer[2:6])[0])
    data = buffer[6:-16]
    check_sum = buffer[-16:]

    return (status, packet_id, data, check_sum)


def read_buffer(socket):
    buffer_size_b = socket.recv(2)
    if len(buffer_size_b) < 1:
        return
    buffer_size = struct.unpack('>H', buffer_size_b)[0]
    return socket.recv(buffer_size)
