import asyncio
import json
from langgraph_sdk import get_client

# 1. Define main() as async function
async def main():
    client = get_client(url="http://localhost:2024")
    
    data = {
        "customer": {
            "name": "John Smith",
            "email": "john.smith@example.com",
            "phoneNumber": "555-123-4567",
            "zipCode": "94105"
        },
        "task": {
            "description": "Kitchen renovation",
            "category": "Remodeling"
        },
        "vendor": {
            "name": "Bay Area Remodelers",
            "email": "contact@bayarearemodelers.com",
            "phoneNumber": "555-987-6543"
        }
    }
    
    print("Sending request...")
    
    # 2. Create thread (required for this SDK version)
    thread = await client.threads.create()

    run = await client.runs.create(
    assistant_id="contractor_workflow",
    thread_id=thread["thread_id"],
    input={
        "customer": data["customer"],
        "task": data["task"],
        "vendor": data["vendor"]
    }
    )
    
    print(f"Run ID: {run['run_id']}")
    
    # 4. Poll status
    while True:
        # 5. Use await INSIDE async function
        status = await client.runs.get(
            run_id=run["run_id"],
            thread_id=thread["thread_id"]
        )
        
        print(f"Status: {status['status']}")
        
        if status["status"] == "completed":
            print("Final Output:")
            print(json.dumps(status, indent=2))
            break
            
        await asyncio.sleep(1)

# 6. Use asyncio.run() entry point
if __name__ == "__main__":
    asyncio.run(main())
