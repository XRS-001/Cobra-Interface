from io import BytesIO
from Bitcoin.ecc import hash256
import requests

def little_endian_to_int(b):
    return int.from_bytes(b, 'little')


def int_to_little_endian(n, length):
    return n.to_bytes(length, 'little')


def read_varint(s):
    i = s.read(1)[0]
    if i == 0xfd:
        return little_endian_to_int(s.read(2))
    elif i == 0xfe:
        return little_endian_to_int(s.read(4))
    elif i == 0xff:
        return little_endian_to_int(s.read(8))
    else:
        return i


def encode_varint(i):
    if i < 0xfd:
        return bytes([i])
    elif i < 0x10000:
        return b'\xfd' + int_to_little_endian(i, 2)
    elif i < 0x100000000:
        return b'\xfe' + int_to_little_endian(i, 4)
    elif i < 0x10000000000000000:
        return b'\xff' + int_to_little_endian(i, 8)
    else:
        raise ValueError('integer too large: {}'.format(i))

import Bitcoin.script as script

SIGHASH_ALL = 1
class Tx:
    
    def __init__(self, version, tx_ins, tx_outs, locktime, testnet=False, segwit=False):
        self.version = version
        self.tx_ins = tx_ins
        self.tx_outs = tx_outs
        self.locktime = locktime
        self.testnet = testnet
        self.segwit = segwit
        self._hash_prevouts = None
        self._hash_sequence = None
        self._hash_outputs = None
    

    def __repr__(self):
        tx_ins = ''
        for tx_in in tx_ins:
            tx_ins += tx_in.__repr__() + '\n'

        tx_outs = ''
        for tx_out in tx_outs:
            tx_outs += tx_out.__repr__() + '\n'

        return f'tx: {self.id()} \nversion: {self.version}\ntx_ins:\n{tx_ins}tx_outs:\n{tx_outs}locktime: {self.locktime}'


    def id(self):
        return self.hash().hex()

    
    def hash(self):
        return hash256(self.serialize_legacy())[::-1]


    def fee(self, testnet=False):
        input_sum, output_sum = 0, 0
        for tx_in in self.tx_ins:
            input_sum += tx_in.value(testnet=testnet)
        for tx_out in self.tx_outs:
            output_sum += tx_out.value(testnet=testnet)
        return input_sum - output_sum
    

    def is_coinbase(self):
        if len(self.tx_ins) != 1:
            return False
        first_input = self.tx_ins[0]
        if first_input.prev_tx != b'\x00' * 32:
            return False
        if first_input.prev_index != 0xffffffff:
            return False
        return True
    

    def coinbase_height(self):
        if not self.is_coinbase():
            return None
        element = self.tx_ins[0].script_sig.cmds[0]
        return little_endian_to_int(element)
    

    @classmethod
    def parse(cls, s, testnet=False):
        s.read(4)
        if s.read(1) == b'x00':
            parse_method = cls.parse_segwit
        else:
            parse_method = cls.parse_legacy
        s.seek(-5, 1)
        return parse_method(s, testnet=testnet)


    @classmethod
    def parse_legacy(cls, stream, testnet=False):
        version = little_endian_to_int(stream.read(4))
        num_inputs = read_varint(stream)
        inputs = []
        for _ in range (num_inputs):
            inputs.append(TxIn.parse(stream))

        num_outputs = read_varint(stream)
        outputs = []
        for _ in range (num_outputs):
            outputs.append(TxOut.parse(stream))
        locktime = little_endian_to_int(stream.read(4))
        return cls(version, inputs, outputs, locktime, testnet=testnet, segwit=False)
    

    @classmethod
    def parse_segwit(cls, s, testnet=False):
        version = little_endian_to_int(s.read(4))
        marker = s.read(2)
        if marker != b'\x00\x01':
            raise RuntimeError('Not a segwit transaction {}'.format(marker))
        num_inputs = read_varint(s)
        inputs = []
        for _ in range(num_inputs):
            inputs.append(TxIn.parse(s))
        num_outputs = read_varint(s)
        outputs = []
        for _ in range(num_outputs):
            outputs.append(TxOut.parse(s))
        for tx_in in inputs: 
            num_items = read_varint(s)
            items = []
            for _ in range(num_items):
                item_len = read_varint(s)
                if item_len == 0:
                    items.append(0)
                else:
                    items.append(s.read(item_len))
            tx_in.witness = items
        locktime = little_endian_to_int(s.read(4))
        return cls(version, inputs, outputs, locktime, 
                   testnet=testnet, segwit=True)


    def serialize(self):
        if self.segwit:
            return self.serialize_segwit()
        else:
            return self.serialize_legacy()


    def serialize_legacy(self):  
        result = int_to_little_endian(self.version, 4)
        result += encode_varint(len(self.tx_ins))
        for tx_in in self.tx_ins:
            result += tx_in.serialize()
        result += encode_varint(len(self.tx_outs))
        for tx_out in self.tx_outs:
            result += tx_out.serialize()
        result += int_to_little_endian(self.locktime, 4)
        return result


    def serialize_segwit(self):
        result = int_to_little_endian(self.version, 4)
        result += b'\x00\x01'  
        result += encode_varint(len(self.tx_ins))
        for tx_in in self.tx_ins:
            result += tx_in.serialize()
        result += encode_varint(len(self.tx_outs))
        for tx_out in self.tx_outs:
            result += tx_out.serialize()
        for tx_in in self.tx_ins:  
            result += int_to_little_endian(len(tx_in.witness), 1)
            for item in tx_in.witness:
                if type(item) == int:
                    result += int_to_little_endian(item, 1)
                else:
                    result += encode_varint(len(item)) + item
        result += int_to_little_endian(self.locktime, 4)
        return result
    

    def sig_hash(self, input_index, redeem_script=None):
        s = int_to_little_endian(self.version, 4)
        s += encode_varint(len(self.tx_ins))
        for i, tx_in in enumerate(self.tx_ins):
            if i == input_index:
                if redeem_script:
                    script_sig = redeem_script
                else:
                    script_sig = tx_in.script_pubkey
            else:
                script_sig = None
            s += TxIn(
                prev_tx=tx_in.prev_tx,
                prev_index=tx_in.prev_index,
                script_sig=script_sig,
                sequence=tx_in.sequence,
            ).serialize()
        s += encode_varint(len(self.tx_outs))
        for tx_out in self.tx_outs:
            s += tx_out.serialize()
        s += int_to_little_endian(self.locktime, 4)
        s += int_to_little_endian(SIGHASH_ALL, 4)
        h256 = hash256(s)
        return int.from_bytes(h256, 'big')
    

    def hash_prevouts(self):
        if self._hash_prevouts is None:
            all_prevouts = b''
            all_sequence = b''
            for tx_in in self.tx_ins:
                all_prevouts += tx_in.prev_tx[::-1] + int_to_little_endian(tx_in.prev_index, 4)
                all_sequence += int_to_little_endian(tx_in.sequence, 4)
            self._hash_prevouts = hash256(all_prevouts)
            self._hash_sequence = hash256(all_sequence)
        return self._hash_prevouts


    def hash_sequence(self):
        if self._hash_sequence is None:
            self.hash_prevouts()  # this should calculate self._hash_prevouts
        return self._hash_sequence


    def hash_outputs(self):
        if self._hash_outputs is None:
            all_outputs = b''
            for tx_out in self.tx_outs:
                all_outputs += tx_out.serialize()
            self._hash_outputs = hash256(all_outputs)
        return self._hash_outputs


    def sig_hash_bip143(self, input_index, redeem_script=None, witness_script=None):
        '''Returns the integer representation of the hash that needs to get
        signed for index input_index'''
        tx_in = self.tx_ins[input_index]
        # per BIP143 spec
        s = int_to_little_endian(self.version, 4)
        s += self.hash_prevouts() + self.hash_sequence() # type: ignore
        s += tx_in.prev_tx[::-1] + int_to_little_endian(tx_in.prev_index, 4)
        if witness_script:
            script_code = witness_script.serialize()
        elif redeem_script:
            script_code = script.p2pkh_script(redeem_script.cmds[1]).serialize()
        else:
            script_code = script.p2pkh_script(tx_in.script_pubkey.cmds[1]).serialize()
        s += script_code
        s += int_to_little_endian(tx_in.amount, 8)
        s += int_to_little_endian(tx_in.sequence, 4)
        s += self.hash_outputs() # type: ignore
        s += int_to_little_endian(self.locktime, 4)
        s += int_to_little_endian(SIGHASH_ALL, 4)
        return int.from_bytes(hash256(s), 'big')


    def verify_input(self, input_index):
        '''Returns whether the input has a valid signature'''
        # get the relevant input
        tx_in = self.tx_ins[input_index]
        # grab the previous ScriptPubKey
        script_pubkey = tx_in.script_pubkey(testnet=self.testnet)
        # check to see if the ScriptPubkey is a p2sh
        if script_pubkey.is_p2sh_script_pubkey():
            # the last cmd has to be the RedeemScript to trigger
            cmd = tx_in.script_sig.cmds[-1]
            # parse the RedeemScript
            raw_redeem = int_to_little_endian(len(cmd), 1) + cmd
            redeem_script = script.Script.parse(BytesIO(raw_redeem))
            # the RedeemScript might be p2wpkh or p2wsh
            if redeem_script.is_p2wpkh_script_pubkey():
                z = self.sig_hash_bip143(input_index, redeem_script)
                witness = tx_in.witness
            elif redeem_script.is_p2wsh_script_pubkey():
                cmd = tx_in.witness[-1]
                raw_witness = encode_varint(len(cmd)) + cmd
                witness_script = script.Script.parse(BytesIO(raw_witness))
                z = self.sig_hash_bip143(input_index, witness_script=witness_script)
                witness = tx_in.witness
            else:
                z = self.sig_hash(input_index, redeem_script)
                witness = None
        else:
            # ScriptPubkey might be a p2wpkh or p2wsh
            if script_pubkey.is_p2wpkh_script_pubkey():
                z = self.sig_hash_bip143(input_index)
                witness = tx_in.witness
            elif script_pubkey.is_p2wsh_script_pubkey():
                cmd = tx_in.witness[-1]
                raw_witness = encode_varint(len(cmd)) + cmd
                witness_script = script.Script.parse(BytesIO(raw_witness))
                z = self.sig_hash_bip143(input_index, witness_script=witness_script)
                witness = tx_in.witness
            else:
                z = self.sig_hash(input_index)
                witness = None
        # combine the current ScriptSig and the previous ScriptPubKey
        combined = tx_in.script_sig + script_pubkey
        # evaluate the combined script
        return combined.evaluate(z, witness)
    

    def verify(self):
        if self.fee() < 0:
            return False
        for i in range(len(self.tx_ins)):
            if not self.verify_input(i):
                return False
        return True


