from pathlib import Path
from datetime import datetime
import json
import re
import shutil
import subprocess
import sys

import pandas as pd
import streamlit as st
import plotly.express as px

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_CSV = RAW_DIR / "responses_raw.csv"

ACTIVE_TABLEAU_EXPORT_DIR = PROJECT_ROOT / "dashboard" / "tableau_exports"

PROJECTS_DIR = PROJECT_ROOT / "data" / "projects"

PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="Bina Insight Dashboard",
    layout="wide"
)

st.title("Bina Insight")
st.caption("Community CSV/Excel data → AI agents → business opportunity dashboard")

def slugify(text):

    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")

    if not text:
        text = "project"

    return text


def create_project_id(project_name):

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{slugify(project_name)}_{timestamp}"


def get_project_dir(project_id):
    return PROJECTS_DIR / project_id


def get_project_metadata_path(project_id):
    return get_project_dir(project_id) / "metadata.json"


def get_project_raw_csv(project_id):
    return get_project_dir(project_id) / "raw" / "responses_raw.csv"


def get_project_tableau_dir(project_id):
    return get_project_dir(project_id) / "dashboard" / "tableau_exports"


def save_metadata(project_id, metadata):
    metadata_path = get_project_metadata_path(project_id)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    metadata_path.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8"
    )


def load_metadata(project_id):
    metadata_path = get_project_metadata_path(project_id)

    if not metadata_path.exists():
        return {
            "project_id": project_id,
            "project_name": project_id,
            "created_at": "",
            "updated_at": "",
            "row_count": 0,
        }

    return json.loads(metadata_path.read_text(encoding="utf-8"))


def list_projects():
    projects = []

    for folder in PROJECTS_DIR.iterdir():
        if folder.is_dir():
            metadata = load_metadata(folder.name)
            projects.append(metadata)

    projects = sorted(
        projects,
        key=lambda x: x.get("updated_at", ""),
        reverse=True
    )

    return projects


def save_uploaded_file_to_project(uploaded_file, project_id):

    project_raw_path = get_project_raw_csv(project_id)
    project_raw_path.parent.mkdir(parents=True, exist_ok=True)

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif file_name.endswith(".xlsx") or file_name.endswith(".xls"):
        df = pd.read_excel(uploaded_file)
    else:
        raise ValueError("Please upload a CSV or Excel file.")

    df.to_csv(project_raw_path, index=False, encoding="utf-8")

    return df


def copy_project_raw_to_active(project_id):

    project_raw_path = get_project_raw_csv(project_id)

    if not project_raw_path.exists():
        raise FileNotFoundError(
            f"This project has no raw CSV yet: {project_raw_path}"
        )

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    shutil.copy2(project_raw_path, RAW_CSV)


def clear_active_outputs():

    active_processed = PROJECT_ROOT / "data" / "processed"

    if active_processed.exists():
        shutil.rmtree(active_processed)

    if ACTIVE_TABLEAU_EXPORT_DIR.exists():
        shutil.rmtree(ACTIVE_TABLEAU_EXPORT_DIR)

    active_processed.mkdir(parents=True, exist_ok=True)
    ACTIVE_TABLEAU_EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def copy_active_outputs_to_project(project_id):

    project_tableau_dir = get_project_tableau_dir(project_id)

    if project_tableau_dir.exists():
        shutil.rmtree(project_tableau_dir)

    project_tableau_dir.parent.mkdir(parents=True, exist_ok=True)

    if ACTIVE_TABLEAU_EXPORT_DIR.exists():
        shutil.copytree(ACTIVE_TABLEAU_EXPORT_DIR, project_tableau_dir)


