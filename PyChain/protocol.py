import socket
import json
import struct


"""
This file contains a bunch of functions that are used to communicate with other nodes.
"""
def send_msg(sock, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)

def recv_msg(sock):
    # Read message length and unpack it into an integer
    raw_msglen = _recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return _recvall(sock, msglen)

def _recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data

#https://stackoverflow.com/questions/17667903/python-socket-receive-large-amount-of-data
def request(host, request: str, body = None):
    """
    Sends a request to a host and returns the response
    """
    host, port = host.split(":")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, int(port)))
        data = {"request": request}
        if body:
            data["body"] = body
        send_msg(sock, json.dumps(data).encode())
        return json.loads(recv_msg(sock).decode())
