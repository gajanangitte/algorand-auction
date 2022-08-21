""" Module that keeps compiled contracts """

from base64 import b64decode
from typing import Tuple
from algosdk.v2client.algod import AlgodClient
from pyteal import compileTeal, Mode, Expr

from source.contracts import approval_program, clear_state_program


class CompiledContracts:
    """ Class that keeps compiled contracts """
    
    def __init__(self,client: AlgodClient):
        self.client = client
        self.approval_program = None
        self.clear_state_program = None
    
    def get_compiled_contracts(self)-> Tuple[bytes, bytes]:
        """ Get compiled contracts"""

        if self.approval_program is None or self.clear_state_program is None:
            self.approval_program = self.compile_contracts(approval_program())
            self.clear_state_program = self.compile_contracts(clear_state_program())
        
        return self.approval_program, self.clear_state_program

    def compile_contracts(self,contract: Expr) -> bytes:
        """ Compiles contracts and returns them """
        teal = compileTeal(contract, mode=Mode.Application, version=5)
        response = self.client.compile(teal)
        return b64decode(response["result"])