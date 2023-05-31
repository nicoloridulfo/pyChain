# PyChain

## A Space Efficient General Purpose Blockchain data structure written in Python

This blockchain is loosely modelled after bitcoin. However, since it is less application specific, it could in theory be used for almost anything (even bitcoin, just have to put things in the body of the block).

## Data structure

### Blocks
The blocks are stored as a list of C style structs. A block consists of the length of the body, a header and the body.
**Bytes**|**Description**|**Range**
:-----:|:-----:|:-----:
4 bytes (I)|length of the body |0:4
4 bytes (I)|block number |4:8
32 bytes (32s)|previous block hash|8:40
32 bytes (32s)|block body hash |40:72
8 bytes (Q)|block creation time|72:80
n bytes (ns)|block body |80:n

This makes the block a minimum of 80 bytes long.
The differences between PyChain's blocks and the bitcoin's are the following:
- Bitcoin's header has these fields, while PyChain doesn't
  - Version 
  - Difficulty target
  - Nonce 
- PyChain has a general purpose block body, while Bitcoin's reserved for transactions.

## Performance
It takes 24ms to add 10'000 blocks to the chain. That is 2.352 us per block.

The resulting blockchain would be 800KB. That is on par with bitcoin.
