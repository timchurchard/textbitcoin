# textbitcoin: Send and receive Bitcoin over SMS

textbitcoin is a custodial on-chain tipping bot for Bitcoin over SMS.  Using a bitcoin full node & wallet as backend.

## Warning

*Warning! This is a proof of concept! Do not use!*

If you are interested in this idea you can contact me through keybase or email tc@omg.log


### Quick start

Send an SMS to one of the numbers to get started.

UK - +447480776370

"INTRO" - Shows the help message with available commands.

"ADDR" - Shows your address

"BALANCE" - Shows your current balance and the Bitcoin price.

"SEND (amount 0.00123 or £1.23) to (Bitcoin address or phone number)" - Send Bitcoin


### Why

testbitcoin enables anyone to send and receive Bitcoin using any phone that can send SMS without the need for an app or internet connection.  Bitcoin is peer-to-peer electronic cash and the people that would benefit most may not have regular internet access.



### How it works

When the bot receives a message it checks the bitcoin full node for an address with a label matching the from number.  If no address exists it creates one.  If an address exists the balance can be checked or sent on to other addresses or phone numbers.


### Run locally / self hosting

Note: Install the [twilio CLI](https://www.twilio.com/docs/twilio-cli/quickstart)
Note: Install the [ngrok CLI](https://dashboard.ngrok.com/get-started)

```shell
python3 -m venv venv
. venv/bin/activate
python3 -m pip install -U setuptools pip
pip3 install -U -r requirements.txt
```

```shell
# Setup your twilio CLI
twilio profiles:create
twilio phone-numbers:update "+447000000000" --sms-url="http://localhost:5000/sms"
```

```shell
# Environment variables
B_RPC_URL   = URL to Bitcoin full node RPC http://user:pass@host:port/
B_SID       = Twilio Account SID
B_AUTH      = Twilio Account AUTH

# From the textbitcoin/src directory (TODO: Write setup.py)
python3 -m textbitcoin
```
