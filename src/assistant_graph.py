import warnings
from typing import Any, List, Optional, TypedDict


warnings.filterwarnings(
    "ignore",
    message=r".*allowed_objects.*",
    category=Warning,
)
warnings.filterwarnings(
    "ignore",
    category=Warning,
    module=r"langgraph\.cache\.base.*",
)

from langgraph.graph import END, START, StateGraph

from src.pinecone_hybrid import get_client, query_hybrid, summarize_matches
from src.safety import classify_query
from src.settings import Settings


class AssistantState(TypedDict, total=False):
    question: str
    member: dict
    plan: dict
    settings: Settings
    answer: str
    route: str
    confidence: float
    matches: List[dict]
    escalated: bool
    should_escalate: bool
    graph_trace: List[str]
    safety_message: Optional[str]
    retrieval_result: dict


def _trace(state: AssistantState, node_name: str) -> List[str]:
    return state.get("graph_trace", []) + [node_name]


def safety_check(state: AssistantState) -> AssistantState:
    from src.rag_answer import inactive_cost_guardrail

    question = state["question"]
    safety = classify_query(question)
    if safety.route != "retrieval":
        escalated = safety.route != "small_talk"
        return {
            "answer": safety.message or "",
            "route": safety.route,
            "confidence": 1.0,
            "matches": [],
            "escalated": escalated,
            "safety_message": safety.message,
            "graph_trace": _trace(state, "safety_check"),
        }

    inactive_message = inactive_cost_guardrail(state["member"], question)
    if inactive_message:
        return {
            "answer": inactive_message,
            "route": "inactive_coverage",
            "confidence": 1.0,
            "matches": [],
            "escalated": True,
            "safety_message": inactive_message,
            "graph_trace": _trace(state, "safety_check"),
        }

    return {
        "route": "retrieval",
        "escalated": False,
        "graph_trace": _trace(state, "safety_check"),
    }


def route_after_safety(state: AssistantState) -> str:
    if state.get("route") != "retrieval":
        return "end"
    return "retrieve"


def retrieve(state: AssistantState) -> AssistantState:
    pc = get_client(state["settings"])
    result = query_hybrid(
        pc=pc,
        settings=state["settings"],
        query=state["question"],
        member_id=state["member"]["member_id"],
        plan_id=state["member"]["plan_id"],
        top_k=5,
    )
    return {
        "retrieval_result": result,
        "graph_trace": _trace(state, "retrieve"),
    }


def confidence_check(state: AssistantState) -> AssistantState:
    summary = summarize_matches(state.get("retrieval_result", {}))
    return {
        "confidence": summary["best_score"],
        "matches": summary["matches"],
        "should_escalate": summary["should_escalate"],
        "graph_trace": _trace(state, "confidence_check"),
    }


def route_after_confidence(state: AssistantState) -> str:
    if state.get("should_escalate"):
        return "escalate"
    return "answer"


def escalation_answer(state: AssistantState) -> AssistantState:
    from src.rag_answer import MEMBER_SERVICES_PHONE

    return {
        "answer": (
            "I am not confident enough to answer that accurately. Please contact "
            f"Member Services at {MEMBER_SERVICES_PHONE}."
        ),
        "route": "low_confidence",
        "escalated": True,
        "graph_trace": _trace(state, "escalation_answer"),
    }


def grounded_answer(state: AssistantState) -> AssistantState:
    from src.rag_answer import generate_grounded_answer

    answer = generate_grounded_answer(
        state["question"],
        state["member"],
        state["plan"],
        state["settings"],
        state.get("matches", []),
    )
    return {
        "answer": answer,
        "route": "answered",
        "escalated": False,
        "graph_trace": _trace(state, "grounded_answer"),
    }


def build_assistant_graph() -> Any:
    graph = StateGraph(AssistantState)
    graph.add_node("safety_check", safety_check)
    graph.add_node("retrieve", retrieve)
    graph.add_node("confidence_check", confidence_check)
    graph.add_node("escalation_answer", escalation_answer)
    graph.add_node("grounded_answer", grounded_answer)

    graph.add_edge(START, "safety_check")
    graph.add_conditional_edges(
        "safety_check",
        route_after_safety,
        {
            "retrieve": "retrieve",
            "end": END,
        },
    )
    graph.add_edge("retrieve", "confidence_check")
    graph.add_conditional_edges(
        "confidence_check",
        route_after_confidence,
        {
            "answer": "grounded_answer",
            "escalate": "escalation_answer",
        },
    )
    graph.add_edge("grounded_answer", END)
    graph.add_edge("escalation_answer", END)
    return graph.compile()


ASSISTANT_GRAPH = build_assistant_graph()


def run_assistant_graph(question: str, member: dict, plan: dict, settings: Settings) -> dict:
    result = ASSISTANT_GRAPH.invoke(
        {
            "question": question,
            "member": member,
            "plan": plan,
            "settings": settings,
            "matches": [],
            "confidence": 0.0,
            "escalated": False,
            "graph_trace": [],
        }
    )
    return {
        "answer": result.get("answer", ""),
        "route": result.get("route", "unknown"),
        "confidence": result.get("confidence", 0.0),
        "matches": result.get("matches", []),
        "escalated": result.get("escalated", False),
        "graph_trace": result.get("graph_trace", []),
    }
