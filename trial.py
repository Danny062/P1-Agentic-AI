# import libraries
import os
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

# libraries for loading model
import re
from openai import OpenAI
import matplotlib.pyplot as plt
import networkx as nx


# model setting
# get API key from .env
from dotenv import load_dotenv
import os
load_dotenv()
grok_api_key = os.getenv("grok_API_KEY")
if not grok_api_key:
    raise ValueError("grok_api_key environment variable not set")

xai_client = OpenAI(
    api_key=grok_api_key,  # Replace with your actual API key
    base_url="https://api.x.ai/v1"
)

# Memory
# The original question or task
class State(TypedDict):
    text: str           # input
    classification: str # class
    entities: List[str] # user/ role
    summary: str        # output

# Classification node
def classification_node(state: dict) -> dict:
    """
    Classify the text into one of predefined categories.

    Parameters:
        state (State): The current state dictionary containing the text to classify

    Returns:
        dict: A dictionary with the "classification" key containing the category result

    Categories:
        - News: Factual reporting of current events
        - Blog: Personal or informal web writing
        - Research: Academic or scientific content
        - Other: Content that doesn't fit the above categories
    """

    text = state["text"]
    try:
        response = xai_client.chat.completions.create(

            model="grok-3-mini-beta",  # Use a supported model
            messages=[
                {"role": "system", "content": """You are a helpful assistant 
                who helps to classify the text 
                into one of the categories:News, Blog, Research, or Other. 
                No need to give reason and only give the result.""" },
                {"role": "user", "content": f"""Classify the following text 
                into one of the categories: 
                News, Blog, Research, or Other.\n\nText:{text}\n\nCategory:"""}
            ],
            max_tokens=1000,
            temperature=0
        )
        state["classification"] = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error: {str(e)}")
        state["classification"] = f"Error: {str(e)}"
    return state

# Extraction node
def entity_extraction_node(state: dict) -> dict:
    # Function to identify and extract named entities from text
    # Organized by category (Person, Organization, Location)

    # Create template for entity extraction prompt
    # Specifies what entities to look for and format (comma-separated)
    text = state["text"]
    try:
        response = xai_client.chat.completions.create(
            model="grok-3-mini-beta",
            messages=[
                {"role": "system",
                 "content": """You are a helpful assistant who helps to 
                 extract all the entities, important noun
                 (Person, Representitives, Organization, Location, etc), from the following text.
                 No need to give reasons and explanations, only give the output."""},
                {"role": "user",
                 "content": f"""Extract all the entities (Person, Representitives ,Organization, Location, etc) 
                 from the following text. Provide the result 
                 as a comma-separated list.\n\nText:{text}\n\nEntities:"""}
            ],
            max_tokens=1500
        )
        state["entities"] = response.choices[0].message.content.split(", ")
    except Exception as e:
        print(f"Error: {str(e)}")
        state["entities"] = f"Error: {str(e)}"
    # state["response"] = "Non-question input detected. Please ask a question."
    return state

# Summarised text
def summarize_text(state: dict) -> dict:
    # Create a template for the summarization prompt
    # This tells the model to summarize the input text in one sentence

    text = state["text"]
    try:
        response = xai_client.chat.completions.create(
            model="grok-3-mini-beta",
            messages=[
                {"role": "system",
                 "content": "You are a helpful assistant who helps to summarize the text"},
                {"role": "user",
                 "content": f"""Summarize the following text in one short sentence. 
                Text: {text} 
                Summary:"""}
            ],
            max_tokens=500
        )
        state["summary"] = response.choices[0].message.content
    except Exception as e:
        print(f"Error: {str(e)}")
        state["summary"] = f"Error: {str(e)}"
    # state["response"] = "Non-question input detected. Please ask a question."
    return state

def create_graph():
    # Initialize StateGraph with a dictionary as state
    workflow = StateGraph(dict)

    # Add nodes
    workflow.add_node("classification", classification_node)
    workflow.add_node("entity_extraction", entity_extraction_node)
    workflow.add_node("summarization", summarize_text)

    # Set entry point and conditional edges
    workflow.set_entry_point("classification")
    workflow.add_edge("classification", "entity_extraction")
    workflow.add_edge("entity_extraction", "summarization")
    workflow.add_edge("summarization", END)

    return workflow.compile()


if __name__ == "__main__":
    # Create and compile graph
    graph = create_graph()
    # Visualize the graph
    # visualize_langgraph(graph, output_file="langgraph.png")

    # Example queries
    test_input = []

    file_path = "testcase.txt"

    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, 1):
                # Strip whitespace and skip empty lines
                text = line.strip()
                if text:
                    test_input.append(text)
    except Exception as e:
        print(f"Error: {str(e)}")

    for text in test_input:
        # Run the graph with a dictionary as initial state
        initial_state = {"text": text, "classification": "",
                         "entities": " ", "summary": ""}
        result = graph.invoke(initial_state)

        # Print result
        print("text:", result["text"])
        print("classification:", result["classification"])
        print("entities:", result["entities"])
        print("summary:", result["summary"])
        print("-" * 50)

# api testing
'''
response = xai_client.chat.completions.create(
            model="grok-3-mini-beta",  # Use a supported model
            messages=[
                {"role": "system", "content": "You are a helpful assistant answering questions concisely."},
                {"role": "user", "content": "Hello! Are you working?"}
            ],
            max_tokens=300,
            temperature=0
        )

print(response.choices[0].message.content)'''
