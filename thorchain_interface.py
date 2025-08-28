import requests
import json
import time
import os
import math
import asyncio
import threading 
from decimal import Decimal

class Thorchain:
    def __init__(self, parent_interface=None):
        import Thorchain.xchainpy2_thorchain as xchainpy2_thorchain
        import Thorchain.xchainpy2_crypto as xchainpy2_crypto
        import Thorchain.xchainpy2_utils as xchainpy2_utils
        from ecdsa import SigningKey, SECP256k1
        import ethereum_interface
        import ripple_interface
        import bitcoin_interface
        import ethereum_tokeninterface
        self.thorchain = xchainpy2_thorchain
        self.private_key = SigningKey
        self.secp256k1 = SECP256k1
        self.crypto = xchainpy2_crypto
        self.utils = xchainpy2_utils
        self.ethereum = ethereum_interface
        self.ripple = ripple_interface
        self.parent_interface = parent_interface
        self.bitcoin = bitcoin_interface
        self.token_interface = ethereum_tokeninterface

    class RunePoolPosition:
        profit = 0.0
        deposit_amount = 0.0
        units = 0.0

    accounts = []
    async def ThorchainInterface(self):
        self.accounts = []
        path = "Thorchain/accounts.json"
        if os.path.isfile(path) and os.stat(path).st_size > 0:
            with open(path, 'r') as file:
                [self.accounts.append(account.strip()) for account in file.readlines()]

        print("1: Thorchain Accounts")
        print("2: Create Thorchain Account")
        print("3: RUNE Transaction")
        print("4: Check Account Balance")
        print("5: TCY Staking")
        print("6: Rune-Pool liquidity")
        print("7: Get Swap Quote")
        print("8: Swap Crypto")
        print("9: Check Transaction Status")
        print("10: Thorchain Block Explorer")
        choice = input("")
        match choice:
            case "1":
                await self.MyThorchainAccounts()
            case "2":
                await self.CreateThorchainAccount()
            case "3":
                await self.SignThorchainTransaction(False)
            case "4":
                await self.CheckThorchainBalance()
            case "5":
                await self.TCYStake()
            case "6":
                await self.RunePool()
            case "7":
                await self.CheckPair()
            case "8":
                await self.MakeSwap()
            case "9":
                await self.CheckTransactionStatus()
            case "10":
                await self.BlockExplorer()
            case _:
                if self.parent_interface:
                    await self.parent_interface.Main()
                else:
                    exit()


    async def MyThorchainAccounts(self):
        total_balance_rune = 0; total_balance_tcy = 0; total_balance_runepool = 0
        for account in self.accounts:
            key = self.private_key.from_string(bytes.fromhex(account), curve=self.secp256k1)
            thor_address = self.crypto.utils.create_address(key.get_verifying_key().to_string("compressed"), prefix="thor") # type: ignore
            balance = await self.GetBalance(thor_address)
            if balance is not None:
                total_balance_rune += balance[0]
                print(f"{thor_address}: ")
                print("{")
                print(f"    RUNE Balance: {balance[0]}")
                if balance[2] != 0:
                    print(f"    TCY Balance: Unstaked: {balance[1]}, Staked: {balance[2]}")
                    total_balance_tcy += balance[1] + balance[2]
                if balance[3].units != 0:
                    total_balance_runepool += balance[3].units
                    print("    Rune-Pool Position:")
                    print("    {")
                    print(f"        Units: {balance[3].units}")
                    print(f"        Deposited: {balance[3].deposit_amount} RUNE")
                    print(f"        Profit: {balance[3].profit} RUNE")
                    print("   }")
                print("}")
            else:
                print("Address does not exist.")
        print(f"Total balance: {total_balance_rune:,.7f} RUNE, {total_balance_tcy:,.7f} TCY, {total_balance_runepool:,.7f} Rune-Pool Units.")
            
        await self.ThorchainInterface()

    
    async def TotalBalance(self):
        accounts = []
        path = "Thorchain/accounts.json"
        if os.path.isfile(path) and os.stat(path).st_size > 0:
            with open(path, 'r') as file:
                [accounts.append(account.strip()) for account in file.readlines()]

        total_balance_rune = 0; total_balance_tcy = 0; total_balance_runepool = 0
        for account in accounts:
            key = self.private_key.from_string(bytes.fromhex(account), curve=self.secp256k1)
            thor_address = self.crypto.utils.create_address(key.get_verifying_key().to_string("compressed"), prefix="thor") # type: ignore
            balance = await self.GetBalance(thor_address)

            if balance is not None:
                total_balance_rune += balance[0]
                if balance[2] != 0:
                    total_balance_tcy += balance[1] + balance[2]
                if balance[3].units != 0:
                    total_balance_runepool += balance[3].units

        return (total_balance_rune, total_balance_tcy, total_balance_runepool)


    async def CreateThorchainAccount(self):
        key = self.private_key.generate(curve=self.secp256k1)
        thor_address = self.crypto.utils.create_address(key.get_verifying_key().to_string("compressed"), prefix="thor") # type: ignore
        print(f"Generated Thorchain address: {thor_address}")

        accounts = self.accounts
        accounts.append(key.to_string().hex())

        path = "Thorchain/accounts.json"
        with open(path, 'w') as file:
            file.writelines(line + "\n" for line in accounts)

        await self.ThorchainInterface()


    def CheckAccountsForAddress(self, address):
        for account in self.accounts:
            private_key_bytes = bytes.fromhex(account)
            key = self.private_key.from_string(private_key_bytes, curve=self.secp256k1)
            thor_address = self.crypto.utils.create_address(key.get_verifying_key().to_string("compressed"), prefix="thor") # type: ignore
            if thor_address == address:
                return private_key_bytes
        return None


    async def SignThorchainTransaction(self, is_swap):
        sending_address = input("Sending address: ")
        private_key = self.CheckAccountsForAddress(sending_address)
        if not private_key:
            print("Account not in accounts list.")
            await self.ThorchainInterface()

        client = self.thorchain.THORChainClient(private_key=private_key)
        if not is_swap:
            await self.Transaction(client)
        else:
            await self.ThorSwap(client, is_swap)
        await self.ThorchainInterface()


    async def Transaction(self, client):
        receiving_address = input("Receiving address: ")
        try:
            amount = int(float(input("Amount: ")) * 1e8)
        except:
            print("Not a valid number.")
            return
        
        crypto_amount = self.utils.CryptoAmount(self.utils.Amount.from_base(amount, decimals=8), self.utils.asset.AssetRUNE) # type: ignore
        tx_hash = await client.transfer(what=crypto_amount, recipient=receiving_address) # type: ignore
        print(f"Transaction broadcasted: {tx_hash}")
        await client.close()


    async def TCYStake(self):
        stake_action = input("Would you like to stake or unstake?: ")
        if stake_action.lower() not in ["stake", "unstake"]:
            print("Not a valid action.")
            await self.ThorchainInterface()

        if stake_action == "stake":
            staking_address = input("Staking address: ")
            private_key = self.CheckAccountsForAddress(staking_address)
            if not private_key:
                print("Address not in accounts list.")
                await self.ThorchainInterface()

            tcy_balance = (await self.GetBalance(staking_address))[1] # type: ignore
            if tcy_balance == 0: 
                print("No TCY in account.")
                await self.ThorchainInterface()

            try:
                stake_percentage = float(input("% to stake: ")) / 100
            except ValueError:
                print("Not a valid number")
                await self.ThorchainInterface()

            client = self.thorchain.THORChainClient(private_key=private_key)
            crypto_amount = self.utils.CryptoAmount(self.utils.Amount.from_base((tcy_balance * 1e8) * stake_percentage, decimals=0), self.utils.asset.AssetTCY) # type: ignore
            tx_hash = await client.deposit(what=crypto_amount, memo="TCY+") # type: ignore
            print(f"Stake broadcasted: {tx_hash}")
            await self.ThorchainInterface()
        else:
            staked_address = input("Staked address: ")
            private_key = self.CheckAccountsForAddress(staked_address)
            if not private_key:
                print("Address not in accounts list.")
                await self.ThorchainInterface()

            tcy_staked = await self.GetBalance(staked_address) 
            if tcy_staked is None or tcy_staked[2] == 0: # type: ignore
                print("No TCY staked.")
                await self.ThorchainInterface()

            try:
                basis_points_unstake = float(input("% to unstake: ")) * 100
            except ValueError:
                print("Not a valid number")
                await self.ThorchainInterface()

            client = self.thorchain.THORChainClient(private_key=private_key)
            tx_hash = await client.deposit(what=0, memo=f"TCY-:{int(basis_points_unstake)}")
            print(f"Unstake broadcasted: {tx_hash}")
            await self.ThorchainInterface()
        await client.close()


    async def RunePool(self):
        pool_action = input("Would you like to deposit or withdraw liquidity?: ")
        if pool_action.lower() not in ["deposit", "withdraw"]:
            print("Not a valid action.")
            await self.ThorchainInterface()

        liquidity_address = input("Address: ")
        private_key = self.CheckAccountsForAddress(liquidity_address)
        if not private_key:
            print("Address not in accounts list.")
            await self.ThorchainInterface()

        if pool_action == "deposit":
            try:
                deposit_amount = float(input("Amount to deposit: "))
            except ValueError:
                print("Not a valid number")
                await self.ThorchainInterface()

            client = self.thorchain.THORChainClient(private_key=private_key)
            crypto_amount = self.utils.CryptoAmount(self.utils.amount.Amount(deposit_amount * 1e8), self.utils.asset.AssetRUNE) # type: ignore
            tx_hash = await client.deposit(what=crypto_amount, memo="POOL+") # type: ignore
            print(f"Deposit broadcasted: {tx_hash}")
        else:
            try:
                basis_points_withdraw = int(float(input("% to withdraw: ")) * 100)
            except ValueError:
                print("Not a valid number")
                await self.ThorchainInterface()

            client = self.thorchain.THORChainClient(private_key=private_key)
            tx_hash = await client.deposit(what=0, memo=f"POOL-:{basis_points_withdraw}")
            print(f"Withdraw broadcasted: {tx_hash}")
        await client.close()
        await self.ThorchainInterface()


    async def ThorSwap(self, client, swap_asset):
        swap_to = input("Swap to: ")
        if swap_to not in ["BTC", "ETH", "XRP", "RUNE", "TCY", "USDC"]:
            print("Not a swappable asset.")
            return

        try:
            amount = int(float(input(f"Swap amount ({swap_asset}): ")) * 1e8)
        except ValueError:
            print("Not a valid number.")
            return

        receiving_address = input(f"Receiving address ({swap_to}): ")
        request = requests.get(f"https://thornode.ninerealms.com/thorchain/quote/swap?from_asset=THOR.{swap_asset}&to_asset={self.ThorchainNotation(swap_to)}&amount={amount}&destination={receiving_address}&streaming_interval=1&streaming_quantity=10")
        data = json.loads(request.text)
        if "code" in data:
            print("API error:", data["message"])
            return
        try:
            print(f"Expected output: {float(data['expected_amount_out']) / 1e8:.8f}")
        except:
            print("Error fetching swap data.")
            return
        
        if 'total_swap_seconds' in data:
            swap_time = int(data['total_swap_seconds'])
            print("Expected time: {} mins, {} seconds ".format(*divmod(swap_time, 60)))
        memo = data['memo']
        if 'fees' in data:
            print(f"Fees: {float(data['fees']['total']) / 1e8:.8f} ({swap_to})")
        continue_check = input("Proceed with swap? (y/n): ").lower() == 'y'
        if continue_check:
            crypto_amount = self.utils.CryptoAmount(self.utils.Amount.from_base(amount, decimals=8), self.utils.asset.AssetRUNE if swap_asset == "RUNE" else self.utils.asset.AssetTCY) # type: ignore
            tx_hash = await client.deposit(what=crypto_amount, memo=memo)
            print(f"Swap submitted: {tx_hash}")
            await client.close()
        else:
            return


    async def CheckThorchainBalance(self):
        address = input("Address: ")
        request = requests.get(f"https://thornode.ninerealms.com/bank/balances/{address}")
        data = json.loads(request.text)
        if "code" in data:
            print("API error:", data["message"])
            await self.ThorchainInterface()

        balance = await self.GetBalance(address)
        if balance:
            print(f"RUNE Balance: {balance[0]}")
            if balance[2] != 0:
                print(f"TCY Balance: Unstaked: {balance[1]}, Staked: {balance[2]}")
                
            if balance[3].units != 0:
                print(f"Rune-Pool Position:")
                print("{")
                print(f"    Units: {balance[3].units}")
                print(f"    Deposited: {balance[3].deposit_amount} RUNE")
                print(f"    Profit: {balance[3].profit} RUNE")
                print("}")
        else:
            print("Account does not exist.")
        await self.ThorchainInterface()


    async def GetBalance(self, address):
        request = requests.get(f"https://thornode.ninerealms.com/bank/balances/{address}")
        data = json.loads(request.text)
        if "code" in data:
            print("API error:", data["message"])
            return None
        elif data['result']:
            request_stake = requests.get(f"https://thornode.ninerealms.com/thorchain/tcy_staker/{address}")
            data_stake = json.loads(request_stake.text)
            staked_tcy = 0
            if "amount" in data_stake:
                staked_tcy = float(data_stake['amount']) / 1e8

            request_runepool = requests.get(f"https://thornode.ninerealms.com/thorchain/rune_provider/{address}")
            data_runepool = json.loads(request_runepool.text)
            runepool_position = self.RunePoolPosition()
            if "units" in data_runepool:
                runepool_position.deposit_amount = float(data_runepool['deposit_amount']) / 1e8
                runepool_position.units = float(data_runepool['units']) / 1e8
                runepool_position.profit = float(data_runepool['pnl']) / 1e8

            return (float(data['result'][0]['amount']) / 1e8, float(data['result'][1]['amount']) / 1e8 if len(data['result']) > 1 else 0, staked_tcy, runepool_position)
        else:
            return None


    async def CheckTransactionStatus(self):
        tx_hash = input("Transaction hash: ")[2:]
        request = requests.get(f"https://thornode.ninerealms.com/thorchain/tx/status/{tx_hash}")
        data = json.loads(request.text)
        if "code" in data:
            print("API error:", data["message"])
            await self.ThorchainInterface()
        elif 'inbound_finalised' in data['stages']:
            print("Transaction accepted." if data['stages']['inbound_finalised']['completed'] else "Transaction pending.")
        elif 'swap_status' in data['stages']:
            print("Swap pending." if data['stages']['swap_status']['pending'] else "Swap completed.")
        else:
            print("Transaction not found.")
        await self.ThorchainInterface()


    async def BlockExplorer(self):
        try:
            block_height = 0
            while True:
                request = requests.get(f"https://thornode.ninerealms.com/thorchain/block")
                data = json.loads(request.text)
                if "id" in data:
                    if data["header"]['height'] == block_height:
                        time.sleep(0.1)
                        continue
                    else:
                        block_height = data["header"]['height']            
                        print(f"Block {block_height:,}:")
                        print("{")
                        print(f"    Hash: {data['id']['hash']}")
                        print(f"    Transactions: {len(data['txs'])}")
                        total_value = 0
                        fees = 0
                        swap_count = 0
                        for tx in data['txs']:
                            for event in tx['result']['events']:
                                if "amount" in event:
                                    if "rune" in event["amount"]:
                                        total_value += float(event['amount'].replace("rune", ""))
                                if "gas_used" in tx['result']:
                                    fees += float(tx['result']["gas_used"])
                                if "type" in event:
                                    if event["type"] == "coin_received":
                                        swap_count += 1
                                        
                        print(f"    Value: {total_value / 1e8:,.2f} RUNE")
                        print(f"    Fees: {fees / 1e8:,} RUNE")
                        print(f"    Swaps: {swap_count}")
                        print("}")
                        time.sleep(0.1)
        except KeyboardInterrupt:
            await self.ThorchainInterface()


    async def MakeSwap(self):
        print("Available swaps:")
        print("BTC ETH XRP RUNE TCY USDC")
        swap_from = input("Swap from: ")
        if swap_from not in ["BTC", "ETH", "XRP", "RUNE", "TCY", "USDC"]:
            print("Not a swappable asset.")
            await self.ThorchainInterface()

        match swap_from:
            case "ETH":
                await self.EtherSwap()
            case "XRP":
                await self.XRPSwap()
            case "RUNE" | "TCY":
                await self.SignThorchainTransaction(swap_from)
            case "BTC":
                await self.BTCSwap()
            case "USDC":
                await self.ERC_Swap(swap_from)
            
        await self.ThorchainInterface()


    def IsHalted(self, entry):
        if entry["halted"]:
            return True
        else:
            return False
        
    
    async def BTCSwap(self):
        response = requests.get("https://thornode.ninerealms.com/thorchain/inbound_addresses")
        response.raise_for_status()
        inbounds = response.json()
        entry = next(item for item in inbounds if item["chain"] == "BTC")
        if self.IsHalted(entry):
            print("BTC vault is halted.")
            return
        
        bitcoin = self.bitcoin.Bitcoin()
        sending_address = input("Sending address: ")
        address_in_file = False
        with open('Bitcoin/keys.json', 'r') as file:
            keys = file.readlines()
        for key in keys:
            if key[:6] == "segwit":
                if bitcoin.key.PrivateKey(int(key[6:], 16)).point.address(segwit=True) == sending_address:
                    address_in_file = True
                    signing_key = bitcoin.key.PrivateKey(int(key[6:], 16))
                    sender_segwit = True
                    break
            else:
                if bitcoin.key.PrivateKey(int(key, 16)).point.address() == sending_address:
                    address_in_file = True
                    signing_key = bitcoin.key.PrivateKey(int(key, 16))
                    sender_segwit = False
                    break

        if not address_in_file:
            print("Address not in keys file.")
            return
        
        swap_to = input("Asset to swap to: ")
        if swap_to not in ["ETH", "XRP", "RUNE", "TCY", "USDC"]:
            print("Not a swappable asset.")
            return
        
        try:
            amount = int(input("Amount (sats): "))
        except:
            print("Not a valid amount.")
            return
        
        try:
            fee = int(input("Fee (sats): "))
        except:
            print("Not a valid amount.")
            return

        rpc = bitcoin.bitcoin_rpc(bitcoin.rpc_url)
        try:
            status_thread = threading.Thread(target=bitcoin.GetScanStatus)
            status_thread.daemon = True
            status_thread.start()
            result = rpc.scantxoutset("start", [{"desc": f"addr({sending_address})"}])
        except Exception as e:
            print(f"Error: {e}")
            return

        balance_sats = int(float(result['total_amount']) * 1e8)
        if amount + fee > balance_sats: # type: ignore
            print("Account balance too low.")
            return
        
        receiving_address = input(f"Receiving address ({swap_to}): ")

        request = requests.get(f"https://thornode.ninerealms.com/thorchain/quote/swap?from_asset=BTC.BTC&to_asset={self.ThorchainNotation(swap_to)}&amount={amount}&destination={receiving_address}&streaming_interval=1&streaming_quantity=10")
        data = json.loads(request.text)
        if "code" in data:
            print("API error:", data["message"])
            return
        try:
            print(f"Expected output: {float(data['expected_amount_out']) / 1e8:.8f}")
        except:
            print("Error fetching swap data.")
            return
        
        if 'total_swap_seconds' in data:
            swap_time = int(data['total_swap_seconds'])
            print("Expected time: {} mins, {} seconds ".format(*divmod(swap_time, 60)))

        inbound_address = data['inbound_address']
        if inbound_address [:2] != "bc":
            return
        
        print(f"Inbound address: {inbound_address}")
        memo = data['memo']
        print(memo)
        if 'fees' in data:
            print(f"Fees: {float(data['fees']['total']) / 1e8:.8f} {swap_to}")
        continue_check = input("Proceed with swap? (y/n): ").lower() == 'y'
        if not continue_check:
            return
        
        tx_ins = []
        input_value = 0
        for utxo in result['unspents']:
            if sender_segwit:
                tx_ins.append(bitcoin.tx.TxIn(bytes.fromhex(utxo['txid']), utxo['vout'], script_pubkey=bitcoin.script.p2wpkh_script(bitcoin.key.decode_bech32("bc", sending_address)[1]), amount=int(float(utxo['amount']) * 1e8)))
            else:
                tx_ins.append(bitcoin.tx.TxIn(bytes.fromhex(utxo['txid']), utxo['vout'], script_pubkey=bitcoin.script.p2pkh_script(bitcoin.key.decode_base58(sending_address)), amount=int(float(utxo['amount']) * 1e8)))
            input_value += int(utxo['amount'] * Decimal(1e8))
            if input_value >= amount + fee: # type: ignore
                break
        
        if input_value - amount - fee != 0:
            if sender_segwit:
                change_h160 = bitcoin.key.decode_bech32("bc", sending_address)[1]
                change_script = bitcoin.script.p2wpkh_script(change_h160)
            else:
                change_h160 = bitcoin.key.decode_base58(sending_address)
                change_script = bitcoin.script.p2pkh_script(change_h160)
            change_output = bitcoin.tx.TxOut(input_value - amount - fee, change_script)
        else:
            change_output = False

        out_160 = bitcoin.key.decode_bech32("bc", inbound_address)[1]
        out_scipt = bitcoin.script.p2wpkh_script(out_160)
        tx_out = bitcoin.tx.TxOut(amount, out_scipt)

        memo_script = bitcoin.script.Script([0x6A, bytes(memo, encoding='utf-8')])
        memo_out = bitcoin.tx.TxOut(0, memo_script)
        tx = bitcoin.tx.Tx(1, tx_ins, [change_output, tx_out, memo_out] if change_output else [tx_out, memo_out], 0)

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
                sig = der + bitcoin.tx.SIGHASH_ALL.to_bytes(1, 'big')
                sec = signing_key.point.sec()
                script_sig = bitcoin.script.Script([sig, sec])
                tx.tx_ins[i].script_sig = script_sig

        if sender_segwit:
            serialized_tx = tx.serialize_segwit().hex()
        else:
            serialized_tx = tx.serialize_legacy().hex()

        try:
            rpc = bitcoin.bitcoin_rpc(bitcoin.rpc_url)
            tx_broadcast = rpc.sendrawtransaction(serialized_tx)
            print(f"Transaction broadcasted: {tx_broadcast}")
        except Exception as e:
            print(f"Error: {e}")


    async def XRPSwap(self):
        response = requests.get("https://thornode.ninerealms.com/thorchain/inbound_addresses")
        response.raise_for_status()
        inbounds = response.json()
        entry = next(item for item in inbounds if item["chain"] == "XRP")
        if self.IsHalted(entry):
            print("XRP vault is halted.")
            return
        
        ripple = self.ripple.Ripple()
        if not os.path.isfile("Ripple/accounts.json") or os.stat("Ripple/accounts.json").st_size == 0:
            print("Create account first.")
            return
        
        with open("Ripple/accounts.json", 'r') as file:
            data = json.load(file)
            for d in data:
                ripple.accounts[ripple.Account.from_dict(d).address] = ripple.Account.from_dict(d)
        
        sender = input("Sending account: ")

        if not ripple.xrpl.core.addresscodec.is_valid_classic_address(sender):
            print("Invalid address.")
            return

        elif not await ripple.async_xrpl.account.does_account_exist(sender, ripple.client):
            print("Account does not exist.")
            return

        elif sender not in ripple.accounts:
            print("Account not in accounts list.")
            return
        
        swap_to = input("Asset to swap to: ")
        if swap_to not in ["BTC", "ETH", "RUNE", "TCY", "USDC"]:
            print("Not a swappable asset.")
            return
        
        try:
            amount = float(input("Amount: "))
        except ValueError:
            print("Not a number.")
            return
        receiving_address = input(f"Receiving address ({swap_to}): ")

        request = requests.get(f"https://thornode.ninerealms.com/thorchain/quote/swap?from_asset=XRP.XRP&to_asset={self.ThorchainNotation(swap_to)}&amount={int(amount * 1e8)}&destination={receiving_address}&streaming_interval=1&streaming_quantity=10")
        data = json.loads(request.text)
        if "code" in data:
            print("API error:", data["message"])
            return
        try:
            print(f"Expected output: {float(data['expected_amount_out']) / 1e8:.8f}")
        except:
            print("Error fetching swap data.")
            return
        
        if 'total_swap_seconds' in data:
            swap_time = int(data['total_swap_seconds'])
            print("Expected time: {} mins, {} seconds ".format(*divmod(swap_time, 60)))

        inbound_address = data['inbound_address']
        print(f"Inbound address: {inbound_address}")
        memo = data['memo']
        if 'fees' in data:
            print(f"Fees: {float(data['fees']['total']) / 1e8:.8f} {swap_to}")
        continue_check = input("Proceed with swap? (y/n): ").lower() == 'y'
        if continue_check:
            tx = ripple.xrpl.models.transactions.Payment(
                account=sender,
                amount=ripple.xrpl.utils.xrp_to_drops(amount),
                destination=inbound_address,
                memos=[ripple.xrpl.models.Memo(memo_data=memo.encode("utf-8").hex())]
            )
            wallet = ripple.xrpl.wallet.Wallet(ripple.accounts[sender].publicKey, ripple.accounts[sender].privateKey)
            try:
                await ripple.async_xrpl.transaction.submit_and_wait(tx, ripple.client, wallet)
                print("Swap successful.")
            except Exception as error:
                print("Swap failed.")
                print(error)


    async def EtherSwap(self):
        response = requests.get("https://thornode.ninerealms.com/thorchain/inbound_addresses")
        response.raise_for_status()
        inbounds = response.json()
        entry = next(item for item in inbounds if item["chain"] == "ETH")
        if self.IsHalted(entry):
            print("Ethereum vault is halted.")
            return

        ethereum = self.ethereum.Ethereum()
        if not ethereum.process:
            print("Error connecting to Ethereum network.")
            return
        try:
            amount = float(input("Swap amount (Ether): "))
        except ValueError:
            print("Not a valid number.")
            return

        swap_to = input("Asset to swap to: ")
        if swap_to not in ["BTC", "XRP", "RUNE", "TCY", "USDC"]:
            print("Not a swappable asset.")
            return
        
        receiving_address = input(f"Receiving address ({swap_to}): ")

        request = requests.get(f"https://thornode.ninerealms.com/thorchain/quote/swap?from_asset=ETH.ETH&to_asset={self.ThorchainNotation(swap_to)}&amount={int(amount * 1e8)}&destination={receiving_address}&streaming_interval=1&streaming_quantity=10")
        data = json.loads(request.text)
        if "code" in data:
            print("API error:", data["message"])
            return
        try:
            inbound_address = ethereum.w3.to_checksum_address(data['inbound_address'])
        except:
            print("Error fetching swap data.")
            return

        print(f"Inbound address: {inbound_address}")

        print(f"Expected output: {float(data['expected_amount_out']) / 1e8:.8f}")

        if 'total_swap_seconds' in data:
            swap_time = int(data['total_swap_seconds'])
            print("Expected time: {} mins, {} seconds ".format(*divmod(swap_time, 60)))

        memo = data['memo']
        continue_check = input("Proceed with swap? (y/n): ").lower() == 'y'
        if continue_check:

            sending_address = input("Swapping address: ")
            for account in ethereum.accounts:
                print(account.address)
            if sending_address not in [account.address for account in ethereum.accounts]:
                print("Address not in accounts file.")
                return
            else:
                for account in ethereum.accounts:
                    if account.address == sending_address:
                        private_key = account.key

            gas_price = int((ethereum.w3.eth.gas_price - (ethereum.w3.eth.max_priority_fee * 0.9)))
            
            nonce = ethereum.GetNonce(sending_address)
            tx = {
                'from':   sending_address,
                'to':     inbound_address,
                'value':  hex(int(amount * 10**18)),
                'gas':    hex(40_000),
                'gasPrice': hex(gas_price),  
                'nonce': hex(nonce),
                'data':   "0x" + memo.encode("utf-8").hex(),
                "chainId": ethereum.w3.eth.chain_id
            }
            if 'fees' in data:
                print(f"Fees: {float(data['fees']['total']) / 1e8:.8f} {swap_to}")
            if input("Continue? y/n: ").lower() == "n":
                return
            
            signed_tx = ethereum.SignTX(tx, private_key)
            if signed_tx is None:
                return
            tx_hash = ethereum.BroadcastTransaction(signed_tx)
            if tx_hash is None:
                print("Error broadcasting.")
                return
            print(f"Swap submitted. Transaction hash: {tx_hash}")
            ethereum.process.kill() 
            return
        else:
            return
        
        
    async def ERC_Swap(self, token):
        token_addresses = {"USDC": ("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", 6)}
        response = requests.get("https://thornode.ninerealms.com/thorchain/inbound_addresses")
        response.raise_for_status()
        inbounds = response.json()
        entry = next(item for item in inbounds if item["chain"] == "ETH")
        if self.IsHalted(entry):
            print("Ethereum vault is halted.")
            return

        ethereum = self.ethereum.Ethereum()
        if not ethereum.process:
            print("Error connecting to Ethereum network.")
            return
        try:
            amount = float(input(f"Swap amount ({token}): "))
        except ValueError:
            print("Not a valid number.")
            return

        swap_to = input("Asset to swap to: ")
        if swap_to not in ["BTC", "ETH", "XRP", "RUNE", "TCY"]:
            print("Not a swappable asset.")
            return
        
        receiving_address = input(f"Receiving address ({swap_to}): ")

        request = requests.get(f"https://thornode.ninerealms.com/thorchain/quote/swap?from_asset={self.ThorchainNotation(token)}&to_asset={self.ThorchainNotation(swap_to)}&amount={int(amount * 1e8)}&destination={receiving_address}&streaming_interval=1&streaming_quantity=10")
        data = json.loads(request.text)
        if "code" in data:
            print("API error:", data["message"])
            return
        try:
            inbound_address = ethereum.w3.to_checksum_address(data['inbound_address'])
            router = data['router']
        except:
            print("Error fetching swap data.")
            return

        print(f"Inbound address: {inbound_address}")
        print(f"Expected output: {float(data['expected_amount_out']) / 1e8:.8f}")

        if 'total_swap_seconds' in data:
            swap_time = int(data['total_swap_seconds'])
            print("Expected time: {} mins, {} seconds ".format(*divmod(swap_time, 60)))

        memo = data['memo']
        continue_check = input("Proceed with swap? (y/n): ").lower() == 'y'
        if continue_check:
            sending_address = input("Swapping address: ")
            if sending_address not in [account.address for account in ethereum.accounts]:
                print("Address not in accounts file.")
                return
            else:
                for account in ethereum.accounts:
                    if account.address == sending_address:
                        private_key = account.key
            if token_addresses[token][0] not in account.tokenAccounts:
                print(f"Account has no {token} balance.")
                return
            
            if 'fees' in data:
                print(f"Fees: {float(data['fees']['total']) / 1e8:.8f} {swap_to}")
            if input("Continue? y/n: ").lower() == "n":
                return
            
            token_contract = ethereum.w3.eth.contract(address=token_addresses[token][0], abi=[{ # type: ignore
                "constant": False,
                "inputs": [
                    {"name": "_spender", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            }])

            amount_to_approve = int(amount * (10 ** token_addresses[token][1]))
            approve_calldata = token_contract.encodeABI(fn_name="approve", args=[router, amount_to_approve])
            
            gas_price = int((ethereum.w3.eth.gas_price - (ethereum.w3.eth.max_priority_fee * 0.9)))
            nonce = ethereum.GetNonce(sending_address)
            approve_tx = {
                "from": sending_address,
                "to": token_addresses[token][0],
                "value": hex(0),
                "gas": hex(100_000),
                "gasPrice": hex(gas_price),
                "nonce": hex(nonce),
                "data": approve_calldata,
                "chainId": ethereum.w3.eth.chain_id
            }
            token_interface = self.token_interface.TokenInterface(ethereum.helios_rpc_url, ethereum.uniswap_v3_router, ethereum.weth9_address, accounts=self.accounts, ethereum_instance=ethereum)
            approve = token_interface.ApprovalTransaction(approve_tx, private_key)
            if approve == False:
                print(f"Error approving {token} transfer.")
                return
                        
            thor_contract = ethereum.w3.eth.contract(address=router, abi=[
            {
                "inputs": [
                    {"internalType": "address payable", "name": "vault", "type": "address"},
                    {"internalType": "address", "name": "asset", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"internalType": "string", "name": "memo", "type": "string"},
                    {"internalType": "uint256", "name": "expiration", "type": "uint256"}
                ],
                "name": "depositWithExpiry",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function"
            }])
            swap_calldata = thor_contract.encodeABI(fn_name="depositWithExpiry", args=[inbound_address, token_addresses[token][0], amount_to_approve, memo, int(time.time() + 3600)])
            tx = {
                'from':   sending_address,
                'to':     router,
                'value':  hex(0),
                'gas':    hex(400_000),
                'gasPrice': hex(gas_price),  
                'nonce': hex(nonce + 1),
                'data':   swap_calldata,
                "chainId": ethereum.w3.eth.chain_id
            }
            signed_tx = ethereum.SignTX(tx, private_key)
            if signed_tx is None:
                return
            tx_hash = ethereum.BroadcastTransaction(signed_tx)
            if tx_hash is None:
                print("Error broadcasting.")
                return
            print(f"Swap submitted. Transaction hash: {tx_hash}")
            ethereum.process.kill() 
            return
        else:
            return
        

    async def CheckPair(self):
        print("Available swaps:")
        print("BTC ETH XRP RUNE TCY USDC")
        swap_from = input("Swap from: ")
        if swap_from not in ["BTC", "ETH", "XRP", "RUNE", "TCY", "USDC"]:
            print("Not a swappable asset.")
            await self.ThorchainInterface()

        swap_to = input("Swap to: ")
        if swap_to not in ["BTC", "ETH", "XRP", "RUNE", "TCY", "USDC"]:
            print("Not a swappable asset.")
            await self.ThorchainInterface()

        match swap_to:
            case "BTC":
                address = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
                fee_decimals = 1e8
            case "ETH":
                address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
                fee_decimals = 4.761133e9
            case "XRP":
                fee_decimals = 1e8
                address = "r3KczxSzs7nwDsd1qioSgxErNPJc8yPPu1"
            case "RUNE" | "TCY":
                fee_decimals = 1e8
                address = "thor1myhtcujj5r4lwlm2hf0a4x6hk6k8nvrs7lr866"

                
        request_string = (
            f"https://thornode.ninerealms.com/thorchain/quote/swap?"
            f"from_asset={self.ThorchainNotation(swap_from)}&"
            f"to_asset={self.ThorchainNotation(swap_to)}&"
            f"amount={100000000 if swap_from in ['BTC', 'ETH'] else 1000000000}&"
            f"destination={address}&streaming_interval=1&streaming_quantity=10")
        
        request = requests.get(request_string)
        data = json.loads(request.text)
        if "code" in data:
            print("API error:", data["message"])
            await self.ThorchainInterface()

        print(f"{1 if swap_from in ['BTC', 'ETH'] else 10} {swap_from} -> {swap_to} {float(data['expected_amount_out']) / 1e8:,}")
        if 'recommended_min_amount_in' in data:
            print(f"Minimum swap: {float(data['recommended_min_amount_in']) / 1e8:.8f} {swap_from}")
        if 'fees' in data:
            print(f"Fees: {float(data['fees']['total']) / fee_decimals:.{int(math.log10(fee_decimals))}f} {swap_to}")
        if 'total_swap_seconds' in data:
            print("Time: {} mins, {} seconds".format(*divmod(int(data['total_swap_seconds']), 60)))
            
        await self.ThorchainInterface()


    def ThorchainNotation(self, text):
        match text:
            case "RUNE" | "TCY":
                return f"THOR.{text}"
            case "USDC":
                return f"ETH.{text}"
            case _:
                return f"{text}.{text}"

if __name__ == "__main__":
    print("Thorchain Interface")
    print("--------------------")
    asyncio.run(Thorchain().ThorchainInterface())