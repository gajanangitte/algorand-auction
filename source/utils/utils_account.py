""" This module contains util functions for algorand client and account """
from typing import List
from algosdk.v2client.algod import AlgodClient
from algosdk.kmd import KMDClient
from source.classes.class_UserAccount import UserAccount

ALGOD_ADDRESS = "http://localhost:4001"
KMD_ADDRESS = "http://localhost:4002"
TOKEN = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
KMD_WALLET_NAME = "unencrypted-default-wallet"
KMD_WALLET_PASSWORD = ""

def initialize_algod_client() -> AlgodClient:
    """ Initialize and return an AlgodClient """
    return AlgodClient(TOKEN, ALGOD_ADDRESS)

def initialize_kmd_client() -> KMDClient:
    """ Initialize a KMD Client"""
    return KMDClient(TOKEN, KMD_ADDRESS)


class GenesisAccounts:
    """ A class to maintain genesis accounts"""
    def __init__(self) -> None:
        """Constructor for Genesis Accounts """
        self.genesis_accounts: List(UserAccount) = []

    def get_genesis_accounts(self):
        """ Returns genesis accounts """
        if len(self.genesis_accounts) == 0:
            key_management_daemon = initialize_kmd_client()

            wallet_id = None
            for wallet in key_management_daemon.list_wallets():
                if wallet["name"] == KMD_WALLET_NAME:
                    wallet_id = wallet["id"]
                    break
            
            assert wallet_id is not None
            
            wallet_handle = key_management_daemon.init_wallet_handle(wallet_id, KMD_WALLET_PASSWORD)

            try:
                accounts_KMD = [ 
                    UserAccount(key_management_daemon.export_key(wallet_handle, KMD_WALLET_PASSWORD, address))
                    for address in key_management_daemon.list_keys(wallet_handle)
                ]
            finally:
                key_management_daemon.release_wallet_handle(wallet_handle)
        
            self.accounts = accounts_KMD
        return self.accounts