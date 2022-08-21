""" Python util lib for auction """

from base64 import b64decode
from typing import Any, Dict, List, Union



def decode_state(state_array: List[Any]) -> Dict[bytes, Union[int, bytes]]:
    """Decodes the state of auction"""
    state: Dict[bytes, Union[int, bytes]] = dict()

    for pair in state_array:
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