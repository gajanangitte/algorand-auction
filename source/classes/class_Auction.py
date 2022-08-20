"""Auction python module"""
from typing import Any, Dict, Tuple, List
from time import sleep, time

from algosdk.v2client.algod import AlgodClient
from algosdk.future import transaction
from algosdk.logic import get_application_address
from algosdk import encoding


from source.classes.class_UserAccount import UserAccount
from source.utils.utils_auction import get_contracts, decode_state
from source.utils.utils_transactions import async_get_transaction

MIN_TRANSACTION_COST = 1000

class Auction:
    """Auction python module"""
    def __init__(self,
        client: AlgodClient,
        artist: UserAccount,
        auctioner: UserAccount,
        nft_id: int,
        nft_amount: int = 1,
        start_time: int = int(time())+10,
        end_time: int = int(time()) + 130,
        reserve: int = 1_000_000,
        min_bid_increment: int = 100_000):
        """Constructor for auction"""

        self.client = client
        self.artist = artist
        self.auctioner = auctioner
        self.nft_id = nft_id
        self.nft_amount = nft_amount
        self.start_time = start_time
        self.end_time = end_time
        self.reserve = reserve
        self.min_bid_increment = min_bid_increment
        self.app_id = None
    
    def init_auction(self) -> int:
        """Returns id of newly created auction"""
        approval, clear = get_contracts(self.client)

        global_schema = transaction.StateSchema(num_uints=7, num_byte_slices=2)
        local_schema = transaction.StateSchema(num_uints=0, num_byte_slices=0)

        app_args = [
            encoding.decode_address(self.artist.get_address()),
            self.nft_id.to_bytes(8, "big"),
            self.start_time.to_bytes(8, "big"),
            self.end_time.to_bytes(8, "big"),
            self.reserve.to_bytes(8, "big"),
            self.min_bid_increment.to_bytes(8, "big"),
        ]

        auction_transaction =  transaction.ApplicationCreateTxn(
            sender=self.auctioner.get_address(),
            on_complete=transaction.OnComplete.NoOpOC,
            approval_program=approval,
            clear_program=clear,
            global_schema=global_schema,
            local_schema=local_schema,
            app_args=app_args,
            sp=self.client.suggested_params(),
        )

        singed_transaction = auction_transaction.sign(self.auctioner.get_private_key())

        self.client.send_transaction(singed_transaction)

        response = async_get_transaction(self.client, singed_transaction.get_txid())
        assert response.application_index is not None and response.application_index > 0

        app_id = response.application_index
        escrow_address = get_application_address(app_id)

        setup_cost = 3*MIN_TRANSACTION_COST + 2*self.min_bid_increment

        fund_auction_transaction = transaction.PaymentTxn(
            sender=self.auctioner.get_address(),
            receiver=escrow_address,
            amt=setup_cost,
            sp=self.client.suggested_params()
        )

        hosting_transaction = transaction.ApplicationCallTxn(
            sender=self.auctioner.get_address(),
            index=app_id,
            on_complete=transaction.OnComplete.NoOpOC,
            app_args=[b"setup"],
            foreign_assets=[self.nft_id],
            sp=self.client.suggested_params()
        )

        nft_fund_transaction = transaction.AssetTransferTxn(
            sender=self.artist.get_address(),
            receiver=get_application_address(app_id),
            index=self.nft_id,
            amt=self.nft_amount,
            sp=self.client.suggested_params()
        )

        transaction.assign_group_id([fund_auction_transaction, hosting_transaction, nft_fund_transaction])        
        
        singed_fund_auc_trans = fund_auction_transaction.sign(self.auctioner.get_private_key())
        signed_hosting_transaction = hosting_transaction.sign(self.auctioner.get_private_key())
        singed_nft_fund_trans = nft_fund_transaction.sign(self.artist.get_private_key())
        
        self.client.send_transactions([singed_fund_auc_trans, signed_hosting_transaction, singed_nft_fund_trans])
        
        async_get_transaction(self.client, signed_hosting_transaction.get_txid())
        self.app_id = app_id
        return app_id

    def get_balance(self) -> Dict[int,int]:
        """ Retrieve account balance """
        balance: Dict[int,int] = dict()

        account_info = self.client.account_info(get_application_address(self.app_id))

        balance[0] = account_info["amount"]

        assets: List[Dict[str, Any]] = account_info.get("assets", [])
        for asset in assets:
            asset_id = asset["asset-id"]
            amount = asset["amount"]
            balance[asset_id] = amount
        
        return balance

    def finish_round(self) -> None:
        """Waits until round finishes"""
        status = self.client.status()
        last_round = status["last-round"]
        block = self.client.block_info(last_round)
        timestamp = block["block"]["ts"]
        if timestamp < self.start_time + 5:
            sleep(self.start_time + 5 - timestamp)

    def place_bid(
        self,
        bidder: UserAccount,
        bid_amount: int) -> None:
        """ Places bid """

        global_state_auction = decode_state(self.client.application_info(self.app_id)["params"]["global-state"])
        
        if any(global_state_auction[b"bid_account"]):
            current_highest_bidder = encoding.encode_address(global_state_auction[b"bid_account"])
            print("Current highest bidder: "+current_highest_bidder)
        else:
            current_highest_bidder = None
        

        print(global_state_auction)

        bid_transaction = transaction.PaymentTxn(
        sender=bidder.get_address(),
        receiver=get_application_address(self.app_id),
        amt=bid_amount,
        sp=self.client.suggested_params(),
        )

        return_bid_trans = transaction.ApplicationCallTxn(
            sender=bidder.get_address(),
            index=self.app_id,
            on_complete=transaction.OnComplete.NoOpOC,
            app_args=[b"bid"],
            foreign_assets=[self.nft_id],
            accounts=[current_highest_bidder] if current_highest_bidder is not None else [],
            sp=self.client.suggested_params(),
        )

        transaction.assign_group_id([return_bid_trans, bid_transaction])
        signed_bid_transaction = bid_transaction.sign(bidder.get_private_key())
        signed_return_bid_trans = return_bid_trans.sign(bidder.get_private_key())

        self.client.send_transactions([signed_return_bid_trans, signed_bid_transaction])

        async_get_transaction(self.client, bid_transaction.get_txid())