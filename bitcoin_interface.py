import secrets
import asyncio
import os
import time
import threading
import json 
from decimal import Decimal

class Bitcoin:  
    def __init__(self, parent_interface=None, initiate_rpc=True):
        self.parent_interface = parent_interface
        from Bitcoin import ecc as key
        from Bitcoin import authproxy
        from Bitcoin import tx
        from Bitcoin import script
        self.key = key
        self.bitcoin_rpc = authproxy.AuthServiceProxy
        self.tx = tx
        self.script = script
        try:
            with open("Bitcoin/cookie_path.txt", "r") as file:
                self.cookie_path = file.read()
        except:
            while True:
                self.cookie_path = input("Enter path to Bitcoin Core cookie file: ")
                if self.cookie_path != "":
                    with open("Bitcoin/cookie_path.txt", "w") as file:
                        file.write(self.cookie_path)
                    break
                
        if initiate_rpc:
            username, password = self.GetCredentials()
            self.rpc_url = f"http://{username}:{password}@127.0.0.1:8332"


    keys = []
    async def BitcoinInterface(self):
        with open("Bitcoin/keys.json", "r") as file:
            self.keys = file.readlines()
        print("1: My Addresses")
        print("2: Create Address")
        print("3: Delete Address")
        print("4: Sign Transaction")
        print("5: Check Address Balance")
        print("6: Blockchain Explorer")
        choice = input("")
        match choice:
            case "1":
                await self.Addresses()
            case "2":
                await self.CreateAddress()
            case "3":
                await self.DeleteAddress()
            case "4":
                await self.SignTransaction()
            case "5":
                await self.GetAddressBalance()
            case "6":
                await self.BlockchainExplorer()
            case _:
                if self.parent_interface:
                    await self.parent_interface.Main()
                else:
                    exit()


    async def Addresses(self):
        update_balances = input("Update balances? y/n: ") in ['Y', 'y']
        if not update_balances:
            with open ("Bitcoin/balances.json", 'r') as balances_read:
                balances = json.load(balances_read)
        else:
            with open("Bitcoin/balances.json", 'w') as balances_write:
                balances = {}
                for key in self.keys:
                    if key[:6] == "segwit":
                        address = self.key.PrivateKey(int(key[6:], 16)).point.address(segwit=True)
                    else:
                        address = self.key.PrivateKey(int(key, 16)).point.address()
                    rpc = self.bitcoin_rpc(self.rpc_url)
                    try:
                        status_thread = threading.Thread(target=self.GetScanStatus, args=[f" for outputs to {address}"])
                        status_thread.daemon = True
                        status_thread.start()
                        result = rpc.scantxoutset("start", [{"desc": f"addr({address})"}])
                    except Exception as e:
                        print(f"Error: {e}")
                        await self.BitcoinInterface()
                    balance = int(result['total_amount'] * Decimal(1e8))
                    balances[address] = balance
                    time.sleep(3)
                json.dump(balances, balances_write)

        total_balance = 0
        for key in self.keys:
            if key[:6] == "segwit":
                address = self.key.PrivateKey(int(key[6:], 16)).point.address(segwit=True)
                balance = balances[address] if address in balances else 0
                print(f"Address: {address} (SegWit), balance: {balance:,} sats")
                total_balance += balance
            else:
                address = self.key.PrivateKey(int(key, 16)).point.address()
                balance = balances[address] if address in balances else 0
                print(f"Address: {address} (Base58), balance: {balance:,} sats")
                total_balance += balance
        print(f"Total balance: {total_balance:,} sats")
        await self.BitcoinInterface()


    async def TotalBalance(self):
        with open ("Bitcoin/balances.json", 'r') as file:
            balances = json.load(file)

        with open("Bitcoin/keys.json", "r") as file:
            self.keys = file.readlines()
            
        total_balance = 0
        for key in self.keys:
            if key[:6] == "segwit":
                address = self.key.PrivateKey(int(key[6:], 16)).point.address(segwit=True)
                balance = balances[address]
                total_balance += balance
            else:
                address = self.key.PrivateKey(int(key, 16)).point.address()
                balance = balances[address]
                total_balance += balance
        return total_balance / 1e8


    async def CreateAddress(self):
        is_segwit = input("SegWit? y/n: ") in ["Y", "y"]
        if is_segwit:
            key = self.key.PrivateKey(int.from_bytes(secrets.token_bytes(32)))
            address = key.point.address(segwit=True)
            print(f"SegWit address generated: {address}")
            key = "segwit" + key.hex() + "\n"
        else:
            key = self.key.PrivateKey(int.from_bytes(secrets.token_bytes(32)))
            address = key.point.address()
            print(f"Base58 address generated: {address}")
            key = key.hex() + "\n"

        self.keys.append(key)
        with open("Bitcoin/keys.json", "w") as keys_file:
            keys_file.writelines(self.keys)
        with open ("Bitcoin/balances.json", 'r') as balance_load:
            balances = json.load(balance_load)
            balances[address] = 0
        with open("Bitcoin/balances.json", "w") as balance_write:
            json.dump(balances, balance_write)

        await self.BitcoinInterface()


    async def DeleteAddress(self):
        address_to_delete = input("Address: ")
        with open("Bitcoin/balances.json", "r") as balances_file:
            balances = json.load(balances_file)
        addresses = []
        key_in_file = ""
        for key in self.keys:
            if key[:6] == "segwit":
                key_in_file = key
                addresses.append(self.key.PrivateKey(int(key[6:], 16)).point.address(segwit=True))
            else:
                addresses.append(self.key.PrivateKey(int(key, 16)).point.address())
                    
        if address_to_delete not in addresses:
            print("Address not in keys file.")
            await self.BitcoinInterface()

        if balances[address_to_delete] != 0:
            print("Address has balance.")
            await self.BitcoinInterface()
        del balances[address_to_delete]
        self.keys.remove(key_in_file)
        with open("Bitcoin/keys.json", "w") as keys_file:
            keys_file.writelines(self.keys)

        with open("Bitcoin/balances.json", "w") as balances_write:
            json.dump(balances, balances_write)
        await self.BitcoinInterface()

        
    async def SignTransaction(self, memo=None):
        sending_address = input("Sending address: ")
        address_in_file = False
        for key in self.keys:
            if key[:6] == "segwit":
                if self.key.PrivateKey(int(key[6:], 16)).point.address(segwit=True) == sending_address:
                    address_in_file = True
                    signing_key = self.key.PrivateKey(int(key[6:], 16))
                    sender_segwit = True
                    break
            else:
                if self.key.PrivateKey(int(key, 16)).point.address() == sending_address:
                    address_in_file = True
                    signing_key = self.key.PrivateKey(int(key, 16))
                    sender_segwit = False
                    break
        if not address_in_file:
            print("Address not in keys file.")
            await self.BitcoinInterface()

        try:
            amount = int(input("Amount (sats): "))
        except:
            print("Not a valid amount.")
            await self.BitcoinInterface()

        try:
            fee = int(input("Fee (sats): "))
        except:
            print("Not a valid amount.")
            await self.BitcoinInterface()

        rpc = self.bitcoin_rpc(self.rpc_url)
        try:
            status_thread = threading.Thread(target=self.GetScanStatus)
            status_thread.daemon = True
            status_thread.start()
            result = rpc.scantxoutset("start", [{"desc": f"addr({sending_address})"}])
        except Exception as e:
            print(f"Error: {e}")
            await self.BitcoinInterface()

        balance_sats = int(float(result['total_amount']) * 1e8)
        if amount + fee > balance_sats: # type: ignore
            print("Account balance too low.")
            await self.BitcoinInterface()
        else:
            is_segwit = input("Receiver is SegWit? y/n: ") in ['y', 'Y']
            receiving_address = input("Receiving address: ")

            if is_segwit:
                if self.key.decode_bech32("bc", receiving_address) == (None, None):
                    print("Invalid SegWit address.")
                    await self.BitcoinInterface()
            else:
                if not self.key.decode_base58(receiving_address):
                    print("Invalid Base58 address.")
                    await self.BitcoinInterface()

            tx_ins = []
            input_value = 0
            for utxo in result['unspents']:
                if sender_segwit:
                    tx_ins.append(self.tx.TxIn(bytes.fromhex(utxo['txid']), utxo['vout'], script_pubkey=self.script.p2wpkh_script(self.key.decode_bech32("bc", sending_address)[1]), amount=int(utxo['amount'] * Decimal(1e8))))
                else:
                    tx_ins.append(self.tx.TxIn(bytes.fromhex(utxo['txid']), utxo['vout'], script_pubkey=self.script.p2pkh_script(self.key.decode_base58(sending_address)), amount=int(utxo['amount'] * Decimal(1e8))))
                input_value += int(utxo['amount'] * Decimal(1e8))
                if input_value >= amount + fee: # type: ignore
                    break
            
            if input_value - amount - fee != 0:
                if sender_segwit:
                    change_h160 = self.key.decode_bech32("bc", sending_address)[1]
                    change_script = self.script.p2wpkh_script(change_h160)
                else:
                    change_h160 = self.key.decode_base58(sending_address)
                    change_script = self.script.p2pkh_script(change_h160)
                change_output = self.tx.TxOut(input_value - amount - fee, change_script)
            else:
                change_output = False

            if is_segwit:
                out_160 = self.key.decode_bech32("bc", receiving_address)[1]
                out_scipt = self.script.p2wpkh_script(out_160)
            else:
                out_160 = self.key.decode_base58(receiving_address)
                out_scipt = self.script.p2pkh_script(out_160)
            tx_out = self.tx.TxOut(amount, out_scipt)

            if memo:
                memo_script = self.script.Script([0x6A, bytes(memo, encoding='utf-8')])
                memo_out = self.tx.TxOut(0, memo_script)
                tx_outs = [change_output, tx_out, memo_out] if change_output else [tx_out, memo_out]
                tx = self.tx.Tx(1, tx_ins, tx_outs, 0)
            else:
                tx_outs = [change_output, tx_out] if change_output else [tx_out]
                tx = self.tx.Tx(1, tx_ins, tx_outs, 0)
            if sender_segwit:
                for i in range(0, len(tx_ins)):
                    z = tx.sig_hash_bip143(i)
                    der = signing_key.sign(z).der()
                    sig = der + bytes([0x01])
                    sec = signing_key.point.sec()
                    tx.tx_ins[i].witness = [sig, sec]
            else:
                for i in range(0, len(tx_ins)):
                    z = tx.sig_hash(i)
                    der = signing_key.sign(z).der()
                    sig = der + self.tx.SIGHASH_ALL.to_bytes(1, 'big')
                    sec = signing_key.point.sec()
                    script_sig = self.script.Script([sig, sec])
                    tx.tx_ins[i].script_sig = script_sig

            if sender_segwit:
                serialized_tx = tx.serialize_segwit().hex()
            else:
                serialized_tx = tx.serialize_legacy().hex()

            try:
                rpc = self.bitcoin_rpc(self.rpc_url)
                tx_broadcast = rpc.sendrawtransaction(serialized_tx)
                print(f"Transaction broadcasted: {tx_broadcast}")
            except Exception as e:
                print(f"Error: {e}")
                
            await self.BitcoinInterface()


    async def GetAddressBalance(self):
        address = input("Address: ")
        rpc = self.bitcoin_rpc(self.rpc_url)

        try:
            status_thread = threading.Thread(target=self.GetScanStatus)
            status_thread.daemon = True
            status_thread.start()
            result = rpc.scantxoutset("start", [{"desc": f"addr({address})"}])
            balance = result['total_amount']
            print(f"Address balance: {balance:,} BTC")
            with open("Bitcoin/balances.json", "r") as file:
                balances = json.load(file)
            if address in balances:
                balances[address] = int(balance * Decimal(1e8))
                with open("Bitcoin/balances.json", "w") as file:
                    json.dump(balances, file)

        except Exception as e:
            print(f"Error: {e}")
        await self.BitcoinInterface()

    def GetScanStatus(self, scan_msg=""):
        rpc = self.bitcoin_rpc(self.rpc_url)
        time.sleep(1)
        while True:
            try:
                status = rpc.scantxoutset("status")['progress']
            except:
                if scan_msg:
                    print(" " * (32 + len(scan_msg)), end="\r")
                break
            print(f"Scanning UTXO set{scan_msg}... {status}%", end="\r")
            time.sleep(3)


    async def BlockchainExplorer(self):
        rpc = self.bitcoin_rpc(self.rpc_url)
        try:
            block_count = rpc.getblockcount()
            block_hash = rpc.getblockhash(block_count)
            block = rpc.getblock(block_hash, 2)
            block_stats = rpc.getblockstats(block_hash)
        except:
            print("Error getting blockchain data.")
            await self.BitcoinInterface()

        print(f"Latest block: {block_count:,}")
        print("{")
        print(f"    Hash: {block['hash']}")
        print(f"    Timestamp: {block['time']}")
        print(f"    Distance: {(divmod(time.time() - block['time'], 60)[0]):.0f} mins {(divmod(time.time() - block['time'], 60)[1]):.0f} secs")
        print(f"    Size: {block['size'] / 1_000_000} MB")
        print(f"    Difficulty: {block['difficulty']:,}")
        total_blocks = block_count + 1
        halvings = 0
        bitcoin_in_circulation = 0
        while True:
            if total_blocks >= 210_000:
                bitcoin_in_circulation += 210_000 * (50 / 2**halvings)
                halvings += 1
                total_blocks -= 210_000
            else:
                bitcoin_in_circulation += total_blocks * (50 / 2**halvings)
                break
        print(f"    Circulating bitcoin: {bitcoin_in_circulation:,}")
        txs = block['tx']
        print(f"    Txs: {len(txs):,}")
        total_value = 0
        total_fees = 0
        for tx in txs:
            for output in tx['vout']:
                total_value += output['value']
            total_fees += tx.get('fee', 0)
        print(f"    Total value: {total_value:,} BTC")
        print(f"    Total fees: {total_fees:,} BTC")
        print(f"    Median fee: {block_stats['medianfee']} sats") 
        block_reward = 50 / (2 ** (block_count // 210_000))
        print(f"    Subsidy: {block_reward} BTC")
        print(f"    Block reward: {block_reward + float(total_fees)} BTC") 
        print("}")
        await self.BitcoinInterface()

    
    def GetCredentials(self):
        with open("Bitcoin/keys.json", "r") as file:
            self.keys = file.readlines()

        cookie_path = os.path.expanduser(self.cookie_path)

        with open(cookie_path, "r") as f:
            cookie = f.read().strip()
            return (cookie.split(":")[0], cookie.split(":")[1])
        

if __name__=="__main__":
    print("Bitcoin Interface")
    print("------------------")
    asyncio.run(Bitcoin().BitcoinInterface())