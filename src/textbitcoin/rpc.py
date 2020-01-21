
import logging
import json

import requests


def call_rpc(rpcurl, method, params):
    payload = json.dumps({'method': method, 'params': params})
    headers = {'content-type': 'application/json', 'cache-control': 'no-cache'}
    try:
        response = requests.request("POST", rpcurl, data=payload, headers=headers)
        return json.loads(response.text)
    except requests.exceptions.RequestException:
        logging.error("Error!", exc_info=True)
    except:
        logging.error('No response from Wallet, check URL!', exc_info=True)
