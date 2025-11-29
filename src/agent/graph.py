"""
LangGraph Agent Graph
Defines the workflow graph for the agent.
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import router_node, semantic_search_node, writing_node


def route_after_router(state: AgentState) -> Literal["search", "write"]:
    """
    Conditional edge function after router node.
    
    Returns:
        Next node name based on state
    """
    return state["next_action"]


def route_after_search(state: AgentState) -> Literal["write"]:
    """
    Conditional edge function after search node.
    Always goes to write node.
    
    Returns:
        "write"
    """
    return "write"


def route_after_write(state: AgentState) -> Literal["__end__"]:
    """
    Conditional edge function after write node.
    Always ends the workflow.
    
    Returns:
        END
    """
    return END


def create_agent_graph() -> StateGraph:
    """
    Create the LangGraph agent workflow.
    
    Workflow:
        START -> router -> (search OR write) -> write -> END
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("search", semantic_search_node)
    workflow.add_node("write", writing_node)
    
    # Set entry point
    workflow.set_entry_point("router")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "router",
        route_after_router,
        {
            "search": "search",
            "write": "write"
        }
    )
    
    workflow.add_conditional_edges(
        "search",
        route_after_search,
        {
            "write": "write"
        }
    )
    
    workflow.add_conditional_edges(
        "write",
        route_after_write,
        {
            END: END
        }
    )
    
    # Compile graph
    app = workflow.compile()
    
    return app
