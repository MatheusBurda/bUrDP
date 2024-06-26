import socket
import sys
import threading
import os

################## Defines ##################
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 7777
#############################################


def handle_client(client_socket):
    while True:
        try:
            buffer = client_socket.recv(1024)
        except socket.error:
            break

        if not buffer:
            break

        # Decode the HTTP request
        request = buffer.decode("utf-8")

        if request.startswith("GET /"):
            filename = request.split()[1]
            print(f"> Client request from {client_socket.getpeername()}\n   {filename}")

            data_path = os.path.join(os.path.dirname(__file__), 'data')
            full_file_path = os.path.join(data_path, filename[1:])

            if os.path.exists(full_file_path):
                if full_file_path.lower().endswith(".html"):
                    with open(full_file_path, "rb") as f:
                        html_file = f.read()

                    header = f'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n'
                    response = header.encode('utf-8') + html_file
                    client_socket.send(response)
                    print(f'   200 OK')
            
                elif full_file_path.lower().endswith(".jpg") or full_file_path.lower().endswith(".jpeg"):
                    with open(full_file_path, "rb") as f:
                        image_data = f.read()

                    header = f'HTTP/1.1 200 OK\r\nContent-Type: image/jpeg\r\n\r\n'
                    response = header.encode('utf-8') + image_data
                    client_socket.send(response)
                    print(f'   200 OK')

            else:
                response = "HTTP/1.1 404 Not Found\r\n\r\n"
                client_socket.send(response.encode("utf-8"))
                print(f'   404 Not Found')
                break

        client_socket.close()


if __name__ == "__main__":

    host = SERVER_HOST
    if len(sys.argv) > 1:
        host = sys.argv[1] 

    port = SERVER_PORT
    if len(sys.argv) > 2:
        port = int(sys.argv[2])

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"Server listening on {host}:{port}")

    while True:
        
        client_socket, address = server_socket.accept()

        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.daemon = True
        client_thread.start()
        client_thread.join()