class TxIn:

    def __init__(self, prev_tx, prev_index, script_sig=None, script_pubkey=None, amount=0, sequence=0xffffffff):
        self.prev_tx = prev_tx
        self.prev_index = prev_index 
        if script_sig == None:
            self.script_sig = script.Script()
        else:
            self.script_sig = script_sig
        self.script_pubkey = script_pubkey
        self.sequence = sequence
        self.amount = amount


    def __repr__(self):
        return f"{self.prev_tx.hex()}:{self.prev_index}"

    
    @classmethod
    def parse(cls, stream):
        prev_tx = stream.read(32)[::-1]
        prev_index = little_endian_to_int(stream.read(4))
        script_sig = script.Script.parse(stream)
        sequence = little_endian_to_int(stream.read(4))
        return cls(prev_tx, prev_index, script_sig, sequence)


    def serialize(self):
        result = self.prev_tx[::-1]
        result += int_to_little_endian(self.prev_index, 4)
        result += self.script_sig.serialize()
        result += int_to_little_endian(self.sequence, 4)
        return result

    
    def fetch_tx(self, testnet=False):
        return TxFetcher.fetch(self.prev_tx.hex(), testnet=testnet)


    def value(self, testnet=False):
        tx = self.fetch_tx(testnet=testnet)
        return tx.tx_outs[self.prev_index].amount

