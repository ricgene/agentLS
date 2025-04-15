# workflow.py
from typing import TypedDict
from langgraph.graph import StateGraph, END
import os
from langsmith.run_helpers import traceable

# Set environment variables for LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "prizm-workflow"

# 1. State Definition
class WorkflowState(TypedDict):
    customer: dict
    task: dict
    vendor: dict
    summary: str  # Added during processing

# 2. Node Implementations
@traceable(project_name="prizm-workflow")
def validate_input(state: WorkflowState):
    required_fields = {
        "customer": ["name", "email", "phoneNumber", "zipCode"],
        "task": ["description", "category"],
        "vendor": ["name", "email", "phoneNumber"]
    }
    
    for section, fields in required_fields.items():
        if section not in state:
            raise ValueError(f"Missing {section} data")
        for field in fields:
            if field not in state[section]:
                raise ValueError(f"Missing {field} in {section}")
    return state

@traceable(project_name="prizm-workflow")
def process_data(state: WorkflowState):
    summary = (
        f"New {state['task']['category']} project for {state['customer']['name']} "
        f"({state['customer']['zipCode']}) assigned to {state['vendor']['name']}"
    )
    return {"summary": summary}

@traceable(project_name="prizm-workflow")
def format_output(state: WorkflowState):
    return {
        "customer_email": state["customer"]["email"],
        "vendor_email": state["vendor"]["email"],
        "project_summary": state["summary"]
    }

# 3. Graph Setup
workflow = StateGraph(WorkflowState)
workflow.add_node("validate", validate_input)
workflow.add_node("process", process_data)
workflow.add_node("format", format_output)

workflow.add_edge("validate", "process")
workflow.add_edge("process", "format")
workflow.add_edge("format", END)

workflow.set_entry_point("validate")

# First compile the workflow
app = workflow.compile()
# Then wrap it with the traceable decorator
#app = traceable(app, project_name="prizm-workflow")

# 4. Test Execution
if __name__ == "__main__":
    input_data = {
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

    result = app.invoke(input_data)
    print("Final Output:", result)