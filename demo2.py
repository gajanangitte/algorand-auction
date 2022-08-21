""" Python module that runs demo """
from time import time
import os
from algosdk.logic import get_application_address
from rich import print
from rich.table import Table
from datetime import datetime

from source.utils.utils_account import initialize_algod_client
from source.classes.class_UserAccounts import UserAccounts
from source.classes.class_Auction import Auction

def demo() -> None:
    """ Runs demo for auction """

    os.system('clear')


    print("\n\t\t[bold red blink]Welcome to NFT AUCTION! [italic ]Powered by Algorand")
    print("\n [bold]Actors in this demo: ")
    print("[yellow1] Artist     [blue] is a hustler.")
    print("[yellow1] Auctioneer [blue] is trusted an agent and shall host auctions.")
    print("[yellow1] Bidder One [blue] is a sly untrustworthy businessman.   [red] bad bidder")
    print("[yellow1] Bidder Two [blue] is single son of a multi-billionaire. [red] good bidder")
    


    print("\n [bold] Let us now list their wallets and balances: ")
    algod_client = initialize_algod_client()
    users = UserAccounts()

    artist = users.initialize_user_account(algod_client)
    auctioneer = users.initialize_user_account(algod_client)
    bidder1 = users.initialize_user_account(algod_client)
    bidder2 = users.initialize_user_account(algod_client)


    table = Table(title="Wallets and assets")
    table.add_column("Person", justify="left", style="yellow1", no_wrap=True)
    table.add_column("Wallet", justify="center", style="green")
    table.add_column("Balances", justify="center", style="blue")

    table.add_row("Artist", artist.get_address(), str(artist.get_balance(algod_client)[0]))
    table.add_row("Auctioneer", auctioneer.get_address(), str(auctioneer.get_balance(algod_client)[0]))
    table.add_row("Bidder One", bidder1.get_address(), str(bidder1.get_balance(algod_client)[0]))
    table.add_row("Bidder Two", bidder2.get_address(), str(bidder2.get_balance(algod_client)[0]))

    print(table)

    print("[bold yellow1]\n\n Artist[green] creates a digital asset. An [purple4]NFT [green]worth thousands!")
    nft = artist.create_asset(algod_client)    
    print(f"[purple4] NFT [green]has been created by ID: [cyan]{nft} \n")  
    
    table = Table(title="Wallets and assets of Artist")
    table.add_column("Person", justify="left", style="yellow1", no_wrap=True)
    table.add_column("Wallet", justify="center", style="green")
    table.add_column("Algos", justify="center", style="blue")
    table.add_column("NFTs", justify="center", style="blue")
    
    table.add_row("Artist", artist.get_address(), str(artist.get_balance(algod_client)[0]), str(artist.get_balance(algod_client)[nft]))
    print(table)

    start_time = int(time()) + 10
    end_time = start_time + 120
    reserve = 1_000_000
    increment = 100_000

    print("[yellow1 bold]\n\n Artist [green]now wants to earn money by selling NFT and contacts [yellow1 bold]Auctioneer.")
    print(f"[yellow1 bold] Auctioneer [green]sets up an auction for NFT [cyan]{nft}.")
    # print(f"[yellow1 bold] Auctioneer Charges: [cyan]{reserve/2} [green]i.e.  half of the reserve amount for setting up the auction.")
   
    

    auction1 = Auction(
        client=algod_client,
        artist=artist,
        auctioneer=auctioneer,
        nft_id=nft,
        start_time=start_time,
        end_time=end_time,
        reserve=reserve,
        min_bid_increment=increment
    )

    app_id = auction1.init_auction()
      
    print(f"\n[white bold] Auction [green]has been created with id: [cyan]{app_id}.") 
    print(f" The [white]escrow [green]account has address: [cyan bold]{get_application_address(app_id)}\n\n")
    table = Table(title="Auction details")
    table.add_column("Auction attribute", justify="left", style="blue", no_wrap=True)
    table.add_column("Value", justify="center", style="bold blue", no_wrap=True)
    
    table.add_row("Start Time", str(datetime.fromtimestamp(start_time)) )
    table.add_row("End Time", str(datetime.fromtimestamp(end_time)) )
    table.add_row("Duration", str(int(end_time-start_time)/60)+" minute/s" )
    table.add_row("Reserve", str(reserve) )
    table.add_row("Minimum Bid Increment", str(increment) )
    print(table , "\n\n")

    table = Table(title="Wallets and assets")
    table.add_column("Person", justify="left", style="yellow1", no_wrap=True)
    table.add_column("Wallet", justify="center", style="green")
    table.add_column("Algos", justify="center", style="blue")
    table.add_column("NFT", justify="center", style="blue")


    table.add_row("Artist", artist.get_address(), str(artist.get_balance(algod_client)[0]), str(0 if len(artist.get_balance(algod_client)) < 2 else artist.get_balance(algod_client)[nft]))
    table.add_row("Auctioneer", auctioneer.get_address(), str(auctioneer.get_balance(algod_client)[0]), str(0 if len(auctioneer.get_balance(algod_client)) < 2 else auctioneer.get_balance(algod_client)[nft]))
    table.add_row("Bidder One", bidder1.get_address(), str(bidder1.get_balance(algod_client)[0]), str(0 if len(bidder1.get_balance(algod_client)) < 2 else bidder1.get_balance(algod_client)[nft]))
    table.add_row("Bidder Two", bidder2.get_address(), str(bidder2.get_balance(algod_client)[0]), str(0 if len(bidder2.get_balance(algod_client)) < 2 else bidder2.get_balance(algod_client)[nft]))
    table.add_row("Escrow Account", get_application_address(app_id), str(auction1.get_balance()[0]), str(0 if len(auction1.get_balance()) < 2 else auction1.get_balance()[nft]))

    print(table)
    auction1.finish_round()

    print(f"\n\n [yellow bold]Bidder One [green]wishes to bid [cyan]{int(reserve/3)} [green]for the asset. He thinks he can bid less than Reserve amount")
    if auction1.place_bid(
        bidder = bidder1,
        bid_amount = reserve/3,
    ):
        auction1.opt_in(bidder1)
    else:
        print("[blue bold ] Bid Failed. Bidder cannot Opt In for the asset transaction.")
    
    print("[green bold] Let's see the account details: ")
    table = Table(title="Wallets and assets")
    table.add_column("Person", justify="left", style="yellow1", no_wrap=True)
    table.add_column("Wallet", justify="center", style="green")
    table.add_column("Algos", justify="center", style="blue")
    table.add_column("NFT", justify="center", style="blue")
    table.add_row("Bidder One", bidder1.get_address(), str(bidder1.get_balance(algod_client)[0]), str(0 if len(bidder1.get_balance(algod_client)) < 2 else bidder1.get_balance(algod_client)[nft]))
    table.add_row("Bidder Two", bidder2.get_address(), str(bidder2.get_balance(algod_client)[0]), str(0 if len(bidder2.get_balance(algod_client)) < 2 else bidder2.get_balance(algod_client)[nft]))
    table.add_row("Escrow Account", get_application_address(app_id), str(auction1.get_balance()[0]), str(0 if len(auction1.get_balance()) < 2 else auction1.get_balance()[nft]))
    print(table)

    print(f"\n\n [yellow bold]Bidder Two [green]wishes to bid [cyan]{reserve/2} [green]for the asset. He thinks he can bid less than Reserve amount")
    if auction1.place_bid(
        bidder = bidder2,
        bid_amount = reserve/2,
    ):
        auction1.opt_in(bidder2)
    else:
        print("[blue bold ] Bid Failed. Bidder cannot Opt In for the asset transaction.")
    
    print("[green bold] Let's see the account details: ")
    table = Table(title="Wallets and assets")
    table.add_column("Person", justify="left", style="yellow1", no_wrap=True)
    table.add_column("Wallet", justify="center", style="green")
    table.add_column("Algos", justify="center", style="blue")
    table.add_column("NFT", justify="center", style="blue")
    table.add_row("Bidder One", bidder1.get_address(), str(bidder1.get_balance(algod_client)[0]), str(0 if len(bidder1.get_balance(algod_client)) < 2 else bidder1.get_balance(algod_client)[nft]))
    table.add_row("Bidder Two", bidder2.get_address(), str(bidder2.get_balance(algod_client)[0]), str(0 if len(bidder2.get_balance(algod_client)) < 2 else bidder2.get_balance(algod_client)[nft]))
    table.add_row("Escrow Account", get_application_address(app_id), str(auction1.get_balance()[0]), str(0 if len(auction1.get_balance()) < 2 else auction1.get_balance()[nft]))
    print(table)

    print("[bold yellow] Artist [green] feels that his work is not good and hence wants to close the auction.")
    auction1.close(artist)

    table = Table(title="Wallets and assets")
    table.add_column("Person", justify="left", style="yellow1", no_wrap=True)
    table.add_column("Wallet", justify="center", style="green")
    table.add_column("Algos", justify="center", style="blue")
    table.add_column("NFT", justify="center", style="blue")


    table.add_row("Artist", artist.get_address(), str(artist.get_balance(algod_client)[0]), str(0 if len(artist.get_balance(algod_client)) < 2 else artist.get_balance(algod_client)[nft]))
    table.add_row("Auctioneer", auctioneer.get_address(), str(auctioneer.get_balance(algod_client)[0]), str(0 if len(auctioneer.get_balance(algod_client)) < 2 else auctioneer.get_balance(algod_client)[nft]))
    table.add_row("Bidder One", bidder1.get_address(), str(bidder1.get_balance(algod_client)[0]), str(0 if len(bidder1.get_balance(algod_client)) < 2 else bidder1.get_balance(algod_client)[nft]))
    table.add_row("Bidder Two", bidder2.get_address(), str(bidder2.get_balance(algod_client)[0]), str(0 if len(bidder2.get_balance(algod_client)) < 2 else bidder2.get_balance(algod_client)[nft]))
    table.add_row("Escrow Account", get_application_address(app_id), str(auction1.get_balance()[0]), str(0 if len(auction1.get_balance()) < 2 else auction1.get_balance()[nft]))

    print(table)
    
    auction1.finish_round() 
     

demo()

