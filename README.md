<p align="center">
  <img src="logo.jpeg" alt = "Logo" width="500" height="200">
</p>

# Bina Insight

🔗 Live Demo: https://bina-insight.streamlit.app/

**Bina Insight** is an AI-powered rural market intelligence prototype for entrepreneurs in rural UAE communities such as **Al Qua'a, Al Ain**.

It helps local entrepreneurs decide what to build using evidence instead of guesswork. The system collects community demand data, cleans it, analyzes opinions with multilingual NLP / keyword sentiment logic, converts the results into business metrics, and displays recommendations in an interactive bilingual dashboard.

The system deploys on **Streamlit Cloud for free** and runs without any model download using the default keyword sentiment mode. The demo uses synthetic data generated to reflect known characteristics of rural Al Ain communities. The pipeline is designed to be re-run immediately with real survey responses using the CSV upload feature.


## 1. Problem

Entrepreneurs in rural communities often make business decisions with very little local data.
They may not know:

- What services people actually need
- Which problems happen most often
- Which customer groups are most affected
- Whether people have enough budget for a solution
- Whether an idea is feasible, scalable, and testable

This means many small businesses start by guessing.
**Bina Insight reduces that uncertainty by turning community survey data into clear business intelligence.**


## 2. Target Users
Primary users:
- Local entrepreneurs
- Small business owners
- Youth founders
- Rural service providers
- Community business planners

Secondary users include:
- Local development teams
- Municipal innovation teams
- NGO or community support programs
- University entrepreneurship programs

The main example community is **Al Qua'a**, a rural area near Al Ain known for camel farming families, remote service needs, and strong stargazing tourism potential.


## 3. Why Would a Rural Entrepreneur Use This?
A rural entrepreneur would use Bina Insight because starting a business in a rural area is risky when there is limited local market data.

In communities like Al Qua'a, people may have very specific needs that are different from urban areas. For example, families may need camel care, transport, farm support, mobile healthcare, tutoring, tourism services, connectivity support, employment support, or maintenance services, but these needs are not always visible through normal business research.

Bina Insight helps rural entrepreneurs answer practical questions such as:

* What service do people in my area actually need?
* Which customer group should I target first?
* Are people willing to pay for this service?
* Is the idea feasible with limited resources?
* Can the idea grow beyond one small village?
* What should I test before investing money?

Instead of relying only on guessing, word-of-mouth, or copying businesses from cities, a rural entrepreneur can use Bina Insight to make decisions based on community responses and clear opportunity scores.

This makes the tool useful for someone who wants to start small, reduce risk, and build a business that matches real local demand.


## 4. What Makes Bina Insight Unique?

Bina Insight is unique because it focuses on **rural market intelligence**, not general business analytics.

Most business tools are designed for cities, large companies, or online markets. They usually assume that users already have structured customer data, sales records, or advanced business knowledge. Rural entrepreneurs often do not have that.

Bina Insight is different because it:

* Focuses on rural UAE communities such as Al Qua'a and Al Ain
* Works with simple survey responses instead of requiring complex business data
* Converts community opinions into business opportunity scores
* Combines demand, feasibility, scalability, and testability in one dashboard
* Supports Arabic and English for local accessibility
* Can run for free on Streamlit Cloud using lightweight keyword sentiment mode
* Can be re-run with real CSV or Excel survey data immediately
* Explains not only what idea is recommended, but also why it is recommended
* Includes evidence and falsifiability so recommendations can be challenged and tested

The uniqueness of Bina Insight is that it acts like a simple AI business advisor for rural entrepreneurs. It turns local voices into practical business decisions.

The core idea is:

```text
Real Voices. Real Opportunities.
```

Bina Insight does not just show data. It helps rural entrepreneurs understand what opportunity is worth building, who needs it, and how confident they should be before starting.

## 5. Solution Overview

Bina Insight uses a **five-stage AI pipeline**.
Each agent is an independent Python module with a single responsibility, defined inputs, and defined outputs. 

```text
Community CSV / Excel Upload
        ↓
Agent 1: Collector
        ↓
Agent 2: Cleaning
        ↓
Agent 3: Multilingual NLP
        ↓
Agent 4: Trend + Business Intelligence
        ↓
Agent 5: Dashboard Export
        ↓
Interactive Streamlit Dashboard
```

