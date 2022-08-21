from pyteal import *


def clear_state_program():
    """Clear state program method"""
    return Approve()

def approval_program():
    """ approval_program method 

        App args:

        start_time = Auction's start time
        end_time = Auction's end time
        seller_addr = The artist's address
        nft_id = The ID of the NFT
        reserve_amount = The minimum amount that artist wants
        min_bid_increment = The minimum amount that should exceed previous bid
        current_high_bid_amount = The current highest bid amount
        current_high_bid_account = The address of current highest bidder
    """

    start_time = Bytes("start")
    end_time = Bytes("end")
    seller_addr = Bytes("seller")
    nft_id = Bytes("nft_id")
    reserve_amount = Bytes("reserve_amount")
    min_bid_increment = Bytes("min_bid_inc")
    current_high_bid_amount = Bytes("bid_amount")
    current_high_bid_account = Bytes("bid_account")
    creator_addr = Bytes("creator")

    @Subroutine(TealType.none)
    def repay_previous_highest_bidder(prev_high_bidder: Expr, prev_high_bid_amount: Expr) -> Expr:
        """ This method repays the last bidder"""
        return Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.Payment,
                    TxnField.amount: prev_high_bid_amount - Global.min_txn_fee(),
                    TxnField.receiver: prev_high_bidder,
                }
            ),
            InnerTxnBuilder.Submit(),
        )

    @Subroutine(TealType.none)
    def transfer_nft(asset_id: Expr, account: Expr) -> Expr:
        """ Transfers a given nft to the given account """
        asset_holding = AssetHolding.balance(
            Global.current_application_address(), asset_id
        )
        return Seq(
            asset_holding,
            If(asset_holding.hasValue()).Then(
                Seq(
                    InnerTxnBuilder.Begin(),
                    InnerTxnBuilder.SetFields(
                        {
                            TxnField.type_enum: TxnType.AssetTransfer,
                            TxnField.xfer_asset: asset_id,
                            TxnField.asset_close_to: account,
                        }
                    ),
                    InnerTxnBuilder.Submit(),
                )
            ),
        )

    @Subroutine(TealType.none)
    def settle_balances(seller_account: Expr) -> Expr:
        """ this method is called to pay the auctioneer and the artist their money

            auctioneer: they gets half of the reverse money
            artist: they get the remaining amount or remainder
        """
        return If(Balance(Global.current_application_address()) != Int(0)).Then(
            Seq(
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.Payment,
                        TxnField.close_remainder_to: seller_account,
                    }
                ),
                InnerTxnBuilder.Submit(),
            )
        )
    
    @Subroutine(TealType.none)
    def pay_auctioneer(creator: Expr, fee: Expr) -> Expr:
        """ this method is called to pay the auctioneer and the artist their money

            auctioneer: they gets half of the reverse money
            artist: they get the remaining amount or remainder
        """
        return Seq(
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.Payment,
                    TxnField.amount: fee - Global.min_txn_fee(),
                    TxnField.receiver: creator,
                }
            ),
            InnerTxnBuilder.Submit(),
        )


    #  We place values in the earlier defined variables

    on_create = Seq(
        Assert(
              Btoi(Txn.application_args[2]) < Btoi(Txn.application_args[3])
        ),
        App.globalPut(seller_addr, Txn.application_args[0]),
        App.globalPut(nft_id, Btoi(Txn.application_args[1])),
        App.globalPut(start_time, Btoi(Txn.application_args[2])),
        App.globalPut(end_time, Btoi(Txn.application_args[3])),
        App.globalPut(reserve_amount, Btoi(Txn.application_args[4])),
        App.globalPut(min_bid_increment, Btoi(Txn.application_args[5])),
        App.globalPut(creator_addr, Txn.application_args[6]),
        App.globalPut(current_high_bid_account, Global.zero_address()),
        Approve(),
    )

    on_fund = Seq(
        Assert(Global.latest_timestamp() < App.globalGet(start_time)),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: App.globalGet(nft_id),
                TxnField.asset_receiver: Global.current_application_address(),
            }
        ),
        InnerTxnBuilder.Submit(),
        Approve(),
    )

    transaction_index = Txn.group_index() - Int(1)
    asa_holdings = AssetHolding.balance(
        Global.current_application_address(), App.globalGet(nft_id)
    )
    on_bid = Seq(
        asa_holdings,
        Assert(
            And(
                # Check if the bidding is open
                App.globalGet(start_time) <= Global.latest_timestamp(),
                Global.latest_timestamp() < App.globalGet(end_time),

                # check for the sender receiver
                Gtxn[transaction_index].sender() == Txn.sender(),
                Gtxn[transaction_index].receiver() == Global.current_application_address(),

                # payment
                Gtxn[transaction_index].type_enum() == TxnType.Payment,
                Gtxn[transaction_index].amount() >= Global.min_txn_fee(),
                # Gtxn[transaction_index].amount() >= App.globalGet(reserve_amount),
            )
        ),
        Seq(
                If(App.globalGet(current_high_bid_account) != Global.zero_address()).Then(
                    Seq(
                    Assert(
                        Gtxn[transaction_index].amount() >= App.globalGet(current_high_bid_amount) + App.globalGet(min_bid_increment)
    
                    ),
                    repay_previous_highest_bidder(
                        App.globalGet(current_high_bid_account),
                        App.globalGet(current_high_bid_amount),
                    )
                    )
                ),
                # update the new highest bid and bidder
                App.globalPut(current_high_bid_amount, Gtxn[transaction_index].amount()),
                App.globalPut(current_high_bid_account, Gtxn[transaction_index].sender()),
                Approve(),
        ),
        Reject(),
    )

    # !complicated
    on_delete = Seq(
        # the closer must be artist or the auctioneer
        Assert(
            Or(
                # sender must either be the seller or the auction creator
                Txn.sender() == App.globalGet(seller_addr),
                Txn.sender() == Global.creator_address(),
            )
        ),
        # if the auction has not yet started
        If(Global.latest_timestamp() < App.globalGet(start_time)).Then(
            Seq(
                # send algos and nft
                transfer_nft(App.globalGet(nft_id), App.globalGet(seller_addr)),
                settle_balances(App.globalGet(seller_addr)),
                Approve(),
            )
        ),
        # Auction has started      
        If(App.globalGet(start_time) <= Global.latest_timestamp()
            ).Then(
                Seq(
                    # We have a maximum bidder with bid 
                    If(App.globalGet(current_high_bid_account) != Global.zero_address())
                    .Then(
                        transfer_nft(
                            App.globalGet(nft_id),
                            App.globalGet(current_high_bid_account),
                        )
                    )
                    .Else(
                        transfer_nft(App.globalGet(nft_id), App.globalGet(seller_addr))
                    ),
                    # pay_auctioneer(App.globalGet(creator_addr), App.globalGet(min_bid_increment)),
                    settle_balances(App.globalGet(seller_addr)),
                    Approve(),
                )
            ),
        Reject(),
    )

    return Cond(
        # default create transaction
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.NoOp, Cond(
            # funding the escrow account by the auctioneer
            [Txn.application_args[0] == Bytes("fund"), on_fund],
            # the bid that is made by bidders goes here
            [Txn.application_args[0] == Bytes("bid"), on_bid],
        )],
        [   
            # closing the escrow
            Txn.on_completion() == OnComplete.DeleteApplication,
            on_delete,
        ],
        [
            Or(
                # Opt In and Close out is handled differently. Not for application. but for NFT
                Txn.on_completion() == OnComplete.OptIn,
                Txn.on_completion() == OnComplete.CloseOut
            ),
            Reject(),
        ],
        [
            # TODO: no option provided for now
            Txn.on_completion() == OnComplete.UpdateApplication,
            Reject()
        ]
    )


if __name__ == "__main__":
    with open("contract_approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=5)
        f.write(compiled)

    with open("contract_clear_state.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=5)
        f.write(compiled)
