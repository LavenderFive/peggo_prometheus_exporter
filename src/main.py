import os
from prometheus_client import start_http_server, Gauge
import time
import requests
from dotenv import load_dotenv

load_dotenv()
NODE_URL = os.getenv('NODE_URL')
ORCHESTRATOR_ADDR = os.getenv('ORCHESTRATOR_ADDRESS')
POLL_SECONDS = int(os.getenv('POLL_SECONDS'))
HTTP_PORT = int(os.getenv('HTTP_PORT'))

# Define a Gauge metric to track peggo event lag
PEGGO_EVENT_LAG = Gauge('peggo_event_lag', 'Peggo event lag')
PEGGO_NETWORK_NONCE = Gauge('peggo_network_nonce', 'Injective network current peggo nonce')
PEGGO_ORCHESTRATOR_NONCE = Gauge('peggo_orchestrator_nonce', 'Peggo orchestrator nonce')

def process_request():
    node_addr = NODE_URL

    r = requests.get(f'{node_addr}/peggo/v1/module_state')
    network_nonce = int(r.json()['state']['last_observed_nonce'])

    r = requests.get(f'{node_addr}/peggo/v1/oracle/event/{ORCHESTRATOR_ADDR}')
    orchestrator_nonce = int(r.json()['last_claim_event']['ethereum_event_nonce'])

    event_lag = network_nonce - orchestrator_nonce

    PEGGO_EVENT_LAG.set(event_lag)
    PEGGO_NETWORK_NONCE.set(network_nonce)
    PEGGO_ORCHESTRATOR_NONCE.set(orchestrator_nonce)

def main():
    start_http_server(HTTP_PORT)

    while True:
        process_request()
        time.sleep(POLL_SECONDS)

if __name__ == '__main__':
    print(f'Polling {NODE_URL} every {POLL_SECONDS} seconds')
    print(f'On port {HTTP_PORT}')
    print(f'Orchestator {ORCHESTRATOR_ADDR}')

    main()
