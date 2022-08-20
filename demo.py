""" Python module that runs demo """
from time import time
import os
from algosdk.logic import get_application_address

from source.utils.utils_account import initialize_algod_client
from source.classes.class_UserAccounts import UserAccounts
from source.classes.class_Auction import Auction

def demo() -> None:
    """ Runs demo for auction """

    os.system('clear')
    os.system('cls')
    print("Welcome to AlgoRand's NFT AUCTION! ")
    algod_client = initialize_algod_client()
    users = UserAccounts()

    artist = users.initialize_user_account(algod_client)
    auctioner = users.initialize_user_account(algod_client)
    bidder1 = users.initialize_user_account(algod_client)
    bidder2 = users.initialize_user_account(algod_client)

    print("Address of artist: " + artist.get_address())
    nft = artist.create_asset(algod_client)    
    print(f"ID of NFT: {nft}")
    print("Artist's balances:", artist.get_balance(algod_client), "\n")
    print("Auctioner's balances:", auctioner.get_balance(algod_client), "\n")


    start_time = int(time()) + 10
    end_time = start_time + 120
    reserve = 1_000_000
    increment = 100_000

    auction1 = Auction(
        client=algod_client,
        artist=artist,
        auctioner=auctioner,
        nft_id=nft,
        start_time=start_time,
        end_time=end_time,
        reserve=reserve,
        min_bid_increment=increment)

    app_id = auction1.init_auction()
    auction1.finish_round()
      
    print(f"Auction has been created with id: {app_id}. \n The escrow account has address: {get_application_address(app_id)}")
    print("Artist's balances:", artist.get_balance(algod_client), "\n")
    print("Auctioner's balances:", auctioner.get_balance(algod_client), "\n")
    print("Auction's balances:", auction1.get_balance(), "\n")
    print("Bidder1's balances:", bidder1.get_balance(algod_client), "\n")
    print("Bidder2's balances:", bidder2.get_balance(algod_client), "\n")

    auction1.place_bid(
        bidder = bidder1,
        bid_amount = 1000,
    )
    # auction1.opt_in(bidder1)
    print("Bidder1's balances:", bidder1.get_balance(algod_client), "\n")

    auction1.place_bid(
        bidder = bidder2,
        bid_amount = 100_000 
    )
    print("Bidder2's balances:", bidder2.get_balance(algod_client), "\n")


demo()
