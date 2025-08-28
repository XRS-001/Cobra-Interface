import json
import os
import time
import asyncio

class Stellar:
    def __init__(self, parent_interface=None):
        from Stellar.stellar_sdk import Keypair, Network, Server, TransactionBuilder, Account as StellarAccount, Asset, TextMemo
        self.memo = TextMemo
        self.Keypair = Keypair
        self.Network = Network
        self.Server = Server
        self.TransactionBuilder = TransactionBuilder
        self.StellarAccount = StellarAccount
        self.Asset = Asset
        from decimal import Decimal
        self.Decimal = Decimal
        self.parent_interface = parent_interface

    class Account:
        def __init__(self):
            self.publicKey = ""
            self.privateKey = ""

        def to_dict(self):
            return {
                "publicKey": self.publicKey,
                "privateKey": self.privateKey
            }
        
        @classmethod
        def from_dict(cls, data):
            acc = cls()
            acc.publicKey = data.get("publicKey", "")
            acc.privateKey = data.get("privateKey", "")
            return acc

    accounts = []
    async def StellarInterface(self):
        Stellar.accounts.clear()
        if os.path.isfile("Stellar/accounts.json") and os.stat("Stellar/accounts.json").st_size > 0:
            with open("Stellar/accounts.json", 'r') as file:
                data = json.load(file)
                for d in data:
                    Stellar.accounts.append(Stellar.Account.from_dict(d))

        print("1: My Accounts")
        print("2: Create Account")
        print("3: Sign Transaction")
        print("4: Check Account Balance")
        print("5: Ledger Explorer")
        choice = input("")
        match choice:
            case "1":
                await self.MyAccounts()
            case "2":
                await self.CreateAccount()
            case "3":
                await self.SignTransaction()
            case "4":
                await self.CheckAccountBalance()
            case "5":
               await self.LedgerExplorer()
            case _:
                if self.parent_interface:
                    await self.parent_interface.Main()
                else:
                    exit()


    async def MyAccounts(self):
        if not os.path.isfile("Stellar/accounts.json") or os.stat("Stellar/accounts.json").st_size == 0:
            print("Create account first.")
            await self.StellarInterface()

        server = self.Server(horizon_url="https://horizon.stellar.org")
        total_balance = 0
        for account in self.accounts:
            print(f"Account: {account.publicKey}")
            try:
                account_on_ledger = server.accounts().account_id(account.publicKey).call()
                balance = 0
                balance = self.GetBalance(account_on_ledger)
                if balance is not None:
                    total_balance += balance
                print(f"Balance: {balance:,.5f} Lumens")
            except Exception:
                print("Account not initialized.")
            print()
        if len(self.accounts) > 1:
            print(f"Total balance: {total_balance:,.5f} Lumens")
        await self.StellarInterface()


    async def TotalBalance(self):
        accounts = []
        if os.path.isfile("Stellar/accounts.json") and os.stat("Stellar/accounts.json").st_size > 0:
            with open("Stellar/accounts.json", 'r') as file:
                data = json.load(file)
                for d in data:
                    accounts.append(Stellar.Account.from_dict(d))

        server = self.Server(horizon_url="https://horizon.stellar.org")
        total_balance = 0
        for account in accounts:
            try:
                account_on_ledger = server.accounts().account_id(account.publicKey).call()
                balance = 0
                balance = self.GetBalance(account_on_ledger)
                if balance is not None:
                    total_balance += balance
            except Exception:
                pass

        return total_balance

    async def CreateAccount(self):
        keypair = self.Keypair.random()
        account = self.Account()
        account.publicKey = keypair.public_key
        account.privateKey = keypair.secret
        self.accounts.append(account)

        with open("Stellar/accounts.json", 'w') as file:
            json.dump([account.to_dict() for account in self.accounts], file, indent=4)

        print("Generated account: " + keypair.public_key)
        await self.StellarInterface()


    async def SignTransaction(self):
        server = self.Server(horizon_url="https://horizon.stellar.org")
        sender = input("Sender: ")
        is_in_accounts_file = False
        for account in self.accounts:
            if account.publicKey == sender:
                is_in_accounts_file = True
                private_key = account.privateKey
                break
        if is_in_accounts_file == False:
            print("Account not in accounts list.")
            await self.StellarInterface()
        receiver = input("Receiver: ")
        amount = input("Amount: ")


        try:
            account = server.load_account(sender)
        except Exception:
            print("Account not initialized.")
            await self.StellarInterface()
        memo = input("Memo: ")
        transaction = (self.TransactionBuilder(source_account=account, network_passphrase=self.Network.PUBLIC_NETWORK_PASSPHRASE, base_fee=100)).add_memo(memo=self.memo(memo))
        try:
            server.load_account(receiver)
            print("Transferring funds...")
            transaction.append_payment_op(destination=receiver, asset=self.Asset.native(), amount=amount)

        except Exception:
            print("Receiving account not initialized, creating funding transaction...")
            transaction.append_create_account_op(destination=receiver, starting_balance=amount)

        finally:
            transaction = transaction.set_timeout(60).build().to_transaction_envelope_v1()
            transaction.sign(self.Keypair.from_secret(private_key))
            server.submit_transaction(transaction)

        print("Transaction successful.")
        await self.StellarInterface()


    async def CheckAccountBalance(self):
        server = self.Server(horizon_url="https://horizon.stellar.org")
        address = input("Account: ")
        try:
            account = server.accounts().account_id(address).call()
        except Exception:
            print("Error.")
            await self.StellarInterface()

        print(f"Balance: {self.GetBalance(account):,} Lumens ")
        await self.StellarInterface()


    def GetBalance(self, account):
        for balance in account["balances"]:
            asset_type = balance["asset_type"]
            if asset_type == "native":
                return float(balance['balance'])

    
    async def LedgerExplorer(self):
        sequence = 0
        while True:
            try:
                server = self.Server(horizon_url="https://horizon.stellar.org")
                
                response = server.ledgers().limit(1).order(desc=True).call()
                latest_ledger = response["_embedded"]["records"][0]
                if sequence != latest_ledger['sequence']:
                    sequence = latest_ledger['sequence']
                    print(f"Ledger {latest_ledger['sequence']:,}")
                    print("{")
                    print(f"    Hash: {latest_ledger['hash']}")
                    print(f"    Transactions: {latest_ledger['successful_transaction_count']}")
                    print(f"    Value in ledger: {self.PaymentsInLedger(sequence, server):,.5f} Lumens")
                    print(f"    Ciculating Lumens: {float(latest_ledger['total_coins']) - 5.5e10:,} Lumens")
                    print(f"    Fee pool: {float(latest_ledger['fee_pool']) / 1e5:,.5} Lumens")
                    print("}")
                    time.sleep(3)
                else:
                    time.sleep(3)
                    continue
            except KeyboardInterrupt:
                await self.StellarInterface()
            except:
                print("Error getting ledger data.")
                await self.StellarInterface()


    def PaymentsInLedger(self, sequence, server):
        total = self.Decimal(0)
        page = server.operations().for_ledger(sequence).call()

        while True:
            for op in page["_embedded"]["records"]:
                if op["type"] == "payment" and op.get("asset_type") == "native":

                    total += self.Decimal(op["amount"])
            next_href = page["_links"]["next"]["href"]
            self_href = page["_links"]["self"]["href"]
            if next_href == self_href:
                break

            last_cursor = page["_embedded"]["records"][-1]["paging_token"]
            page = (server.operations().for_ledger(sequence).cursor(last_cursor).call())
        return total

if __name__=="__main__":
    print("Stellar Interface")
    print("------------------")
    asyncio.run(Stellar().StellarInterface())