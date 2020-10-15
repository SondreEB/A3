
from socket import *


# --------------------
# Constants
# --------------------
# The states that the application can be in
states = [
    "disconnected",  # Connection to a chat server is not established
    "connected",  # Connected to a chat server, but not authorized (not logged in)
    "authorized"  # Connected and authorized (logged in)
]
TCP_PORT = 1300  # TCP port used for communication
SERVER_HOST = "datakomm.work"  # Set this to either hostname (domain) or IP address of the chat server

# --------------------
# State variables
# --------------------
current_state = "disconnected"  # The current state of the system
# When this variable will be set to false, the application will stop
must_run = True
# Use this variable to create socket connection to the chat server
# Note: the "type: socket" is a hint to PyCharm about the type of values we will assign to the variable
client_socket = None  # type: socket


def quit_application():
    """ Update the application state so that the main-loop will exit """
    # Make sure we reference the global variable here. Not the best code style,
    # but the easiest to work with without involving object-oriented code
    global must_run
    must_run = False


def send_command(command, arguments):
    """
    Send one command to the chat server.
    :param command: The command to send (login, sync, msg, ...(
    :param arguments: The arguments for the command as a string, or None if no arguments are needed
        (username, message text, etc)
    :return:
    """
    global client_socket

    try:
        client_socket.send((command + " " + arguments + "\n").encode())
        return True
    except IOError as e:
        print("Error happened: ", e)
        return False


def read_one_line(sock):
    """
    Read one line of text from a socket
    :param sock: The socket to read from.
    :return:
    """
    newline_received = False
    message = ""
    while not newline_received:
        character = sock.recv(1).decode()
        if character == '\n':
            newline_received = True
        elif character == '\r':
            pass
        else:
            message += character
    return message


def get_servers_response():
    """
    Wait until a response command is received from the server
    :return: The response of the server, the whole line as a single string
    """
    global client_socket

    try:
        server_answer = read_one_line(client_socket)
        return server_answer
    except IOError as e:
        print("Error happened: ", e)
        return False


def connect_to_server():
    # Must have these two lines, otherwise the function will not "see" the global variables that we will change here
    global client_socket
    global current_state

    client_socket = socket(AF_INET, SOCK_STREAM)

    try:
        client_socket.connect((SERVER_HOST, TCP_PORT))
        current_state = "connected"
        send_command("sync", "")
        server_response = get_servers_response()
        if server_response == "modeok":
            print("Success. modeok recieved")
        else:
            print("Error. Message not returned as expected. Returned: ", server_response)
        return True
    except IOError as e:
        print("Error happened:", e)
        return False


def disconnect_from_server():

    global client_socket
    global current_state
    try:
        client_socket.close()
        current_state = "disconnected"
        return True
    except IOError as e:
        print("error happened", e)
        return False


def login():
    global current_state
    global client_socket

    try:
        username = input("Enter username: ")
        send_command("login", username)
        server_response = read_one_line(client_socket)
        if server_response == "loginok":
            print("Login successful. Logged inn as: ", username)
            current_state = "authorized"
            return True
        if server_response == "loginerr incorrect username format":
            print("Error. Username can only consist of alphanumeric characters: letters and digits. Try again")
            return False
        else:
            print("Error. Message not returned as expected. Returned: ", server_response)
            return False

    except IOError as e:
            print("Error happened: ", e)
            return False


def public_message():
    global client_socket

    try:
        message = input("Write the message you wish to send: ")
        send_command("msg", message)
        server_response = read_one_line(client_socket)
        server_response_splitted = server_response.split(" ")
        if server_response_splitted[0] == "msgok":
            print("Success. Message sent.")
            return True
        else:
            print("Error. Message not sent. Try again")
            return False

    except IOError as e:
        print("Error! Not a valid username input. Start over.")
        return False


def get_user_list():
    global client_socket
    # protocol for users list: users\n
    try:
        send_command("users", "")
        string_users = read_one_line(client_socket)
        users_list = string_users.split(" ")
        # removing "users" at the start of the list
        del(users_list[0])
        print("Success. Received list of users: ", users_list)

    except IOError as e:
        print("Error happened: ", e)
        return False


def private_message():
    global client_socket

    try:
        recipient = input("Enter username of recipient: ")
        message = input("Enter message to be sent: ")
        recipient_and_message = recipient + " " + message
        send_command("privmsg", recipient_and_message)
        server_response = read_one_line(client_socket)
        server_response_splitted = server_response.split(" ")
        if server_response_splitted[0] == "msgok":
            if server_response_splitted[1] == "1":
                print("Success. Message sent")
                return True
            else:
                string_server_response = str(server_response_splitted[1])
                print("Success, but message was sent to %i recipients!" % string_server_response)
                return True
        elif server_response_splitted[0] == "msgerr":
            print("Error. Wrong recipient. Can't send to Anonymous users. Tried to send to: ", recipient)
            return False
        else:
            print("Error. Message was not sent. Server response: ", server_response)
            return False

    except IOError as e:
        print("Error happened: ", e)
        return False