The dashboard answers the main entrepreneur question:
```text
What should I build, and why?
```
It provides:
* Demand analysis
* Customer segment insights
* Business opportunity scores
* Feasibility scores
* Scalability scores
* Testability scores
* Evidence behind each recommendation
* Business opportunity matrix
* Arabic / English interface
* CSV and Excel upload support
  

## 6. Main Features

### AI Pipeline
| Stage | File | Purpose |
|---|---|---|
| Agent 1 | `agents/collector_agent.py` | Collects uploaded CSV/Excel data or generates demo data |
| Agent 2 | `agents/cleaning_agent.py` | Cleans, standardizes, and prepares the data |
| Agent 3 | `agents/nlp_agent.py` | Runs multilingual sentiment analysis and topic/keyword extraction |
| Agent 4 | `agents/trend_agent.py` | Converts analysis into business metrics and recommendations |
| Agent 5 | `agents/dashboard_agent.py` | Exports clean files for dashboard and Tableau-style BI use |
| Dashboard | `dashboard/dashboard_app.py` | Shows insights in an interactive web app |

### Dashboard

The dashboard includes:

* Executive summary
* KPI cards
* Strongest business recommendation
* Business opportunity matrix
* Feasibility, scalability, and testability scores
* Evidence and falsifiability section
* Regional needs analysis
* Customer segment analysis
* Topic and keyword insights
* Arabic / English toggle
* CSV / Excel upload option


## 7. AI and Analysis Methods
Bina Insight is not only a dashboard. The analysis layer includes:

* Demand scoring
* Sentiment scoring
* Category-level opportunity ranking
* Customer segmentation
* Regional demand comparison
* Feasibility scoring
* Scalability scoring
* Testability scoring
* Business recommendation generation

By default, the system uses a lightweight keyword-based sentiment mode so it can deploy quickly on Streamlit Cloud without downloading large models.

Optional advanced mode can use transformer-based multilingual sentiment analysis if enabled locally.

### Default Deployment Mode

```text
USE_TRANSFORMER=false
```

This mode is best for:

* Streamlit Cloud deployment
* Fast demo loading
* No model download
* Stable hackathon presentation

### Optional Local Advanced Mode

```text
USE_TRANSFORMER=true
```

This mode is best for:

* Local testing
* Deeper multilingual NLP
* More advanced sentiment analysis
* Environments that can download and run larger AI models


## 8. Example Business Opportunities
The prototype can identify and rank opportunities such as:

- Mobile camel veterinary booking
- Livestock medicine delivery
- Stargazing tourism packages
- Marketplace for camel milk, dates, and local products
- Farm equipment rental and maintenance
- Rural transport to Al Ain
- Mobile healthcare visits
- Education and tutoring services
The strongest recommendation depends on the uploaded data and the generated demand patterns.


## 9. Project Structure
```text
rural-market-intelligence/
│
├── agents/
│   ├── __init__.py
│   ├── collector_agent.py
│   ├── cleaning_agent.py
│   ├── nlp_agent.py
│   ├── nlp_analyzer_agent.py
│   ├── trend_agent.py
│   ├── dashboard_agent.py
│   └── generate_demo_data.py
│
├── dashboard/
│   ├── dashboard_app.py
│   └── tableau_exports/
│       ├── kpi_cards.csv
│       ├── main_tableau_export.csv
│       ├── opportunity_scores.csv
│       ├── regional_needs.csv
│       ├── targeting_summary.csv
│       └── top_customer_segments.csv
│
├── data/
│   ├── raw/
│   │   ├── responses_raw.csv
│   │   └── collection_metadata.json
│   │
│   ├── cleaned/
│   │   ├── responses_cleaned.csv
│   │   └── categories/
│   │
│   └── processed/
│       ├── agent3_nlp/
│       ├── agent4_business/
│       └── tableau/
│
├── notebooks/
│   └── data_collection.ipynb
│
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── run_pipeline.py
```

Note: `agents/nlp_analyzer_agent.py` is kept as a small compatibility wrapper for older file names/imports. The main NLP implementation is `agents/nlp_agent.py`.


