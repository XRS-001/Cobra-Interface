import json
import os
import time
import Ethereum.requests as requests
import ethereum_tokeninterface
import ethereum_nameservice
import asyncio
import subprocess
import threading
import secrets

class Ethereum: 
    def __init__(self, parent_interface=None):
        from Ethereum.web3 import Web3
        self.Web3 = Web3
        self.w3 = self.Web3()
        self.parent_interface=parent_interface
        try:
            open("Ethereum/eth_rpc.txt", "r")
        except:
            self.Setup()

        helios_daemon = threading.Thread(target=self.StartHelios, name="helios_daemon")
        helios_daemon.daemon = True
        helios_daemon.start()
        time.sleep(5)
        self.accountsCreated = False
        if os.path.isfile("Ethereum/accounts.json") and os.stat("Ethereum/accounts.json").st_size > 0:
            self.accountsCreated = True
            with open("Ethereum/accounts.json", 'r') as accountsFile:
                data = json.load(accountsFile)
                self.accounts = [Ethereum.Account.from_dict(d) for d in data]


    class Account:
        def __init__(self):
            self.key = ""
            self.tokenAccounts = []
            self.address = ""

        def to_dict(self):
            return {
                "key": self.key,
                "tokenAccounts": self.tokenAccounts,
                "address": self.address
            }
        
        @classmethod
        def from_dict(cls, data):
            acc = cls()
            acc.key = data.get("key", "")
            acc.tokenAccounts = data.get("tokenAccounts", [])
            acc.address = data.get("address", "")
            return acc
        
    helios_rpc_url = "http://127.0.0.1:8545"
    uniswap_v3_router = '0xE592427A0AEce92De3Edee1F18E0157C05861564' 
    weth9_address = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2'
    accounts = []
    process = None
    def StartHelios(self):
        helios_path = r"Ethereum\helios\target\release\helios.exe"
        with open("Ethereum/eth_rpc.txt", "r") as file:
            eth_rpc_url = file.read()

        cmd = [helios_path, "ethereum", "--execution-rpc", eth_rpc_url]

        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.process.communicate()
        except Exception as e:
            print("Failed to run Helios:", e)


    def Setup(self):
        rpc_url = ""
        while rpc_url == "":
            rpc_url = input("Enter an Ethereum RPC URL (Helios will use it to trustlessly bootstrap a light client): ")
        with open("Ethereum/eth_rpc.txt", "w") as file:
            file.write(rpc_url)


    async def EthereumInterface(self):
        if not self.process:
            exit()
        print("1: My Accounts")
        print("2: Add Account")
        print("3: Sign Transaction")
        print("4: Check Address Balance")
        print("5: Token Interface")
        print("6: Ethereum Name Service")
        print("7: Blockchain Explorer")
        print("8: Check Transaction Status")
        print("9: Deploy Contract")
        choice = input()
        match choice:
            case "1":
                if self.accountsCreated:
                    await self.MyAccounts()
                else :
                    print("Create an account first.")
                    await self.EthereumInterface()
            case "2":
                await self.AddAccount()
            case "3":
                await self.SignTransaction()
            case "4":
                await self.AddressBalance()
            case "5":
                await ethereum_tokeninterface.TokenInterface(self.helios_rpc_url, self.uniswap_v3_router, self.weth9_address, accounts=self.accounts, ethereum_instance=self).TokenInterface()
            case "6":
                await ethereum_nameservice.EthereumNameService(self.Web3(self.Web3.HTTPProvider(self.helios_rpc_url)), self).ENSInterface()
            case "7":
                await self.BlockchainExplorer()
            case "8":
                await self.GetTransactionStatus()
            case "9":
                await self.DeployContract()
            case _:
                if self.parent_interface:
                    await self.parent_interface.Main()
                else:
                    self.process.kill() # type: ignore
                    exit()


    async def AddAccount(self):
        generated_account = self.w3.eth.account.create(secrets.token_bytes(32))
        account = Ethereum.Account() 
        account.key = generated_account.key.hex()[2:]

        account.address = generated_account.address

        accounts = self.accounts
        path = "Ethereum/accounts.json"

        accounts.append(account)

        with open(path, 'w') as file:
            json.dump([a.to_dict() for a in accounts], file, indent=4)

        print(f"Account added with address {account.address}.")
        await self.EthereumInterface()


    async def BlockchainExplorer(self):
        try:
            blockCount = 0
            while True:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_getBlockByNumber",
                    "params": ["latest", True],
                    "id": 1
                }

                block_data = self.Request(payload)
                if block_data is not None:
                    if int(block_data['number'], 16) == blockCount:
                        time.sleep(3)
                        continue
                    else:
                        blockCount = int(block_data['number'], 16)
                    total_value = sum(int(tx['value'], 16) for tx in block_data['transactions'])
                    total_value_eth = total_value / 1e18

                    gas = int(block_data['baseFeePerGas'], 16) / 1e9
                    gasLimit = int(block_data['gasLimit'], 16)
                    gasUsed = int(block_data['gasUsed'], 16) / gasLimit * 100
                    hash = block_data['hash']
                    timestamp = int(block_data['timestamp'], 16)
                    transaction_count = len(block_data["transactions"])
                else:
                    await self.EthereumInterface()

                print(f"Block {blockCount:,}")
                print("{")
                print(f"    Hash: {hash}")
                print(f"    Value: {total_value_eth:,.2f} Ether")
                print(f"    Transactions: {transaction_count}")
                print(f"    Gas price: {gas:.2f} Gwei")
                print(f"    Gas limit: {gasLimit:,}")
                print(f"    Gas used: {gasUsed:.2f}%")
                print(f"    Timestamp: {timestamp}")
                print("}")
                time.sleep(3)
        except KeyboardInterrupt:
            await self.EthereumInterface()


    async def GetTransactionStatus(self):
        tx_hash = input("Transaction hash: ")
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getTransactionReceipt",
            "params": [tx_hash],
            "id": 1
        }

        receipt = self.Request(payload)

        if receipt is None:
            print("Transaction pending.")
            await self.EthereumInterface()

        status_hex = receipt.get("status", "") # type: ignore
        try:
            status_int = int(status_hex, 16)
        except (ValueError, TypeError):
            status_int = None

        if status_int == 1:
            print("transaction accepted.")
        elif status_int == 0:
            print("transaction failed.")
        else:
            print("unknown status.")
        
        await self.EthereumInterface()


    async def SignTransaction(self):
        sending_address = input("Sending address: ")
        if Ethereum.CheckAddress(self, sending_address) == False: await self.EthereumInterface()
        if sending_address not in [account.address for account in self.accounts]:
            print("Address not in accounts file.")
            await self.EthereumInterface()
        else:
            for account in self.accounts:
                if account.address == sending_address:
                    private_key = account.key
        
        receiving_address = input("Receiving address: ")
        if Ethereum.CheckAddress(self, receiving_address) == False: await self.EthereumInterface()
        gas_price = int((self.w3.eth.gas_price - (self.w3.eth.max_priority_fee * 0.8)))

        try:
            value_in_wei = int(float(input("Send amount (Ether): ")) * 1e18)
        except ValueError:
            print("Not a valid number.")
            await self.EthereumInterface()
        
        nonce = self.GetNonce(sending_address)
        unsigned_tx = {
            "from": sending_address,
            "to": receiving_address,
            "value": value_in_wei,
            "gas": 21_000,
            "gasPrice": gas_price,
            "nonce": nonce,
            "data": "0x",
            "chainId": self.w3.eth.chain_id
        }
        if gas_estimate := self.EstimateGas(unsigned_tx) != None:
            print(f"Estimated fee: Ξ{(gas_estimate * gas_price) / 1e18:.18f}")
        else:
            print("Error estimating gas.")
            await self.EthereumInterface()
            
        if input("Continue? y/n: ").lower() == "n":
            await self.EthereumInterface()

        signed_tx = self.SignTX(unsigned_tx, private_key)
        if signed_tx is None:
            print("Error signing transaction.")
            await self.EthereumInterface()

        tx_hash = self.BroadcastTransaction(signed_tx)
        if tx_hash is None:
            print("Error broadcasting.")
            await self.EthereumInterface()

        print("Transaction hash:", tx_hash)
        await self.EthereumInterface()


    def GetNonce(self, address):
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getTransactionCount",
            "params": [address, "latest"],
            "id": 1
        }
        nonce = self.Request(payload)
        if nonce is None:
            nonce = 0
        else:
            nonce = int(nonce, 16)
            
        return nonce


    def SignTX(self, unsigned_tx, key):
        try:
            self.w3.eth.call(unsigned_tx) 
        except Exception as error:
            print("Simulation failure:", error)
            return None
        try:
            return self.w3.eth.account.sign_transaction(unsigned_tx, key).rawTransaction
        except:
            return None


    def BroadcastTransaction(self, signed_tx):
        try:
            return self.w3.eth.send_raw_transaction(signed_tx).hex()
        except:
            return None


    async def MyAccounts(self):
        total_balance = 0
        for account in self.accounts:
            address = account.address
            balance = self.CheckBalance(address)
            total_balance += balance
            tokenBalances = []
            for tokenAccount in account.tokenAccounts:
                value = ethereum_tokeninterface.TokenInterface(self.helios_rpc_url, self.uniswap_v3_router, self.weth9_address, accounts=self.accounts, ethereum_instance=self).CheckTokenBalance(tokenAccount, address)
                if not isinstance(value, bool):
                    if value[0] > 0:
                        tokenBalances.append(f"{value[0]:,.5f}, {value[1]}")

            if len(tokenBalances) > 0:
                ens = ethereum_nameservice.EthereumNameService(self.Web3(self.Web3.HTTPProvider(self.helios_rpc_url)), self)
                ens_name = ens.ReverseResolve(address)
                if ens_name:
                    print(f"Address: {address} ({ens_name}) Balance:")  
                else:
                    print(f"Address: {address} Balance:")  
                print("{")
                print(f"    Ξ{balance}")
                for tokenBalance in tokenBalances:
                    print(f"    {tokenBalance}")
                print("}")
            else:
                ens = ethereum_nameservice.EthereumNameService(self.Web3(self.Web3.HTTPProvider(self.helios_rpc_url)), self)
                ens_name = ens.ReverseResolve(address)
                if ens_name:
                    print(f"Address: {address} ({ens_name}) Balance: Ξ{balance}")  
                else:
                    print(f"Address: {address} Balance: Ξ{balance}")  

        if len(self.accounts) > 1:
            print(f"Total balance: Ξ{total_balance:,.5f} ({total_balance * 1000:.5f} Kwei)")

        await self.EthereumInterface()


    async def DeployContract(self):
        sending_address = input("Sending address: ").strip()
        if Ethereum.CheckAddress(self, sending_address) == False: await self.EthereumInterface()
        if sending_address not in [account.address for account in self.accounts]:
            print("Address not in accounts file.")
            await self.EthereumInterface()
        else:
            for account in self.accounts:
                if account.address == sending_address:
                    private_key = account.key

        contract_bytecode_path = input("Contract ByteCode (path): ")
        try:
            with open(contract_bytecode_path, 'r') as bytecode_file:
                bytecode = bytecode_file.read()
        except:
            print("Error retrieving bytecode.")
            await self.EthereumInterface()

        nonce = self.GetNonce(sending_address)
        gas_price = int((self.w3.eth.gas_price - (self.w3.eth.max_priority_fee * 0.8)))
        gas_check_tx = {
            "from": sending_address,
            "to": None,  
            "value": hex(0),
            "gas": hex(1_000_000),
            "gasPrice": hex(gas_price),
            "nonce": hex(nonce),
            "data": "0x"+ bytecode
        }
        if gas := self.EstimateGas(gas_check_tx) == None:
            print("Error estimating gas.")
            await self.EthereumInterface()

        unsigned_tx = {
            "from": sending_address,
            "to":  None,
            "value": hex(0),
            "gas": hex(gas),
            "gasPrice": hex(gas_price),
            "nonce": hex(nonce),
            "data": "0x"+ bytecode,
            "chainId": self.w3.eth.chain_id
        }
        print(f"Estimated fee: Ξ{(gas * gas_price) / 1e18:.18f}")
        if input("Continue? y/n: ").lower() == "n":
            await self.EthereumInterface()

        signed_tx = self.SignTX(unsigned_tx, private_key)
        if signed_tx is None:
            print("Error signing transaction.")
            await self.EthereumInterface()

        tx_hash = self.BroadcastTransaction(signed_tx)
        if tx_hash is None:
            print("Error broadcasting.")
            await self.EthereumInterface()

        print("Transaction hash:", tx_hash)
        print("Waiting for successful deployment...")
        time.sleep(120)
        print("Contract address:", self.w3.eth.wait_for_transaction_receipt(tx_hash, 300).contractAddress) # type: ignore
        await self.EthereumInterface()


    async def TotalBalance(self):
        if os.path.isfile("Ethereum/accounts.json") and os.stat("Ethereum/accounts.json").st_size > 0:
            with open("Ethereum/accounts.json", 'r') as accountsFile:
                data = json.load(accountsFile)
                accounts = [Ethereum.Account.from_dict(d) for d in data]

        total_balance = 0
        token_dict = {}
        for account in accounts:
            address = account.address
            balance = self.CheckBalance(address)
            total_balance += balance
            for tokenAccount in account.tokenAccounts:
                value = ethereum_tokeninterface.TokenInterface(self.helios_rpc_url, self.uniswap_v3_router, self.weth9_address, accounts=self.accounts, ethereum_instance=self).CheckTokenBalance(tokenAccount, address)
                if not isinstance(value, bool):
                    if value[0] > 0:
                        token_dict[value[1]] = (value[0], ethereum_tokeninterface.TokenInterface(self.helios_rpc_url, self.uniswap_v3_router, self.weth9_address, accounts=self.accounts, ethereum_instance=self).GetTokenSymbol(tokenAccount))

        token_dict['eth'] = total_balance
        return token_dict

    async def AddressBalance(self):
        address = input("Ethereum address: ")
        if Ethereum.CheckAddress(self, address) == False: await self.EthereumInterface()

        eth_balance = self.CheckBalance(address)
        
        if eth_balance is not None:
            print(f"Balance: Ξ{eth_balance:,.5f}")
        else:
            print("Account not found.")
            
        await self.EthereumInterface()
        

    def CheckBalance(self, address):
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [address, "latest"],
            "id": 1,
        }
        balance_hex = self.Request(payload)
        if  balance_hex is not None:
            balance_wei = int(balance_hex, 16)
        else:
            return 0
        balance_eth = balance_wei / 1e18
        return balance_eth


    def Request(self, payload):
        headers = { "Content-Type": "application/json" }
        try:
            response = requests.post(Ethereum.helios_rpc_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            result = response.json()
            if "result" in result:
                return result["result"]
            
        except requests.RequestException:
            return None


    def CheckAddress(self, input):
        if not self.Web3.is_checksum_address(input):
            print("Not a valid address.")
            return False


    def EstimateGas(self, tx):
        try:
            return self.w3.eth.estimate_gas(tx) # type: ignore
        except Exception as error:
            return None


if __name__=="__main__":
    print("Ethereum Interface")
    print("------------------")
    asyncio.run(Ethereum().EthereumInterface())