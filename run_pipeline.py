from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parent


STEPS = [
    PROJECT_ROOT / "agents" / "collector_agent.py",
    PROJECT_ROOT / "agents" / "cleaning_agent.py",
    PROJECT_ROOT / "agents" / "nlp_agent.py",
    PROJECT_ROOT / "agents" / "trend_agent.py",
    PROJECT_ROOT / "agents" / "dashboard_agent.py",
]


def run_step(script_path):

    if not script_path.exists():
        raise FileNotFoundError(f"Missing pipeline step: {script_path}")

    print("\n" + "=" * 80)
    print(f"Running: {script_path.name}")
    print("=" * 80)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        check=True
    )

    return result.returncode


def main():
    print("Starting Bina Insight pipeline...")

    for step in STEPS:
        run_step(step)

    print("\nPipeline complete.")
    print()
    print("Run the Streamlit dashboard with:")
    print(r".venv\Scripts\python.exe -m streamlit run web\dashboard_app.py")
    print()
    print("Final dashboard files are in:")
    print(r"dashboard\tableau_exports")
    print()
    print("Main Tableau file:")
    print(r"dashboard\tableau_exports\main_tableau_export.csv")
    print()
    print("Business recommendation file:")
    print(r"dashboard\tableau_exports\opportunity_scores.csv")


if __name__ == "__main__":
    main()