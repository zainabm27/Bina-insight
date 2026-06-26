from pathlib import Path
import subprocess
import sys

import pandas as pd
import streamlit as st
import plotly.express as px

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_CSV = RAW_DIR / "responses_raw.csv"

TABLEAU_EXPORT_DIR = PROJECT_ROOT / "dashboard" / "tableau_exports"

MAIN_EXPORT = TABLEAU_EXPORT_DIR / "main_tableau_export.csv"
KPI_CARDS = TABLEAU_EXPORT_DIR / "kpi_cards.csv"
OPPORTUNITY_SCORES = TABLEAU_EXPORT_DIR / "opportunity_scores.csv"
TOP_SEGMENTS = TABLEAU_EXPORT_DIR / "top_customer_segments.csv"
REGIONAL_NEEDS = TABLEAU_EXPORT_DIR / "regional_needs.csv"
TARGETING_SUMMARY = TABLEAU_EXPORT_DIR / "targeting_summary.csv"

RAW_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="Bina Insight Dashboard",
    layout="wide"
)

st.title("Bina Insight")
st.caption("Community data → AI agents → business opportunity dashboard")



def run_agent(script_name):

    script_path = PROJECT_ROOT / "agents" / script_name

    if not script_path.exists():
        raise FileNotFoundError(f"Missing agent file: {script_path}")

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Agent failed: {script_name}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )

    return result.stdout


def run_pipeline():

    agents = [
        "cleaning_agent.py",
        "nlp_agent.py",
        "trend_agent.py",
        "dashboard_agent.py",
    ]

    logs = []

    for agent in agents:
        output = run_agent(agent)
        logs.append(f"Completed {agent}\n{output}")

    return "\n\n".join(logs)


def load_csv(path):

    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(path)


def save_uploaded_file(uploaded_file):

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif file_name.endswith(".xlsx") or file_name.endswith(".xls"):
        df = pd.read_excel(uploaded_file)
    else:
        raise ValueError("Please upload a CSV or Excel file.")

    df.to_csv(RAW_CSV, index=False, encoding="utf-8")

    return df


def show_kpi_cards(kpi_df):

    if kpi_df.empty:
        st.info("No KPI data yet. Upload data and run the pipeline.")
        return

    cols = st.columns(4)

    for index, row in kpi_df.iterrows():
        col = cols[index % 4]

        with col:
            st.metric(
                label=str(row.get("kpi_name", "")),
                value=str(row.get("kpi_value", ""))
            )


st.sidebar.header("Upload Data")

