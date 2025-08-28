import json
import os
import time
import asyncio

class Ripple:
    def __init__(self, parent_interface=None):
        import Ripple.xrpl as xrpl
        import xrpl.asyncio
        self.xrpl = xrpl
        self.async_xrpl = xrpl.asyncio
        self.client = xrpl.clients.JsonRpcClient(self.ledger_url)
        self.parent_interface=parent_interface

    class Account:
        def __init__(self):
            self.address = ""
            self.publicKey = ""
            self.privateKey = ""

        def to_dict(self):
            return {
                "address": self.address,
                "publicKey": self.publicKey,
                "privateKey": self.privateKey
            }
        
        @classmethod
        def from_dict(cls, data):
            acc = cls()
            acc.address = data.get("address", "")
            acc.publicKey = data.get("publicKey", "")
            acc.privateKey = data.get("privateKey", "")
            return acc

    accounts = {}
    ledger_url = "wss://xrplcluster.com/"
    async def RippleInterface(self):
        if os.path.isfile("Ripple/accounts.json") and os.stat("Ripple/accounts.json").st_size > 0:
            with open("Ripple/accounts.json", 'r') as file:
                data = json.load(file)
                for d in data:
                    Ripple.accounts[Ripple.Account.from_dict(d).address] = Ripple.Account.from_dict(d)
        print("1: My Accounts")
        print("2: Create Account")
        print("3: Delete Account")
        print("4: Sign Transaction")
        print("5: Check Account Balance")
        print("6: Ledger Explorer")
        choice = input("")
        match choice:
            case "1":
                await self.MyAccounts()
            case "2":
                await self.CreateAccount()
            case "3":
                await self.DeleteAccount()
            case "4":
                await self.SignTransaction()
            case "5":
                await self.CheckAccountBalance()
            case "6":
                await self.LedgerExplorer()
            case _:
                if self.parent_interface:
                    await self.parent_interface.Main()
                else:
                    exit()


    async def MyAccounts(self):
        if not os.path.isfile("Ripple/accounts.json") or os.stat("Ripple/accounts.json").st_size == 0:
            print("Create account first.")
            await self.RippleInterface()

        totalBalance = 0
        for account in Ripple.accounts:
            print(f"Address: {account}")
            if not await self.async_xrpl.account.does_account_exist(account, self.client):
                print("Account not initialized, deposit 1 XRP to initialize")
            else:
                balance = await self.async_xrpl.account.get_balance(account, self.client) / 1e6
                totalBalance += balance
                print(f"Balance: {balance:,.6f} XRP")
                print()
        if len(Ripple.accounts) > 1:
            print(f"Total balance: {totalBalance:,.6f} XRP")
        await self.RippleInterface()


    async def TotalBalance(self):
        accounts = {}
        if os.path.isfile("Ripple/accounts.json") and os.stat("Ripple/accounts.json").st_size > 0:
            with open("Ripple/accounts.json", 'r') as file:
                data = json.load(file)
                for d in data:
                    accounts[Ripple.Account.from_dict(d).address] = Ripple.Account.from_dict(d)

        totalBalance = 0
        for account in accounts:
            if await self.async_xrpl.account.does_account_exist(account, self.client):
                balance = await self.async_xrpl.account.get_balance(account, self.client) / 1e6
                totalBalance += balance

        return totalBalance

    async def CreateAccount(self):
        new_account = self.xrpl.wallet.Wallet.create()
        account = Ripple.Account()
        account.address = new_account.classic_address
        account.publicKey = new_account.public_key
        account.privateKey = new_account.private_key

        Ripple.accounts[account.address] = account

        with open("Ripple/accounts.json", 'w') as file:
            json.dump([Ripple.accounts[a].to_dict() for a in Ripple.accounts], file, indent=4)

        print(f"Account added: {new_account.classic_address}.")

        await self.RippleInterface()

    
    async def SignTransaction(self):
        if not os.path.isfile("Ripple/accounts.json") or os.stat("Ripple/accounts.json").st_size == 0:
            print("Create account first.")
            await self.RippleInterface()
        sender = input("Sending account: ")

        if not self.xrpl.core.addresscodec.is_valid_classic_address(sender):
            print("Invalid address.")
            await self.RippleInterface()

        elif not await self.async_xrpl.account.does_account_exist(sender, self.client):
            print("Account does not exist.")
            await self.RippleInterface()

        elif sender not in Ripple.accounts:
            print("Account not in accounts list.")
            await self.RippleInterface()

        receiver = input("Receiving account: ")
        if not self.xrpl.core.addresscodec.is_valid_classic_address(receiver):
            print("Invalid address.")
            await self.RippleInterface()

        try:
            amount = float(input("Amount: "))
        except ValueError:
            print("Not a number.")
            await self.RippleInterface()

        tx = self.xrpl.models.transactions.Payment(
            account=sender,
            amount=self.xrpl.utils.xrp_to_drops(amount),
            destination=receiver,
        )
        wallet = self.xrpl.wallet.Wallet(Ripple.accounts[sender].publicKey, Ripple.accounts[sender].privateKey)
        try:
            await self.async_xrpl.transaction.submit_and_wait(tx, self.client, wallet)
            print("Transaction successful.")
        except Exception as error:
            print(error)
        await self.RippleInterface()


    async def DeleteAccount(self):
        if not os.path.isfile("Ripple/accounts.json") or os.stat("Ripple/accounts.json").st_size == 0:
            print("Create account first.")
            await self.RippleInterface()

        sender = input("Account to delete: ")

        if not self.xrpl.core.addresscodec.is_valid_classic_address(sender):
            print("Invalid address.")
            await self.RippleInterface()

        elif not await self.async_xrpl.account.does_account_exist(sender, self.client):
            print("Account does not exist.")
            await self.RippleInterface()

        elif sender not in Ripple.accounts:
            print("Account not in accounts list.")
            await self.RippleInterface()

        receiver = input("Remaining balance recipient: ")
        if not self.xrpl.core.addresscodec.is_valid_classic_address(receiver):
            print("Invalid address.")
            await self.RippleInterface()

        tx = self.xrpl.models.transactions.AccountDelete(
            account=sender,
            destination=receiver,
        )
        wallet = self.xrpl.wallet.Wallet(Ripple.accounts[sender].publicKey, Ripple.accounts[sender].privateKey)
        try:
            await self.async_xrpl.transaction.submit_and_wait(tx, self.client, wallet)
            print("Delete successful.")
        except Exception as error:
            print(error)
        await self.RippleInterface()


    async def CheckAccountBalance(self):
        account = input("Account: ")

        if not self.xrpl.core.addresscodec.is_valid_classic_address(account):
            print("Invalid address.")
            await self.RippleInterface()

        if not await self.async_xrpl.account.does_account_exist(account, self.client):
            print("Account does not exist.")
        else:
            print(f"Balance: {await self.async_xrpl.account.get_balance(account, self.client) / 1e6:,.6f} XRP")
        await self.RippleInterface()


    async def LedgerExplorer(self):
        try:
            index = 0
            while True:
                ledger_request = self.xrpl.models.requests.Ledger(
                    ledger_index="validated",
                    transactions=True,       
                    expand=True              
                )

                response = await self.client.request(ledger_request)
                ledger_data = response.result["ledger"]
                if index != ledger_data['ledger_index']:
                    index = ledger_data['ledger_index']
                    print(f"Ledger Index: {index:,}")
                    print("{")
                    print(f"    Hash: 0x{ledger_data['ledger_hash']}")
                    print(f"    Transactions: {len(ledger_data['transactions'])}")
                    print(f"    Total XRP: {float(ledger_data['total_coins']) / 1e6:,}")
                    print(f"    Timestamp: {ledger_data['close_time']}")
                    print("}")
                    time.sleep(3)
                else:
                    time.sleep(3)
                    continue
        except KeyboardInterrupt:
            await self.RippleInterface()

if __name__=="__main__":
    print("Ripple Interface")
    print("-----------------")
    asyncio.run(Ripple().RippleInterface())