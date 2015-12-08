#Python3

import socket
import sys
import subprocess
import time
import os


def main():
    print(' ', '#'*40, '\n\n programs:\n client\n server\n QUIT\n\n', '#'*40)
    available_programs = ['client', 'server', 'QUIT']

    while True:
        selection = input('>>>')

        if selection in available_programs:
            if selection == 'client':
                run_client()
            elif selection == 'server':
                run_server()
            elif selection == 'QUIT':
                print('exiting..')
                sys.exit()
        else:
            print('invalid selection...')


"""
messaging:
any messages sent between programs will be preceded by
by the message length, so the reciver knows when the full
message has been recieved, and can move on.

Both send_message and get_message are utilized by client and
server.
"""


def get_message(connection):
    temp_message = connection.recv(1024)
    if temp_message:
        message_length  = int(temp_message.decode())
        message = ''
        while message_length > 0:
            temp_message = connection.recv(1024)
            message += temp_message.decode()
            message_length -= len(temp_message.decode())
        return message
    else:
        return temp_message
    

def send_message(connection, message):
    message_length = str(len(message))
    try:
        connection.send(message_length.encode())
        connection.send(message.encode())
    except:
        print('unable to send...')
        

def get_result(shell):
    """
    returns any results from stderr and stdout
    using Popen.communicate()
        
    if there is nothing to read from stdout or
    stderr it returns an acknowledgement of the
    command completion
    """
    try:
        return shell.stdout.read()
    except:
        return 'command complete'

    
def do_command(shell, command):
    """
    writes command to shell
    command must be str object
    """
    shell.stdin.write(command + '\n')
    shell.stdin.flush()
    print('command complete...')


def run_client():
    """
    run_client creates a client socket to send commands
    to an ssh server.
    """
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(5.0)
    connection = False

    while not connection:
        """
        client connect loop

        trys connecting with user specified server, if
        connection fails, the user is given the option to quit
        or try again.
        """
        host = input('target ip adress:\n')
        port = input('target port:\n')

        try:
            client.connect((host,int(port)))
            print('connected with: ', host)
            connection = True
        except:
            print('cannot connect...')
            try_again = input('do you want to try again?(y/n):\n')
            if try_again.lower() == 'y':
                continue
            else:
                print('exiting...')
                break

    while connection:
        """
        main client loop

        while there is a connection to a server, a command will
        be accepted and sent to the server. Then the client will wait
        for a response.
        """
        command = input('>>>')
        
        if command == 'QUIT':
            print('exiting...')
            client.close()
            connection = False
        else:
            try:
                send_message(client, command)
                reply = get_message(client)
                if reply:
                    print(reply)
                else:
                    print('connection closed by server!')
                    break
            except:
                continue
            

def run_server():
    """
    run_server creates a socket/shell to accept commands
    from a client program.

    The commands will be passed to an instance of shell.
    the shell stderr and stdout will be sent back to the
    client the command originated from.
    """

    import fcntl
    
    addr = ''
    port = 1024

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((addr, port))
    server.listen(1)
    print('listening at: ', addr, port)

    while True:
        no_conn = True
        
        while no_conn:
            conn_to_client, client_addr = server.accept()

            if conn_to_client:
                print('connected to: ', client_addr)
                no_conn = False

                
        """      
        The universal_newlines attribute of
        the subrocess shell(set to '= True'),
        allows stdin.write() to pass strings.
        Adding a newline charachter(\n) to the
        end of the string will tell the shell
        EOL.
        
        If universal_newline = False, and a
        byte string is passed, or if Universal_newlines
        is True and no new_line character is not
        added, std.write() will block as there
        is nothing telling the shell EOL.
        """
        shell = subprocess.Popen(['/bin/bash', '-s'],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 universal_newlines=True)

        
        """      
        set shell.stdout to nonblocking(linux only)
        """
        flags = fcntl.fcntl(shell.stdout, fcntl.F_GETFL)
        fcntl.fcntl(shell.stdout, fcntl.F_SETFL, flags| os.O_NONBLOCK)
                            

        while not no_conn:
            """
            main server loop
            """
            command = get_message(conn_to_client)

            if command:
                print(time.ctime(), client_addr, command)
                
                do_command(shell, command)
                time.sleep(0.2)
                '''
                time.sleep(0.2) is called to allow
                time for the longer processes to
                execute, and write any stdout data.

                this will eventually need a proper
                solution as there is no way to be
                certain all commands will exec in .2
                seconds.(exponential backoff?)
                '''
                result = get_result(shell)
                send_message(conn_to_client, result)
            else:
                print('connection closed by master...')
                shell.kill()
                break
            

if __name__ == '__main__':
    main()
    
