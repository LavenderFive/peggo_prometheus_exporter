import os
import requests
import time

from dotenv import load_dotenv
from prometheus_client import start_http_server, Gauge
from retry import retry

load_dotenv()
NODE_URL = os.getenv("NODE_URL")
ORCHESTRATOR_ADDR_STR = os.getenv("ORCHESTRATOR_ADDRESS")
ORCHESTRATOR_ADDR_ARRAY = ORCHESTRATOR_ADDR_STR.split(",") if ORCHESTRATOR_ADDR_STR else []
POLL_SECONDS = int(os.getenv("POLL_SECONDS"))
HTTP_PORT = int(os.getenv("HTTP_PORT"))

# Define a Gauge metric to track peggo event lag
PEGGO_EVENT_LAG = Gauge("peggo_event_lag", "Peggo event lag", ["orchestrator_address"])
PEGGO_NETWORK_NONCE = Gauge("peggo_network_nonce", "Injective network current peggo nonce")
PEGGO_ORCHESTRATOR_NONCE = Gauge("peggo_orchestrator_nonce", "Peggo orchestrator nonce", ["orchestrator_address"])
PEGGO_ORCHESTRATOR_BALANCE = Gauge(
    "peggo_orchestrator_balance", "Peggo orchestrator INJ balance", ["orchestrator_address"]
)


@retry(delay=10, tries=3)
def request_json(url: str) -> dict:
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    return {}


def process_request():
    peggo_state = request_json(f"{NODE_URL}/peggy/v1/module_state")

    if not peggo_state:
        return

    network_nonce = int(peggo_state["state"]["last_observed_nonce"])
    PEGGO_NETWORK_NONCE.set(network_nonce)

    for address in ORCHESTRATOR_ADDR_ARRAY:
        orchestrator_request = request_json(f"{NODE_URL}/peggy/v1/oracle/event/{address}")
        orchestrator_nonce = int(orchestrator_request["last_claim_event"]["ethereum_event_nonce"])

        inj_balance_request = request_json(f"{NODE_URL}/cosmos/bank/v1beta1/balances/{address}/by_denom?denom=inj")
        inj_balance = int(inj_balance_request["balance"]["amount"])
        inj_balance = float(inj_balance) / 10**18

        event_lag = network_nonce - orchestrator_nonce

        PEGGO_EVENT_LAG.labels(address).set(event_lag)
        PEGGO_ORCHESTRATOR_NONCE.labels(address).set(orchestrator_nonce)
        PEGGO_ORCHESTRATOR_BALANCE.labels(address).set(inj_balance)


def main():
    start_http_server(HTTP_PORT)

    while True:
        process_request()
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    print(f"Polling {NODE_URL} every {POLL_SECONDS} seconds")
    print(f"On port {HTTP_PORT}")
    print(f"Orchestator {ORCHESTRATOR_ADDR_STR}")

    main()
