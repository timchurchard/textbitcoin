ARG PYTHON_VERSION=3.7

FROM python:${PYTHON_VERSION}-buster

WORKDIR /app
COPY requirements.txt /app
COPY src/textbitcoin /app/textbitcoin

RUN python3 -m venv venv && \
    ./venv/bin/python3 -m pip install --no-cache-dir -U setuptools pip && \
    ./venv/bin/pip3 install --no-cache-dir -U -r requirements.txt

RUN groupadd -r textbitcoin && \
    useradd -r -s /bin/false -g textbitcoin textbitcoin

USER textbitcoin

ENV B_RPC_URL=""
ENV B_SID=""
ENV B_AUTH=""

CMD ["./venv/bin/python3", "-m", "textbitcoin"]
