import os
import hashlib


################## Defines ##################
SERVER_IP = '127.0.0.1'
SERVER_PORT = 7777
DATA_SIZE = 1002

ACTION_STATUS = {
    "OK": 0xFF,
    "FILE_NOT_FOUND_ERROR": 0xFA,
    "BAD_REQUEST_ERROR": 0xAA,
    # "INTERNAL_ERROR": 0x80,
    "EOF": 0x88
}
#############################################

def get_status(value):
    if value in ACTION_STATUS.values():
        return list(ACTION_STATUS.keys())[list(ACTION_STATUS.values()).index(value)]
    
    return 'Unknown'


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
