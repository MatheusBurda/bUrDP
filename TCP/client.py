import select
import socket
import struct
import os
import threading
import time
import sys

from utils import ActionStatus
import utils

class Client:

    def __init__(self, server_ip, server_port, client_n):

        self.running = True

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(1)
        self.socket.connect((server_ip, server_port))

        print(f'Connected to host on {server_ip}:{server_port}')
        
        self.current_file = None
        self.filename = None
        self.reset_file()     

        self.has_printed_input_char = False
        self.input_message_queue = []

        self.files_path = os.path.join(os.path.dirname(__file__), 'output', str(client_n))

        os.mkdir(self.files_path)

        input_thread = threading.Thread(target=self.input, args=())
        input_thread.daemon = True  
        input_thread.start()


    def check_input(self, input_message):

        request = None
        splitted_input = input_message.split(' ')

        # parses the input to check what procedure to do
        if input_message.upper() == 'EXIT':
            request = utils.data_pack(ActionStatus.END_CONNECTION)
            self.running = False

        elif splitted_input[0].upper() == 'FILE':
            # await finish of last file recieve
            while self.current_file is not None:
                pass

            self.filename = splitted_input[1]

            full_file_path = os.path.join(self.files_path, self.filename)

            if os.path.exists(full_file_path):
                os.remove(full_file_path)

            self.current_file = open(full_file_path, 'wb+')

            request = utils.data_pack(ActionStatus.FILE_REQUEST, data=self.filename.encode('utf-8'))
            self.transfer_start_time = time.time()
            
        else:
            request = utils.data_pack(ActionStatus.CHAT, data=input_message.encode('utf-8'))
        
        return request
    

    def run(self):
        while self.running:

            try:
                if len(self.input_message_queue) > 0: 
                    request_message = self.check_input(self.input_message_queue.pop())
                    self.socket.sendall(request_message)

                try:
                    buffer = utils.read_buffer(self.socket)
                except TimeoutError:
                    continue

                if buffer is None:
                    break

                status, packet_id, data, check_sum = utils.parse_query(buffer)

                if status == ActionStatus.CHAT:
                    print(f'[server]: {data.decode('utf-8')}')

                elif status == ActionStatus.FILE_PACKET:    
                    if self.packets_read == packet_id and utils.is_md5_checksum_valid(data, check_sum):
                        self.current_file.write(data)
                        self.bytes_read += len(data)
                        self.packets_read += 1
                    else:
                        # print(f'{packet_id} of len {len(data)}:\n{data} \n\nchecksum {check_sum} != {utils.calculate_md5(data)}\n\n\n')  
                        self.packets_lost += 1
                        
                elif status == ActionStatus.EOF:
                    elapsed_time = time.time() - self.transfer_start_time

                    if self.packets_lost > 0:
                        print(f'Saving file that may be corrupted!!!!!!!!!')

                    self.current_file.close()

                    print(f"{self.filename} Transfer finished in {elapsed_time:0.2f} seconds\n{self.bytes_read} bytes read and {self.packets_lost}/{self.packets_read} packets lost ({(self.packets_lost / self.packets_read * 100):0.2f} %)")

                    self.reset_file()

                elif status == ActionStatus.FILE_NOT_FOUND_ERROR:
                    raise FileNotFoundError("FILE_NOT_FOUND_ERROR: ", data.decode('utf-8'))
                
                elif status == ActionStatus.BAD_REQUEST_ERROR:
                    raise FileNotFoundError("BAD_REQUEST_ERROR: ", data.decode('utf-8'))
                
                elif status == ActionStatus.OK:
                    continue
                
                else:
                    break

            except (FileNotFoundError) as err:
                print(str(err))
                if self.current_file:
                    self.current_file.close()
                    os.remove(os.path.join(self.files_path, self.filename))
                    self.reset_file()
                
            except KeyboardInterrupt:
                self.socket.close()

        self.socket.close()
        print('Connection to host closed!')
        self.running = False


    def reset_file(self):
        self.current_file = None
        self.filename = None
        self.packets_read = 0
        self.bytes_read = 0
        self.packets_lost = 0
        self.transfer_start_time = 0


    def input(self):
        while self.running:
            inp = input('')       

            self.input_message_queue.append(inp)

    # def input(self, prompt):
        
    #     if not self.has_printed_input_char:
    #         print(prompt, end='', flush=True)
    #         self.has_printed_input_char = True
    #     i, o, e = select.select([sys.stdin], [], [], 1)

    #     if (i):
    #         inp = sys.stdin.readline().strip()
    #         if inp == 'ETX':
    #             raise KeyboardInterrupt
    #         self.has_printed_input_char = False
    #         return inp
        
    #     return None


if __name__ == "__main__":

    ip = utils.SERVER_HOST
    if len(sys.argv) > 1:
        ip = sys.argv[1]

    port = utils.SERVER_PORT
    if len(sys.argv) > 2:
        port = sys.argv[2]

    client_n = len(os.listdir(os.path.join(os.path.dirname(__file__), 'output')))

    client = Client(ip, int(port), client_n)
    client.run()

