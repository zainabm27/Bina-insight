"""
Run the full Bina Insight pipeline.

Demo:
python run_pipeline.py --demo

Upload:
python run_pipeline.py --input path/to/file.csv
"""
import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

def run_command(args):
    print("\n" + "=" * 80)
    print("Running:", " ".join(str(arg) for arg in args))
    print("=" * 80)
    subprocess.run([sys.executable] + [str(arg) for arg in args], cwd=PROJECT_ROOT, check=True)

def main():
    parser = argparse.ArgumentParser(description="Run Bina Insight collector, cleaning, NLP, BI, and dashboard-export agents.")
    parser.add_argument("--input", required=False, help="Optional CSV/Excel input file. If omitted, demo data is generated.")
    parser.add_argument("--demo", action="store_true", help="Generate demo Al Qua'a data.")
    parser.add_argument("--mode", choices=["overwrite", "append"], default="overwrite")
    args = parser.parse_args()
    if args.input and not args.demo:
        run_command(["agents/collector_agent.py", "--input", args.input, "--mode", args.mode])
    else:
        run_command(["agents/collector_agent.py", "--demo", "--mode", args.mode])
    run_command(["agents/cleaning_agent.py"])
    run_command(["agents/nlp_agent.py"])
    run_command(["agents/trend_agent.py"])
    run_command(["agents/dashboard_agent.py"])
    print("\nPipeline complete.")
    print("Run dashboard with: streamlit run dashboard/dashboard_app.py")

if __name__ == "__main__":
    main()