def run_pipeline_for_project(project_id):

    copy_project_raw_to_active(project_id)
    clear_active_outputs()

    pipeline_path = PROJECT_ROOT / "agents" / "pipeline_runner.py"

    if not pipeline_path.exists():
        raise FileNotFoundError(
            "Missing agents/pipeline_runner.py. Create it first."
        )

    result = subprocess.run(
        [sys.executable, str(pipeline_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Pipeline failed.\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        )

    copy_active_outputs_to_project(project_id)

    metadata = load_metadata(project_id)
    metadata["updated_at"] = datetime.now().isoformat(timespec="seconds")

    raw_df = pd.read_csv(get_project_raw_csv(project_id))
    metadata["row_count"] = int(len(raw_df))

    save_metadata(project_id, metadata)

    return result.stdout


def delete_project(project_id):
    project_dir = get_project_dir(project_id)

    if project_dir.exists():
        shutil.rmtree(project_dir)


def load_project_csv(project_id, filename):
    path = get_project_tableau_dir(project_id) / filename

    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(path)

st.sidebar.header("Projects")

projects = list_projects()
project_options = {
    f'{p.get("project_name", p["project_id"])}  |  {p.get("updated_at", "")}': p["project_id"]
    for p in projects
}

selected_project_label = None
selected_project_id = None

if project_options:
    selected_project_label = st.sidebar.selectbox(
        "Open past project",
        options=list(project_options.keys())
    )
    selected_project_id = project_options[selected_project_label]
else:
    st.sidebar.info("No projects yet. Create one below.")


st.sidebar.divider()

st.sidebar.subheader("Create New Project")

new_project_name = st.sidebar.text_input(
    "Project name",
    placeholder="Example: Hatta delivery study"
)

new_project_file = st.sidebar.file_uploader(
    "Upload CSV or Excel",
    type=["csv", "xlsx", "xls"],
    key="new_project_upload"
)

if st.sidebar.button("Create project and run analysis"):
    try:
        if not new_project_name.strip():
            st.sidebar.error("Please enter a project name.")
        elif new_project_file is None:
            st.sidebar.error("Please upload a CSV or Excel file.")
        else:
            project_id = create_project_id(new_project_name)

            project_dir = get_project_dir(project_id)
            project_dir.mkdir(parents=True, exist_ok=True)

            df = save_uploaded_file_to_project(
                uploaded_file=new_project_file,
                project_id=project_id
            )

            metadata = {
                "project_id": project_id,
                "project_name": new_project_name,
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "updated_at": datetime.now().isoformat(timespec="seconds"),
                "row_count": int(len(df)),
            }

            save_metadata(project_id, metadata)

            with st.spinner("Running agents for new project..."):
                logs = run_pipeline_for_project(project_id)

            st.success("Project created and analysis completed.")
            st.code(logs[-3000:])

            st.rerun()

    except Exception as error:
        st.sidebar.error(str(error))

if selected_project_id:
    metadata = load_metadata(selected_project_id)

    st.sidebar.divider()
    st.sidebar.subheader("Selected Project")

    st.sidebar.write(f"**Name:** {metadata.get('project_name', '')}")
    st.sidebar.write(f"**Rows:** {metadata.get('row_count', 0)}")
    st.sidebar.write(f"**Updated:** {metadata.get('updated_at', '')}")

    if st.sidebar.button("Re-run selected project"):
        try:
            with st.spinner("Re-running agents..."):
                logs = run_pipeline_for_project(selected_project_id)

            st.success("Project analysis refreshed.")
            st.code(logs[-3000:])
            st.rerun()

        except Exception as error:
            st.error(str(error))

    st.sidebar.subheader("Replace Project CSV")

    replacement_file = st.sidebar.file_uploader(
        "Upload new CSV/Excel for this project",
        type=["csv", "xlsx", "xls"],
        key="replace_project_upload"
    )

    if st.sidebar.button("Replace data and re-run"):
        try:
            if replacement_file is None:
                st.sidebar.error("Please upload a replacement file.")
            else:
                df = save_uploaded_file_to_project(
                    uploaded_file=replacement_file,
                    project_id=selected_project_id
                )

                metadata["updated_at"] = datetime.now().isoformat(timespec="seconds")
                metadata["row_count"] = int(len(df))
                save_metadata(selected_project_id, metadata)

                with st.spinner("Re-running agents with replacement data..."):
                    logs = run_pipeline_for_project(selected_project_id)

                st.success("Project data replaced and analysis updated.")
                st.code(logs[-3000:])
                st.rerun()

        except Exception as error:
            st.error(str(error))

    st.sidebar.subheader("Delete Project")

    confirm_delete = st.sidebar.checkbox(
        "I understand this will delete the selected project"
    )

    if st.sidebar.button("Delete selected project"):
        if confirm_delete:
            delete_project(selected_project_id)
            st.success("Project deleted.")
            st.rerun()
        else:
            st.sidebar.warning("Check the confirmation box first.")

if not selected_project_id:
    st.info("Create a project from the sidebar to begin.")
    st.stop()

main_df = load_project_csv(selected_project_id, "main_tableau_export.csv")
kpi_df = load_project_csv(selected_project_id, "kpi_cards.csv")
opportunity_df = load_project_csv(selected_project_id, "opportunity_scores.csv")
segments_df = load_project_csv(selected_project_id, "top_customer_segments.csv")
regional_df = load_project_csv(selected_project_id, "regional_needs.csv")
targeting_df = load_project_csv(selected_project_id, "targeting_summary.csv")


metadata = load_metadata(selected_project_id)

st.header(metadata.get("project_name", selected_project_id))
st.caption(f"Project ID: {selected_project_id}")


if main_df.empty and opportunity_df.empty:
    st.warning("This project has no dashboard outputs yet. Click 'Re-run selected project' in the sidebar.")
    st.stop()


def show_kpi_cards(kpi_df):
    if kpi_df.empty:
        st.info("No KPI cards available.")
        return

    cols = st.columns(4)

    for index, row in kpi_df.iterrows():
        with cols[index % 4]:
            st.metric(
                label=str(row.get("kpi_name", "")),
                value=str(row.get("kpi_value", ""))
            )

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
    st.subheader("Executive Overview")

    show_kpi_cards(kpi_df)

    st.divider()

    if not opportunity_df.empty and "business_opportunity_score" in opportunity_df.columns:
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

    if not targeting_df.empty:
        st.subheader("Targeting Summary")
        st.dataframe(targeting_df, use_container_width=True)


with tab_opportunities:
    st.subheader("Opportunity Analysis")

    if opportunity_df.empty:
        st.info("No opportunity data available.")
    else:
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

        st.dataframe(opportunity_df, use_container_width=True)


with tab_segments:
    st.subheader("Top Customer Segments")

    if segments_df.empty:
        st.info("No segment data available.")
    else:
        top_n = st.slider("Number of segments to show", 5, 25, 10)

        if "pilot_readiness_score" in segments_df.columns:
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
    st.subheader("Regional Needs")

    if regional_df.empty:
        st.info("No regional needs data available.")
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
    st.subheader("Raw Community Insights")

    if main_df.empty:
        st.info("No raw dashboard export available.")
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