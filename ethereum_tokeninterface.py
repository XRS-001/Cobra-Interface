import os
import json
import time

class TokenInterface:
    def __init__(self, *interface_elements, accounts, ethereum_instance):
        self.helios_rpc_url, self.uniswap_v3_router, self.weth9_address = interface_elements
        self.accounts = accounts
        self.ethereum_instance = ethereum_instance


    async def TokenInterface(self):
        print("1: Check Address Balance")
        print("2: Transfer Token")
        print("3: Place Token Order")
        print("4: Withdraw Wrapped Ether")
        print("5: Add Token Account")
        choice = input()
        match choice:
            case "1":
                await self.TokenAddressBalance()
            case "2":
                await self.TransferToken()
            case "3":
                await self.PlaceTokenOrder()
            case "4":
                await self.WithdrawWrappedEther()
            case "5":
                await self.AddTokenAccount()
            case _:
                await self.ethereum_instance.EthereumInterface()
    
    
    async def TokenAddressBalance(self):
        contract_address = input("Contract address: ")
        if self.ethereum_instance.CheckAddress(contract_address) == False: await self.TokenInterface()

        token_address = input("Token address: ")
        if self.ethereum_instance.CheckAddress(token_address) == False: await self.TokenInterface() 

        value = self.CheckTokenBalance(contract_address, token_address)
        if value is False:
            print("Balance is empty.")
        else:
            print(f"Balance: {value[0]:,.3f} {value[1]}")
            
        await self.TokenInterface()


    def CheckTokenBalance(self, contract_address, token_address, original_decimals=False):
        payload_balance = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_call",
            "params": [
                {
                    "to": contract_address,
                    "data": "0x70a08231" + token_address.lower().replace("0x", "").zfill(64)
                },
                "latest"
            ]
        }
        balance = self.ethereum_instance.Request(payload_balance)
        if balance is not None:
            balance = int(balance, 16)

            decimals = self.GetTokenDecimals(contract_address)
            if decimals is not None:
                decimals = int(decimals, 16)
                if not original_decimals:
                    actual_balance = balance / 10 ** decimals
                else:
                    actual_balance = balance
                name = self.GetTokenName(contract_address)
                return (actual_balance, name)
            else:
                return False
        else:
            return False


    async def AddTokenAccount(self):
        if os.path.isfile("Ethereum/accounts.json") and os.stat("Ethereum/accounts.json").st_size > 0:
            with open("Ethereum/accounts.json", 'r') as accountsFile:
                data = json.load(accountsFile)
            accounts = [self.ethereum_instance.Account.from_dict(d) for d in data]
        else:
            print("Add ethereum account first.")
            await self.TokenInterface()
        contract_address = input("Contract address: ")
        if self.ethereum_instance.CheckAddress(contract_address) == False: await self.TokenInterface()

        token_address = input("Token account: ")
        if self.ethereum_instance.CheckAddress(token_address) == False: await self.TokenInterface() 

        for account in accounts:
            if account.address == token_address:
                account.tokenAccounts.append(contract_address)

        with open("Ethereum/accounts.json", 'w') as file:
            json.dump([a.to_dict() for a in accounts], file, indent=4)

        print("Account added.")
        await self.TokenInterface()


    def GetTokenDecimals(self, contract_address):
        payloadUnits = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_call",
                "params": [
                    {
                        "to": contract_address,
                        "data": "0x313ce567"
                    },
                    "latest"
                ]
            }
        return self.ethereum_instance.Request(payloadUnits)

        
    def GetTokenName(self, contract_address):
        payloadName = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_call",
            "params": [
                {
                    "to": contract_address,
                    "data": "0x06fdde03"
                },
                "latest"
            ]
        }
        result_hex = self.ethereum_instance.Request(payloadName)
        if result_hex is not None:
            data = bytes.fromhex(result_hex[2:])
            string_length = int.from_bytes(data[32:64], byteorder='big')
            string_bytes = data[64:64 + string_length]
            name = string_bytes.decode('utf-8')
            return name
        else:
            return ""
        

    def GetTokenSymbol(self, contract_address):
        payloadSymbol = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_call",
            "params": [
                {
                    "to": contract_address,
                    "data": "0x95d89b41"
                },
                "latest"
            ]
        }
        result_hex = self.ethereum_instance.Request(payloadSymbol)
        if result_hex is not None:
            data = bytes.fromhex(result_hex[2:])
            string_length = int.from_bytes(data[32:64], byteorder='big')
            string_bytes = data[64:64 + string_length]
            symbol = string_bytes.decode('utf-8')
            return symbol
        else:
            return ""


    async def TransferToken(self):
        contract_address = input("Contract address: ")
        if self.ethereum_instance.CheckAddress(contract_address) == False: await self.TokenInterface()

        sending_address = input("Sending address: ")
        if self.ethereum_instance.CheckAddress(sending_address) == False: await self.TokenInterface()
        if sending_address not in [account.address for account in self.ethereum_instance.accounts]:
            print("Address not in accounts file.")
            await self.TokenInterface()
        else:
            for account in self.ethereum_instance.accounts:
                if account.address == sending_address:
                    private_key = account.key

        receiving_address = input("Receiving address: ")
        if self.ethereum_instance.CheckAddress(receiving_address) == False: await self.TokenInterface()

        value_input = input("Send amount: ")
        try:
            value = float(value_input)
        except ValueError:
            if value_input.lower() == "all":
                value = self.CheckTokenBalance(contract_address, sending_address)
                print(f"Sending entire balance: {value[0]}, {value[1]}") # type: ignore
                value = value[0] # type: ignore
            else:
                print("Not a valid number.")
                await self.TokenInterface()

        gas_price = int((self.ethereum_instance.w3.eth.gas_price - (self.ethereum_instance.w3.eth.max_priority_fee * 0.9)))

        decimals = self.GetTokenDecimals(contract_address)
        if decimals is not None:
            decimals = int(decimals, 16)
            value = int(value * (10 ** decimals))

            ERC20_ABI = [ {
                "name": "transfer",
                "type": "function",
                "stateMutability": "nonpayable",
                "inputs": [ {"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"} ],
                "outputs": [ {"name": "", "type": "bool"} ] } ]
            
            token_contract = self.ethereum_instance.w3.eth.contract(address=contract_address, abi=ERC20_ABI) # type: ignore

            transfer_calldata = token_contract.encodeABI(
                fn_name="transfer",
                args=[receiving_address, value]
            )

            unsigned_tx = {
                "from": sending_address,
                "to": contract_address,
                "value": hex(0), 
                "gas": hex(60000),  
                "gasPrice": hex(gas_price),
                "nonce": hex(self.ethereum_instance.GetNonce(sending_address)),
                "data": transfer_calldata,
                "chainId": self.ethereum_instance.w3.eth.chain_id
            }
            if gas_estimate := self.ethereum_instance.EstimateGas(unsigned_tx) != None:
                print(f"Estimated fee: Ξ{(gas_estimate * gas_price) / 1e18:.18f}")
            else:
                print("Error estimating gas.")
                await self.TokenInterface()

            if input("Continue? y/n: ").lower() == "n":
                self.ethereum_instance.EthereumInterface()

            signed_tx = self.ethereum_instance.SignTX(unsigned_tx, private_key)
            if signed_tx is None:
                print("Error signing.")
                await self.TokenInterface()

            transaction_hash = self.ethereum_instance.BroadcastTransaction(signed_tx)
            if transaction_hash is None:
                print("Error broadcasting.")
                await self.TokenInterface()

            print(f"Transfer broadcasted: {transaction_hash}")
            await self.TokenInterface()

        else:
            print("Error getting token data.")
            await self.TokenInterface()


    async def PlaceTokenOrder(self):
        choice = input("Paying with Ether? y/n: ").lower()
        if choice == "y":
            paying_with_eth = True

            contract_address = input("Contract address (buy): ").strip()
            if self.ethereum_instance.CheckAddress(contract_address) == False: await self.TokenInterface()

            try:
                amount_wei_to_buy = int(float(input("Amount to buy for (Ether): ")) * 1e18)
            except ValueError:
                print("Not a valid number.")
                await self.TokenInterface()

        elif choice == "n":
            paying_with_eth = False
            
            contract_address_sell = input("Contract address (sell): ").strip()
            if self.ethereum_instance.CheckAddress(contract_address_sell) == False: await self.TokenInterface()

            contract_address_buy = input("Contract address (buy): ").strip()
            if self.ethereum_instance.CheckAddress(contract_address_buy) == False: await self.TokenInterface()

            try:
                amount_to_sell = float(input("Amount to sell: "))
            except ValueError:
                print("Not a valid number.")
                await self.TokenInterface()

        else:
            await self.TokenInterface()

        sending_address = input("Paying address: ").strip()
        if self.ethereum_instance.CheckAddress(sending_address) == False: await self.TokenInterface()
        if sending_address not in [account.address for account in self.ethereum_instance.accounts]:
            print("Address not in accounts file.")
            await self.TokenInterface()
        else:
            for account in self.ethereum_instance.accounts:
                if account.address == sending_address:
                    private_key = account.key

        gas_price = int((self.ethereum_instance.w3.eth.gas_price - (self.ethereum_instance.w3.eth.max_priority_fee * 0.9)))

        try:
            expected_output = float(input("Expected output: "))
        except ValueError:
            print("Not a valid number.")
            await self.TokenInterface()

        try:
            slippage = float(input("Slippage (%): ")) / 100
        except ValueError:
            print("Not a valid number.")
            await self.TokenInterface()

        decimals_buy = self.GetTokenDecimals(contract_address if paying_with_eth else contract_address_buy)
        if decimals_buy is None:
            print("Error retrieving token decimals.")
            await self.TokenInterface()
            return

        decimals_buy = int(decimals_buy, 16)
        amount_out_min = int(expected_output * (1 - slippage) * (10 ** decimals_buy))

        fee_amount = 0
        while True:
            fee = input("Fee % (0.01, 0.05, 0.3, 1): ")
            match fee:
                case "0.01": fee_amount = 100; break
                case "0.05": fee_amount = 500; break
                case "0.3": fee_amount = 3000; break
                case "1": fee_amount = 10000; break
                case _: await self.TokenInterface() 

        try:
            deadline = int(time.time()) + int(input("Deadline (mins): ")) * 60
        except ValueError:
            print("Not a valid number.")
            await self.TokenInterface()

        ABI = [
            {
                "inputs": [
                    {
                        "components": [
                            {"internalType": "address", "name": "tokenIn", "type": "address"},
                            {"internalType": "address", "name": "tokenOut", "type": "address"},
                            {"internalType": "uint24", "name": "fee", "type": "uint24"},
                            {"internalType": "address", "name": "recipient", "type": "address"},
                            {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                            {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                            {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                        ],
                        "internalType": "struct ISwapRouter.ExactInputSingleParams",
                        "name": "params",
                        "type": "tuple"
                    }
                ],
                "name": "exactInputSingle",
                "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
                "stateMutability": "payable",
                "type": "function"
            }
        ]
        if not paying_with_eth:
            decimals_sell = self.GetTokenDecimals(contract_address_sell)
            if decimals_sell is None:
                print("Error retrieving token decimals.")
                await self.TokenInterface()

            decimals_sell = int(decimals_sell, 16) # type: ignore
        contract = self.ethereum_instance.w3.eth.contract(address=self.uniswap_v3_router, abi=ABI)  # type: ignore
        params = ({
            "tokenIn": self.weth9_address if paying_with_eth else contract_address_sell,
            "tokenOut": contract_address if paying_with_eth else contract_address_buy,
            "fee": fee_amount,
            "recipient": sending_address,
            "deadline": deadline,
            "amountIn": amount_wei_to_buy if paying_with_eth else int(amount_to_sell * (10 ** decimals_sell)),
            "amountOutMinimum": amount_out_min,
            "sqrtPriceLimitX96": 0
        },)
        contract_calldata = contract.encodeABI(fn_name="exactInputSingle", args=params)
        nonce = self.ethereum_instance.GetNonce(sending_address)
        swap_tx = {
            "from": sending_address,
            "to": self.uniswap_v3_router,
            "value": hex(amount_wei_to_buy if paying_with_eth else 0),
            "gas": hex(200_000),
            "gasPrice": hex(gas_price),
            "nonce": hex(nonce),
            "data": contract_calldata,
            "chainId": self.ethereum_instance.w3.eth.chain_id
        }

        if not paying_with_eth:
            token_contract = self.ethereum_instance.w3.eth.contract(address=contract_address_sell, abi=[{ # type: ignore
                "constant": False,
                "inputs": [
                    {"name": "_spender", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            }])

            amount_to_approve = int(amount_to_sell * (10 ** decimals_sell))
            approve_calldata = token_contract.encodeABI(fn_name="approve", args=[
                self.uniswap_v3_router,
                amount_to_approve
            ])

            approve_tx = {
                "from": sending_address,
                "to": contract_address_sell,
                "value": hex(0),
                "gas": hex(100_000),
                "gasPrice": hex(gas_price),
                "nonce": hex(nonce),
                "data": approve_calldata,
                "chainId": self.ethereum_instance.w3.eth.chain_id
            }
            try:
                swap_cost = ((self.ethereum_instance.EstimateGas(approve_tx) + self.ethereum_instance.EstimateGas(swap_tx)) * gas_price) / 1e18
            except:
                print("Error estimating gas.")
                await self.TokenInterface()

            swap_tx['nonce'] = hex(nonce + 1)
        else:
            if gas_estimate := self.ethereum_instance.EstimateGas(swap_tx) != None:
                swap_cost = (gas_estimate * gas_price) / 1e18
            else:
                print("Error estimating gas.")
                await self.TokenInterface()

        if input(f"Swap cost: Ξ{swap_cost:.18f}. Continue with swap? y/n: ").lower() == "n":
            await self.TokenInterface()

        if not paying_with_eth:
            approval = self.ApprovalTransaction(approve_tx, private_key)
            if approval == False:
                await self.TokenInterface()

        signed_tx = self.ethereum_instance.SignTX(swap_tx, private_key)
        if signed_tx is not None:
            swap_tx_hash = self.ethereum_instance.BroadcastTransaction(signed_tx)
            if swap_tx_hash is None:
                print("Error broadcasting swap.")
                self.TokenInterface
            print(f"Swap transaction sent: {swap_tx_hash}")
            print("Waiting for swap to confirm...")

            time.sleep(120)
            receipt = self.ethereum_instance.w3.eth.wait_for_transaction_receipt(swap_tx_hash, 1e10) # type: ignore
            if receipt["status"] != 1:
                print("Swap failed.")
                await self.TokenInterface()
                return

            print("Swap confirmed.")
        else:
            print("Swap signing failed.")

        await self.TokenInterface()
        

    def ApprovalTransaction(self, approve_tx, key):
        signed_approve_tx = self.ethereum_instance.SignTX(approve_tx, key)
        if signed_approve_tx is None:
            print("Approval signing failed.")
            return False

        approval_tx_hash = self.ethereum_instance.BroadcastTransaction(signed_approve_tx)
        if approval_tx_hash is None:
            print("Error broadcasting ERC-20 approval.")
            return False
        
        print(f"Approval transaction sent: {approval_tx_hash}")
        print("Waiting for approval to be confirmed...")

        time.sleep(120)
        receipt = self.ethereum_instance.w3.eth.wait_for_transaction_receipt(approval_tx_hash, 1e10) # type: ignore
        if receipt["status"] != 1:
            print("Approval transaction failed.")
            return False

        print("Approval confirmed.")


    async def WithdrawWrappedEther(self):
        sending_address = input("Wrapped Ether address: ")
        if sending_address not in [account.address for account in self.ethereum_instance.accounts]:
            print("Address not in accounts file.")
            await self.TokenInterface()
        else:
            for account in self.ethereum_instance.accounts:
                if account.address == sending_address:
                    private_key = account.key

        if self.ethereum_instance.CheckAddress(sending_address) == False: await self.TokenInterface()
        
        gas_price = int((self.ethereum_instance.w3.eth.gas_price - (self.ethereum_instance.w3.eth.max_priority_fee * 0.9)))

        weth_abi = [{
            "name": "withdraw",
            "type": "function",
            "stateMutability": "nonpayable",
            "inputs": [{"name": "wad", "type": "uint256"}],
            "outputs": []
        }]
        
        balance = self.CheckTokenBalance(self.weth9_address, sending_address, True)
        if not isinstance(balance, bool):
            if balance[0] > 0:
                amount_wei = balance[0]
                weth_contract = self.ethereum_instance.w3.eth.contract(address=self.weth9_address, abi=weth_abi)  # type: ignore
                calldata = weth_contract.encodeABI(fn_name="withdraw", args=[amount_wei])  

                unsigned_tx = {
                    "from": sending_address,
                    "to": self.weth9_address,
                    "value": hex(0),
                    "gas": hex(100_000),
                    "gasPrice": hex(gas_price),
                    "nonce": hex(self.ethereum_instance.GetNonce(sending_address)),
                    "data": calldata,
                    "chainId": self.ethereum_instance.w3.eth.chain_id
                }
                if gas_estimate := self.ethereum_instance.EstimateGas(unsigned_tx) != None:
                    print(f"Estimated fee: Ξ{(gas_estimate * gas_price) / 1e18:.18f}")
                else:
                    print("Error estimating gas.")
                    await self.TokenInterface()

                if input("Continue? y/n: ").lower() == "n":
                    await self.TokenInterface()

                signed_tx = self.ethereum_instance.SignTX(unsigned_tx, private_key)
                if signed_tx is None:
                    print("Error signing.")
                    await self.TokenInterface()

                transaction_hash = self.ethereum_instance.BroadcastTransaction(signed_tx)
                if transaction_hash is None:
                    print("Error broadcasting.")
                    await self.TokenInterface()
                    
                print(f"Transaction hash: {transaction_hash}")
                await self.TokenInterface()
        else:
            print("Error unwrapping ether.")
            await self.TokenInterface()