# AUCTION APP

**_[A project developed for AlgoBharat hackathon.]_**

[View our demo video here](https://www.youtube.com/watch?v=0uZAVnnSSd8)

**Powered by Algorand's Sandbox and PyTeal library**

### Problem Statement 🎫
  
- [x] Build a smart contract for a simple auction.
- [x] The smart contract is initiated with a minimum bid amount and a time limit.
- [x] The contract keeps track of the owner’s wallet.
- [x] Any user can call the “bid” function with a bid amount.
- [x] If the bid amount is less than the minimum bid amount, the transaction fails.
- [x] If the bid amount is less than the previous highest bidder, the transaction fails.
- [x] Otherwise, the current bidder becomes the highest bidder and the bid amount for the previous highest bidder is returned to that bidder.
- [x] After the bid time limit has expired, no further bidding is permitted.
- [x] The owner (only) should be able to call the “close_bid” function to close the bidding and transfer the bid amount to the owner.



### Installation

The following commands are for `Ubuntu` distro.

0. You should have [Docker Desktop](https://www.docker.com/products/docker-desktop) installed on your system. Also you must have `Python`, `Pip` and `Virtualenv` installed on your system.

1. Open your terminal in the folder you wish to work in.
```bash
    mkdir $WORK_FOLDER && cd $WORK_FOLDER
    git clone https://github.com/algorand/sandbox sandbox
    cd sandbox
```

2. Open the `docker-compose.yml` file.
3. Locate `services.algod` and copy the following lines beneath ports.
    ```yml
    volumes:
      - type: bind
        source: /data
    ```
4. In your terminal, run the following command. It might take a few minutes to set up and configure the images and the sandbox.
```bash
    ./sandbox up
```

5. After the sandbox has been successfully created. Follow the commands to clone this repository
```bash
    cd ..
    git clone https://github.com/gajanangitte/algorand-auction
    cd algorand-auction
    virtualenv -p py .
    source bin/activate
    pip install -r requirements.txt
    python demo.py
    python demo2.py
```

### Enjoy your auction app!