#!env/bin/python
import json
from operator import truediv
import socketserver
import sys
import threading
import time
import logging
from PyChain import Blockchain, request
from PyChain.protocol import recv_msg, send_msg

"""
A PyChain full node
This network communicated through sockets.
Messages are encoded using JSON.
The fields are:
    - request: the type of request
    - body (optional, depends on request): the body of the request
    - time
A full node's job is to keep track of the blockchain,
by receiving blocks, verifying them and finally adding them to the blockchain.
They also answer to requests from other participants of the blockchain.
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
            logging.info(f"Got {n} peers from {peer}")
            new_peers.union(response["response"])
        except:
            pass

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
    Returns the blockchain with the longest chain from the peers.
    This function also verifies that the chain is valid.
    """
    peer_length = {}
    for peer in peers:
        try:
            response = request(peer, "get_length")
            peer_length[peer] = response["response"]
        except Exception as e:
            print(e)
    sorted_peer_length = {k: v for k, v in sorted(
        peer_length.items(), key=lambda item: -item[1])}

    for peer, length in sorted_peer_length.items():
        # If the peer with the longest chain does not have a longer chain than the local one: break
        if length <= len(blockchain.blocks):
            break
        response = request(peer, "get_blocks")
        assert len(response["response"]) == length
        chain = Blockchain()
        chain.import_chain([
            Blockchain.encode_block(0, b"", 0, "Genesis block")])
        for block in response["response"][1:]:
            chain.blocks.append(Blockchain.dict_to_block(block))
        valid, reason = chain.verify_chain()
        if valid:
            return chain


class RequestHandler(socketserver.BaseRequestHandler):
    @staticmethod
    def create_response(response: str | dict, http_code: int):
        return {"response": response,
                "time": time.time(),
                "http_code": http_code}

    """
    Here come request handing functions
    """

    def get_blocks(self):
        return self.create_response([Blockchain.block_to_dict(block)
                                     for block in blockchain.blocks], 200)

    def get_block(self, index: int):
        return self.create_response(Blockchain.block_to_dict(blockchain.blocks[index]), 200)

    def get_blochchain_length(self):
        return self.create_response(len(blockchain.blocks), 200)

    def get_peers(self):
        return self.create_response(peers, 200)

    def recieve_block(self, block: dict):
        blockchain.blocks.append(Blockchain.dict_to_block(block))
        if not blockchain.verify_chain()[0]:
            blockchain.blocks.pop()
            return self.create_response("Invalid chain", 400)
        return self.create_response("OK, block added", 200)

    def add_peer(self, host: str):
        if host in peers:
            return self.create_response("Already in peers", 400)
        peers.append(host)
        return self.create_response("OK", 200)

    def handle(self):
        """
        This method is called when a request is received
        It checks the request type and returns a response
        """
        host, port = self.client_address
        data = recv_msg(self.request).decode()
        request = json.loads(data)

        logging.info(f"{host}:{port} requested {request['request']}")
        match request['request']:
            case 'get_blocks':
                response = self.get_blocks()
            case 'get_block':
                response = self.get_block(request['body'])
            case "ping":
                response = self.create_response("pong", 200)
            case "recieve_block":
                response = self.recieve_block(request["body"])
            case "get_peers":
                response = self.get_peers()
            case "get_length":
                response = self.get_blochchain_length()
            case "add_peer":
                response = self.add_peer(request["body"])
            case _:
                response = self.create_response("Unknown request", 400)

        send_msg(self.request, json.dumps(response).encode())


def poll_peers_thread():
    global blockchain
    global is_on_server
    logging.info("Polling peers has started")
    while True:
        longest_chain_found = longest_chain(peers)
        if longest_chain_found:
            logging.info(
                f"New longest chain of length {len(longest_chain_found.blocks)} found.")
            blockchain = longest_chain_found
        time.sleep(5)


if __name__ == '__main__':
    is_on_server = True
    HOST, PORT = 'localhost', int(sys.argv[1])
    static_peers = [line for line in open(
        'peers.txt', 'r').read().split('\n') if line != '']
    peers = get_peers(check_peers(static_peers))
    socketserver.TCPServer.allow_reuse_address = True
    polling_thread = threading.Thread(target=poll_peers_thread)
    polling_thread.start()
    with socketserver.ThreadingTCPServer((HOST, PORT), RequestHandler) as server:
        logging.info("Starting server on {}:{}".format(HOST, PORT))
        server.serve_forever()
        logging.info("Stopping server")
