from hashlib import sha256
from time import time
import struct
from typing import List


class Blockchain:
    """
    A generic blockchain data structure that can be used to store any kind of data.
    It is easy to extend this chain by adding data to the payload.
    A block consists of:

    ==========================
    4 bytes    (I): length of the body : 0:4
    ========HEADER========
    4 bytes    (I): block number       : 4:8
    32 bytes (32s): previous block hash: 8:40
    32 bytes (32s): block body hash    : 40:72
    8 bytes    (Q): block creation time: 72:80
    ======END HEADER======
    ======BODY============
    n bytes   (ns): block body         : 80:n
    ======END BODY========
    ==========================

    ( "=" is used to not use padding )
    """
    blocks = []
    
    HEADER_SLICE = slice(4, 80)
    BLOCK_NR_SLICE = slice(4, 8)
    PREV_HASH_SLICE = slice(8, 40)
    BODY_HASH_SLICE = slice(40, 72)
    BLOCK_CREATION_TIME_SLICE = slice(72, 80)
    BODY_SLICE = slice(80, None)


    def add_block(self, body: str):
        prev_header = self.blocks[-1][self.HEADER_SLICE]
        prev_hash = sha256(prev_header).digest()
        block = self.encode_block(
            len(self.blocks), prev_hash, int(time()), body)
        self.blocks.append(block)

    def verify_chain(self):
        if len(self.blocks) == 0:
            return True

        for i in range(1, len(self.blocks)):
            # Check that all the hashes are correct
            prev_hash = sha256(self.blocks[i-1][self.HEADER_SLICE]).digest()
            curr_hash = self.blocks[i][self.PREV_HASH_SLICE]
            if prev_hash != curr_hash:
                return False

            # Check that the payload hashes are correct
            body_hash = self.blocks[i][self.BODY_HASH_SLICE]
            calc_body_hash = sha256(self.blocks[i][self.BODY_SLICE]).digest()
            if body_hash != calc_body_hash:
                return False

            # Check that the index is correct
            block_index = struct.unpack("=I", self.blocks[i][self.BLOCK_NR_SLICE])[0]
            if block_index != i:
                return False

            # Check that all the times are in order
            prev_time = struct.unpack("=Q", self.blocks[i-1][self.BLOCK_CREATION_TIME_SLICE])[0]
            curr_time = struct.unpack("=Q", self.blocks[i][self.BLOCK_CREATION_TIME_SLICE])[0]
            if curr_time < prev_time:
                return False

        return True

    def import_chain(self, chain: List[bytes] | bytes):
        if isinstance(chain, list):
            self.blocks = chain
        elif isinstance(chain, bytes):
            self.blocks = [chain]
        else:
            raise Exception("Invalid import data")

    def export_chain(self):
        return self.blocks

    @staticmethod
    def encode_block(n: int, prev_hash: bytes, time: int, body: str):
        """
        Encode a block
        Packs the block into an array of bytes

        :param n: block number
        :param prev_hash: previous block hash
        :param time: time of block creation
        :param body: block body
        """
        block = struct.pack(f"=2I32s32sQ{len(body)}s",
                            len(body), n, prev_hash, sha256(body.encode()).digest(), time, body.encode())
        return block

    @staticmethod
    def decode_block(block: bytes):
        """
        Decode a block
        Unpacks the block into an array of bytes

        Note: the 80 in the format string is the length of the header

        :param block: block to decode
        """
        block_len, n, prev_hash, body_hash, time, body = struct.unpack(
            f"=2I32s32sQ{len(block)-80}s", block)
        return block_len, n, prev_hash, body_hash, time, body.decode()

if __name__ == "__main__":
    bc = Blockchain()
    bc.import_chain(bc.encode_block(0, b"", 0, "Genesis block"))
    N = 10**4
    t0 = time()
    for n in range(N):
        bc.add_block("")
    t1 = time()
    print(f"Time to add {N} blocks:", round((t1-t0)*10**3), "ms")
    print(f"Time to add 1 block:", round(((t1-t0)/N)*10**6, 3), "us")
    print("Verify chain: ", bc.verify_chain())
    print(f"Size of a blockchain of {N} blocks:", sum([len(block) for block in bc.blocks])//1024, "kB")