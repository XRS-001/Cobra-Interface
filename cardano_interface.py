import os
import time
import asyncio

class Cardano:
    def __init__(self, parent_interface=None):
        from pycardano import Address, PaymentSigningKey, PaymentVerificationKey, TransactionBuilder, \
        TransactionOutput, BlockFrostChainContext, Network
        self.Address = Address
        self.PaymentSigningKey = PaymentSigningKey
        self.PaymentVerificationKey = PaymentVerificationKey
        self.TransactionBuilder = TransactionBuilder
        self.TransactionOutput = TransactionOutput
        self.BlockFrostChainContext = BlockFrostChainContext
        self.Network = Network
        from blockfrost import BlockFrostApi, ApiUrls
        self.BlockFrostApi = BlockFrostApi
        self.ApiUrls = ApiUrls
        self.parent_interface=parent_interface
        try:
            with open("Cardano/api_key.txt", "r") as file:
                self.api_key = file.read()
        except:
            while True:
                self.api_key = input("Blockfrost API key: ")
                if self.api_key != "":
                    with open("Cardano/api_key.txt", "w") as file:
                        file.write(self.api_key)
                    break


    async def CardanoInterface(self):
        print("1: My Accounts")
        print("2: Create Account")
        print("3: Sign Transaction")
        print("4: Check Account Balance")
        print("5: Blockchain Explorer")
        choice = input("")
        match choice:
            case "1":
                await self.MyAccounts()
            case "2":
                await self.CreateAccount()
            case "3":
                await self.SignTransaction()
            case "4":
                await self.CheckBalance()
            case "5":
                await self.BlockchainExplorer()
            case _:
                if self.parent_interface:
                    await self.parent_interface.Main()
                else:
                    exit()


    def GetAddress(self, public_key):
        return self.Address(payment_part=public_key.hash(),
                       network=self.Network.MAINNET) # type: ignore


    async def MyAccounts(self):
        totalBalance = 0
        if len(os.listdir("Cardano/Accounts")) == 0:
            print("Create an account first.")
            await self.CardanoInterface()
        for address in os.listdir("Cardano/Accounts"):
            print(f"Address: {address.replace('.skey', '')}")
            try:
                balance = self.GetBalance(address.replace('.skey', ''))
                totalBalance += balance
                print(f"Balance: ₳{balance:,.6f}")
            except:
                print(f"Account not funded.")
            print()
        if len(os.listdir("Cardano/Accounts")) > 1:
            print(f"Total balance: ₳{totalBalance:,.6f}")
        await self.CardanoInterface()

    
    async def TotalBalance(self):
        totalBalance = 0
        for address in os.listdir("Cardano/Accounts"):
            try:
                balance = self.GetBalance(address.replace('.skey', ''))
                totalBalance += balance
            except:
                pass
        return totalBalance

    async def CheckBalance(self):
        address = input("Address: ")
        try:
            print(f"Balance: ₳{self.GetBalance(address):,.6f}")
        except Exception:
            print("Error")
        await self.CardanoInterface()

    
    def GetBalance(self, address):
        api = self.BlockFrostApi(self.api_key, base_url=self.ApiUrls.mainnet.value)
        utxos = api.address_utxos(address=address)
        return sum(int(next(a.quantity for a in utxo.amount if a.unit == "lovelace")) for utxo in utxos) / 1e6 # type: ignore[reportAttributeAccessIssue]


    async def SignTransaction(self):
        if len(os.listdir("Cardano/Accounts")) == 0:
            print("Create an account first.")
            await self.CardanoInterface()
        context = self.BlockFrostChainContext(self.api_key, base_url=self.ApiUrls.mainnet.value)

        sender = input("Sending Address: ")

        if not os.path.isfile(f"Cardano/Accounts/{sender}.skey"):
            print("Address not in address list.")
            await self.CardanoInterface()
        sk_path = f'Cardano/Accounts/{sender}.skey'

        receiver = input("Receiving Address: ")

        try:
            amount = int(float(input("Amount: ")) * 1e6)
        except:
            print("Not a number.")
            await self.CardanoInterface()

        tx_builder = self.TransactionBuilder(context=context)
        tx_builder.add_input_address(sender)
        tx_builder.add_output(self.TransactionOutput.from_primitive([receiver, amount])) # type: ignore
        payment_signing_key = self.PaymentSigningKey.load(sk_path)
        signed_tx = tx_builder.build_and_sign([payment_signing_key], change_address=self.Address.from_primitive(sender)) # type: ignore[reportArgumentType]
        print(f"Transaction submitted: {signed_tx.id}")
        context.submit_tx(signed_tx.to_cbor())
        await self.CardanoInterface()


    async def CreateAccount(self):
        payment_signing_key = self.PaymentSigningKey.generate()
        payment_verification_key = self.PaymentVerificationKey.from_signing_key(payment_signing_key)
        address = self.GetAddress(payment_verification_key)
        print(f"Created account: {address}")
        payment_signing_key.save(f"Cardano/Accounts/{address}.skey")
        await self.CardanoInterface()

    
    async def BlockchainExplorer(self):
        blockCount = 0
        try:
            while True:
                api = self.BlockFrostApi(self.api_key, base_url=self.ApiUrls.mainnet.value)
                try:
                    latest = api.block_latest()
                    if latest.height != blockCount: # type: ignore[reportArgumentType]
                        print(f"Block: {latest.height:,}") # type: ignore[reportArgumentType]
                        print("{")
                        print(f"    Hash: {latest.hash}") # type: ignore[reportArgumentType]
                        print(f"    Time: {latest.time}") # type: ignore[reportArgumentType]
                        print(f"    Transactions: {latest.tx_count}") # type: ignore[reportArgumentType]
                        print(f"    Value: ₳{float(latest.output) / 1e6:,}") # type: ignore[reportArgumentType]
                        print(f"    Fees: ₳{float(latest.fees) / 1e6:,}") # type: ignore[reportArgumentType]
                        print(f"    Size: {latest.size / 1000}Kb") # type: ignore[reportArgumentType]
                        print("}")
                        print()
                        blockCount = latest.height # type: ignore[reportArgumentType]
                        time.sleep(3)
                    else:
                        time.sleep(3)
                        continue
                except Exception as e:
                    print(e, end="")
                    break
        except KeyboardInterrupt:
            await self.CardanoInterface()

if __name__=="__main__":
    print("Cardano Interface")
    print("------------------")
    asyncio.run(Cardano().CardanoInterface())