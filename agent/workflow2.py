# workflow2.py
from dotenv import load_dotenv
load_dotenv()
from typing import TypedDict, Dict, Any, List, Annotated
from langgraph.graph import StateGraph, END
import os
from langsmith.run_helpers import traceable
import json
import random
from datetime import datetime
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langgraph.graph import add_messages
from functools import lru_cache
from langchain_openai import ChatOpenAI
import openai
# Set environment variables for local LangGraph tracing
#os.environ["LANGCHAIN_TRACING_V2"] = "true"
#os.environ["LANGCHAIN_PROJECT"] = "prizm-workflow-2"
if os.environ.get("LOCAL_LANGGRAPH_SERVER"):
    LANGCHAIN_ENDPOINT = os.environ["LANGCHAIN_ENDPOINT_LOCAL"]  # Use local LangGraph server
    #os.environ["LANGCHAIN_API_KEY"] = ""  # Empty API key for local server
else:
    LANGCHAIN_ENDPOINT = os.environ["LANGCHAIN_ENDPOINT_CLOUD"]


LANGCHAIN_API_KEY = os.environ["LANGCHAIN_API_KEY"]
LANGSMITH_API_KEY = os.environ["LANGSMITH_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# Default to False if not set
MOCK_USER_RESPONSES = os.environ.get("MOCK_USER_RESPONSES", "False").lower() == "true"
MOCK_SENTIMENT_ANALYSIS = os.environ.get("MOCK_SENTIMENT_ANALYSIS", "False").lower() == "true"

# Global variables to control mocking behavior
#MOCK_USER_RESPONSES = os.environ["MOCK_USER_RESPONSES"]  # Set to False for real user interaction
#MOCK_SENTIMENT_ANALYSIS = os.environ["MOCK_SENTIMENT_ANALYSIS"]  # Set to False for real LLM sentiment analysis

# Define mock user responses
POSITIVE_RESPONSES = [
    "Yes, I'll contact them tomorrow. Thanks!",
    "Sounds great, I'll reach out to them right away.",
    "Perfect timing, I was just looking for someone like this!"
]

NEGATIVE_RESPONSES = [
    "I'm a bit concerned about the budget. Can we discuss this further?",
    "I'm not sure if I can afford this right now.",
    "I have some concerns about the timeline. Can they start next month instead?"
]

# 1. Enhanced State Definition
class WorkflowState(TypedDict):
    customer: dict
    task: dict
    vendor: dict
    summary: str  # Added during processing
    messages: Annotated[List[BaseMessage], add_messages]  # For conversation tracking
    sentiment: str  # For tracking customer sentiment
    reason: str  # For storing sentiment reason
    current_step: str  # For tracking workflow progress
    sentiment_attempts: int  # For tracking sentiment analysis attempts

# Step 1: Initialize Models (from your example)
@lru_cache(maxsize=4)
def _get_model(model_name: str, system_prompt: str = None):
    if model_name == "openai":
        model = ChatOpenAI(temperature=0, model_name="gpt-4o")
    else:
        raise ValueError(f"Unsupported model type: {model_name}")
    
    if system_prompt:
        model = model.bind(system_message=system_prompt)
    
    # I'm omitting the tools binding since we don't have the tools import
    # model = model.bind_tools(tools)
    return model

# 2. Node Implementations
@traceable(project_name="prizm-workflow-2")
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
    
    # Initialize workflow tracking fields if not present
    if "current_step" not in state:
        state["current_step"] = "initialize_state"
    if "messages" not in state:
        state["messages"] = []
    if "sentiment" not in state:
        state["sentiment"] = ""
    if "reason" not in state:
        state["reason"] = ""
    if "sentiment_attempts" not in state:
        state["sentiment_attempts"] = 0
        
    return state

@traceable(project_name="prizm-workflow-2")
def initialize_state(state: WorkflowState):
    """Initialize the agent state with customer, task, and vendor information"""
    # The validate_input function has already validated the required fields
    # Just update the current step
    return {
        "current_step": "initial_prompt"
    }

@traceable(project_name="prizm-workflow-2")
def generate_initial_prompt(state: WorkflowState):
    """Generate the initial prompt for customer interaction"""
    customer = state["customer"]
    task = state["task"]
    vendor = state["vendor"]
    
    # Construct the greeting message
    greeting = f"""Congratulations on your new {task['category']} Task! I'm here to assist you. We have found an excellent vendor, {vendor['name']}, to perform this task. Can you reach out to them today or tomorrow?"""
    
    # Add the greeting as a system message
    system_prompt = f"""You are an AI concierge helping customers connect with vendors for their projects.
Generate a follow-up message based on the customer's response.
Be friendly and professional.

Customer details: {json.dumps(customer, indent=2)}
Task details: {json.dumps(task, indent=2)}
Vendor details: {json.dumps(vendor, indent=2)}"""
    
    # Add the messages
    messages = [
        SystemMessage(content=system_prompt),
        AIMessage(content=greeting)
    ]
    
    return {
        "messages": messages,
        "current_step": "analyze_sentiment"
    }

#################
@traceable(project_name="prizm-workflow-2")
def analyze_sentiment(state: WorkflowState):
    """Analyze customer sentiment from conversation"""
    # Add this line to tell Python you're using the global variable
    global MOCK_SENTIMENT_ANALYSIS
    
    # Keep track of the current state values
    current_sentiment = state.get("sentiment", "")
    current_reason = state.get("reason", "")
    
    print(f"Starting analyze_sentiment with sentiment={current_sentiment}, reason={current_reason}")

    # Validate OpenAI API key if not in mock mode
    if not MOCK_SENTIMENT_ANALYSIS:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("ERROR: OPENAI_API_KEY environment variable not set")
            # Fall back to mock analysis
            MOCK_SENTIMENT_ANALYSIS = True
        else:
            print(f"Using OpenAI API key: {api_key[:4]}...{api_key[-4:]}")
            try:
                # Simple test call to validate key
                response = openai.moderations.create(input="Test")
                print("OpenAI API key is valid")
            except Exception as e:
                print(f"OpenAI API key validation failed: {str(e)}")
                # Fall back to mock analysis
                MOCK_SENTIMENT_ANALYSIS = True
    
    messages = state.get("messages", [])
    sentiment_attempts = state.get("sentiment_attempts", 0) + 1
    
    print(f"Found {len(messages)} messages at start")
    
    # STEP 1: Add mock user response if needed
    if MOCK_USER_RESPONSES and all(not isinstance(m, HumanMessage) for m in messages):
        # Choose random response type (positive/negative)
        is_positive = random.choice([True, False])
        
        if is_positive:
            response = random.choice(POSITIVE_RESPONSES)
            print(f"\nAdding mock POSITIVE response: '{response}'")
        else:
            response = random.choice(NEGATIVE_RESPONSES)
            print(f"\nAdding mock NEGATIVE response: '{response}'")
        
        # Add the response to messages
        messages = messages + [HumanMessage(content=response)]
        print(f"Added mock user response, now have {len(messages)} messages")
    
    # STEP 2: Find the human message
    last_human_message = None
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            last_human_message = message
            break
    
    if not last_human_message:
        print("No human messages found even after trying to add one!")
        return {
            **state,
            "messages": messages  # Make sure to return the updated messages list
        }
    
    print(f"Found human message: '{last_human_message.content}'")
    
    # STEP 3: Analyze sentiment
    sentiment = ""
    reason = ""
    
    try:
        if MOCK_SENTIMENT_ANALYSIS:
            # Simple keyword-based analysis for mock mode
            text = last_human_message.content.lower()
            
            if any(word in text for word in ["yes", "thanks", "great", "perfect", "will do"]):
                sentiment = "positive"
                reason = ""
                print("MOCK: Detected positive sentiment")
            elif any(word in text for word in ["no", "can't", "won't", "concerned", "worried", "budget"]):
                sentiment = "negative"
                
                # Simple reason detection for mock mode
                if "budget" in text or "afford" in text or "cost" in text or "expensive" in text:
                    reason = "budget concerns"
                elif "time" in text or "timeline" in text or "schedule" in text or "delay" in text:
                    reason = "timeline concerns"
                elif "quality" in text or "expertise" in text or "experience" in text:
                    reason = "quality concerns"
                else:
                    reason = "general concerns"
                    
                print(f"MOCK: Detected negative sentiment with reason: {reason}")
            else:
                sentiment = "unknown"
                reason = "no clear sentiment indicators"
                print("MOCK: Unknown sentiment")
        else:
            # Use real OpenAI for sentiment analysis - SIMPLIFIED APPROACH
            print("Calling OpenAI for sentiment analysis...")
            
            # First, determine only positive/negative sentiment
            sentiment_prompt = """Analyze the following customer message and determine if the sentiment is positive or negative.
Reply with ONLY ONE WORD - either 'positive' or 'negative'."""
            
            model = _get_model("openai")
            
            # First call - just to determine positive/negative
            try:
                sentiment_analysis = model.invoke([
                    SystemMessage(content=sentiment_prompt),
                    last_human_message
                ])
                
                sentiment_text = sentiment_analysis.content.strip().lower()
                print(f"OpenAI sentiment response: '{sentiment_text}'")
                
                # Set sentiment based on response
                if "positive" in sentiment_text:
                    sentiment = "positive"
                    reason = ""
                    print("Detected positive sentiment")
                elif "negative" in sentiment_text:
                    sentiment = "negative"
                    
                    # Second call - specifically to extract the reason
                    print("Making second call to extract reason...")
                    reason_prompt = """The customer has expressed a negative sentiment. 
Analyze their message and identify the specific concern or reason for their negative sentiment.
Respond with ONLY the main concern in 3-5 words, with no additional explanation.
Examples of good responses: 'budget constraints', 'timeline issues', 'quality concerns'"""
                    
                    try:
                        reason_analysis = model.invoke([
                            SystemMessage(content=reason_prompt),
                            last_human_message
                        ])
                        
                        extracted_reason = reason_analysis.content.strip()
                        print(f"Extracted reason: '{extracted_reason}'")
                        
                        # Clean up response if needed
                        if extracted_reason and len(extracted_reason) < 50:  # Sanity check
                            reason = extracted_reason
                        else:
                            # Fall back to keyword extraction
                            text = last_human_message.content.lower()
                            if "budget" in text or "afford" in text or "cost" in text:
                                reason = "budget concerns"
                            elif "time" in text or "timeline" in text or "schedule" in text:
                                reason = "timeline concerns"
                            else:
                                reason = "general concerns"
                    except Exception as e:
                        print(f"Error extracting reason: {e}")
                        reason = "unspecified concerns"
                        
                    print(f"Final reason: '{reason}'")
                else:
                    # Handle unexpected response
                    sentiment = "unknown"
                    reason = "ambiguous sentiment"
                    print(f"Unexpected sentiment response: '{sentiment_text}'")
            except Exception as e:
                print(f"Error in sentiment analysis: {e}")
                # Fall back to keyword analysis
                text = last_human_message.content.lower()
                if any(word in text for word in ["yes", "thanks", "great", "perfect", "will do"]):
                    sentiment = "positive"
                    reason = ""
                elif any(word in text for word in ["no", "can't", "won't", "concerned", "worried", "budget"]):
                    sentiment = "negative"
                    
                    # Simple reason detection for fallback
                    if "budget" in text or "afford" in text:
                        reason = "budget concerns"
                    elif "time" in text or "timeline" in text:
                        reason = "timeline concerns"
                    else:
                        reason = "general concerns"
                else:
                    sentiment = "unknown"
                    reason = "no clear indicators"
    except Exception as e:
        print(f"Global error in sentiment analysis: {str(e)}")
        sentiment = "unknown"
        reason = f"Error: {str(e)}"
    
    print(f"Final sentiment analysis: sentiment={sentiment}, reason={reason}")
    
    # Return the FULL state including the new values and updated messages
    full_state = {
        **state,
        "messages": messages,
        "sentiment": sentiment,
        "reason": reason,
        "current_step": "process_sentiment",
        "sentiment_attempts": 0
    }
    
    print(f"Returning from analyze_sentiment with sentiment={full_state['sentiment']}")
    return full_state
############################


@traceable(project_name="prizm-workflow-2")
def process_sentiment(state: WorkflowState):
    """Process action based on sentiment analysis"""
    # Log incoming state
    print(f"process_sentiment received sentiment={state.get('sentiment', '')}, reason={state.get('reason', '')}")
    
    sentiment = state.get("sentiment", "")
    # Get the existing messages from state
    existing_messages = state.get("messages", [])
    
    if sentiment == "positive":
        # For positive sentiment, proceed with the task
        response = "Wonderful, talk to you soon."
        
    elif sentiment == "negative":
        # For negative sentiment, ask for more information
        response = "I understand you have some concerns. Could you please tell me more about them?"
        
    elif sentiment == "sentiment-loop":
        # Handle sentiment loop (too many attempts)
        response = "I'm having trouble understanding your sentiment. Let me escalate this to our support team."
    
    else:
        # For unknown sentiment, provide a generic response
        response = "Thank you for your response. Is there anything else you'd like to know about this task?"
    
    # Add the response to the messages
    messages = existing_messages + [AIMessage(content=response)]
    
    return {
        **state,  # Include ALL existing state
        "messages": messages,
        "current_step": "process_data",
    }

@traceable(project_name="prizm-workflow-2")
def process_data(state: WorkflowState):
    # Log incoming state
    print(f"process_data received sentiment={state.get('sentiment', '')}, reason={state.get('reason', '')}")
    
    summary = (
        f"New {state['task']['category']} project for {state['customer']['name']} "
        f"({state['customer']['zipCode']}) assigned to {state['vendor']['name']}"
    )
    
    # Include sentiment information in the summary
    if state.get("sentiment"):
        summary += f" (Customer sentiment: {state.get('sentiment')})"
    
    # Return the FULL state with summary added
    return {
        **state,  # Include ALL existing state
        "summary": summary
    }

# Add this function to convert message objects to serializable dictionaries
def messages_to_dict(messages):
    """Convert message objects to serializable dictionaries."""
    result = []
    for message in messages:
        if isinstance(message, BaseMessage):  # Better check for message types
            result.append({
                "type": message.type,
                "content": message.content
            })
        elif isinstance(message, dict) and "type" in message and "content" in message:
            # Already a dict with the right format
            result.append(message)
    return result

@traceable(project_name="prizm-workflow-2")
def format_output(state: WorkflowState):
    # Log what's coming in
    print(f"format_output received sentiment={state.get('sentiment', '')}, reason={state.get('reason', '')}")
    
    # Convert message objects to serializable dictionaries
    messages_dict = messages_to_dict(state.get("messages", []))
    
    # Ensure all values are present
    result = {
        "customer_email": state.get("customer", {}).get("email"),
        "vendor_email": state.get("vendor", {}).get("email"),
        "project_summary": state.get("summary", ""),
        "sentiment": state.get("sentiment", ""),
        "reason": state.get("reason", ""),
        "messages": messages_dict
    }
    
    # Log what's going out
    print(f"format_output returning sentiment={result['sentiment']}, reason={result['reason']}")
    
    return result

# 3. Graph Setup
workflow = StateGraph(WorkflowState)
workflow.add_node("validate", validate_input)
workflow.add_node("initialize_state", initialize_state)
workflow.add_node("generate_initial_prompt", generate_initial_prompt)
workflow.add_node("analyze_sentiment", analyze_sentiment)
workflow.add_node("process_sentiment", process_sentiment)
workflow.add_node("process", process_data)
workflow.add_node("format", format_output)

# Add edges
workflow.add_edge("validate", "initialize_state")
workflow.add_edge("initialize_state", "generate_initial_prompt")
workflow.add_edge("generate_initial_prompt", "analyze_sentiment")
workflow.add_edge("analyze_sentiment", "process_sentiment")
workflow.add_edge("process_sentiment", "process")
workflow.add_edge("process", "format")
workflow.add_edge("format", END)

workflow.set_entry_point("validate")

# First compile the workflow
app = workflow.compile()

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

    print("Starting workflow execution...")
    print(f"Mock user responses: {'ON' if MOCK_USER_RESPONSES else 'OFF'}")
    print(f"Mock sentiment analysis: {'ON' if MOCK_SENTIMENT_ANALYSIS else 'OFF'}")
    
    result = app.invoke(input_data)
    
    # Print result without JSON serialization first
    print("\nFinal Output:")
    print(f"Customer Email: {result.get('customer_email')}")
    print(f"Vendor Email: {result.get('vendor_email')}")
    print(f"Project Summary: {result.get('project_summary')}")
    print(f"Sentiment: {result.get('sentiment')}")
    # Print messages in a readable format
    print("\nMessages:")
    messages = result.get('messages', [])
    
    # Handle both cases: message objects or already dictionaries
    for msg in messages:
        if isinstance(msg, dict):
            print(f"- {msg.get('type', 'unknown')}: {msg.get('content', '')}")
        elif hasattr(msg, 'type') and hasattr(msg, 'content'):
            print(f"- {msg.type}: {msg.content}")
        else:
            print(f"- Unknown message format: {type(msg)}")
    
    print("\nWorkflow execution complete. You can view the trace in the LangGraph UI.")
    print("Visit: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024")