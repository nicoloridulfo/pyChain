#!env/bin/python
import json
import socketserver
import socket
import sys
import time
import logging
from urllib import response

from PyChain import Blockchain

"""
A PyChain full node
This network communicated through sockets.
Messages are encoded using JSON.
The fields are:
    - request: the type of request
    - body (optional, depends on request): the body of the request
    - time
"""

logging.basicConfig(level=logging.DEBUG)

blockchain = Blockchain()
blockchain.import_chain([
    Blockchain.encode_block(0, b"", 0, "Genesis block")])


def get_peers(old_peers: list):
    new_peers = set(old_peers)

    for peer in static_peers:
        try:
            response = request(peer, "get_peers")
            n = len(response["response"])
            print(f"Got {n} peers from {peer}")
            new_peers.union(response["response"])
        except:
            print("Could not connect to peer", peer)

    return list(new_peers)


def check_peers(peers: list):
    """
    Checks if a peer responds to ping
    """
    alive_peers = []
    for peer in peers:
        try:
            response = request(peer, "ping")
            if response["response"] == "pong":
                alive_peers.append(peer)
                request(peer, "add_me", f"{HOST}:{PORT}")
        except:
            pass
    return alive_peers


def longest_chain(peers: list):
    """
    Returns the peer with the longest chain
    """
    longest_chain = None
    longest_length = 0
    for peer in peers:
        try:
            response = request(peer, "get_blocks")
            if len(response["response"]) < longest_length:
                continue
            chain = Blockchain()
            blockchain.import_chain([
                Blockchain.encode_block(0, b"", 0, "Genesis block")])
            for block in response["response"]:
                chain.blocks.append(Blockchain.dict_to_block(block))
            valid, reason = chain.verify_chain()
            if valid:
                longest_chain = chain
                longest_length = len(response["response"])
        except:
            pass
    return longest_chain


def request(host, request: str, body: str | dict = None):
    """
    Send a request to a host and return the response.
    host: "ip:port"
    request: the type of request [get_blocks, ping, get_peers, recieve_block]
    body: string or dict

    returns the json response
    """
    host, port = host.split(":")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, int(port)))
        data = {"request": request}
        if body:
            data["body"] = body
        sock.sendall(json.dumps(data).encode())
        return json.loads(sock.recv(1024).decode())


class RequestHandler(socketserver.BaseRequestHandler):
    @staticmethod
    def create_response(response: str | dict, http_code: int):
        return {"response": response,
                "time": time.time(),
                "http_code": http_code}

    def get_blocks(self):
        return self.create_response([Blockchain.block_to_dict(block)
                                     for block in blockchain.blocks], 200)

    def get_peers(self):
        return self.create_response(peers, 200)

    def recieve_block(self, block: dict):
        blockchain.blocks.append(Blockchain.dict_to_block(block))
        if not blockchain.verify_chain()[0]:
            blockchain.blocks.pop()
            return self.create_response("Invalid chain", 400)
        return self.create_response("OK, block added", 200)

    def add_me(self, host: str):
        if host in peers:
            return self.create_response("Already in peers", 400)
        peers.append(host)
        return self.create_response("OK", 200)

    def handle(self):
        host, port = self.client_address
        self.data = self.request.recv(1024).strip()
        request = json.loads(self.data.decode())

        logging.info(f"{host}:{port} requested {request['request']}")
        match request['request']:
            case 'get_blocks':
                response = self.get_blocks()
            case "ping":
                response = self.create_response("pong", 200)
            case "recieve_block":
                response = self.recieve_block(request["body"])
            case "get_peers":
                response = self.get_peers()
            case "add_me":
                response = self.add_me(request["body"])
            case _:
                return

        self.request.sendall(json.dumps(response).encode())


if __name__ == '__main__':
    HOST, PORT = 'localhost', int(sys.argv[1])
    static_peers = [line for line in open(
        'peers.txt', 'r').read().split('\n') if line != '']
    peers = get_peers(check_peers(static_peers))
    longest_chain_found = longest_chain(peers)
    if longest_chain_found:
        blockchain = longest_chain_found
    server = socketserver.TCPServer((HOST, PORT), RequestHandler)
    logging.info("Starting server on {}:{}".format(HOST, PORT))
    server.serve_forever()
