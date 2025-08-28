from Ethereum.ens import ns as name_service
import secrets
import time

resolver_abi = [
  {
    "constant": False,
    "inputs": [
      { "name": "node", "type": "bytes32" },
      { "name": "a",    "type": "address" }
    ],
    "name": "setAddr",
    "outputs": [],
    "payable": False,
    "stateMutability": "nonpayable",
    "type": "function"
  }
]

ens_abi = [
    {
        "inputs": [
            {"internalType": "string", "name": "name", "type": "string"},
            {"internalType": "uint256", "name": "duration", "type": "uint256"}
        ],
        "name": "rentPrice",
        "outputs": [
            {"internalType": "uint256", "name": "base", "type": "uint256"},
            {"internalType": "uint256", "name": "premium", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "name", "type": "string"}
        ],
        "name": "available",
        "outputs": [
            {"internalType": "bool", "name": "", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "name", "type": "string"},
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "uint256", "name": "duration", "type": "uint256"},
            {"internalType": "bytes32", "name": "secret", "type": "bytes32"},
            {"internalType": "address", "name": "resolver", "type": "address"},
            {"internalType": "bytes[]", "name": "data", "type": "bytes[]"},
            {"internalType": "bool", "name": "reverseRecord", "type": "bool"},
            {"internalType": "uint16", "name": "ownerControlledFuses", "type": "uint16"}
        ],
        "name": "makeCommitment",
        "outputs": [
            {"internalType": "bytes32", "name": "", "type": "bytes32"}
        ],
        "stateMutability": "pure",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "commitment", "type": "bytes32"}
        ],
        "name": "commit",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "name", "type": "string"},
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "uint256", "name": "duration", "type": "uint256"},
            {"internalType": "bytes32", "name": "secret", "type": "bytes32"},
            {"internalType": "address", "name": "resolver", "type": "address"},
            {"internalType": "bytes[]", "name": "data", "type": "bytes[]"},
            {"internalType": "bool", "name": "reverseRecord", "type": "bool"},
            {"internalType": "uint16", "name": "ownerControlledFuses", "type": "uint16"}
        ],
        "name": "register",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {
            "internalType": "string",
            "name": "name",
            "type": "string"
            },
            {
            "internalType": "uint256",
            "name": "duration",
            "type": "uint256"
            }
        ],
        "name": "renew",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]