## 10. Data Schema
The pipeline expects survey data with columns similar to:
```text
response_id
age_group
gender
region
occupation
source
main_problem
needed_service
service_category
importance_level
frequency_of_problem
preferred_solution_type
monthly_budget
opinion_text
date_collected
```
The collector agent can fill some optional fields automatically.


## 11. Example Column Values

### gender
```text
male
female
prefer not to say
```
### age_group
```text
18-24
25-34
35-44
45-54
55-64
65+
```
### region
```text
Al Qua'a
Ghayathi
Liwa
Hatta
Masafi
Al Madam
Al Sila
Delma Island
Al Ain outskirts
```
### source
```text
volunteer
survey
government information
other
uploaded_file
```
### monthly_budget
```text
0-50 AED
51-100 AED
101-250 AED
251-500 AED
501-1000 AED
1000+ AED
```
### service_category
Examples:
```text
Veterinary & Camel Care
Tourism & Stargazing
Market Access
Farm Operations
Rural Transport
Mobile Healthcare
Education & Tutoring
Utilities & Maintenance
```
These are the main categories used by the current prototype and dashboard translation layer.


## 12. Setup Instructions
### 1. Clone the repository

```powershell
git clone <your-repository-url>
cd rural-market-intelligence
```
### 2. Create a virtual environment

```powershell
python -m venv .venv
```
### 3. Activate the virtual environment

```powershell
.venv\Scripts\activate
```
### 4. Install dependencies

```powershell
pip install -r requirements.txt
```
### 5. Create local environment file

```powershell
Copy-Item .env.example .env
```

Default `.env.example`:

```env
PROJECT_NAME=Bina Insight
RAW_DATA_PATH=data/raw/responses_raw.csv
CLEANED_DATA_PATH=data/cleaned/responses_cleaned.csv
PROCESSED_DATA_DIR=data/processed

USE_TRANSFORMER=false

USE_CLAUDE=false
ANTHROPIC_API_KEY=
CLAUDE_MODEL=claude-sonnet-4-6
```


## 13. Running the Project Locally
### Run the full pipeline

```powershell
python run_pipeline.py
```

### Run the dashboard

```powershell
streamlit run dashboard/dashboard_app.py
```

Then open the local URL shown in the terminal, usually:

```text
http://localhost:8501
```


## 14. Uploading a CSV or Excel File

The dashboard includes an upload section.

When a user uploads a file, the app automatically runs:

```text
collector_agent.py
cleaning_agent.py
nlp_agent.py
trend_agent.py
dashboard_agent.py
```

Then the dashboard refreshes with new results.

### Upload Flow

```text
CSV / Excel uploaded
        ↓
Saved to data/dashboard_uploads/
        ↓
Collector standardizes it
        ↓
Raw data saved to data/raw/responses_raw.csv
        ↓
Cleaning agent prepares clean data
        ↓
NLP agent analyzes text
        ↓
Trend agent creates business scores
        ↓
Dashboard agent exports BI files
        ↓
Dashboard updates
```


## 15. Dashboard Sections

The Streamlit dashboard includes:

### Landing Page

A bilingual introduction for Bina Insight.

### Upload Section

Allows CSV or Excel upload.

### What Should I Build?

Shows the strongest opportunity immediately.

### KPI Overview

Shows:

- Responses analyzed
- Regions covered
- Service categories
- Average budget

### AI Recommendation Cards

Shows the top opportunities with:

- Opportunity score
- Feasibility
- Scalability
- Testability
- Suggested business idea
- Best pilot segment
- Recommendation source
  
### Evidence and Falsifiability

Shows why the recommendation was selected and what kind of evidence could weaken or disprove it.

### Charts

Includes:

- Opportunity ranking
- Demand by service category
- Demand by region and category
- Business opportunity matrix

### Business Opportunity Matrix

This is the main decision-making chart.

It compares:

```text
x-axis = feasibility
y-axis = scalability
bubble size = opportunity score
color = service category
```

It also divides opportunities into decision zones:

- High priority
- Ready to scale
- Needs development
- Needs review

### Arabic / English Mode

