import socket
import os
from messenger import *  # Includes global variable KEY_SIZE
from subprocess import Popen, PIPE, STDOUT
from time import ctime, sleep
from queue import Queue
from threading import Thread
from Crypto.PublicKey import RSA
from Crypto import Random


def main():
    address = ""
    port = 22

    # generate RSA key set
    random_generator = Random.new().read
    local_key = RSA.generate(KEY_SIZE, random_generator)
    local_public_key = local_key.publickey().exportKey()  # export returns a byte string of the key

    # create listening socket for incoming connections
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((address, port))
    server.listen(1)

    while True:
        print("{}: Listening at port {}".format(ctime(), port))
        remote_sock, remote_address = server.accept()
        print("{}: {} CONNECTED".format(ctime(), remote_address))

        verified_keys = False

        while not verified_keys:
            """exchange public RSA keys and verify they were received without error"""

            print("exchanging keys")
            send_message(remote_sock, local_public_key, encode=False)
            remote_key = RSA.importKey(recv_message(remote_sock, decode=False))

            print("verifying keys")
            """
            exchange a random sequence with the remote client, using both sets of keys for
            encryption/decryption. if the sequence returned matches the one sent then
            both public keys were received without error
            """
            verify_sequence = encrypted_recv(remote_sock, local_key)
            encrypted_send(remote_sock, verify_sequence, remote_key)

            verified = encrypted_recv(remote_sock, local_key)

            # remote client will send "True" if the sequences matched
            if verified == "True":
                verified_keys = True
                print("{}: {} keys exchanged and verified".format(ctime(), remote_address))

        # create a shell to pass commands to
        shell, pwd = make_shell()
        stdout_queue = Queue()

        # stdout_reader is run in it's own thread to prevent blocking
        stdout_reader = Thread(target=get_result, args=(shell, stdout_queue))
        stdout_reader.daemon = True
        stdout_reader.start()

        while True:
            """
            Main server loop. runs until closed connection from
            client.

            Handles writing commands to the shell, and reading output from
            the stdout queue.
            """

            try:
                command = encrypted_recv(remote_sock, local_key)
            except ConnectionResetError:
                print("{} : CONNECTION LOST".format(ctime(), remote_address))
                remote_sock.close()
                break

            if command:
                print("{}: COMMAND : {}".format(ctime(), command))

                # send the command to the shell
                shell.stdin.write(command + "\n")
                shell.stdin.flush()
                sleep(.2)  # allows longer processes to generate output

                # get output if any
                message = ""
                while not stdout_queue.empty():
                    message += stdout_queue.get()

                # send output to remote client
                encrypted_send(remote_sock, message, remote_key)
            else:
                # if the message received is an empty string the connection was closed
                print("{} : CONNECTION CLOSED".format(ctime()))
                remote_sock.close()
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
    returns a subprocess Popen object connected to the local CLI
    """
    if os.name == "nt":
        command_line = ["CMD", "/k"]
        current_directory = "cd"
    else:
        command_line = ["bin/sh", "-s"]  # -s means commands will be read from standard input
        current_directory = "pwd"

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
    return shell, current_directory


if __name__ == "__main__":
    main()
