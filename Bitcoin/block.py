from tx import little_endian_to_int, int_to_little_endian, hash256
from merkle import merkle_root

class Block:
    
    def __init__(self, version, prev_block, merkle_root, timestamp, bits, nonce, tx_hashes=None ):
        self.version = version
        self.prev_block = prev_block
        self.merkle_root = merkle_root
        self.timestamp = timestamp
        self.bits = bits
        self.nonce = nonce
        self.tx_hashes = tx_hashes

    @classmethod
    def parse(cls, s):
        version = little_endian_to_int(s.read(4))
        prev_block = s.read(32)[::-1]
        merkle_root = s.read(32)[::-1]
        timestamp = little_endian_to_int(s.read(4))
        bits = s.read(4)
        nonce = s.read(4)
        return cls(version, prev_block, merkle_root, timestamp, bits, nonce)


    def serialize(self):
        result = int_to_little_endian(self.version, 4)
        result += self.prev_block[::-1]
        result += self.merkle_root[::-1]
        result += int_to_little_endian(self.timestamp, 4)
        result += self.bits
        result += self.nonce
        return result


    def hash(self):
        s = self.serialize()
        sha = hash256(s)
        return sha[::-1]
    

    def bip9(self):
        return self.version >> 29 == 0b001

    def bip91(self):
        return self.version >> 4 & 1 == 1

    def bip141(self):
        return self.version >> 1 & 1 == 1
    

    def difficulty(self):
        return 0xffff * 256**(0x1d-3) / self.target()
    

    def target(self):
        return bits_to_target(self.bits)
    

    def check_pow(self):
        sha = hash256(self.serialize())
        proof = little_endian_to_int(sha)
        return proof < self.target()
    

    def validate_merkle_root(self):
        hashes = [h[::-1] for h in self.tx_hashes] # type: ignore
        root = merkle_root(hashes)
        return root[::-1] == self.merkle_root
    

def bits_to_target(bits):
    exponent = bits[-1]
    coefficient = little_endian_to_int(bits[:-1])
    return coefficient * 256**(exponent - 3)


def target_to_bits(target):
    raw_bytes = target.to_bytes(32, 'big')
    raw_bytes = raw_bytes.lstrip(b'\x00') 
    if raw_bytes[0] > 0x7f: 
        exponent = len(raw_bytes) + 1
        coefficient = b'\x00' + raw_bytes[:2]
    else:
        exponent = len(raw_bytes) 
        coefficient = raw_bytes[:3]  
    new_bits = coefficient[::-1] + bytes([exponent]) 
    return new_bits


TWO_WEEKS = 60 * 60 * 24 * 14
def calculate_new_bits(previous_bits, time_differential):
    if time_differential > TWO_WEEKS * 4:
        time_differential = TWO_WEEKS * 4
    if time_differential < TWO_WEEKS // 4:
        time_differential = TWO_WEEKS // 4
    new_target = bits_to_target(previous_bits) * time_differential // TWO_WEEKS
    return target_to_bits(new_target) 