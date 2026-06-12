import html

import streamlit as st

from src.member_data import (
    get_benefits,
    get_claims,
    get_member,
    get_members,
    get_pcp,
    get_plan,
    get_providers,
    money,
)
from src.rag_answer import MEMBER_SERVICES_PHONE, answer_question
from src.settings import get_settings


st.set_page_config(
    page_title="CareGuide Member Portal",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --care-blue: #075a9c;
            --care-blue-dark: #073f6d;
            --care-blue-soft: #e8f2fb;
            --care-border: #d6e0ea;
            --care-bg: #f6f8fb;
            --care-text: #182b3a;
            --care-muted: #566b7d;
            --care-green: #0f7b55;
            --care-red: #a33b32;
            --care-amber: #8a5a00;
        }
        html, body, [class*="css"] {
            color: var(--care-text);
            font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        .stApp {
            background: var(--care-bg);
        }
        .block-container {
            padding-top: 0.6rem;
            padding-bottom: 2rem;
            max-width: 1320px;
        }
        .section-title {
            font-size: 1rem;
            font-weight: 750;
            margin: 0.45rem 0 0.35rem 0;
        }
        .answer-card {
            background: #ffffff;
            border: 1px solid var(--care-border);
            border-radius: 8px;
            padding: 1rem;
            margin-top: 0.85rem;
        }
        .ai-banner {
            background: #eef6fd;
            border: 1px solid #bfd9ee;
            border-left: 4px solid var(--care-blue);
            border-radius: 8px;
            padding: 0.75rem 0.85rem;
            margin: 0.55rem 0 0.85rem 0;
            color: #143e5f;
            font-size: 0.95rem;
            font-weight: 650;
        }
        .answer-label {
            color: var(--care-muted);
            font-size: 0.76rem;
            font-weight: 750;
            margin-bottom: 0.2rem;
        }
        .answer-question {
            font-size: 0.98rem;
            font-weight: 750;
            margin-bottom: 0.75rem;
        }
        .answer-text {
            font-size: 0.98rem;
            line-height: 1.48;
        }
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--care-border);
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--care-border);
            border-radius: 8px;
            padding: 0.6rem 0.7rem;
        }
        .stChatMessage {
            border-radius: 8px;
        }
        div[data-testid="stTabs"] button {
            font-weight: 650;
        }
        div[data-testid="stTabs"] [role="tablist"] {
            gap: 0.4rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(member: dict, plan: dict) -> None:
    with st.container(border=True):
        left, right = st.columns([0.72, 0.28], vertical_alignment="center")
        with left:
            st.markdown("### Member Coverage Details")
            selected_page = st.segmented_control(
                "Navigation",
                ["Ask CareGuide", "Find Care", "Benefits", "Claims", "Forms"],
                default=st.session_state.get("active_page", "Ask CareGuide"),
                label_visibility="collapsed",
                key="active_page",
            )
        with right:
            st.caption("MEMBER SERVICES")
            st.markdown(f"**{MEMBER_SERVICES_PHONE}**")
    return selected_page


def render_dashboard(member: dict, plan: dict) -> None:
    pcp = get_pcp(member)
    deductible_total = float(plan["deductible_individual"])
    deductible_met = float(member["deductible_met"])
    oop_total = float(plan["out_of_pocket_max_individual"])
    oop_met = float(member["out_of_pocket_met"])
    deductible_remaining = max(deductible_total - deductible_met, 0)
    oop_remaining = max(oop_total - oop_met, 0)

    with st.container(border=True):
        top_cols = st.columns([0.2, 0.2, 0.2, 0.2, 0.2])
        top_cols[0].caption("SIGNED-IN MEMBER")
        top_cols[0].markdown(f"**{member['display_name']}**")
        top_cols[0].caption(member["masked_member_id"])
        top_cols[1].caption("COVERAGE")
        if member["status"] == "Active":
            top_cols[1].success("Active")
        else:
            top_cols[1].error("Inactive")
        top_cols[2].caption("PLAN")
        top_cols[2].markdown(f"**{plan['plan_name']}**")
        top_cols[2].caption(plan["plan_type"])
        top_cols[3].caption("GROUP ID")
        top_cols[3].markdown(f"**{member['group_id']}**")
        top_cols[4].caption("PCP")
        top_cols[4].markdown(f"**{pcp['provider_name'] if pcp else 'Not selected'}**")

        st.divider()

        metric_cols = st.columns(4)
        metric_cols[0].metric(
            "Deductible remaining",
            money(deductible_remaining),
            help=f"{money(deductible_met)} met of {money(deductible_total)}",
        )
        metric_cols[1].metric(
            "Out-of-pocket remaining",
            money(oop_remaining),
            help=f"{money(oop_met)} met of {money(oop_total)}",
        )
        metric_cols[2].metric("Referral required", plan["referral_required"])
        metric_cols[3].metric("In-network coinsurance", f"{plan['coinsurance_in_network']}%")


def render_benefits(plan: dict) -> None:
    st.markdown('<div class="section-title">Benefits</div>', unsafe_allow_html=True)
    st.dataframe(
        get_benefits(plan["plan_id"]),
        hide_index=True,
        width="stretch",
        column_config={
            "plan_id": None,
            "service_category": "Service",
            "cost_share": "Cost share",
            "requires_deductible": "Deductible",
            "requires_prior_auth": "Prior auth",
            "notes": "Notes",
        },
    )


def render_claims(member: dict) -> None:
    st.markdown('<div class="section-title">Claims</div>', unsafe_allow_html=True)
    claims = get_claims(member["member_id"])
    if not claims:
        st.info("No recent claims.")
        return

    st.dataframe(
        claims,
        hide_index=True,
        width="stretch",
        column_config={
            "claim_id": "Claim",
            "member_id": None,
            "service_date": "Date",
            "provider_name": "Provider",
            "service_category": "Service",
            "amount_billed": "Billed",
            "plan_paid": "Plan paid",
            "member_responsibility": "Member cost",
            "status": "Status",
            "denial_reason": "Reason",
            "next_step": "Next step",
        },
    )


def render_find_care(plan: dict) -> None:
    st.markdown('<div class="section-title">Find Care</div>', unsafe_allow_html=True)
    providers = get_providers()
    query = st.text_input("Search providers", placeholder="Search by provider, specialty, network, or city")
    if query:
        normalized = query.lower()
        providers = [
            provider
            for provider in providers
            if normalized
            in " ".join(
                [
                    provider["provider_name"],
                    provider["specialty"],
                    provider["network_name"],
                    provider["network_status"],
                    provider["location"],
                ]
            ).lower()
        ]

    st.dataframe(
        providers,
        hide_index=True,
        width="stretch",
        column_config={
            "provider_id": None,
            "provider_name": "Provider",
            "provider_type": "Type",
            "specialty": "Specialty",
            "network_name": "Network",
            "network_status": "Status",
            "accepting_new_patients": "Accepting patients",
            "requires_referral": "Referral",
            "location": "Location",
            "phone": "Phone",
        },
    )


def render_forms() -> None:
    st.markdown('<div class="section-title">Forms</div>', unsafe_allow_html=True)
    rows = [
        {"Form": "Profile update", "Use for": "Phone, email, or address changes", "Status": "Secure verification required"},
        {"Form": "Dependent verification", "Use for": "Add spouse, child, or other eligible dependent", "Status": "Documentation required"},
        {"Form": "Special enrollment", "Use for": "Qualifying life event plan changes", "Status": "Review required"},
        {"Form": "Claim appeal", "Use for": "Denied or disputed claims", "Status": "Member Services review"},
    ]
    st.dataframe(rows, hide_index=True, width="stretch")


def init_chat(member_id: str) -> None:
    if st.session_state.get("chat_member_id") != member_id:
        st.session_state.chat_member_id = member_id
        st.session_state.qa_history = []


def render_chat(member: dict, plan: dict) -> None:
    with st.container(border=True):
        st.markdown("### Ask CareGuide")
        st.markdown(
            """
            <div class="ai-banner">
                AI-powered chatbot tool for benefits, claims, providers, coverage, and account support.
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("careguide_search", clear_on_submit=True):
            search_cols = st.columns([0.86, 0.14], vertical_alignment="bottom")
            with search_cols[0]:
                typed = st.text_input(
                    "Search",
                    label_visibility="collapsed",
                    placeholder="Ask about benefits, claims, providers, coverage, or account support",
                )
            with search_cols[1]:
                submitted = st.form_submit_button("Ask", width="stretch")
            if submitted and typed:
                st.session_state.pending_question = typed

        if st.session_state.get("qa_history"):
            for item in reversed(st.session_state.qa_history):
                safe_question = html.escape(item["question"])
                safe_answer = html.escape(item["answer"])
                st.markdown(
                    f"""
                    <div class="answer-card">
                        <div class="answer-label">YOU ASKED</div>
                        <div class="answer-question">{safe_question}</div>
                        <div class="answer-label">CAREGUIDE ANSWERED</div>
                        <div class="answer-text">{safe_answer}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    question = st.session_state.pop("pending_question", None)
    if not question:
        return

    with st.spinner("Checking your coverage details..."):
        try:
            settings = get_settings(require_api_key=True)
            result = answer_question(question, member, plan, settings)
            answer = result["answer"]
            escalated = result.get("escalated", False)
        except Exception as exc:
            answer = (
                "I could not reach the support service right now. Please try again or contact "
                "Member Services."
            )
            escalated = True
            st.caption(str(exc))

    st.session_state.qa_history.append(
        {
            "question": question,
            "answer": answer,
            "escalated": escalated,
        }
    )
    st.rerun()


def main() -> None:
    apply_styles()

    members = get_members()
    member_labels = {
        f"{member['display_name']} - {member['status']} - {member['masked_member_id']}": member["member_id"]
        for member in members
    }

    with st.sidebar:
        st.header("CareGuide")
        selected_label = st.selectbox("Member profile", list(member_labels.keys()))
        member_id = member_labels[selected_label]
        st.divider()
        with st.container(border=True):
            st.markdown("**Member Services**")
            st.markdown(f"**{MEMBER_SERVICES_PHONE}**")

    member = get_member(member_id)
    plan = get_plan(member["plan_id"])
    init_chat(member_id)

    active_page = render_header(member, plan)
    render_dashboard(member, plan)

    if active_page == "Ask CareGuide":
        render_chat(member, plan)
    elif active_page == "Find Care":
        render_find_care(plan)
    elif active_page == "Benefits":
        render_benefits(plan)
    elif active_page == "Claims":
        render_claims(member)
    elif active_page == "Forms":
        render_forms()


if __name__ == "__main__":
    main()
