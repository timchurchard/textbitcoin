
import logging

from time import sleep

from threading import Thread, Event, Lock
from queue import Queue, Empty

import requests

from twilio.rest import Client

from .const import DEFAULT_LANG, FROM_NUM
from .const import PRICE_URL, PRICE_REFRESH
from .const import BALANCE_REFRESH
from .const import ENV_B_SID, ENV_B_AUTH, ENV_B_RPC_URL
from .rpc import call_rpc
from .session import Session


class Runner:

    def __init__(self, config):
        self.__config = config

        self.__twclient = Client(config[ENV_B_SID], config[ENV_B_AUTH])
        self.__smsqueue = Queue()
        self.__stop = Event()
        self.__sessions_lock = Lock()

        # Dictionary of sessions by from number.  Not ideal but messages need to be routed.
        self.__sessions = {}

        # Dictionary of price data
        self.__last_price = {}

    def start(self):
        Thread(target=self.__fetch_price_thread).start()
        sleep(1)
        self.__load_sessions(new=False)
        Thread(target=self.__notice_balance_thread).start()
        Thread(target=self.__outgoing_sms_thread).start()

    def stop(self):
        self.__stop.set()

    def submit(self, mfrom, mbody):
        if mfrom not in self.__sessions:
            # Note: params label, address_type
            # https://bitcoincore.org/en/doc/0.17.0/rpc/wallet/getnewaddress/
            call_rpc(self.__config[ENV_B_RPC_URL], 'getnewaddress', [mfrom, 'bech32'])  # todo: check result
            self.__load_sessions(new=True)
        # 
        # TODO: error checking here ?!
        # 
        self.__sessions[mfrom].submit_message(mbody)

    def __load_sessions(self, new=False):
        # Note: params min_conf, include_empty, include_watchonly
        # https://bitcoincore.org/en/doc/0.17.0/rpc/wallet/listreceivedbyaddress/
        listrecvd = call_rpc(self.__config[ENV_B_RPC_URL], 'listreceivedbyaddress', [0, True, False])
        if listrecvd:
            with self.__sessions_lock:
                for result in listrecvd['result']:
                    if result['label'].startswith('+'):  # TODO: Assume this is a from +NUM we've created!
                        if result['label'] not in self.__sessions:
                            self.__sessions[result['label']] = Session(result['label'], result['address'], result['amount'], self.__config[ENV_B_RPC_URL], self.__smsqueue, new)
                            self.__sessions[result['label']].submit_price(
                                self.__last_price['bpi']['USD']['rate_float'],
                                self.__last_price['bpi']['GBP']['rate_float'],
                                self.__last_price['bpi']['EUR']['rate_float'])

    def __fetch_price_thread(self):
        while not self.__stop.is_set():
            rsp = requests.get(PRICE_URL)
            self.__last_price = rspjson = rsp.json()
            with self.__sessions_lock:
                for mfrom, s in self.__sessions.items():
                    s.submit_price(
                        rspjson['bpi']['USD']['rate_float'],
                        rspjson['bpi']['GBP']['rate_float'],
                        rspjson['bpi']['EUR']['rate_float'])
            self.__stop.wait(timeout=PRICE_REFRESH)

    def __notice_balance_thread(self):
        while not self.__stop.is_set():
            with self.__sessions_lock:
                for mfrom, s in self.__sessions.items():
                    s.update_balance()
            self.__stop.wait(timeout=BALANCE_REFRESH)

    def __outgoing_sms_thread(self):
        while not self.__stop.is_set():
            try:
                qmsg = self.__smsqueue.get(timeout=5)
            except Empty:
                continue
            if qmsg:
                self.__twclient.messages.create(
                    body=qmsg['body'],
                    from_=FROM_NUM[DEFAULT_LANG],
                    to=qmsg['to'])
