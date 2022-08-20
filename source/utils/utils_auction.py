""" Python util lib for auction """

from base64 import b64decode
from typing import Any, Dict, List, Tuple, Union
from algosdk.v2client.algod import AlgodClient
from algosdk.future import transaction
from algosdk import encoding
from pyteal import compileTeal, Mode, Expr

from source.classes.class_UserAccount import UserAccount
from source.contracts import approval_program, clear_state_program

from .utils_transactions import async_get_transaction


APPROVAL_PROGRAM = b""
CLEAR_STATE_PROGRAM = b""

def compile_contracts(client: AlgodClient, contract: Expr) -> bytes:
    """ Compiles contracts and returns them """
    teal = compileTeal(contract, mode=Mode.Application, version=5)
    response = client.compile(teal)
    return b64decode(response["result"])

def get_contracts(client: AlgodClient) -> Tuple[bytes, bytes]:
    """ Returns the pyteal contracts """
    global APPROVAL_PROGRAM
    global CLEAR_STATE_PROGRAM

    if len(APPROVAL_PROGRAM) == 0:
        APPROVAL_PROGRAM = compile_contracts(client, approval_program())
        CLEAR_STATE_PROGRAM = compile_contracts(client, clear_state_program())

    return APPROVAL_PROGRAM, CLEAR_STATE_PROGRAM

def decode_state(stateArray: List[Any]) -> Dict[bytes, Union[int, bytes]]:
    """Decodes the state of auction"""
    state: Dict[bytes, Union[int, bytes]] = dict()

    for pair in stateArray:
        key = b64decode(pair["key"])

        value = pair["value"]
        valueType = value["type"]

        if valueType == 2:
            # value is uint64
            value = value.get("uint", 0)
        elif valueType == 1:
            # value is byte array
            value = b64decode(value.get("bytes", ""))
        else:
            raise Exception(f"Unexpected state type: {valueType}")

        state[key] = value

    return state
    