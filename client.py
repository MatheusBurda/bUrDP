import socket
import struct
import os
import time

from utils import SERVER_PORT, SERVER_IP, DATA_SIZE, ACTION_STATUS, is_md5_checksum_valid, get_status

while True:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(10)

    message = input('> ')

    if message == '':
        break

    file = None

    try:
        start_time = time.time()
        client_socket.sendto(message.encode(), (SERVER_IP, SERVER_PORT))

        status = ACTION_STATUS["OK"]
        packets_read = 0
        bytes_read = 0
        packets_lost = 0
        filename = None

        if 'GET' in message.upper():
            message_splitted = message.split(' ')
            if len(message_splitted) != 2:
                raise Exception('filename not correct')
            filename = message_splitted[1]

        if filename: 
            file = open(os.path.join(os.getcwd(), 'output', filename), 'wb+')

        while status != ACTION_STATUS["EOF"]:
            buffer, _ = client_socket.recvfrom(1024)

            # [action_status(2), packet_id (4), data_size (2), data(1000), checksum (16)] 
            status = struct.unpack('>H', buffer[:2])[0]
            packet_id = int(struct.unpack('>I', buffer[2:6])[0])
            data = buffer[6:-16]
            check_sum = buffer[-16:]

            if status == ACTION_STATUS["FILE_NOT_FOUND_ERROR"]:
                raise FileNotFoundError("FILE_NOT_FOUND_ERROR: ", data.decode('utf-8'))
            elif status == ACTION_STATUS["BAD_REQUEST_ERROR"]:
                raise FileNotFoundError("BAD_REQUEST_ERROR: ", data.decode('utf-8'))
            elif status == ACTION_STATUS["OK"]:
                if packets_read == packet_id:
                    if is_md5_checksum_valid(data, check_sum):
                        file.write(data)
                        bytes_read += len(data)
                        client_socket.sendto(bytes(f'ACK {packets_read}', encoding='utf-8'), (SERVER_IP, SERVER_PORT))
                        packets_read += 1

                else:
                    client_socket.sendto(bytes(f'RSD {packets_read}', encoding='utf-8'), (SERVER_IP, SERVER_PORT))
                    packets_lost += 1
                
        elapsed_time = time.time() - start_time
        file.close()
        print(f"""
        Transfer finished in {elapsed_time:0.2f} seconds
        {bytes_read} bytes read and {packets_lost}/{packets_read} packets lost ({(packets_lost/packets_read*100):0.2f} %)
        """)
        client_socket.close()
    
    except (TimeoutError, Exception, FileNotFoundError) as err:
        print(str(err))
        if file:
            file.close()
            os.remove(os.path.join(os.getcwd(), 'output', filename))

