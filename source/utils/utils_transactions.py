""" A transaction utility class """
from algosdk.v2client.algod import AlgodClient

from source.classes.class_Transaction import Transaction

def async_get_transaction(
    client: AlgodClient, 
    transaction_id: str, 
    timeout: int = 10) -> Transaction:
    """ Waits for a transaction amd executes it"""
    client_status = client.status()
    last_round = client_status["last-round"]
    start_round = last_round

    while last_round < timeout + start_round:
        last_round += 1
        pending_trans = client.pending_transaction_info(transaction_id)

        if pending_trans.get("confirmed-round", 0) > 0:
            return Transaction(pending_trans)     
        if pending_trans["pool-error"]:
            error = pending_trans["pool-error"]
            raise Exception(f"Pool Error: {error}")

        client_status = client.status_after_block(last_round)
    raise Exception(f"Transaction with ID: {transaction_id} not confirmed after {timeout} rounds")
