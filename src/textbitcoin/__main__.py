
import os
from sys import exit, stdout

import logging

from flask.logging import default_handler
from flask import Flask, request, redirect, jsonify, make_response

from .const import HEAD, ENV_B_SID, ENV_B_AUTH, ENV_B_RPC_URL
from .runner import Runner


runner = None

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/sms", methods=['GET', 'POST'])
def sms_ahoy_reply():
    global runner

    mfrom = request.form.get('From', None)
    mbody = request.form.get('Body', None)

    logging.info(f"message from {mfrom} with body '{mbody}'")  # todo: maybe don't do this?
    runner.submit(mfrom, mbody)

    return make_response('<Response></Response>', 200)


def load_env():
    assert ENV_B_SID in os.environ
    assert ENV_B_AUTH in os.environ
    assert ENV_B_RPC_URL in os.environ

    return {
        ENV_B_SID: os.environ[ENV_B_SID],
        ENV_B_AUTH: os.environ[ENV_B_AUTH],
        ENV_B_RPC_URL: os.environ[ENV_B_RPC_URL]
    }


def flask_thread():
    global app


def main():
    global runner
    global app

    logger = logging.getLogger()
    default_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    default_handler.setLevel(logging.DEBUG)
    logger.addHandler(default_handler)

    logging.info(HEAD)

    config = load_env()

    runner = Runner(config)
    runner.start()

    app.run(debug=True, use_reloader=False)

    runner.stop()


if __name__ == '__main__':
    exit(main())
