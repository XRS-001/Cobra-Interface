import os
import asyncio

class Hedera:
    def __init__(self, parent_interface=None):
        from Hedera import hiero_sdk_python
        self.hedera = hiero_sdk_python
        self.parent_interface = parent_interface

    accounts = []
    async def HederaInterface(self):
        print("1: My Accounts")
        print("2: Add Account")
        print("3: Sign Transaction")
        print("4: Check Address Balance")
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
            case _:
                if self.parent_interface:
                    await self.parent_interface.Main()
                else:
                    exit()


    async def Accounts(self):
        network = self.hedera.Network(network='mainnet')
        client = self.hedera.Client(network)
        total_balance = 0
        for address in os.listdir("Hedera/Accounts"):
            balance_query = self.hedera.CryptoGetAccountBalanceQuery().set_account_id(self.hedera.AccountId().from_string(address.__str__().replace(".txt", ""))) 
            balance = balance_query.execute(client)
            print(f"{address.__str__().replace('.txt', '')} balance: {float(balance.hbars.__str__()[:-2]):,} HBAR")
            total_balance += float(balance.hbars.__str__()[:-2])
        print(f"Total balance: {total_balance:,.8f} HBAR")

        await self.HederaInterface()


    async def TotalBalance(self):
        network = self.hedera.Network(network='mainnet')
        client = self.hedera.Client(network)
        total_balance = 0
        for address in os.listdir("Hedera/Accounts"):
            balance_query = self.hedera.CryptoGetAccountBalanceQuery().set_account_id(self.hedera.AccountId().from_string(address.__str__().replace(".txt", ""))) # type: ignore
            balance = balance_query.execute(client)
            total_balance += float(balance.hbars.__str__()[:-2])

        return total_balance


    async def AddAccount(self):
        creator = input("Account creator id: ")
        if f"{creator}.txt" not in os.listdir("Hedera/Accounts"):
            print("Account not in accounts directory.")
            await self.HederaInterface()

        with open(f"Hedera/Accounts/{creator}.txt", "r") as file:
            private_key = self.hedera.PrivateKey.from_string(file.read())

        network = self.hedera.Network(network='mainnet')

        client = self.hedera.Client(network)
        client.set_operator(self.hedera.AccountId.from_string(creator), private_key)

        balance_query = self.hedera.CryptoGetAccountBalanceQuery().set_account_id(self.hedera.AccountId().from_string(creator)) # type: ignore
        if float(balance_query.execute(client).hbars.__str__()[:-2]) < 1:
            print("Fund account creator with more than 1 HBAR first.")
            await self.HederaInterface()

        new_account_private_key = self.hedera.PrivateKey.generate_ed25519()
        new_account_public_key = new_account_private_key.public_key()
        transaction = self.hedera.AccountCreateTransaction(key=new_account_public_key, initial_balance=self.hedera.Hbar(1)).freeze_with(client) # type: ignore
        transaction.sign(private_key)
        receipt = transaction.execute(client)
        new_account_id = receipt.accountId
        print(f"Account created: {new_account_id}")
        with open(f"Hedera/Accounts/{new_account_id}.txt", "x") as file:
            file.write(new_account_private_key.to_string())

        await self.HederaInterface()


    async def SignTransaction(self):
        sending_address = input("Sending id: ")
        if f"{sending_address}.txt" not in os.listdir("Hedera/Accounts"):
            print("Account not in accounts directory.")
            await self.HederaInterface()

        with open(f"Hedera/Accounts/{sending_address}.txt", "r") as file:
            private_key = self.hedera.PrivateKey.from_string(file.read())
            

        try:
            amount = int(float(input("Amount: ")) * 1e8)
        except:
            print("Not a valid number.")
            await self.HederaInterface()

        receiving_address = input("Receiving id: ")
        memo = input("Memo: ")

        network = self.hedera.Network(network='mainnet')
        client = self.hedera.Client(network)

        sender_id = self.hedera.AccountId.from_string(sending_address)
        recipient_id = self.hedera.AccountId.from_string(receiving_address)
        client.set_operator(sender_id, private_key)

        transaction = (
            self.hedera.TransferTransaction()
            .add_hbar_transfer(sender_id, amount * -1) # type: ignore
            .add_hbar_transfer(recipient_id, amount) # type: ignore
            .set_transaction_memo(memo)
            .freeze_with(client)
        )

        transaction.sign(private_key)
        transaction.execute(client)
        print("HBAR transfer successful.")
        await self.HederaInterface()
    

    async def CheckAddressBalance(self):
        network = self.hedera.Network(network='mainnet')
        client = self.hedera.Client(network)

        account_id = input("Account id: ")

        balance_query = self.hedera.CryptoGetAccountBalanceQuery().set_account_id(self.hedera.AccountId().from_string(account_id)) # type: ignore
        balance = balance_query.execute(client)
        
        print(f"Balance: {float(balance.hbars.__str__()[:-2]):,} HBAR")
        await self.HederaInterface()


if __name__ == "__main__":
    print("Hedera Interface")
    print("-----------------")
    asyncio.run(Hedera().HederaInterface())