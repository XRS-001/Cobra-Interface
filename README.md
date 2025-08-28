# Cobra-Interface

## Introduction

Cobra is an all in one crypto-currency command line interface in Python, it includes support for 8 different networks -Bitcoin, Ethereum, Solana, Ripple, Stellar, Cardano, Hedera, Thorchain- all provided as standalone modules that are linked together in one command line interface. You can download any one network's wallet if you'd like, but the Cobra interface includes a Thorchain interface for BTC-ETH-XRP-USDC-RUNE-TCY swaps and some other tools like a QR code generator and a portfolio dashboard.

**Note that in its current form, Cobra is experimental and there may still be bugs that I haven't found. Always test value transfers with small amounts.**

## Setup
The majority of the neccesary libraries are already included, but because of the number of dependencies, if you choose to use the Cardano wallet you will need to install pycardano in Python:
```
pip install pycardano
```
Apart from that, the only other software you might need is a Bitcoin Core node running on localhost if you chose to use the Bitcoin support.
## Tables
Here's an overview of every network supported and its connection to its respective network.

| Left columns  | Right columns |
| ------------- |:-------------:|
| Bitcoin     | [Bitcoin Core](https://github.com/bitcoin/bitcoin) on localhost (not included)     |
| Ethereum      | [Helios](https://github.com/a16z/helios) (included)     |
| XRPL      | [XRPL Python](https://xrpl.org/docs/tutorials/python/build-apps/get-started)     |
| Stellar      | https://horizon.stellar.org|
| Cardano      | Blockfrost API|
| Solana      | https://api.mainnet-beta.solana.com|
| Thorchain      | https://thornode.ninerealms.com|
| Hedera      | [Hiero SDK](https://github.com/hiero-ledger/hiero-sdk-python)|

## Usage
The wallet functionality for most supported networks is just basic value transfers and block explorers that go without saying. The Ethereum and Thorchain support however are more complicated so I'll give some explanation as to how to traverse their command lines. You'll also be asked to provide a API key for CoinMarketCap.com because the interface uses the USD value of Bitcoin to calculate a bitcoin denominated value of your portfolio. You can get an API key here: https://coinmarketcap.com/api/

### Main Interface
The main interface gives you access to every module, the Thorchain interface, a QR code generator and a portfolio dashboard tool that quotes your account's value denominated in Sats. Here's what the interface looks like:
```
Cobra Client v0.1
-----------------
1: Bitcoin
2: Ethereum
3: Ripple
4: Cardano
5: Stellar
6: Solana
7: Hedera
8: Thorchain
9: Account QR Code
10: Portfolio
```
### Ethereum
You can run the interface code to get started with python3 interface.py.
```bash
C:\Users\user_name>cd desktop/ethereum-cobra

C:\Users\user_name\Desktop\Ethereum-Cobra>python3 interface.py
Ethereum Interface
------------------
Enter an Ethereum RPC URL (Helios will use it to trustlessly bootstrap a light client):
```
You'll be asked to provide an RPC URL on the first startup. Helios will use this URL to bootstrap a light client connection to the Ethereum network trustlessly, I recommend getting an Alchemy or Infura RPC URL to use with Helios. 

Once you've setup Helios you'll be presented with the main interface.
```bash
1: My Accounts
2: Add Account
3: Sign Transaction
4: Check Address Balance
5: Token Interface
6: Ethereum Name Service
7: Blockchain Explorer
8: Check Transaction Status
9: Deploy Contract
```
**My Accounts** uses Helios to check the Ether and ERC-20 token balances of the accounts saved in the accounts.json file in the Ethereum folder.

**Add Account** adds a new account to the accounts.json file using secrets to generate a random private key. There's no account importing so if you have existing Ethereum accounts I'd reccomend creating a new one with this function and sending a small amount of Ether to test some of the interface's functions.

**Sign Transaction** is a simple function for sending Ether from one address to another, gas prices are generated automatically and a confirmation appears with an estimated fee denominated in Ether before signing and broadcast. This confirmation with estimated fee functionality is implemented across the entire interface for every value transfer. Every value transfer also has checks to make sure the recipient is a valid checksummed address.

**Check Address Balance** is pretty simple, it just checks the Ether balance of a checksummed address.

**Token Interface** loads up the tokeninterface.py menu, which I'll get into later.

**Ethereum Name Service** loads up the nameservice.py menu, which I'll get into later.

**Block Explorer** provides you with an updating stream of the latest block and some data about it, you can use it to look at some metrics like gas prices. You need to press CTRL-C to exit from the explorer.

**Check Transaction Status** checks whether a transation is included in the mempool or included in a block, or neither.

**Deploy Contract** is a function for deploying bytecode to the network and returning the contract address after deployment. Estimated deployment fees are also displayed before deployment.

If you were to have selected 5 here you would be brought to the token interface menu which has functions for interacting with ERC-20 tokens and Uniswap.
``` bash
1: Check Address Balance
2: Transfer Token
3: Place Token Order
4: Withdraw Wrapped Ether
5: Add Token Account
```

**Check Address Balance** is similiar to the Ether version except you first provide the ERC-20 token's contract address.

**Transfer Token** is a function for transferring ERC-20 tokens from one address to another.

**Place Token Order** lets you place an order for an ERC-20 token on Uniswap either with Ether or another ERC-20 token, there's different functionality for both scenarios as swaps that are paid for in ERC-20 need approval transaction to be broadcast first. You also need to select some different parameters like maximum slips and fee pools. I recommend checking swap data on the Uniswap website before attempting a swap. Also make sure that you're checking the Uniswap V3 router as I've hard coded support for only the V3 router currently.

**Withdraw Wrapped Ether** is for when you've executed an ERC-20 to Ether swap and you need to unwrap the received Ether as Uniswap uses Wrapped Ether rather than native Ether for swaps where you're receiving Ether.

**Add Token Account** is for manually linking one of your Ethereum accounts to an ERC-20 token contract to check for balances in the token that are listed when you select **My Accounts** in the main interface.

If you were to have selected 6 in the main interface you would be brought to the Ethereum Name Service menu for resolving/purchasing/renewing ENS names.
``` bash
1: Resolve Name
2: Resolve Address
3: Purchase Name
4: Renew Name
```
**Resolve Name** takes an ENS name and returns the resolved address.

**Resolve Address** this takes an address and reverse resolves it into an ENS name, note that reverse resolving does not guarentee that the ENS name resolves to the address as it doesn't guarentee the address is the owner.

**Purchase Name** lets you purchase an ENS name with one of the accounts that you own, by default I've hardcoded it so that the address you purchase with is what the ENS name resolves too. Purchasing a name involves a two transaction process for commiting to the purchase and purchasing two minutes after the commit is included in a block.

**Renew Name** Renews the purchase of an ENS name you own for an amount of days.

## Thorchain
If you don't know, Thorchain is a cross-chain liquidity protocol for making trustless cross-chain swaps over some major networks. I've added support in Cobra for swaps using BTC, ETH, XRP, USDC, RUNE, and TCY. The Thorchain interface integrates with your existing accounts on respective networks, so when you choose to conduct a swap you'll be asked to pick an account to fund the swap sell-side and a receiving account buy-side. Here's what the Thorchain interface menu looks like:
```
1: Thorchain Accounts
2: Create Thorchain Account
3: RUNE Transaction
4: Check Account Balance
5: TCY Staking
6: Rune-Pool liquidity
7: Get Swap Quote
8: Swap Crypto
9: Check Transaction Status
10: Thorchain Block Explorer
```
**Thorchain Accounts** provides you with RUNE and TCY balances for accounts you've imported or created and RunePool units if you hold them.

**Create Thorchain Account** Randomly generates a new Thorchain account.

**RUNE Transaction** is just basic value transfers.

**Check Account Balance** queries the network for an accounts RUNE and TCY balance.

**TCY Staking** lets you stake TCY that you own to earn rewards.

**Rune-Pool liquidity** lets you deposit RUNE into the automated RunePool to earn rewards for providing liquidity.

**Get Swap Quote** lets you check current swap rates and times.

**Swap Crypto** is where you can conduct swaps over the supported networks -BTC-ETH-XRP-USDC-RUNE-TCY- and fund them with accounts imported into the respective network's Cobra module.

**Check Transaction Status** takes a transaction's hash and checks whether it transaction was successfull.

**Thorchain Block Explorer** Is just a basic block explorer for watching the network operate.

