import socket
import sys
from messenger import *  # includes global variables KEY_SIZE, BLOCK SIZE, RANDOM_SAMPLE
from Crypto.PublicKey import RSA
from Crypto import Random
from Crypto.Random import random


def main():
    # create an RSA key set
    random_generator = Random.new().read
    local_key = RSA.generate(KEY_SIZE, random_generator)
    local_public_key = local_key.publickey().exportKey()  # export returns a byte string of the key

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # booleans used to control looping
    connected = False
    verified_keys = False

    while not connected:
        """
        connection loop: will attempt to create a connection with
        user specified address
        """
        address = input('Target IP address: ')
        port = int(input('Target port: '))

        try:
            print("Attempting to connect...")
            client.connect((address, port))
            print("successful connect with {} {}".format(address, port))
            connected = True
        except socket.error as err:
            print("Unable to connect\n" + str(err))

        while not verified_keys:
            """
            exchange public RSA keys, and verify they were received without error
            """
            print("exchanging keys")
            remote_key = RSA.importKey(recv_message(client, decode=False))
            send_message(client, local_public_key, encode=False)

            print("verifying keys")
            # generate a random sequence to verify both keys were received correctly
            random_sequence = ""
            while len(random_sequence) < BLOCK_SIZE:
                random_sequence += random.choice(RANDOM_SAMPLE)

            """
            exchange the random sequence with the server, using both sets of keys for
            encryption/decryption. if the sequence returned matches the one sent then
            both public keys were received without error
            """
            encrypted_send(client, random_sequence, remote_key)
            returned_sequence = encrypted_recv(client, local_key)

            if returned_sequence == random_sequence:
                encrypted_send(client, "True", remote_key)
                verified_keys = True
                print("keys verified, ready to go")
            else:
                print("key verification failed...")
                encrypted_send(client, "False", remote_key)
                # sending False is arbitrary, anything but True will trigger the key exchange to restart

        while True:
            """
            Main ssh loop. Handles sending and receiving messages with server, and updates
            current working directory.
            """
            command = input(">>>")

            if command == 'QUIT':
                print('exiting...')
                client.close()
                sys.exit()

            try:
                encrypted_send(client, command, remote_key)
                message = encrypted_recv(client, local_key)
            except ConnectionResetError:
                print("Connection with server lost...")
                break

            if message:
                print(message)
            else:
                print('server closed connection..')
                break

        connected = False
        verified_keys = False
        client.detach()


if __name__ == '__main__':
    main()
