
import logging

from threading import Lock
from time import monotonic
from random import seed, randint

from .const import (MSG_HELLO_NEW, MSG_INTRO, MSG_BALANCE, MSG_ADDR_LINK, MSG_SEND_CHECK,
                    MSG_NO_FUNDS, MSG_YES_WRONG, MSG_TX_LINK, DEFAULT_LANG, BLOCK_TARGET,
                    MSG_HELLO_RECV, SITE_URL)
from .rpc import call_rpc


class Session:

    def __init__(self, mfrom, addr, balance, rpcurl, smsqueue, new=False):
        self.__mfrom = mfrom
        self.__addr = addr
        self.__balance = balance
        self.__rpcurl = rpcurl
        self.__smsqueue = smsqueue

        self.__lock = Lock()
        self.__new = new
        self.__last_price = None
        self.__yes_dict = None

        seed(monotonic())

    def submit_price(self, price_usd, price_gbp, price_eur):
        with self.__lock:
            self.__last_price = {'usd': price_usd, 'gbp': price_gbp, 'eur': price_eur}

    def submit_message(self, mbody):
        if self.__new:
            self.__new = False
            self.__smsqueue.put({'to': self.__mfrom, 'body': MSG_HELLO_NEW[DEFAULT_LANG]})

        cmd = mbody.strip().lower()[:10]
        if cmd.startswith('intro'):
            self.__smsqueue.put({'to': self.__mfrom, 'body': MSG_INTRO[DEFAULT_LANG]})
        elif cmd.startswith('addr'):
            self.__send_addr()
        elif cmd.startswith('balance'):
            self.update_balance()
            self.__send_balance_changed()
        elif cmd.startswith('send'):
            self.__prepare_send(mbody)
        elif cmd.startswith('yes'):
            self.__attempt_send(mbody)
        elif cmd.startswith('no'):
            self.__yes_dict = None
        else:
            logging.warning("Unknown message: %s", mbody)

    def __listunspent(self):
        unspent = []
        # Note: Params min_conf, max_conf, list_addresses
        # https://bitcoincore.org/en/doc/0.17.0/rpc/wallet/listunspent/
        listunspent = call_rpc(self.__rpcurl, "listunspent", [0, 9999999, [self.__addr]])
        if listunspent:
            for result in listunspent['result']:
                if result['spendable'] or result['solvable']:
                    if result['label'] == self.__mfrom:  # todo: needed?
                        unspent.append(result)
        return unspent

    def update_balance(self):
        with self.__lock:
            bal, fiat = self.__unspent_to_bal_fiat()
            changed = self.__balance != bal
            self.__balance = bal
            if changed and self.__last_price is not None:
                self.__send_balance_changed()
            return self.__balance, changed

    def __unspent_to_bal_fiat(self, unspent=None):
        if unspent is None:
            unspent = self.__listunspent()
        bal = 0
        for result in unspent:
            bal += result['amount']

        fiat = None
        if self.__last_price is not None:
            fiat = self.__last_price['gbp'] * bal
        return bal, fiat

    def __send_balance_changed(self):
        gbp = "£%.02f" % (self.__last_price['gbp'] * self.__balance)
        self.__smsqueue.put({
            'to': self.__mfrom,
            'body': MSG_BALANCE[DEFAULT_LANG].format(self.__balance, gbp, "£%.02f" % self.__last_price['gbp'])
        })

    def __send_addr(self):
        self.__smsqueue.put({'to': self.__mfrom, 'body': MSG_ADDR_LINK[DEFAULT_LANG].format(self.__addr)})
        self.__smsqueue.put({'to': self.__mfrom, 'body': self.__addr})

    def __prepare_send(self, mbody):
        self.__yes_dict = None

        unspent = self.__listunspent()
        bal, fiat = self.__unspent_to_bal_fiat(unspent)

        parts = mbody.strip().split(' ')
        if 'send' in parts[0].lower():
            amount_in = 'bitcoin'
            if parts[1].lower().strip() == 'all':
                amount_in = 'all'
                amount = bal
                amount_other = fiat
            elif '£' in parts[1]:
                amount_in = 'gbp'
                amount = float(parts[1].strip('£'))
                amount_other = float('%.08f' % (amount / self.__last_price['gbp']))

                if fiat < amount:
                    self.__smsqueue.put({'to': self.__mfrom, 'body': MSG_NO_FUNDS[DEFAULT_LANG].format(bal, amount_other)})
                    return
            else:
                amount = float(parts[1])
                amount_other = '£%.02f' % (amount * self.__last_price['gbp'])
                if bal < amount:
                    self.__smsqueue.put({'to': self.__mfrom, 'body': MSG_NO_FUNDS[DEFAULT_LANG].format(bal, amount)})
                    return

            n = 2
            if parts[n].lower() == 'to':
                n = 3

            # TODO: validate phone number function
            send_in = 'bitcoin'
            send_to = None
            if parts[n].startswith('07') and len(parts[n]) == 11:
                send_in = 'phone'
                send_to = '+44' + parts[n][1:]
            elif parts[n].startswith('+447') and len(parts[n]) == 13:
                send_in = 'phone'
                send_to = parts[n]

            # TODO: validate bitcoin address function
            elif parts[n].startswith('bc1') or parts[n].startswith('1') or parts[n].startswith('3'):
                if len(parts[n]) > 10:
                    send_to = parts[n]

            else:
                # TODO: Unable to work out sender ?!
                return

            self.__yes_dict = {
                'code': randint(1000, 9999),
                'bal': bal,
                'amount_in': amount_in,
                'amount': amount,
                'amount_other': amount_other,
                'send_in': send_in,
                'send_to': send_to
            }
            self.__smsqueue.put({'to': self.__mfrom, 'body': MSG_SEND_CHECK[DEFAULT_LANG].format(
                amount, amount_in.upper(), amount_other, send_to, self.__yes_dict['code'])})

    def __attempt_send(self, mbody):
        if self.__yes_dict:
            if mbody.strip().lower() == f'yes {self.__yes_dict["code"]}':

                logging.critical("yes_dict %s", self.__yes_dict)

                # Note to self flow
                # - estimatesmartfee 12 -- {"result":{"feerate":0.00001000,"blocks":19}
                # - createrawtransaction (enough inputs to cover send, one output to target)
                # - fundrawtransaction hex {changeAddress: self, feeRate: estimate from above}
                # - dumpprivkey self.__addr -- To ensure only sending from own address !
                # - signrawtransactionwithkey hex [privkey]
                # - sendrawtransaction hex

                feerate = call_rpc(self.__rpcurl, 'estimatesmartfee', [BLOCK_TARGET])['result']['feerate']

                amount = 0
                target = feerate
                if self.__yes_dict['amount_in'] == 'all':
                    target = self.__balance - feerate
                    amount = self.__balance - feerate
                elif self.__yes_dict['amount_in'] == 'bitcoin':
                    target += self.__yes_dict['amount']
                    amount = self.__yes_dict['amount']
                else:
                    target += self.__yes_dict['amount_other']
                    amount += self.__yes_dict['amount_other']
                target = float('%.08f' % target)
                amount = float('%.08f' % amount)

                rawtrans = []
                tot = 0
                unspent = self.__listunspent()
                for tx in unspent:
                    if tot < target:
                        rawtrans.append({'txid': tx['txid'],'vout': tx['vout']})
                        tot += tx['amount']

                to_addr = self.__yes_dict['send_to']
                if self.__yes_dict['send_in'] == 'phone':
                    to_addr = self.__phone_to_address(self.__yes_dict['send_to'])

                rpcresult = call_rpc(self.__rpcurl, 'createrawtransaction', [rawtrans, {to_addr: amount}, 0, False])

                rawhex = rpcresult['result']
                if rawhex is None:
                    logging.critical("createraw got rpcresult %s", rpcresult)
                    return

                rpcresult = call_rpc(self.__rpcurl, 'fundrawtransaction', [rawhex, {'changeAddress': self.__addr, 'feeRate': feerate}])
                rawhex = rpcresult['result']['hex']

                rpcresult = call_rpc(self.__rpcurl, 'dumpprivkey', [self.__addr])
                privkey = rpcresult['result']

                rpcresult = call_rpc(self.__rpcurl, 'signrawtransactionwithkey', [rawhex, [privkey]])
                rawhex = rpcresult['result']['hex']

                rpcresult = call_rpc(self.__rpcurl, 'sendrawtransaction', [rawhex])
                logging.critical("sendraw got rpcresult %s", rpcresult)
                txid = rpcresult['result']

                self.__smsqueue.put({'to': self.__mfrom, 'body': MSG_TX_LINK[DEFAULT_LANG].format(txid)})

            else:
                self.__smsqueue.put({'to': self.__mfrom, 'body': MSG_YES_WRONG[DEFAULT_LANG]})
                self.__yes_dict = None

    def __phone_to_address(self, num):
        listrecvd = call_rpc(self.__rpcurl, 'listreceivedbyaddress', [0, True, False])
        if listrecvd:
            for result in listrecvd['result']:
                if result['label'] == num:
                    return result['address']
        call_rpc(self.__rpcurl, 'getnewaddress', [num, 'bech32'])  # todo: check result
        self.__smsqueue.put({'to': num, 'body': MSG_HELLO_RECV[DEFAULT_LANG].format(mfrom)})
        return self.__phone_to_address(num)
