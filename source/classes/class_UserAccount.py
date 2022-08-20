""" Module with user account """

from typing import Any, Dict, List
from algosdk import account, mnemonic
from algosdk.v2client.algod import AlgodClient
from algosdk.future import transaction

from random import randint

from source.utils.utils_transactions import async_get_transaction

class UserAccount:
    """User Account Class"""
    secret = None

    def __init__(self, p_secret: str) -> None:
        self.secret = p_secret
        self.address = account.address_from_private_key(self.secret)
    
    def get_address(self) -> str:
        """Returns address"""
        return self.address
    
    def get_private_key(self) -> str:
        """Returns private key"""
        return self.secret

    def get_mnemonic(self) -> str:
        """Returns Mnemonic"""
        return mnemonic.from_private_key(self.secret)
    
    @classmethod 
    def get_object_from_mnemonic(cls, mem: str) -> "UserAccount":
        """ Returns account with specific mnemonic"""
        return cls(mnemonic.to_private_key(mem))

    def get_balance(self, client: AlgodClient) -> Dict[int,int]:
        """ Retrieve account balance """
        balance: Dict[int,int] = dict()

        account_info = client.account_info(self.get_address())

        balance[0] = account_info["amount"]

        assets: List[Dict[str, Any]] = account_info.get("assets", [])
        for asset in assets:
            asset_id = asset["asset-id"]
            amount = asset["amount"]
            balance[asset_id] = amount
        
        return balance

    def create_asset(self, client: AlgodClient) -> int:
        """ Lets the user create an asset"""
        asset_number = randint(0,999)
        asset_note = bytes(randint(0,255) for _ in range(20))

        asset_transaction = transaction.AssetCreateTxn(
            sender= self.get_address(),
            total=1,
            decimals=0,
            default_frozen=False,
            manager=self.get_address(),
            reserve=self.get_address(),
            freeze=self.get_address(),
            clawback=self.get_address(),
            unit_name=f"AU{asset_number}",
            asset_name=f"AN{asset_number}",
            url=f"https://www.google.com/search?q={asset_number}",
            note=asset_note,
            sp=client.suggested_params(),
        )
        signed_transaction = asset_transaction.sign(self.get_private_key())

        client.send_transaction(signed_transaction)

        response = async_get_transaction(client, signed_transaction.get_txid())
        assert response.asset_index is not None and response.asset_index > 0
        return response.asset_index
