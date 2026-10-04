"""Aether 360 Copilot — Patient/Member 360 with cited clinical and regulatory answers.

Local mode reads synthetic CSVs. Snowflake mode (Streamlit in Snowflake) can swap loaders later.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aether360.qa import answer_question, resolve_member
from aether360.store import load_bundle

st.set_page_config(
    page_title="Aether 360 Copilot",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;500;600;700&family=Source+Serif+4:wght@500;600&display=swap');
html, body, [class*="stApp"] {
  font-family: "Source Sans 3", sans-serif;
  background: #F6F3EC;
  color: #1C2B33;
}
.block-container { padding-top: 1.4rem; max-width: 1280px; }
h1, h2, h3 { font-family: "Source Serif 4", serif; color: #0B3D4A; letter-spacing: -0.02em; }
.aether-hero {
  background: #0B3D4A;
  color: #F6F3EC;
  padding: 1.25rem 1.5rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}
.aether-hero p { margin: 0.35rem 0 0 0; color: #D5E3E6; font-size: 0.95rem; }
.badge {
  display: inline-block; padding: 0.15rem 0.55rem; border-radius: 2px;
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase;
}
.badge-vh { background: #7A1F1F; color: #fff; }
.badge-h { background: #C45C26; color: #fff; }
.badge-m { background: #C9A227; color: #1C2B33; }
.badge-l { background: #2F6F4E; color: #fff; }
.source-card {
  background: #fff; border: 1px solid #D9D2C5; padding: 0.75rem 0.9rem; margin-bottom: 0.5rem;
}
.source-card code { font-size: 0.78rem; }
.stTabs [data-baseweb="tab-list"] { gap: 0.5rem; }
div[data-testid="stMetric"] {
  background: #fff;
  border: 1px solid #D9D2C5;
  border-radius: 6px;
  padding: 0.85rem 1rem;
  min-height: 6.5rem;
  justify-content: center;
}
label[data-testid="stMetricLabel"],
label[data-testid="stMetricLabel"] p {
  color: #42545D !important;
  font-size: 0.95rem !important;
  line-height: 1.3 !important;
  white-space: normal !important;
  overflow-wrap: anywhere;
  opacity: 1 !important;
}
div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] div {
  color: #0B3D4A !important;
  -webkit-text-fill-color: #0B3D4A !important;
  font-size: clamp(1.65rem, 2.5vw, 2.25rem) !important;
  font-weight: 700 !important;
  line-height: 1.2 !important;
  opacity: 1 !important;
}
div[data-testid="stCaptionContainer"] { color: #5C6B73; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_resource
def bundle():
    return load_bundle()


def tier_badge(tier: str) -> str:
    cls = {"Very High": "badge-vh", "High": "badge-h", "Moderate": "badge-m", "Low": "badge-l"}.get(tier, "badge-m")
    return f'<span class="badge {cls}">{tier}</span>'


def render_sources(sources: list[dict]) -> None:
    if not sources:
        st.info("No sources — this response abstained or refused.")
        return
    for i, s in enumerate(sources, start=1):
        st.markdown(
            f"""<div class="source-card"><strong>[{i}]</strong> {s.get('source_type')}
            · <code>{s.get('object')}</code> · <code>{s.get('key')}</code><br/>
            {s.get('claim')}<br/><em>{(s.get('snippet') or '')[:380]}</em></div>""",
            unsafe_allow_html=True,
        )


SAMPLES = [
    "Why is Jordan Hale high risk? List ATRI factors and sources.",
    "Is ibuprofen safe given MEM-10007's anticoagulant?",
    "What does the synthetic warfarin label say about NSAIDs?",
    "Which members have an open A1c / GSD-style care gap?",
    "River Chen is on an SGLT2 — what does the safety communication require?",
    "Does Ellis Navarro meet PA-GLP1-2026 diabetes criteria?",
    "Summarize the synthetic CMS CGM coverage criteria.",
    "How many members are Very High ATRI?",
]


def main() -> None:
    data = bundle()
    df360 = pd.DataFrame(data.member_360)
    st.markdown(
        """<div class="aether-hero">
        <h1 style="color:#F6F3EC;margin:0;">Aether 360 Copilot</h1>
        <p>Patient / Member 360 and clinical–regulatory document copilot. Fully synthetic corpus. Every answer carries source evidence. ATRI is a rules index, not a black-box prediction.</p>
        </div>""",
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.subheader("Corpus")
        st.caption(f"As of {data.as_of} · {len(data.member_360)} members · {len(data.chunks)} chunks · {len(data.manifest)} documents")
        st.caption("EHR keys `PAT-*` join payer keys `MEM-*` on a deterministic synthetic crosswalk.")
        pick = st.selectbox(
            "Focus member",
            options=["(none)"] + [f"{r['member_id']} — {r['full_name']}" for r in data.member_360],
        )
        focus = None if pick.startswith("(none)") else pick.split(" — ")[0]
        st.markdown("**Hero members for demo**")
        st.caption("MEM-10007 Hale · MEM-10014 Chen · MEM-10021 Okonkwo · MEM-10003 Patel · MEM-10031 Navarro")

    tab_pop, tab_360, tab_qa, tab_docs, tab_coco = st.tabs(
        ["Population", "Member 360", "Cited copilot", "Evidence library", "CoCo lifecycle"]
    )

    with tab_pop:
        st.subheader("Population overview")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Members", f"{len(df360):,}")
        c2.metric("Very High ATRI", f"{int((df360.atri_tier == 'Very High').sum()):,}")
        c3.metric("30-day readmit", f"{int(df360.readmit_30d_flag.astype(bool).sum()):,}")
        c4.metric("Open care gaps", f"{len(data.care_gaps):,}")
        st.caption("Source: GOLD.MEMBER_360 built from siloed EHR + claims. ATRI points in GOLD.ATRI_FACTORS.")
        left, right = st.columns((2, 1))
        with left:
            st.subheader("Panel by ATRI tier")
            st.bar_chart(df360.groupby("atri_tier").size().reindex(["Very High", "High", "Moderate", "Low"]))
        with right:
            st.subheader("Line of business")
            st.bar_chart(df360.groupby("line_of_business").size())
        show = df360[
            [
                "member_id",
                "full_name",
                "age_years",
                "panel",
                "atri_score",
                "atri_tier",
                "ed_visits_90d",
                "readmit_30d_flag",
                "open_gap_list",
                "safety_flag_list",
            ]
        ]
        st.dataframe(show, use_container_width=True, hide_index=True)

    with tab_360:
        if not focus:
            st.info("Select a focus member in the sidebar.")
        else:
            row = data.member(focus)
            f1, f2, f3, f4 = st.columns(4)
            f1.markdown(f"### {row['full_name']}")
            st.markdown(tier_badge(row["atri_tier"]), unsafe_allow_html=True)
            f2.metric("ATRI", row["atri_score"])
            f3.metric("Active meds", row["active_med_count"])
            f4.metric("ED 90d", row["ed_visits_90d"])
            st.caption(
                f"{row['member_id']} · EHR {row['patient_id']} · {row['age_years']}y {row['sex']} · "
                f"{row['line_of_business']} · {row['panel']} · PCP {row['pcp_name']}"
            )
            a, b = st.columns(2)
            with a:
                st.markdown("**Conditions**")
                st.write(row["active_condition_list"] or "—")
                st.markdown("**Medications**")
                st.write(row["active_med_list"] or "—")
                st.markdown("**Labs**")
                st.write(f"Last A1c {row['last_a1c_value']} on {row['last_a1c_date']}")
            with b:
                st.markdown("**Utilization & quality**")
                st.write(
                    f"Last encounter {row['last_encounter_date']} · 30-day readmit `{row['readmit_30d_flag']}` · "
                    f"Allowed 12m ${row['allowed_12m']:,.0f}"
                )
                st.write(f"Gaps: {row['open_gap_list'] or 'none'}")
                st.write(f"Safety: {row['safety_flag_list'] or 'none'}")
            st.subheader("ATRI factor ledger")
            st.caption("Each row is a fired rule with a source object and key. Nothing is a latent model feature.")
            fac = pd.DataFrame([f for f in data.atri_factors if f["member_id"] == focus])
            if fac.empty:
                st.write("No factors fired.")
            else:
                st.dataframe(
                    fac[["factor_code", "points", "source_object", "source_key", "evidence"]],
                    use_container_width=True,
                    hide_index=True,
                )
            st.subheader("Encounters")
            enc = pd.DataFrame([e for e in data.encounters if e["member_id"] == focus])
            if not enc.empty:
                st.dataframe(
                    enc[["encounter_id", "encounter_class", "start_date", "reason", "unplanned_readmit_30d"]],
                    use_container_width=True,
                    hide_index=True,
                )

    with tab_qa:
        st.subheader("Ask with citations required")
        st.caption("The copilot retrieves structured rows and document chunks, then answers or abstains. It will not invent doses or coverage rules.")
        sample = st.selectbox("Sample questions", [""] + SAMPLES)
        q = st.text_area("Question", value=sample, height=90)
        go = st.button("Retrieve and answer", type="primary")
        if go and q.strip():
            result = answer_question(q, data, member_id=focus)
            kind = result["response_type"]
            if kind == "refuse":
                st.error(result["answer"])
            elif kind == "abstain":
                st.warning(result["answer"])
            else:
                st.markdown(result["answer"])
                st.caption(f"Confidence: {result.get('confidence')} · member {result.get('member_id') or 'population'}")
            st.markdown("#### Source evidence")
            render_sources(result.get("sources") or [])
            with st.expander("JSON payload (agent contract)"):
                st.code(json.dumps(result, indent=2)[:8000])

    with tab_docs:
        st.subheader("Unstructured corpus")
        man = pd.DataFrame(data.manifest)
        st.dataframe(man, use_container_width=True, hide_index=True)
        doc_id = st.selectbox("Open document", [m["doc_id"] for m in data.manifest])
        if doc_id:
            meta = next(m for m in data.manifest if m["doc_id"] == doc_id)
            st.caption(f"{meta['document_class']} · {meta['filename']} · member {meta.get('member_id') or 'n/a'}")
            st.markdown(data.documents.get(doc_id, "_missing_"))

    with tab_coco:
        st.subheader("How CoCo is used across the lifecycle")
        st.markdown(
            """
1. **Planning** — `coco/planning/` (problem, model, ontology, workflow). Prompt: `coco/prompts/01-planning.md`.
2. **Development** — skills `$synthetic-care-data`, `$patient-360-builder`, `$cited-clinical-qa`, `$risk-strat-explainer`. SQL in `sql/`.
3. **Execution** — Dynamic Tables, Task `ATRI_NIGHTLY_REFRESH`, Cortex Search, Cortex Agent, this Streamlit app.
4. **Testing** — `coco/prompts/04-testing.md`, `pytest tests`, eval questions in `tests/eval_questions.yaml`.

Reusable plugin: `.cortex-plugin/` (`aether-360`). MCP action tool: `mcp/care_ops_server.py` (open care-gap tickets).
Guardrail hook: `hooks/block_unsafe_sql.py`.
            """
        )
        st.markdown("Run locally: `python scripts/generate_synthetic.py` then `streamlit run app/streamlit_app.py`.")


if __name__ == "__main__":
    main()
