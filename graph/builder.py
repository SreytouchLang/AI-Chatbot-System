from langgraph.graph import StateGraph, START, END
from graph.state import State

from graph.nodes.load_memory import load_memory
from graph.nodes.retrieve_context import retrieve_context
from graph.nodes.generate_answer import generate_answer
from graph.nodes.store_memory import store_memory
from graph.nodes.summarize import summarize

def build_graph():
    workflow = StateGraph(State)

    workflow.add_node("load_memory", load_memory)
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("generate_answer", generate_answer)
    workflow.add_node("store_memory", store_memory)
    workflow.add_node("summarize", summarize)

    workflow.add_edge(START, "load_memory")
    workflow.add_edge("load_memory", "retrieve_context")
    workflow.add_edge("retrieve_context", "generate_answer")
    workflow.add_edge("generate_answer", "summarize")
    workflow.add_edge("summarize", "store_memory")
    workflow.add_edge("store_memory", END)

    return workflow.compile()
