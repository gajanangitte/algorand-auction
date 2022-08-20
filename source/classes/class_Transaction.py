""" Contains the transaction class """

from base64 import b64decode
from typing import List, Dict, Any, Optional


class Transaction:
    """ The transaction class"""

    def __init__(self, response: Dict[str, Any] ):
        """ Constructor """
        self.pool_error: str = response["pool-error"]
        self.txn: Dict[str, Any] = response["txn"]

        self.application_index: Optional[int] = response.get("application-index")
        self.asset_index: Optional[int] = response.get("asset-index")
        self.global_state_delta: Optional[Any] = response.get("global-state-delta")
        self.local_state_delta: Optional[Any] = response.get("local-state-delta")
        self.receiver_rewards: Optional[int] = response.get("receiver-rewards")
        self.sender_rewards: Optional[int] = response.get("sender-rewards")
        self.close_rewards: Optional[int] = response.get("close-rewards")
        self.closing_amount: Optional[int] = response.get("closing-amount")
        self.confirmed_round: Optional[int] = response.get("confirmed-round")    
        self.inner_txns: List[Any] = response.get("inner-txns", [])
        self.logs: List[bytes] = [b64decode(l) for l in response.get("logs", [])]
