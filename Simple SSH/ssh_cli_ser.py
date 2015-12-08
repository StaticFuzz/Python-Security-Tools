#Python3

def main():
    options = {'client': ssh_client, 'server': ssh_server}

    parser = argparse.ArgumentParser(description='SSH client/server')

    parser.add_argument('role', choices=options,
                        default='server',
                        help='choose client or server')
    parser.add_argument('-p', type=int, default=22,
                        help='Port number for SSH server, or target\
                             SSH server, default =  22')
    parser.add_argument('-a', type=str, default='',
                        help='IP address default = localhost')

    args = parser.parse_args()
    ssh_function = options[args.role]
    ssh_port = args.p
    ssh_address = args.a
    ssh_function(ssh_address, ssh_port)


def ssh_server(address, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((address, port))
    server.listen(1)

    while True:
        client_sock, client_address = server.accept()
        print('{}: {} CONNECTED'.format(ctime(), client_address))

        shell = make_shell()
        stdout_queue = Queue()

        stdout_reader = Thread(target=get_result, args=(shell, stdout_queue))
        stdout_reader.daemon = True
        stdout_reader.start()
        """
        stdout_reader is run in it's own thread to prevent blocking
        from shell.stdout.read()
        """

        server_run(client_sock, shell, stdout_queue)

        shell.kill()


def server_run(client, shell, stdout_queue):
    """
    Main server loop. runs until closed connection from
    client.
    """
    while True:
        command = get_message(client)
        if command:
            print('{}: COMMAND : {}'.format(ctime(), command))
            shell.stdin.write(command + '\n')
            shell.stdin.flush()
            sleep(.2)
            message = ''
            while not stdout_queue.empty():
                message += stdout_queue.get()
	    if not message:
     	    	message = "Command Complete...
            send_message(client, message)
        else:
            print('{} : CONNECTION CLOSED'.format(ctime()))
            break


def get_result(shell, stdout_queue):
    """
    checks for output from shell.stdout and adds it to
    the stdout_queue
    """
    while True:
        for line in iter(shell.stdout.readline()):
            stdout_queue.put(line)


def make_shell():
    """
    used by server_run()
    returns a subprocess Popen object that
    """
    if os.name == 'nt':
        command_line = ['CMD', '/k']
    elif os.name == 'posix':
        command_line = ['bin/bash', '-s']
    else:
        print('incompatible operating system...\nexiting')
        sys.exit()

    shell = Popen(command_line,
                  stdin=PIPE,
                  stdout=PIPE,
                  stderr=STDOUT,
                  universal_newlines=True)
    """
    universal_newlines allows the Popen object pass strings
    to the stdin in and recieve strings from stdout. All strings
    passed to stdin must be followed by newline. newlines are
    added by the server_run() function before the command is
    passed.
    """
    return shell


def ssh_client(address, port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((address, port))
    except socket.error as err:
        print('unable to connect: {}'.format(err))
        sys.exit()

    while True:
        command = input('>>>')

        if command == 'QUIT':
            print('exiting...')
            break

        send_message(client, command)
        result = get_message(client)
        if result:
            print(result)
        else:
            print('server closed connection..')
            sys.exit()


"""
messages between client and server will be preceded by
the length of the full message.
"""
def get_message(connection):
    raw_message = connection.recv(1024)

    if raw_message:
        message_length = int(raw_message.decode())
        message = ''
        while message_length > 0:
            temp_message = connection.recv(1024).decode()
            message += temp_message
            message_length -= len(temp_message)
        return message
    else:
        return raw_message


def send_message(connection, message):
    message_length = str(len(message))

    try:
        connection.send(message_length.encode())
        connection.send(message.encode())
    except socket.error as err:
        print('bad connection:\n{}'.format(err))


if __name__ == '__main__':
    import socket
    from subprocess import Popen, PIPE, STDOUT
    import os
    import sys
    from time import ctime, sleep
    from queue import Queue
    from threading import Thread
    import argparse
    main()