class EthereumNameService:
    def __init__(self, web3, ethereum_instance):
        self.web3 = web3
        self.resolver_address = web3.to_checksum_address("0x231b0Ee14048e9dCcD1d247744d114a4EB5E8E63")
        self.ens_address = web3.to_checksum_address("0x253553366da8546fc250f225fe3d25d0c782303b")
        self.ens = name_service.from_web3(web3)
        self.ethereum = ethereum_instance


    async def ENSInterface(self):
        print("1: Resolve Name")
        print("2: Resolve Address")
        print("3: Purchase Name")
        print("4: Renew Name")
        choice = input("")
        match choice:
            case "1":
                await self.ResolveName()    
            case "2":
                await self.ResolveAddress()    
            case "3":
                await self.PurchaseName()
            case "4":
                await self.RenewName()
            case _:
                await self.ethereum.EthereumInterface()


    async def ResolveName(self):
        name_to_resolve = input("Name to resolve: " )
        print(f"Address: {self.ens.address(name_to_resolve)}")
        await self.ENSInterface()


    async def ResolveAddress(self):
        address_to_resolve = input("Address to resolve: " )
        print(f"Name: {self.ReverseResolve(address_to_resolve)}")
        await self.ENSInterface()

    
    def ReverseResolve(self, address):
        return self.ens.name(self.web3.to_checksum_address(address))


    async def PurchaseName(self):
        ens_contract = self.web3.eth.contract(address=self.ens_address, abi=ens_abi)

        name = input("Name to buy: ").lower()
        available = ens_contract.functions.available(name.replace(".eth", "")).call()
        if not available:
            print("Name not available.")
            await self.ENSInterface()
        try:
            duration = int(input("Time to buy (days): ")) * 24 * 3600
        except:
            print("Not a valid number.")
            await self.ENSInterface()

        base_price, premium = ens_contract.functions.rentPrice(name.replace(".eth", ""), duration).call()
        total_price = base_price + premium
        print(f"Total to pay (ETH): {total_price / 1e18:.18f}")

        paying_address = input("Paying address: ")
        if self.ethereum.CheckAddress(paying_address) == False: await self.ENSInterface()
        if paying_address not in [account.address for account in self.ethereum.accounts]:
            print("Address not in accounts file.")
            await self.ENSInterface()
        else:
            for account in self.ethereum.accounts:
                if account.address == paying_address:
                    private_key = account.key

        resolving_address = input("Resolving address: ")
        if self.ethereum.CheckAddress(resolving_address) == False: await self.ENSInterface()

        resolver_contract = self.web3.eth.contract(
            address=self.resolver_address,
            abi=resolver_abi
        )
        node_hash = self.web3.ens.namehash(name)
        call_data_resolver = resolver_contract.encodeABI(
            fn_name="setAddr",
            args=[node_hash, resolving_address]
        )
        data_array = [bytes.fromhex(call_data_resolver[2:])]
        secret = self.web3.keccak(secrets.token_bytes(32))
        commitment_hash = ens_contract.functions.makeCommitment(name.replace(".eth", ""), paying_address, duration, secret, self.resolver_address, data_array, True, 0).call()

        gas_price = int((self.web3.eth.gas_price - (self.web3.eth.max_priority_fee * 0.9)))

        nonce = self.ethereum.GetNonce(paying_address)
        call_data_commit = ens_contract.encodeABI(
            fn_name="commit",
            args=[commitment_hash]
        )
        tx_commit = {
            "from": paying_address,
            "to": self.ens_address,
            "value": hex(0),
            "nonce": hex(nonce),
            "gas": hex(100_000),
            "data": call_data_commit,
            "gasPrice": hex(gas_price),
            "chainId": self.ethereum.w3.eth.chain_id
        }
        register_params = [
            name.replace(".eth", ""),
            paying_address,
            duration,
            secret,
            self.resolver_address,
            data_array,
            True,
            0
        ]
        call_data_register = ens_contract.encodeABI(
            fn_name="register",
            args = register_params
        )
        tx_register = {
            "from": paying_address,
            "to": self.ens_address,
            "value": hex(total_price), 
            "nonce": hex(nonce + 1),
            "gas": hex(400_000),      
            "data": call_data_register, 
            "gasPrice": hex(gas_price),
            "chainId": self.ethereum.w3.eth.chain_id
        }
        if gas_estimate := (self.ethereum.EstimateGas(tx_commit) + self.ethereum.EstimateGas(tx_register)) != None:
            print(f"Estimated fee: Ξ{(gas_estimate * gas_price) / 1e18:.18f}")
        else:
            print("Error estimating gas.")
            await self.ENSInterface()

        if input("Continue? y/n: ").lower() == "n":
            await self.ENSInterface()

        signed_tx = self.ethereum.SignTX(tx_commit, private_key)
        if signed_tx is None:
            print("Error signing transaction.")
            await self.ENSInterface()

        tx_hash = self.ethereum.BroadcastTransaction(signed_tx)
        if tx_hash is None:
            print("Error broadcasting.")
            await self.ENSInterface()

        print(f"Commitment broadcasted: {tx_hash}, waiting for confirmation...")
        self.web3.eth.wait_for_transaction_receipt(tx_hash, 1e10)
        print("Commitment confirmed, waiting 2 mins to broadcast purchase...")
        time.sleep(120)
        print("Signing register...")

        signed_register = self.ethereum.SignTX(tx_register)
        if signed_register is None:
            print("Error signing transaction.")
            await self.ENSInterface()

        tx_hash_register = self.ethereum.BroadcastTransaction(signed_register)
        if tx_hash_register is None:
            print("Error broadcasting.")
            await self.ENSInterface()
        
        print("Register tx sent:", tx_hash_register)
        self.web3.eth.wait_for_transaction_receipt(tx_hash_register, 1e10)
        print("Registration complete.")
        await self.ENSInterface()


    async def RenewName(self):
        ens_contract = self.web3.eth.contract(address=self.ens_address, abi=ens_abi)

        name = input("Name to renew: ").lower()
        available = ens_contract.functions.available(name.replace(".eth", "")).call()
        if available:
            print("Name not registered.")
            await self.ENSInterface()
        try:
            duration = int(input("Renewal duration (days): ")) * 24 * 3600
        except:
            print("Not a valid number.")
            await self.ENSInterface()

        base_price, premium = ens_contract.functions.rentPrice(name.replace(".eth", ""), duration).call()
        total_price = base_price + premium
        print(f"Total to pay (ETH): {total_price / 1e18:.18f}")

        paying_address = input("Paying address: ")
        if self.ethereum.CheckAddress(paying_address) == False: await self.ENSInterface()
        if paying_address not in [account.address for account in self.ethereum.accounts]:
            print("Address not in accounts file.")
            await self.ENSInterface()
        else:
            for account in self.ethereum.accounts:
                if account.address == paying_address:
                    private_key = account.key

        gas_price = int((self.web3.eth.gas_price - (self.web3.eth.max_priority_fee * 0.9)))

        nonce = self.ethereum.GetNonce(paying_address)
        call_data_renew = ens_contract.encodeABI(
            fn_name="renew",
            args=[name.replace(".eth", ""), duration]
        )
        tx_renew = {
            "from": paying_address,
            "to": self.ens_address,
            "value": hex(total_price), 
            "nonce": hex(nonce),
            "gas": hex(400_000),      
            "data": call_data_renew, 
            "gasPrice": hex(gas_price),
            "chainId": self.ethereum.w3.eth.chain_id
        }
        if gas_estimate := self.ethereum.EstimateGas(tx_renew) != None:
            print(f"Estimated fee: Ξ{((gas_estimate) * gas_price) / 1e18:.18f}")
        else:
            print("Error estimating gas.")
            await self.ENSInterface()

        if input("Continue? y/n: ").lower() == "n":
            await self.ENSInterface()

        signed_tx = self.ethereum.SignTX(tx_renew, private_key)
        if signed_tx is None:
            print("Error signing transaction.")
            await self.ENSInterface()

        tx_hash = self.ethereum.BroadcastTransaction(signed_tx)
        if tx_hash is None:
            print("Error broadcasting.")
            await self.ENSInterface()
        print(f"Renewal broadcasted: {tx_hash}")

        self.web3.eth.wait_for_transaction_receipt(tx_hash, 1e10)
        print("Renewal accepted.")
