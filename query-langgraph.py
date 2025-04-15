
""" 
- run the server
- run the workflow
- query the server - with this:
poetry run python query-langgraph.py

Run ID: 1f015775-662d-6346-b682-eadedfa13151
Started: 2025-04-09 19:17:55.709066
Outputs: {'customer': {'name': 'John Smith', 'email': 'john.smith@example.com', 'phoneNumber': '555-123-4567', 'zipCode': '94105'}, 'task': {'description': 'Kitchen renovation', 'category': 'Remodeling'}, 'vendor': {'name': 'Bay Area Remodelers', 'email': 'contact@bayarearemodelers.com', 'phoneNumber': '555-987-6543'}}
 """


import json
from langgraph_sdk import get_sync_client



# LangGraph server endpoint
BASE_URL = "http://127.0.0.1:2024"

def list_threads(client):
    threads = client.threads.list()
    print(f"Found {len(threads)} threads:")
    for thread in threads:
        print(f"Thread ID: {thread.get('id')}")
        print(f"Created: {thread.get('created_at')}")
        print(f"Modified: {thread.get('updated_at')}")
        print("---")

def list_runs(client):
    runs = client.runs.list()
    print(f"Found {len(runs)} runs:")
    for run in runs:
        print(f"Run ID: {run.get('id')}")
        print(f"Started: {run.get('start_time')}")
        print(f"Status: {run.get('status')}")
        print(f"Graph: {run.get('graph_id')}")
        if 'outputs' in run:
            print("Outputs:")
            print(json.dumps(run.get('outputs'), indent=2))
        print("---")

def main():
    # Initialize LangGraph SDK client
    client = get_sync_client(url=BASE_URL)

    # List threads and runs
    print("\nListing Threads:")
    list_threads(client)

    print("\nListing Runs:")
    list_runs(client)

if __name__ == "__main__":
    main()
