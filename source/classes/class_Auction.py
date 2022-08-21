"""Auction python module"""
from typing import Any, Dict,  List
from time import sleep, time
from rich import print as rprint

from algosdk.v2client.algod import AlgodClient
from algosdk.future import transaction
from algosdk.logic import get_application_address
from algosdk import encoding, error


from source.classes.class_UserAccount import UserAccount
from source.classes.class_ContractCompiler import CompiledContracts
from source.utils.utils_transactions import async_get_transaction
from source.classes.class_Transaction import Transaction
from source.utils.utils_auction import decode_state

MIN_TRANSACTION_COST = 1000

class Auction:
    """Auction python module"""
    def __init__(self,
        client: AlgodClient,
        artist: UserAccount,
        auctioneer: UserAccount,
        nft_id: int,
        nft_amount: int = 1,
        start_time: int = int(time())+10,
        end_time: int = int(time()) + 130,
        reserve: int = 1_000_000,
        min_bid_increment: int = 100_000):
        """Constructor for auction"""

        self.client = client
        self.artist = artist
        self.auctioneer = auctioneer
        self.nft_id = nft_id
        self.nft_amount = nft_amount
        self.start_time = start_time
        self.end_time = end_time
        self.reserve = reserve
        self.min_bid_increment = min_bid_increment
        self.app_id = None
    
    def init_auction(self) -> int:
        """Returns id of newly created auction"""
        contracts = CompiledContracts(self.client)
        approval, clear = contracts.get_compiled_contracts()

        global_schema = transaction.StateSchema(num_uints=7, num_byte_slices=3)
        local_schema = transaction.StateSchema(num_uints=0, num_byte_slices=0)

        app_args = [
            encoding.decode_address(self.artist.get_address()),
            self.nft_id.to_bytes(8, "big"),
            self.start_time.to_bytes(8, "big"),
            self.end_time.to_bytes(8, "big"),
            self.reserve.to_bytes(8, "big"),
            self.min_bid_increment.to_bytes(8, "big"),
            encoding.decode_address(self.auctioneer.get_address()),
        ]

        auction_transaction =  transaction.ApplicationCreateTxn(
            sender=self.auctioneer.get_address(),
            on_complete=transaction.OnComplete.NoOpOC,
            approval_program=approval,
            clear_program=clear,
            global_schema=global_schema,
            local_schema=local_schema,
            app_args=app_args,
            sp=self.client.suggested_params(),
        )

        singed_transaction = auction_transaction.sign(self.auctioneer.get_private_key())

        self.client.send_transaction(singed_transaction)

        response = async_get_transaction(self.client, singed_transaction.get_txid())
        assert response.application_index is not None and response.application_index > 0

        app_id = response.application_index
        escrow_address = get_application_address(app_id)

        fund_cost = 3*MIN_TRANSACTION_COST + 2*self.min_bid_increment

        fund_auction_transaction = transaction.PaymentTxn(
            sender=self.auctioneer.get_address(),
            receiver=escrow_address,
            amt=fund_cost,
            sp=self.client.suggested_params()
        )

        hosting_transaction = transaction.ApplicationCallTxn(
            sender=self.auctioneer.get_address(),
            index=app_id,
            on_complete=transaction.OnComplete.NoOpOC,
            app_args=[b"fund"],
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
        
        singed_fund_auc_trans = fund_auction_transaction.sign(self.auctioneer.get_private_key())
        signed_hosting_transaction = hosting_transaction.sign(self.auctioneer.get_private_key())
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
        # print(timestamp, self.start_time)
        if timestamp > self.start_time + 1000:
            rich.print("[bold red] TIME SYNCHRONISATION ERROR. Reset the sandbox!\n")
            exit(1)
        if timestamp < self.start_time + 5:
            sleep(self.start_time + 5 - timestamp)

    def place_bid(
        self,
        bidder: UserAccount,
        bid_amount: int) -> bool:
        """ Places bid """
        try:  
            global_state_auction = decode_state(self.client.application_info(self.app_id)["params"]["global-state"])
            
            if any(global_state_auction[b"bid_account"]):
                current_highest_bidder = encoding.encode_address(global_state_auction[b"bid_account"])
                
                min_new_bid = global_state_auction[b"bid_amount"] + self.min_bid_increment 

            else:
                current_highest_bidder = None
            

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

            transaction.assign_group_id([ bid_transaction, return_bid_trans])
            signed_bid_transaction = bid_transaction.sign(bidder.get_private_key())
            signed_return_bid_trans = return_bid_trans.sign(bidder.get_private_key())

            self.client.send_transactions([signed_bid_transaction, signed_return_bid_trans])

            async_get_transaction(self.client, signed_bid_transaction.get_txid())
            return True
        except error.WrongAmountType:
            rprint("[red bold] Wrong amount input for bid")
        except error.AlgodHTTPError:
            global_state_auction = decode_state(self.client.application_info(self.app_id)["params"]["global-state"])
            min_new_bid = global_state_auction[b'bid_amount'] + self.min_bid_increment 
            rprint(f"[red bold] The proposed bid is smaller than the required bid amount, i.e. {min_new_bid}")
            
        return False
            

    def opt_in(self, bidder: UserAccount) -> Transaction :
        """Opts in the given transaction"""

        opt_in_transaction = transaction.AssetOptInTxn(
            sender=bidder.get_address(),
            index=self.nft_id,
            sp=self.client.suggested_params()
        )

        signed_opt_in = opt_in_transaction.sign(bidder.get_private_key())
        self.client.send_transaction(signed_opt_in)
        return async_get_transaction(self.client, signed_opt_in.get_txid())
    
    def close(self, transactor: UserAccount ):
        """Close an auction."""
        try:
            app_global_state = decode_state(self.client.application_info(self.app_id)["params"]["global-state"])

            accounts: List[str] = [encoding.encode_address(app_global_state[b"seller"])]

            if any(app_global_state[b'bid_account']):
                accounts.append(encoding.encode_address(app_global_state[b"bid_account"]))
            

            end_auction_transaction = transaction.ApplicationDeleteTxn(
                sender=transactor.get_address(),
                index = self.app_id,
                accounts=accounts,
                foreign_assets=[self.nft_id],
                sp=self.client.suggested_params()
            )
            signed_end_auction_transaction = end_auction_transaction.sign(transactor.get_private_key())
            self.client.send_transaction(signed_end_auction_transaction)

            async_get_transaction(self.client, signed_end_auction_transaction.get_txid())
            return True
        except error.AlgodHTTPError as exception:
            if not (transactor.get_address() ==  self.artist.get_address() or
                    transactor.get_address() ==  self.auctioneer.get_address()):

                rprint("[red bold] This close_bid transaction is not authorized. Only artist or auctioneer can close auctions.")
            else:
                if str(exception) == "application does not exist":
                    rprint("[red3 bold] The auction has already been closed.")
                else:
                    rprint(f"Error : {exception}")
        
        return False




        
        