class TxOut:

    def __init__(self, amount, script_pubkey):
        self.amount = amount
        self.script_pub_key = script_pubkey


    def __repr__(self):
        return f'{self.amount}:{self.script_pub_key}'


    @classmethod
    def parse(cls, stream):
        amount = little_endian_to_int(stream.read(8))
        script_pubkey = script.Script.parse(stream)
        return cls(amount, script_pubkey)

    
    def serialize(self):
        result = int_to_little_endian(self.amount, 8)
        result += self.script_pub_key.serialize()
        return result

class TxFetcher():
    cache = {}

    @classmethod
    def fetch(cls, tx_id, testnet=False, fresh=False):
        if fresh or (tx_id not in cls.cache):
            rpc_url = ""
            response = requests.get(rpc_url)
            try:
                raw = bytes.fromhex(response.text.strip())
            except ValueError:
                raise ValueError(f'unexpected response: {response.text}')
            if raw[4] == 0:
                raw = raw[:4] + raw[:6]
                tx = Tx.parse(BytesIO(raw), testnet)
                tx.locktime = little_endian_to_int(raw[-4:])
            else:
                tx = Tx.parse(BytesIO(raw), testnet=testnet)
            if tx.id() != tx_id:
                raise ValueError(f'not the same id: {tx.id()} vs {tx_id}')
            
            cls.cache[tx_id] = tx
        cls.cache[tx_id].testnet = testnet
        return cls.cache[tx_id ]