uploaded_file = st.sidebar.file_uploader(
    "Upload community responses CSV or Excel",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file is not None:
    try:
        uploaded_df = save_uploaded_file(uploaded_file)

        st.sidebar.success(
            f"Uploaded {len(uploaded_df)} rows to data/raw/responses_raw.csv"
        )

        with st.sidebar.expander("Preview uploaded data"):
            st.dataframe(uploaded_df.head(10), use_container_width=True)

    except Exception as error:
        st.sidebar.error(str(error))


st.sidebar.header("Run Pipeline")

if st.sidebar.button("Run all agents"):
    try:
        with st.spinner("Running agents..."):
            logs = run_pipeline()

        st.success("Pipeline completed successfully.")

        with st.expander("Pipeline logs"):
            st.text(logs)

    except Exception as error:
        st.error("Pipeline failed.")
        st.code(str(error))


main_df = load_csv(MAIN_EXPORT)
kpi_df = load_csv(KPI_CARDS)
opportunity_df = load_csv(OPPORTUNITY_SCORES)
segments_df = load_csv(TOP_SEGMENTS)
regional_df = load_csv(REGIONAL_NEEDS)
targeting_df = load_csv(TARGETING_SUMMARY)


tab_overview, tab_opportunities, tab_segments, tab_regions, tab_raw = st.tabs(
    [
        "Executive Overview",
        "Opportunities",
        "Customer Segments",
        "Regional Needs",
        "Raw Insights",
    ]
)

with tab_overview:
    st.header("Executive Overview")

    show_kpi_cards(kpi_df)

    st.divider()

    if not opportunity_df.empty and "business_opportunity_score" in opportunity_df.columns:
        st.subheader("Business Opportunity Ranking")

        fig = px.bar(
            opportunity_df.sort_values("business_opportunity_score", ascending=True),
            x="business_opportunity_score",
            y="service_category",
            orientation="h",
            hover_data=[
                "feasibility_score",
                "scalability_score",
                "testability_score",
                "recommendation",
                "suggested_business_idea",
            ],
            title="Business Opportunity Score by Service Category"
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No opportunity scores yet. Run the pipeline first.")

    if not targeting_df.empty:
        st.subheader("Targeting Summary")
        st.dataframe(targeting_df, use_container_width=True)

with tab_opportunities:
    st.header("Opportunity Analysis")

    if opportunity_df.empty:
        st.info("No opportunity data yet.")
    else:
        st.subheader("Feasibility, Scalability, and Testability")

        score_columns = [
            "feasibility_score",
            "scalability_score",
            "testability_score",
        ]

        available_score_columns = [
            col for col in score_columns
            if col in opportunity_df.columns
        ]

        if available_score_columns:
            melted = opportunity_df.melt(
                id_vars=["service_category"],
                value_vars=available_score_columns,
                var_name="score_type",
                value_name="score"
            )

            fig = px.bar(
                melted,
                x="service_category",
                y="score",
                color="score_type",
                barmode="group",
                title="Feasibility vs Scalability vs Testability"
            )

            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Opportunity Table")
        st.dataframe(opportunity_df, use_container_width=True)

with tab_segments:
    st.header("Top Customer Segments")

    if segments_df.empty:
        st.info("No customer segment data yet.")
    else:
        if "pilot_readiness_score" in segments_df.columns:
            top_n = st.slider("Number of segments to show", 5, 25, 10)

            top_segments = segments_df.head(top_n)

            fig = px.bar(
                top_segments.sort_values("pilot_readiness_score", ascending=True),
                x="pilot_readiness_score",
                y="pilot_segment",
                orientation="h",
                hover_data=[
                    "service_category",
                    "region",
                    "occupation",
                    "age_group",
                    "suggested_business_idea",
                ],
                title="Top Customer Segments to Test First"
            )

            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(segments_df, use_container_width=True)

with tab_regions:
    st.header("Regional Needs")

    if regional_df.empty:
        st.info("No regional needs data yet.")
    else:
        region_options = sorted(regional_df["region"].dropna().unique())

        selected_region = st.selectbox(
            "Select region",
            options=["All"] + region_options
        )

        filtered_region_df = regional_df.copy()

        if selected_region != "All":
            filtered_region_df = filtered_region_df[
                filtered_region_df["region"] == selected_region
            ]

        if "local_need_score" in filtered_region_df.columns:
            fig = px.bar(
                filtered_region_df.sort_values("local_need_score", ascending=True),
                x="local_need_score",
                y="service_category",
                color="region",
                orientation="h",
                hover_data=[
                    "response_count",
                    "avg_budget_aed",
                    "avg_would_pay",
                    "local_priority",
                ],
                title="Local Need Score by Region and Service Category"
            )

            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(filtered_region_df, use_container_width=True)

with tab_raw:
    st.header("Raw Community Insights")

    if main_df.empty:
        st.info("No raw dashboard export yet.")
    else:
        filtered_df = main_df.copy()

        filter_columns = [
            "service_category",
            "region",
            "occupation",
            "age_group",
            "gender",
            "monthly_budget",
            "recommendation",
            "priority_level",
        ]

        with st.expander("Filters", expanded=True):
            for column in filter_columns:
                if column in filtered_df.columns:
                    options = sorted(filtered_df[column].dropna().unique())
                    selected = st.multiselect(
                        f"Filter by {column}",
                        options=options
                    )

                    if selected:
                        filtered_df = filtered_df[
                            filtered_df[column].isin(selected)
                        ]

        st.write(f"Showing {len(filtered_df)} rows")

        useful_columns = [
            "response_id",
            "region",
            "occupation",
            "age_group",
            "gender",
            "service_category",
            "monthly_budget",
            "would_pay",
            "sentiment_label",
            "business_opportunity_score",
            "recommendation",
            "suggested_business_idea",
            "opinion_text",
        ]

        available_columns = [
            col for col in useful_columns
            if col in filtered_df.columns
        ]

        st.dataframe(
            filtered_df[available_columns],
            use_container_width=True
        )