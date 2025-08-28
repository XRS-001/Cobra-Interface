import asyncio
import qrcode
import os

class CryptoInterface:
    api_key = ""
    async def Main(self):
        if not os.path.exists("cmc_api_key.tx"):
            while True:
                key = input("Enter an API key for CoinMarketCap.com (neccesary for portfolio value calculations): ")
                if key != "":
                    with open("cmc_api_key.txt", "w") as file:
                        file.write(key)
                    self.api_key = key
                    break
        else:
            with open("cmc_api_key.txt", "r") as file:
                self.api_key = file.read()

        while True:
            print("Cobra Client v0.1")
            print("-----------------")
            print("1: Bitcoin")
            print("2: Ethereum")
            print("3: Ripple")
            print("4: Cardano")
            print("5: Stellar")
            print("6: Solana")
            print("7: Hedera")
            print("8: Thorchain")
            print("9: Account QR Code")
            print("10: Portfolio")
            choice = input()
            match choice:
                case "1":
                    import bitcoin_interface
                    await bitcoin_interface.Bitcoin(parent_interface=self).BitcoinInterface()
                case "2":
                    import ethereum_interface
                    await ethereum_interface.Ethereum(parent_interface=self).EthereumInterface()
                case "3":
                    import ripple_interface
                    await ripple_interface.Ripple(parent_interface=self).RippleInterface()
                case "4":
                    import cardano_interface
                    await cardano_interface.Cardano(parent_interface=self).CardanoInterface()
                case "5":
                    import stellar_interface
                    await stellar_interface.Stellar(parent_interface=self).StellarInterface()
                case "6":
                    import solana_interface
                    await solana_interface.Solana(parent_interface=self).SolanaInterface()
                case "7":
                    import hedera_interface
                    await hedera_interface.Hedera(parent_interface=self).HederaInterface()
                case "8":
                    import thorchain_interface
                    await thorchain_interface.Thorchain(parent_interface=self).ThorchainInterface()
                case "9":
                    await self.ShowAccountQRCode()
                case "10":
                    await self.Portfolio()
                case "":
                    exit()



    async def ShowAccountQRCode(self):
        address = input("Address: ")

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.ERROR_CORRECT_L,
            box_size=1,
            border=1,
        )
        qr.add_data(address)
        qr.make(fit=True)

        matrix = qr.get_matrix()

        for row in matrix:
            print("".join(["██" if cell else "  " for cell in row]))
        print() 
        await self.Main()


    async def Portfolio(self):
        import bitcoin_interface
        import ethereum_interface
        import ripple_interface
        import cardano_interface
        import stellar_interface
        import solana_interface
        import hedera_interface
        import thorchain_interface
        import requests

        print("Portfolio: ")
        print("{")
        holdings = {}
        holdings['BTC'] = await bitcoin_interface.Bitcoin(initiate_rpc=False).TotalBalance()
        ethereum = ethereum_interface.Ethereum()
        eth_balances = await ethereum.TotalBalance()
        ethereum.process.kill() # type: ignore
        holdings['ETH'] = eth_balances['eth']
        eth_balance = eth_balances.popitem()[1]
        for balance in eth_balances.keys():
            holdings[eth_balances[balance][1]] = eth_balances[balance][0]

        sol_balances = await solana_interface.Solana().TotalBalance()
        holdings['SOL'] = sol_balances['sol']
        sol_balance = sol_balances.popitem()[1]
        for balance in sol_balances.keys():
            holdings[balance] = sol_balances[balance]

        thorchain_balances = await thorchain_interface.Thorchain().TotalBalance()
        holdings['RUNE'] = thorchain_balances[0]
        holdings['TCY'] = thorchain_balances[1]

        xrp_balance = await ripple_interface.Ripple().TotalBalance()
        holdings['XRP'] = xrp_balance

        stellar_balance = await stellar_interface.Stellar().TotalBalance()
        holdings['XLM'] = stellar_balance

        cardano_balance = await cardano_interface.Cardano().TotalBalance()
        holdings['ADA'] = cardano_balance

        hedera_balance = await hedera_interface.Hedera().TotalBalance()
        holdings['HBAR'] = hedera_balance

        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.api_key,
        }
        total_value = 0
        for symbol in holdings.keys():
            url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest"
            parameters = {
                'symbol': symbol,
            }
            try:
                value = requests.get(url, headers=headers, params=parameters).json()['data'][symbol][0]['quote']['USD']['price']
                if value:
                    total_value += value * holdings[symbol]
                    holdings[symbol] = (holdings[symbol], value * holdings[symbol])
            except:
                pass

        print(f"    BTC: {holdings['BTC'][0]}, {holdings['BTC'][1] / total_value * 100:,.2f}%") # type: ignore
        if len(eth_balances) > 0:
            print("    Ethereum:")
            print("    {")
            print(f"        Ether: {eth_balance:,.3f}, {holdings['ETH'][1] / total_value * 100:.2f}%")
            for balance in eth_balances.keys():
                print(f"        {balance}: {eth_balances[balance][0]:,.3f}, {holdings[eth_balances[balance][1]][1] / total_value * 100:.2f}%")
            print("    }")
        else:
            print(f"    Ether: {eth_balance:,.3f}, {holdings['ETH'][1] / total_value * 100:.2f}%")

        if len(sol_balances) > 0:
            print("    Solana:")
            print("    {")
            print(f"        Sol: {sol_balance:,.3f}, {holdings['SOL'][1] / total_value * 100:.2f}%")
            for balance in sol_balances.keys():
                print(f"        {balance}: {sol_balances[balance]:,.3f}, {holdings[balance][1] / total_value * 100:.2f}%")
            print("    }")
        else:
            print(f"    Sol: {sol_balance:,.3f}, {holdings['SOL'][1] / total_value * 100:.2f}%")

        print(f"    Thorchain:")
        print("    {")
        print(f"        Rune: {thorchain_balances[0]:,.3f}, {holdings['RUNE'][1] / total_value * 100:.2f}%") # type: ignore
        print(f"        TCY: {thorchain_balances[1]:,.3f}")
        print(f"        Rune-Pool Units: {thorchain_balances[2]:,.3f}")
        print("    }")

        print(f"    XRP: {holdings['XRP'][0]:,.3f}, {holdings['XRP'][1] / total_value * 100:.2f}%") # type: ignore
        print(f"    XLM: {holdings['XLM'][0]:,.3f}, {holdings['XLM'][1] / total_value * 100:.2f}%") # type: ignore
        print(f"    ADA: {holdings['ADA'][0]:,.3f}, {holdings['ADA'][1] / total_value * 100:.2f}%") # type: ignore
        print(f"    HBAR: {holdings['HBAR'][0]:,.3f}, {holdings['HBAR'][1] / total_value * 100:.2f}%") # type: ignore

        btc_url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest"
        parameters = {
            'symbol': "BTC",
        }
        btc_value = requests.get(btc_url, headers=headers, params=parameters).json()['data']["BTC"][0]['quote']['USD']['price']
        value_in_sats = int(total_value / btc_value * 1e8)
        print(f"    Total value: {value_in_sats:,} Sats")
        print("}")
        print()


if __name__=="__main__":
    asyncio.run(CryptoInterface().Main())
