
HEAD = "textbitcoin: Bitcoin over SMS"

DEFAULT_LANG = 'en'

FROM_NUM = {
    'en': '+447480776370'
}

SITE_URL = 'https://timchurchard.github.io/textbitcoin'

ENV_B_RPC_URL = 'B_RPC_URL'
ENV_B_SID = 'B_SID'
ENV_B_AUTH = 'B_AUTH'

# How often (seconds) the price should be updated
PRICE_URL = 'https://api.coindesk.com/v1/bpi/currentprice.json'
PRICE_REFRESH = 60 * 60

# How often (seconds) the background thread should refresh balance for each wallet
BALANCE_REFRESH = 60 * 1

# block target for (estimatesmartfee)
BLOCK_TARGET = 1 + 18

MSG_HELLO_NEW = {
    'en': f'Welcome to textbitcoin! Send "INTRO" for all commands. See the quickstart here: {SITE_URL}\n\nThis bot is work in progress. DO NOT USE.'
}

MSG_HELLO_RECV = {
    'en': 'Hello! {} has sent you some Bitcoin using textbitcoin!'
}

MSG_INTRO = {
    'en': f'Commands:\n"ADDR" to see your Bitcoin address.\n\n"BALANCE" to get current wallet balance.\n\n"SEND (amount £1.23 or 0.0123 or ALL) to (address or phonenumber)" to send Bitcoin.'
}

MSG_BALANCE = {
    'en': 'Balance: {} BTC = {} @ {}'
}

MSG_ADDR_LINK = {
    'en': 'Your Bitcoin address can be seen on a blockchain explorer: https://www.blockchain.com/btc/address/{}'
}

MSG_TX_LINK = {
    'en': 'Transaction sent. https://www.blockchain.com/btc/tx/{}'
}

MSG_SEND_CHECK = {
    'en': 'Send {} {} ({}) to {} ? Reply "YES {}"'
}

MSG_NO_FUNDS = {
    'en': 'Unable to send.  Insufficient funds. {} < {}'
}

MSG_YES_WRONG = {
    'en': 'Wrong YES code. Resend the SEND message to try again.'
}
