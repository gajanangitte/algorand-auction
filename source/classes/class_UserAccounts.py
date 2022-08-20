""" Module containing useraccount and related functions """

from time import clock_settime
from typing import List
from algosdk.future import transaction
from algosdk.v2client.algod import AlgodClient

from source.utils.utils_account import GenesisAccounts
from source.utils.utils_transactions import async_get_transaction
from .class_UserAccount import UserAccount
from algosdk import account, mnemonic

MAX_ACCOUNTS_GENERATED = 8

class UserAccounts:
    """User Account Management Class"""

    def __init__(self) -> None:
        """Constructor for user accounts"""
        self.user_accounts: List[UserAccount] = []

    def initialize_user_account(self, client: AlgodClient) -> None:
        """Initialize a new user account """
        if len(self.user_accounts) == 0:
            self.user_accounts = [ UserAccount(account.generate_account()[0]) for i in range(MAX_ACCOUNTS_GENERATED)]

            genesis_accounts = GenesisAccounts()
            genesisaccount_list = genesis_accounts.get_genesis_accounts()

            transactions: List[transaction.Transaction] = []
            
            
            for i, a in enumerate(self.user_accounts): 
                funding_account = genesisaccount_list[i % len(genesisaccount_list) ]
                transactions.append(transaction.PaymentTxn(
                    sender = funding_account.get_address(),
                    receiver = a.get_address(),
                    amt = 10000000,
                    sp = client.suggested_params()
                ))

            signed_transactions = [
                transaction.sign(genesisaccount_list[i%len(genesisaccount_list)].get_private_key())
                for i, transaction in enumerate(transaction.assign_group_id(transactions))
            ]
            client.send_transactions(signed_transactions)

            async_get_transaction(client, signed_transactions[0].get_txid())
    
        return self.user_accounts.pop()
 