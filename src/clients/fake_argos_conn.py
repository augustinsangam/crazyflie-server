import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('0.0.0.0', 3995))


while True:
    print('Commands:\n1 - Send message\n2 - Recieve message\n3 - Reconnect\n4 - Quit')
    inp = input()
    if inp == '1':
        print('Input drone number:')
        num = input()
        print(
            'Sending: {"type":"pulse","data":{"name":"fake_drone_' + str(num) + '","timestamp": ' + str(num) + ',"speed": ' + str(num) + ',"battery": ' + str(num) + ',"position": [' + str(num) + ', ' + str(num) + ', ' + str(num) + '],"flying": false,"ledOn": false,"real": false}}')
        client.send(bytes(
            '{"type":"pulse","data":{"name":"fake_drone_' + str(num) + '","timestamp": ' + str(num) + ',"speed": ' + str(num) + ',"battery": ' + str(num) + ',"position": [' + str(num) + ', ' + str(num) + ', ' + str(num) + '],"orientation": 0.785,"ranges": [127,127,127,127],"flying": false,"ledOn": false,"real": false}}', 'ascii'))
        print('Sent')
    elif inp == '2':
        print('Waiting for message:')
        response = client.recv(4096)
        print('Message recieved:')
        print(response)
    elif inp == '3':
        print('Reconnecting')
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('127.0.0.1', 3995))
            print('Reconnected')
        except:
            print('Could not reconnect')
    elif inp == '4':
        break
print('Closed')