The interface can switch between English and Arabic.

Arabic equivalents are shown when Arabic mode is selected.

### Tables

The dashboard shows clean simplified tables instead of raw technical column names.



## 16. Arabic / English Support

Bina Insight supports bilingual presentation.

The dashboard includes:

* English labels
* Arabic labels
* Arabic RTL layout
* Arabic service category translations
* Arabic table display
* Arabic explanations for key dashboard sections

This is important because rural UAE survey responses may include Arabic, English, or both.


## 17. Deployment

The project is designed to deploy on **Streamlit Community Cloud**.

Deployment settings:

```text
Repository: your GitHub repository
Branch: main
Main file path: dashboard/dashboard_app.py
Python version: 3.11 or 3.12
```

The default deployment mode uses:

```env
USE_TRANSFORMER=false
USE_CLAUDE=false
```

This allows the deployed app to run without downloading a large model.

The dashboard can still run using the committed synthetic demo data and can also process uploaded CSV or Excel files.


## 18. Optional External AI API

Claude API support is optional.

To use Claude, set:

```env
USE_CLAUDE=true
ANTHROPIC_API_KEY=your_key_here
```

For the public demo, keep:

```env
USE_CLAUDE=false
ANTHROPIC_API_KEY=
```

If no key is set, the system uses the built-in recommendation engine.


## 19. Running Individual Agents

### Collector Agent

```powershell
python agents/collector_agent.py
```

Outputs:

```text
data/raw/responses_raw.csv
data/raw/collection_metadata.json
```

### Cleaning Agent

```powershell
python agents/cleaning_agent.py
```

Outputs:

```text
data/cleaned/responses_cleaned.csv
data/cleaned/categories/
```

### NLP Agent

```powershell
python agents/nlp_agent.py
```

Outputs:

```text
data/processed/agent3_nlp/
```

### Trend Agent

```powershell
python agents/trend_agent.py
```

Outputs:

```text
data/processed/agent4_business/
```

### Dashboard Export Agent

```powershell
python agents/dashboard_agent.py
```

Outputs:

```text
dashboard/tableau_exports/
data/processed/tableau/
```


## 20. Files That Should Not Be Committed
Do not commit:

```text
.env
.venv/
__pycache__/
*.pyc
data/dashboard_uploads/
data/uploaded_files/
.streamlit/secrets.toml
```

For a practice or demo version, commit small synthetic demo outputs so the dashboard can be run immediately with:

```powershell
streamlit run dashboard/dashboard_app.py
```

Safe demo files include:

```text
data/raw/responses_raw.csv
data/cleaned/responses_cleaned.csv
data/processed/
dashboard/tableau_exports/*.csv
```

Do not commit private real survey data.


## 21. Troubleshooting

### Streamlit cannot find the dashboard

Run from the project root:

```powershell
streamlit run dashboard/dashboard_app.py
```

### Missing packages

Run:

```powershell
pip install -r requirements.txt
```

### Claude API key error

Set:

```env
USE_CLAUDE=false
ANTHROPIC_API_KEY=
```

### App is slow on Streamlit Cloud

Use the default lightweight mode:

```env
USE_TRANSFORMER=false
```

This avoids large model downloads.

### Uploaded CSV does not work

Check that the file includes key columns such as:

```text
region
service_category
importance_score
frequency_score
opinion_text
```

### Dashboard does not refresh after code changes

Stop and restart Streamlit:

```powershell
Ctrl + C
streamlit run dashboard/dashboard_app.py
```


## 22. Future Improvements

After the hackathon, the project can be improved with:

* Real survey collection from rural communities
* WhatsApp-based survey collection
* Database storage
* Login accounts for entrepreneurs
* Saved projects
* PDF report export
* Admin dashboard
* More advanced Arabic NLP
* Geospatial demand mapping
* Production API backend
* Mobile-friendly entrepreneur view


## 23. Status

```text
Prototype ready
Synthetic demo data included
CSV / Excel upload supported
Keyword sentiment mode enabled by default
Optional transformer mode available
Optional Claude API support available
Arabic / English dashboard available
Interactive Streamlit dashboard ready for deployment
```

## 24. License

This project was built as a hackathon prototype.

