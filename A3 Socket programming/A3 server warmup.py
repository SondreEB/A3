# A Simple TCP server, used as a warm-up exercise for assignment A3
from socket import *
import threading
welcome_socket = socket(AF_INET, SOCK_STREAM)


def stop_server():
    global welcome_socket
    try:
        welcome_socket.close()
        print("Server shutdown")
        return True
    except IOError as e:
        print("Error happened:", e)
        return False


def start_server():
    global welcome_socket
    try:
        welcome_socket.bind(("", 5678))
        welcome_socket.listen(1)
        print("Server ready for connection")
        return True
    except IOError as e:
        print("Error happened:", e)
        return False


def handle_next_client(connection_socket, client_id):
    while True:
        message = connection_socket.recv(100).decode()
        print("Message from client #%i: %s" % (client_id, message))
        if message == "Game over":
            break
        message_list = message.split()
        respond = int(message_list[0]) + int(message_list[2])
        respond_to_send = str(respond)
        connection_socket.send(respond_to_send.encode())
    connection_socket.close()


def run_server():
    global welcome_socket
    print("Starting TCP server...")

    if not start_server():
        print("Error! Failed to start the server")

    need_to_run = True
    client_id = 1
    while need_to_run:
        connection_socket, client_address = welcome_socket.accept()
        print("Client #%i connected from %s" % (client_id, client_address))
        client_thread = threading.Thread(target=handle_next_client, args=(connection_socket, client_id))
        client_id += 1
        client_thread.start()

    if not stop_server():
        print("Error! Failed to stop the server")


# Main entrypoint of the script
if __name__ == '__main__':
    run_server()

