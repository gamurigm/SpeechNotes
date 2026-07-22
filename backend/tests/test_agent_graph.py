import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock, call

_dependency_names = ("langgraph", "langgraph.graph", "src.agent.state", "src.agent.nodes")
_saved_modules = {name: sys.modules.get(name) for name in _dependency_names}
_langgraph = ModuleType("langgraph")
_langgraph_graph = ModuleType("langgraph.graph")
_langgraph_graph.StateGraph = MagicMock
_langgraph_graph.END = "__end__"
_state = ModuleType("src.agent.state")
_state.AgentState = dict
_nodes = ModuleType("src.agent.nodes")
_nodes.router_node = MagicMock(name="router_node")
_nodes.semantic_search_node = MagicMock(name="semantic_search_node")
_nodes.writing_node = MagicMock(name="writing_node")
sys.modules.update(
    {
        "langgraph": _langgraph,
        "langgraph.graph": _langgraph_graph,
        "src.agent.state": _state,
        "src.agent.nodes": _nodes,
    }
)
graph = importlib.import_module("src.agent.graph")
for _name, _saved in _saved_modules.items():
    if _saved is None:
        sys.modules.pop(_name, None)
    else:
        sys.modules[_name] = _saved


def test_graph_routes_are_deterministic():
    assert graph.route_after_router({"next_action": "search"}) == "search"
    assert graph.route_after_router({"next_action": "write"}) == "write"
    assert graph.route_after_search({}) == "write"
    assert graph.route_after_write({}) == "__end__"


def test_create_agent_graph_registers_nodes_edges_and_compiles(monkeypatch):
    workflow = MagicMock()
    workflow.compile.return_value = "compiled-app"
    state_graph = MagicMock(return_value=workflow)
    monkeypatch.setattr(graph, "StateGraph", state_graph)

    assert graph.create_agent_graph() == "compiled-app"

    state_graph.assert_called_once_with(dict)
    assert workflow.add_node.call_args_list == [
        call("router", graph.router_node),
        call("search", graph.semantic_search_node),
        call("write", graph.writing_node),
    ]
    workflow.set_entry_point.assert_called_once_with("router")
    assert workflow.add_conditional_edges.call_args_list == [
        call("router", graph.route_after_router, {"search": "search", "write": "write"}),
        call("search", graph.route_after_search, {"write": "write"}),
        call("write", graph.route_after_write, {"__end__": "__end__"}),
    ]
    workflow.compile.assert_called_once_with()