def inbox():
    global client_socket

    try:
        send_command("inbox", "")
        server_answer = read_one_line(client_socket)
        server_answer_splitt = server_answer.split(" ")
        if server_answer_splitt[1] == "0":
            print("No new messages in inbox.")
            return True
        else:
            print("Your inbox has %i new messages." % int(server_answer_splitt[1]))
            for i in range(1, int(server_answer_splitt[1]) + 1):
                inbox_content = read_one_line(client_socket)
                inbox_content_splitted = inbox_content.split(" ")
                sender = inbox_content_splitted[1]
                del(inbox_content_splitted[0:2])
                messages = " "
                message = messages.join(inbox_content_splitted)
                print("Message %i is from " % i + sender + " and reads: " + message)
            return True

    except IOError as e:
        print("Error happened: ", e)
        return False


"""
The list of available actions that the user can perform
Each action is a dictionary with the following fields:
description: a textual description of the action
valid_states: a list specifying in which states this action is available
function: a function to call when the user chooses this particular action. The functions must be defined before
            the definition of this variable
"""
available_actions = [
    {
        "description": "Connect to a chat server",
        "valid_states": ["disconnected"],
        "function": connect_to_server
    },
    {
        "description": "Disconnect from the server",
        "valid_states": ["connected", "authorized"],
        "function": disconnect_from_server
    },
    {
        "description": "Authorize (log in)",
        "valid_states": ["connected", "authorized"],
        "function": login
    },
    {
        "description": "Send a public message",
        "valid_states": ["connected", "authorized"],
        "function": public_message
    },
    {
        "description": "Send a private message",
        "valid_states": ["authorized"],
        "function": private_message
    },
    {
        "description": "Read messages in the inbox",
        "valid_states": ["connected", "authorized"],
        "function": inbox
    },
    {
        "description": "See list of users",
        "valid_states": ["connected", "authorized"],
        "function": get_user_list
    },
    {
        "description": "Get a joke",
        "valid_states": ["connected", "authorized"],
        # TODO - optional step - implement the joke fetching from the server.
        # Hint: this part is not described in the protocol. But the command is simple. Try to find
        # out how it works ;)
        "function": None
    },
    {
        "description": "Quit the application",
        "valid_states": ["disconnected", "connected", "authorized"],
        "function": quit_application
    },
]


def run_chat_client():
    """ Run the chat client application loop. When this function exists, the application will stop """

    while must_run:
        print_menu()
        action = select_user_action()
        perform_user_action(action)
    print("Thanks for watching. Like and subscribe! 👍")


def print_menu():
    """ Print the menu showing the available options """
    print("==============================================")
    print("What do you want to do now? ")
    print("==============================================")
    print("Available options:")
    i = 1
    for a in available_actions:
        if current_state in a["valid_states"]:
            # Only hint about the action if the current state allows it
            print("  %i) %s" % (i, a["description"]))
        i += 1
    print()


def select_user_action():
    """
    Ask the user to choose and action by entering the index of the action
    :return: The action as an index in available_actions array or None if the input was invalid
    """
    number_of_actions = len(available_actions)
    hint = "Enter the number of your choice (1..%i):" % number_of_actions
    choice = input(hint)
    # Try to convert the input to an integer
    try:
        choice_int = int(choice)
    except ValueError:
        choice_int = -1

    if 1 <= choice_int <= number_of_actions:
        action = choice_int - 1
    else:
        action = None

    return action


def perform_user_action(action_index):
    """
    Perform the desired user action
    :param action_index: The index in available_actions array - the action to take
    :return: Desired state change as a string, None if no state change is needed
    """
    if action_index is not None:
        print()
        action = available_actions[action_index]
        if current_state in action["valid_states"]:
            function_to_run = available_actions[action_index]["function"]
            if function_to_run is not None:
                function_to_run()
            else:
                print("Internal error: NOT IMPLEMENTED (no function assigned for the action)!")
        else:
            print("This function is not allowed in the current system state (%s)" % current_state)
    else:
        print("Invalid input, please choose a valid action")
    print()
    return None

# Entrypoint for the application. In PyCharm you should see a green arrow on the left side.
# By clicking it you run the application.
if __name__ == '__main__':
    run_chat_client()