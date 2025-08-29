import asyncio 
import os
import json 
import time 
from Solana import requests
import base64
import re

class Solana:
    class Account:
        def __init__(self):
            self.address = ""
            self.privateKey = ""

        def to_dict(self):
            return {
                "address": self.address,
                "privateKey": self.privateKey
            }
        
        @classmethod
        def from_dict(cls, data):
            acc = cls()
            acc.address = data.get("address", "")
            acc.privateKey = data.get("privateKey", "")
            return acc
        

    def __init__(self, parent_interface=None):
        from Solana.solathon import Client, Keypair, Transaction, PublicKey
        from Solana.solathon.core.instructions import transfer, Instruction, AccountMeta
        from Solana.playwright.async_api import async_playwright
        from Solana.bs4 import BeautifulSoup
        self.async_playwright = async_playwright
        self.BeautifulSoup = BeautifulSoup
        self.PublicKey = PublicKey
        self.Transaction = Transaction
        self.SolanaClient = Client
        self.Keypair = Keypair
        self.transfer = transfer
        self.Instruction = Instruction
        self.AccountMeta = AccountMeta
        self.parent_interface = parent_interface

    accounts = {}
    async def SolanaInterface(self):
        if os.path.isfile("Solana/accounts.json") and os.stat("Solana/accounts.json").st_size > 0:
            with open("Solana/accounts.json", 'r') as file:
                data = json.load(file)
                for d in data:
                    Solana.accounts[Solana.Account.from_dict(d).address] = Solana.Account.from_dict(d)

        print("1: My Accounts")
        print("2: Add Account")
        print("3: Sign Transaction")
        print("4: Check Address Balance")
        print("5: Swap Interface")
        print("6: Blockchain Explorer")
        choice = input("")
        match choice:
            case "1":
                await self.Accounts()
            case "2":
                await self.AddAccount()
            case "3":
                await self.SignTransaction()
            case "4":
                await self.CheckAddressBalance()
            case "5":
                await self.SwapInterface()
            case "6":
                await self.BlockchainExplorer()
            case _:
                if self.parent_interface:
                    await self.parent_interface.Main()
                else:
                    exit()


    async def Accounts(self):
        client = self.SolanaClient("https://api.mainnet-beta.solana.com")
        total_balance = 0
        for account in self.accounts:
            if total_balance != 0:
                time.sleep(5)
            result = client.get_balance(account)
            total_balance += result / 1e9 # type: ignore
            print(f"Address: {account} balance: {result / 1e9} SOL") # type: ignore

            headers = {"accept": "application/json", "content-type": "application/json"}
            payload = {
                "id": 1,
                "jsonrpc": "2.0",
                "method": "getTokenAccountsByOwner",
                "params": [
                    account,
                    {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                    {"encoding": "jsonParsed"},
                ],
            }
            response = requests.post("https://api.mainnet-beta.solana.com", json=payload, headers=headers).json()
            if response['result']['value']:
                print("{")
                for token_account in response['result']['value']: 
                    balance = token_account['account']['data']['parsed']['info']['tokenAmount']['uiAmount'] # type: ignore
                    mint = token_account['account']['data']['parsed']['info']['mint'] # type: ignore
                    address = token_account['pubkey']
                    print(f"    {address} Balance: {balance} {await self.GetTokenSymbol(mint)}") # type: ignore
                print("}")

        print(f"Total balance: {total_balance:,.9f} SOL")
        await self.SolanaInterface()


    async def TotalBalance(self):
        accounts = {}
        if os.path.isfile("Solana/accounts.json") and os.stat("Solana/accounts.json").st_size > 0:
            with open("Solana/accounts.json", 'r') as file:
                data = json.load(file)
                for d in data:
                    accounts[Solana.Account.from_dict(d).address] = Solana.Account.from_dict(d)

        client = self.SolanaClient("https://api.mainnet-beta.solana.com")
        total_balance = 0
        token_dict = {}
        for account in accounts:
            if total_balance != 0:
                time.sleep(5)
            result = client.get_balance(account)
            total_balance += result / 1e9 # type: ignore

            headers = {"accept": "application/json", "content-type": "application/json"}
            payload = {
                "id": 1,
                "jsonrpc": "2.0",
                "method": "getTokenAccountsByOwner",
                "params": [
                    account,
                    {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                    {"encoding": "jsonParsed"},
                ],
            }
            response = requests.post("https://api.mainnet-beta.solana.com", json=payload, headers=headers).json()
            if response['result']['value']:
                for token_account in response['result']['value']: 
                    balance = token_account['account']['data']['parsed']['info']['tokenAmount']['uiAmount'] # type: ignore
                    mint = token_account['account']['data']['parsed']['info']['mint'] # type: ignore
                    token_dict[await self.GetTokenSymbol(mint)] = balance

        token_dict['sol'] = total_balance
        return token_dict


    async def AddAccount(self):
        new_account = self.Keypair()
        print(f"Account added: {new_account.public_key.base58_encode().decode('utf-8')}")
        account = Solana.Account()
        account.address = new_account.public_key.base58_encode().decode('utf-8') # type: ignore
        account.privateKey = new_account.private_key.__str__() # type: ignore
        Solana.accounts[new_account.public_key.base58_encode().decode('utf-8')] = account

        with open("Solana/accounts.json", 'w') as file:
            json.dump([Solana.accounts[a].to_dict() for a in Solana.accounts], file, indent=4)

        await self.SolanaInterface()
                    

    async def SignTransaction(self):
        client = self.SolanaClient("https://api.mainnet-beta.solana.com")
        sending_address = input("Sending address: ")
        if sending_address in self.accounts:
            receiving_address = input("Receiving address: ")
            try:
                amount = float(input("Amount: "))
            except ValueError:
                print("Not a valid number: ")
                await self.SolanaInterface()
                
            sender = self.Keypair.from_private_key(self.accounts[sending_address].privateKey)
            receiver = self.PublicKey(receiving_address)

            instruction = self.transfer(
                from_public_key=sender.public_key,
                to_public_key=receiver, 
                lamports=int(amount * 1e9)
            )

            transaction = self.Transaction(instructions=[instruction], signers=[sender])

            result = client.send_transaction(transaction)
            print("Transaction broadcasted:", result)
        else:
            print("Address not in accounts file.")
        await self.SolanaInterface()


    async def CheckAddressBalance(self):
        client = self.SolanaClient("https://api.mainnet-beta.solana.com")
        address = input("Address: ")
        result = client.get_balance(address)
        print(f"Balance: {result / 1e9} SOL") # type: ignore
        await self.SolanaInterface()


    async def SwapInterface(self):
        print("1: Get Quote")
        print("2: Swap Tokens")
        choice = input("")
        match choice:
            case "1":
                await self.Swap(False)
            case "2":
                await self.Swap(True)
            case _:
                await self.SolanaInterface()


    async def Swap(self, swapping):
        client = self.SolanaClient("https://api.mainnet-beta.solana.com")
        input_token = input("Input token: ")
        try:
            account_info = client.get_account_info(input_token)
            mint_data = account_info.data # type: ignore
            base64_data = mint_data[0] # type: ignore
            decoded_data = base64.b64decode(base64_data)
            input_decimals = decoded_data[44] # type: ignore
        except:
            print("Token not found.")
            await self.SolanaInterface()
        input_symbol = await self.GetTokenSymbol(input_token)

        try:
            amount = int(float(input("Amount: ")) * (10 ** input_decimals)) # type: ignore
        except:
            print("Not a valid number.")
            await self.SolanaInterface()

        output_token = input("Output token: ")
        try:
            account_info = client.get_account_info(output_token)
            mint_data = account_info.data # type: ignore
            base64_data = mint_data[0] # type: ignore
            decoded_data = base64.b64decode(base64_data)
            output_decimals = decoded_data[44] # type: ignore
        except:
            print("Token not found.")
            await self.SolanaInterface()

        output_symbol = await self.GetTokenSymbol(output_token)
        quote = requests.get(f"https://lite-api.jup.ag/swap/v1/quote?inputMint={input_token}&outputMint={output_token}&amount={amount}&slippageBps=50&restrictIntermediateTokens=true&asLegacyTransaction=true").json()
        if not swapping:
            await self.SolanaInterface()
        else:
            print(f"{amount / (10 ** input_decimals)} {input_symbol} -> {output_symbol}: {int(quote['outAmount']) / (10 ** output_decimals)}")
            continue_swap = input("Continue with swap? y/n: ") in ["Y", "y"]
            if continue_swap:
                sending_address = input("Sending address: ")
                if sending_address not in self.accounts:
                    print("Address not in accounts file.")
                    await self.SolanaInterface()
                else:
                    url = "https://lite-api.jup.ag/swap/v1/swap"
                    payload = { "userPublicKey": sending_address, "wrapUnwrapSOL": True, "asLegacyTransaction": True, "quoteResponse": quote }
                    response = requests.post(url, json=payload).json()['swapTransaction']

                    keypair = self.Keypair().from_private_key(self.accounts[sending_address].privateKey)

                    raw_tx_bytes = base64.b64decode(response)
                    transaction = self.Transaction.from_buffer(raw_tx_bytes, [keypair])
                    result = client.send_transaction(transaction)
                    print("Swap broadcasted: ", result)

        await self.SolanaInterface()


    async def GetTokenSymbol(self, address):
        async with self.async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            await page.goto(f"https://solscan.io/token/{address}", timeout=300000)
            await page.wait_for_load_state('networkidle')
            html = await page.content()
            await browser.close()

        soup = self.BeautifulSoup(html, 'html.parser')
        symbol = soup.find('meta', property='og:title')['content'] if soup.find('meta', property='og:title') else None # type: ignore
        match = re.search(r'\((.*?)\)', symbol) # type: ignore
        symbol = match.group(1) 
        return symbol

    
    async def BlockchainExplorer(self):
        client = self.SolanaClient("https://api.mainnet-beta.solana.com")
        try:
            blockCount = 0
            while True:
                if client.get_block_height() == blockCount:
                    time.sleep(3)
                    continue
                else:
                    blockCount = client.get_block_height()
                    print(f"Block {blockCount:,}")
                    print("{")
                    print(f"    Hash: {client.get_latest_blockhash().blockhash}") # type: ignore
                    print(f"    Time: {client.get_block_time(blockCount)}") # type: ignore
                    print(f"    Transactions in epoch: {client.get_epoch_info().transaction_count:,}") # type: ignore
                    print(f"    Current inflation rate: {client.get_inflation_rate().total * 100:.2f}%") # type: ignore
                    print(f"    Node health: {client.get_health()}") # type: ignore
                    print("}")
                    time.sleep(3)

        except KeyboardInterrupt:
            await self.SolanaInterface()

if __name__=="__main__":
    print("Solana Interface")
    print("------------------")
    asyncio.run(Solana().SolanaInterface())