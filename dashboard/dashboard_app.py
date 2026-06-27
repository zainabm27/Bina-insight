"""
Bina Insight Streamlit Dashboard
--------------------------------
Interactive dashboard for judges and entrepreneurs.

Final fixed version:
1. Centered landing page in English and Arabic.
2. Button-like sidebar filters using st.pills when available.
3. Arabic / English translation for labels, categories, regions, priorities, and source text.
4. Clean table names instead of technical column names.
5. Replaces the ugly budget/importance scatter with a Business Opportunity Matrix.
6. Adds a falsifiability and evidence section for judge evaluation.
7. Keeps Streamlit internal Deploy/settings popovers readable.
"""

from pathlib import Path
from datetime import datetime
import hashlib
import json
import subprocess
import sys
import pandas as pd
import streamlit as st
import plotly.express as px

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "dashboard_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
AGENT4_DIR = PROCESSED_DIR / "agent4_business"
TABLEAU_DIR = PROCESSED_DIR / "tableau"

RECOMMENDATIONS_CSV = AGENT4_DIR / "business_recommendations.csv"
REGION_NEEDS_CSV = AGENT4_DIR / "region_needs.csv"
SEGMENT_RECOMMENDATIONS_CSV = AGENT4_DIR / "segment_recommendations.csv"
TARGETING_SUMMARY_CSV = AGENT4_DIR / "customer_targeting_summary.csv"
TABLEAU_EXPORT_CSV = TABLEAU_DIR / "tableau_ready_export.csv"
METADATA_JSON = DATA_DIR / "raw" / "collection_metadata.json"

st.set_page_config(
    page_title="Bina Insight",
    page_icon="🌙",
    layout="wide",
)

LANGUAGE_OPTIONS = {
    "English": "en",
    "العربية": "ar",
}

TRANSLATIONS = {
    "en": {
        "view_insights": "View community insights →",
        "hero_title": "🌙 Bina Insight",
        "hero_subtitle": (
            "Community intelligence for Al Qua'a — one of the UAE's strongest rural entrepreneurship stories: "
            "camel farming families, remote service needs, and dark-sky stargazing tourism potential."
        ),
        "landing_subtitle": (
            "Market intelligence for rural entrepreneurs.<br>"
            "Built for communities like Al Qua'a, Al Ain — where camel farming, "
            "remote service access, and stargazing tourism create unique local opportunities."
        ),
        "upload_title": "Upload new community data",
        "upload_help": (
            "Upload a survey CSV or Excel file. The app will collect it, clean it, run NLP, "
            "generate business recommendations, and refresh the dashboard."
        ),
        "upload_label": "Upload a survey CSV or Excel file",
        "pipeline_running": "Running analysis pipeline...",
        "demo_running": "Preparing demo data and running the AI-agent pipeline...",
        "analysis_complete": "Analysis complete. Dashboard refreshed.",
        "analysis_failed": "Analysis failed.",
        "demo_failed": "The demo pipeline failed.",
        "already_analyzed": "This file was already analyzed.",
        "what_build": "What should I build?",
        "strongest_opportunity": "is the strongest opportunity in your community right now.",
        "start_here": "Start here:",
        "no_recommendations": "No recommendation data found yet.",
        "feasibility": "Feasibility",
        "scalability": "Scalability",
        "testability": "Testability",
        "feasibility_help": "How realistic is this to start with limited resources?",
        "scalability_help": "Can this grow beyond Al Qua'a to other communities?",
        "testability_help": "Can you test this idea cheaply before committing?",
        "overview": "Community intelligence overview",
        "responses": "Responses analyzed",
        "regions": "Regions covered",
        "categories": "Service categories",
        "avg_budget": "Average budget AED",
        "importance": "Importance",
        "top_opportunities": "Top AI-generated business opportunities",
        "opportunity_score": "Opportunity score",
        "best_pilot": "Best pilot segment",
        "why": "Why this opportunity",
        "source": "Recommendation source",
        "opportunity_ranking": "Opportunity ranking",
        "opportunity_chart_title": "Business opportunity score by service category",
        "demand_category": "Demand by service category",
        "demand_category_chart_title": "Number of responses by service category",
        "demand_region": "Demand by region and category",
        "demand_region_chart_title": "Where needs are concentrated",
        "opportunity_matrix": "Business opportunity matrix",
        "opportunity_matrix_title": "Feasibility vs scalability by service category",
        "details": "Detailed recommendation table",
        "local_needs": "Local needs by region",
        "segments": "Best customer segments to test first",
        "targeting": "Targeting summary",
        "raw": "Raw analyzed community responses",
        "filters": "Filters",
        "region": "Region",
        "service_category": "Service category",
        "all": "All",
        "language": "Language / اللغة",
        "arabic_note": (
            "Note: the dashboard interface is translated. Raw uploaded survey responses are shown as collected."
        ),
        "recommendation_from_ai": "Generated by Claude API",
        "recommendation_from_fallback": "Built-in recommendation engine",
        "need_score": "Need score",
        "payment_readiness": "Payment readiness",
        "pilot_segment": "Best pilot segment",
        "median_feasibility": "Median feasibility",
        "median_scalability": "Median scalability",
        "evidence_title": "Falsifiability & Evidence",
        "evidence_subtitle": (
            "This section shows what evidence supports the top recommendation, "
            "what assumptions are being made, and what would prove the recommendation wrong."
        ),
        "dataset_type": "Dataset type",
        "dataset_size": "Dataset size",
        "top_evidence_category": "Evidence category",
        "synthetic_dataset": "Synthetic / demo dataset",
        "uploaded_dataset": "Uploaded dataset",
        "loaded_dataset": "Loaded dashboard dataset",
        "evidence_warning": (
            "Current results should be treated as prototype evidence. If the data is synthetic, "
            "it proves the pipeline works, not that the real community demand has been validated."
        ),
        "evidence_for_recommendation": "Evidence behind the top recommendation",
        "top_category_responses": "Responses mentioning this category",
        "response_share": "Share of dataset",
        "avg_importance_evidence": "Average importance",
        "avg_budget_evidence": "Average budget",
        "top_region_evidence": "Most common region",
        "top_segment_evidence": "Most common segment",
        "scoring_formula": "Transparent scoring components",
        "scoring_formula_text": (
            "The opportunity ranking is based on measurable components generated by the pipeline: "
            "need, payment readiness, feasibility, scalability, and testability."
        ),
        "component": "Component",
        "value": "Value",
        "falsifiable_claim": "Falsifiable claim",
        "falsifiable_claim_text": (
            "Given this dataset and scoring method, the top category currently has the strongest "
            "business evidence. This claim can be disproven by uploading real survey data where "
            "another category has stronger need, willingness to pay, or broader segment demand."
        ),
        "what_would_disprove": "What would weaken or disprove this recommendation?",
        "disprove_1": "Fewer than 15% of real respondents mention this need.",
        "disprove_2": "Average importance falls below 3 out of 5.",
        "disprove_3": "Payment readiness or average budget is too low for a practical pilot.",
        "disprove_4": "The need appears in only one narrow customer segment.",
        "disprove_5": "Real interviews rank another service category as more urgent.",
        "validation_tests": "Internal validation checks",
        "test_name": "Check",
        "test_result": "Result",
        "test_status": "Status",
        "passed": "Pass",
        "needs_more_evidence": "Needs more evidence",
        "traceability_check": "Top recommendation is traceable to raw responses",
        "sample_size_check": "Dataset has at least 30 responses",
        "demand_threshold_check": "Average importance is at least 3 / 5",
        "segment_diversity_check": "Need appears across at least 2 occupations or segments",
        "upload_to_disprove": "How to test this live",
        "upload_to_disprove_text": (
            "Upload a new CSV or Excel file where transport, healthcare, education, or another category "
            "has stronger evidence. If the system is working, the top recommendation and matrix should change."
        ),
    },

    "ar": {
        "view_insights": "عرض رؤى المجتمع ←",
        "hero_title": "🌙 بناء إنسايت",
        "hero_subtitle": (
            "ذكاء مجتمعي لمنطقة القوع — قصة ريادة أعمال ريفية في الإمارات: "
            "أسر تعمل في مزارع الإبل، احتياجات خدمية بعيدة، وفرص سياحة فلكية بسبب السماء المظلمة."
        ),
        "landing_subtitle": (
            "ذكاء سوقي لرواد الأعمال في المجتمعات الريفية.<br>"
            "مصمم لمناطق مثل القوع في العين، حيث توجد مزارع الإبل، "
            "والحاجة للخدمات عن بعد، وفرص سياحة النجوم."
        ),
        "upload_title": "رفع بيانات مجتمعية جديدة",
        "upload_help": (
            "ارفع ملف استبيان بصيغة CSV أو Excel. سيقوم النظام بجمع البيانات وتنظيفها "
            "وتحليلها بالذكاء الاصطناعي ثم تحديث لوحة المعلومات."
        ),
        "upload_label": "ارفع ملف CSV أو Excel للاستبيان",
        "pipeline_running": "جاري تشغيل خط التحليل...",
        "demo_running": "جاري تجهيز بيانات تجريبية وتشغيل خط وكلاء الذكاء الاصطناعي...",
        "analysis_complete": "اكتمل التحليل. تم تحديث لوحة المعلومات.",
        "analysis_failed": "فشل التحليل.",
        "demo_failed": "فشل تشغيل خط البيانات التجريبية.",
        "already_analyzed": "تم تحليل هذا الملف مسبقاً.",
        "what_build": "ماذا يجب أن أبني؟",
        "strongest_opportunity": "هي أقوى فرصة في المجتمع حالياً.",
        "start_here": "ابدأ من هنا:",
        "no_recommendations": "لا توجد بيانات توصيات حتى الآن.",
        "feasibility": "قابلية التنفيذ",
        "scalability": "قابلية التوسع",
        "testability": "قابلية الاختبار",
        "feasibility_help": "ما مدى واقعية بدء هذا المشروع بموارد محدودة؟",
        "scalability_help": "هل يمكن توسيع الفكرة خارج القوع إلى مجتمعات أخرى؟",
        "testability_help": "هل يمكن اختبار الفكرة بتكلفة منخفضة قبل الاستثمار الكامل؟",
        "overview": "نظرة عامة على ذكاء المجتمع",
        "responses": "عدد الردود المحللة",
        "regions": "المناطق المشمولة",
        "categories": "فئات الخدمات",
        "avg_budget": "متوسط الميزانية بالدرهم",
        "importance": "الأهمية",
        "top_opportunities": "أفضل الفرص التجارية المقترحة بالذكاء الاصطناعي",
        "opportunity_score": "درجة الفرصة",
        "best_pilot": "أفضل شريحة للتجربة الأولية",
        "why": "سبب اختيار هذه الفرصة",
        "source": "مصدر التوصية",
        "opportunity_ranking": "ترتيب الفرص",
        "opportunity_chart_title": "درجة الفرصة التجارية حسب فئة الخدمة",
        "demand_category": "الطلب حسب فئة الخدمة",
        "demand_category_chart_title": "عدد الردود حسب فئة الخدمة",
        "demand_region": "الطلب حسب المنطقة وفئة الخدمة",
        "demand_region_chart_title": "أماكن تركز الاحتياجات",
        "opportunity_matrix": "مصفوفة الفرص التجارية",
        "opportunity_matrix_title": "قابلية التنفيذ مقابل قابلية التوسع حسب فئة الخدمة",
        "details": "جدول التوصيات التفصيلي",
        "local_needs": "الاحتياجات المحلية حسب المنطقة",
        "segments": "أفضل شرائح العملاء للاختبار أولاً",
        "targeting": "ملخص الاستهداف",
        "raw": "البيانات المجتمعية المحللة",
        "filters": "الفلاتر",
        "region": "المنطقة",
        "service_category": "فئة الخدمة",
        "all": "الكل",
        "language": "Language / اللغة",
        "arabic_note": (
            "ملاحظة: تم ترجمة واجهة لوحة المعلومات. أما ردود الاستبيان الأصلية فتظهر كما تم جمعها."
        ),
        "recommendation_from_ai": "تم توليدها باستخدام Claude API",
        "recommendation_from_fallback": "محرك توصيات داخلي",
        "need_score": "درجة الحاجة",
        "payment_readiness": "جاهزية الدفع",
        "pilot_segment": "أفضل شريحة للتجربة",
        "median_feasibility": "متوسط قابلية التنفيذ",
        "median_scalability": "متوسط قابلية التوسع",
        "evidence_title": "قابلية الاختبار والأدلة",
        "evidence_subtitle": (
            "يوضح هذا القسم الأدلة التي تدعم أفضل توصية، والافتراضات المستخدمة، "
            "وما الذي يمكن أن يضعف أو يثبت خطأ التوصية."
        ),
        "dataset_type": "نوع البيانات",
        "dataset_size": "حجم البيانات",
        "top_evidence_category": "فئة الدليل",
        "synthetic_dataset": "بيانات تجريبية / اصطناعية",
        "uploaded_dataset": "بيانات مرفوعة",
        "loaded_dataset": "بيانات لوحة المعلومات",
        "evidence_warning": (
            "يجب التعامل مع النتائج الحالية كدليل أولي للنموذج. إذا كانت البيانات اصطناعية، "
            "فهي تثبت أن خط التحليل يعمل، ولا تثبت أن الطلب الحقيقي في المجتمع تم التحقق منه."
        ),
        "evidence_for_recommendation": "الأدلة خلف أفضل توصية",
        "top_category_responses": "عدد الردود التي ذكرت هذه الفئة",
        "response_share": "نسبة الفئة من البيانات",
        "avg_importance_evidence": "متوسط الأهمية",
        "avg_budget_evidence": "متوسط الميزانية",
        "top_region_evidence": "أكثر منطقة تكراراً",
        "top_segment_evidence": "أكثر شريحة تكراراً",
        "scoring_formula": "مكونات التقييم الشفافة",
        "scoring_formula_text": (
            "يعتمد ترتيب الفرص على مكونات قابلة للقياس ينتجها خط التحليل: "
            "درجة الحاجة، جاهزية الدفع، قابلية التنفيذ، قابلية التوسع، وقابلية الاختبار."
        ),
        "component": "المكون",
        "value": "القيمة",
        "falsifiable_claim": "ادعاء قابل للاختبار",
        "falsifiable_claim_text": (
            "بناءً على هذه البيانات وطريقة التقييم، تمتلك الفئة الأعلى حالياً أقوى دليل تجاري. "
            "يمكن إثبات خطأ هذا الادعاء برفع بيانات استبيان حقيقية تظهر أن فئة أخرى لديها حاجة أقوى، "
            "أو استعداد دفع أعلى، أو طلب أوسع بين الشرائح."
        ),
        "what_would_disprove": "ما الذي قد يضعف أو يثبت خطأ هذه التوصية؟",
        "disprove_1": "إذا ذكر أقل من 15٪ من المشاركين الحقيقيين هذه الحاجة.",
        "disprove_2": "إذا انخفض متوسط الأهمية إلى أقل من 3 من 5.",
        "disprove_3": "إذا كانت جاهزية الدفع أو الميزانية المتوسطة منخفضة جداً لتجربة أولية.",
        "disprove_4": "إذا ظهرت الحاجة في شريحة ضيقة واحدة فقط.",
        "disprove_5": "إذا صنفت المقابلات الحقيقية فئة خدمة أخرى كأكثر إلحاحاً.",
        "validation_tests": "فحوصات تحقق داخلية",
        "test_name": "الفحص",
        "test_result": "النتيجة",
        "test_status": "الحالة",
        "passed": "نجح",
        "needs_more_evidence": "يحتاج أدلة أكثر",
        "traceability_check": "أفضل توصية يمكن تتبعها إلى الردود الخام",
        "sample_size_check": "حجم البيانات لا يقل عن 30 رداً",
        "demand_threshold_check": "متوسط الأهمية لا يقل عن 3 من 5",
        "segment_diversity_check": "الحاجة تظهر في مهنتين أو شريحتين على الأقل",
        "upload_to_disprove": "كيفية اختبار ذلك مباشرة",
        "upload_to_disprove_text": (
            "ارفع ملف CSV أو Excel جديداً تكون فيه فئة النقل أو الصحة أو التعليم أو أي فئة أخرى "
            "أقوى من حيث الأدلة. إذا كان النظام يعمل بشكل صحيح، يجب أن تتغير أفضل توصية والمصفوفة."
        ),
    },
}


CATEGORY_TRANSLATIONS_AR = {
    "Veterinary & Camel Care": "الرعاية البيطرية والإبل",
    "Tourism & Stargazing": "السياحة ورصد النجوم",
    "Market Access": "الوصول إلى الأسواق",
    "Farm Operations": "تشغيل وإدارة المزارع",
    "Rural Transport": "النقل الريفي",
    "Mobile Healthcare": "الرعاية الصحية المتنقلة",
    "Education & Tutoring": "التعليم والدروس الخصوصية",
    "Utilities & Maintenance": "الخدمات والصيانة",
    "Employment": "التوظيف",
    "Connectivity": "الاتصال والإنترنت",
    "Education": "التعليم",
    "Transport": "النقل",
    "Delivery": "التوصيل",
    "Agriculture": "الزراعة",
    "Repair": "الصيانة",
    "Tourism": "السياحة",
    "Other": "أخرى",
}

REGION_TRANSLATIONS_AR = {
    "Al Qua'a": "القوع",
    "Al Quaa": "القوع",
    "Al Ain outskirts": "أطراف العين",
    "Al Ain": "العين",
    "Sweihan": "سويحان",
    "Al Wathba": "الوثبة",
    "Liwa": "ليوا",
    "Ghayathi": "غياثي",
    "Al Sila": "السلع",
    "Al Silaa": "السلع",
    "Al Madam": "المدام",
    "Madam": "المدام",
    "Masfout": "مصفوت",
    "Hatta": "حتا",
    "Masafi": "مسافي",
    "Delma Island": "جزيرة دلما",
    "Dalma Island": "جزيرة دلما",
}

OCCUPATION_TRANSLATIONS_AR = {
    "camel farm owner": "مالك مزرعة إبل",
    "camel farm worker": "عامل في مزرعة إبل",
    "date farmer": "مزارع تمور",
    "small grocery owner": "مالك بقالة صغيرة",
    "home-based food seller": "بائع طعام منزلي",
    "teacher": "معلم",
    "student": "طالب",
    "driver": "سائق",
    "tourism guide": "مرشد سياحي",
    "craft seller": "بائع حرف يدوية",
    "healthcare worker": "عامل في الرعاية الصحية",
    "homemaker": "رب/ربة منزل",
    "mechanic": "ميكانيكي",
    "livestock supplier": "مورد مواشي",
    "farmer": "مزارع",
    "retired": "متقاعد",
    "employee": "موظف",
    "unemployed": "باحث عن عمل",
}

SOLUTION_TRANSLATIONS_AR = {
    "WhatsApp bot": "بوت واتساب",
    "mobile app": "تطبيق هاتف",
    "phone call service": "خدمة اتصال هاتفي",
    "SMS updates": "رسائل نصية",
    "in-person kiosk": "نقطة خدمة حضورية",
    "web dashboard": "لوحة ويب",
    "volunteer-assisted form": "نموذج بمساعدة متطوع",
    "unknown": "غير معروف",
}

RECOMMENDATION_TRANSLATIONS_AR = {
    "Strong opportunity": "فرصة قوية",
    "Promising, test with pilot": "واعدة، اختبرها بتجربة أولية",
    "Needs validation": "تحتاج إلى تحقق",
    "Low priority for now": "أولوية منخفضة حالياً",
    "High priority": "أولوية عالية",
    "Medium priority": "أولوية متوسطة",
    "Low priority": "أولوية منخفضة",
    "high priority": "أولوية عالية",
    "medium priority": "أولوية متوسطة",
    "low priority": "أولوية منخفضة",
}

SOURCE_TRANSLATIONS = {
    "anthropic_claude": {
        "en": "Generated by Claude API",
        "ar": "تم توليدها باستخدام Claude API",
    },
    "gemini_api": {
        "en": "Generated by Gemini API",
        "ar": "تم توليدها باستخدام Gemini API",
    },
    "fallback_no_api_key": {
        "en": "Built-in recommendation engine",
        "ar": "محرك توصيات داخلي",
    },
}

FALLBACK_IDEAS_AR = {
    "Veterinary & Camel Care": (
        "تطبيق حجز طبيب بيطري متنقل لمزارع الإبل في القوع، "
        "مع توصيل أدوية المواشي في نفس اليوم من مدينة العين."
    ),
    "Tourism & Stargazing": (
        "منصة حجز لتجارب رصد النجوم في القوع تربط الزوار بالمرشدين المحليين، "
        "مع باقات تخييم وتلسكوبات ومنتجات محلية."
    ),
    "Market Access": (
        "سوق مجتمعي لبيع حليب الإبل والتمور والمنتجات المحلية، "
        "مع تنظيم التوصيل إلى العين وأبوظبي."
    ),
    "Farm Operations": (
        "خدمة تنسيق لتأجير معدات المزارع وصيانتها لمزارع الإبل والتمور في منطقة القوع."
    ),
    "Rural Transport": (
        "خدمة نقل ريفي مجدولة تربط أسر ومزارع القوع بالخدمات الأساسية في مدينة العين."
    ),
    "Mobile Healthcare": (
        "خدمة فحوصات صحية متنقلة وتوصيل أدوية للعائلات وكبار السن والعاملين في المزارع في القوع."
    ),
    "Education & Tutoring": (
        "دروس هجينة وورش مهارات رقمية للطلاب ورواد الأعمال الشباب في القوع."
    ),
    "Utilities & Maintenance": (
        "دليل موثوق للصيانة المتنقلة يشمل التكييف والري والطاقة الشمسية والإنترنت ومعدات المزارع في القوع."
    ),
    "Employment": (
        "منصة محلية تربط الباحثين عن عمل في المناطق الريفية بفرص مؤقتة في المزارع والسياحة والخدمات."
    ),
    "Connectivity": (
        "خدمة لتجميع بلاغات ضعف الإنترنت في المناطق الريفية وتحويلها إلى تقارير واضحة لمزودي الخدمة."
    ),
}


selected_language_label = st.sidebar.selectbox(
    "Language / اللغة",
    list(LANGUAGE_OPTIONS.keys()),
)

LANG = LANGUAGE_OPTIONS[selected_language_label]

def t(key: str) -> str:
    return TRANSLATIONS[LANG].get(key, key)


def display_category(category) -> str:
    category = str(category)
    return CATEGORY_TRANSLATIONS_AR.get(category, category) if LANG == "ar" else category


def display_region(region) -> str:
    region = str(region)
    return REGION_TRANSLATIONS_AR.get(region, region) if LANG == "ar" else region


def display_occupation(occupation) -> str:
    occupation = str(occupation)
    occupation_key = occupation.lower().strip()
    return OCCUPATION_TRANSLATIONS_AR.get(occupation_key, occupation) if LANG == "ar" else occupation


def display_solution(solution) -> str:
    solution = str(solution)
    return SOLUTION_TRANSLATIONS_AR.get(solution, solution) if LANG == "ar" else solution


def display_recommendation(label) -> str:
    label = str(label)
    return RECOMMENDATION_TRANSLATIONS_AR.get(label, label) if LANG == "ar" else label


def display_source(source) -> str:
    source = str(source)
    if source in SOURCE_TRANSLATIONS:
        return SOURCE_TRANSLATIONS[source][LANG]
    return source


def display_business_idea(row) -> str:
    category = str(row.get("service_category", ""))
    if LANG == "ar":
        return FALLBACK_IDEAS_AR.get(category, str(row.get("suggested_business_idea", "")))
    return str(row.get("suggested_business_idea", ""))


def format_pilot_segment(row) -> str:
    region = row.get("best_test_region", "")
    occupation = row.get("best_test_occupation", "")
    age = row.get("best_test_age_group", "")

    if (pd.isna(region) or str(region).strip() == "") and "first_pilot_segment" in row:
        parts = str(row.get("first_pilot_segment", "")).split("|")
        parts = [part.strip() for part in parts]
        region = parts[0] if len(parts) > 0 else ""
        occupation = parts[1] if len(parts) > 1 else ""
        age = parts[2] if len(parts) > 2 else ""

    if LANG == "ar":
        return f"{display_region(region)} | {display_occupation(occupation)} | {age}"

    return f"{region} | {occupation} | {age}"


def format_why(row) -> str:
    need = row.get("need_score", "")
    payment = row.get("payment_readiness_score", "")
    pilot = format_pilot_segment(row)

    try:
        need = f"{float(need):.1f}"
    except (TypeError, ValueError):
        need = str(need)

    try:
        payment = f"{float(payment):.1f}"
    except (TypeError, ValueError):
        payment = str(payment)

    return f"{t('need_score')}: {need}, {t('payment_readiness')}: {payment}, {t('pilot_segment')}: {pilot}"


def add_display_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "service_category" in df.columns:
        df["display_service_category"] = df["service_category"].apply(display_category)

    if "region" in df.columns:
        df["display_region"] = df["region"].apply(display_region)

    if "occupation" in df.columns:
        df["display_occupation"] = df["occupation"].apply(display_occupation)

    if "preferred_solution_type" in df.columns:
        df["display_solution"] = df["preferred_solution_type"].apply(display_solution)

    if "recommendation" in df.columns:
        df["display_recommendation"] = df["recommendation"].apply(display_recommendation)

    if "priority_level" in df.columns:
        df["display_priority"] = df["priority_level"].apply(display_recommendation)

    if "local_priority" in df.columns:
        df["display_local_priority"] = df["local_priority"].apply(display_recommendation)

    if "pilot_priority" in df.columns:
        df["display_pilot_priority"] = df["pilot_priority"].apply(display_recommendation)

    if "recommendation_source" in df.columns:
        df["display_source"] = df["recommendation_source"].apply(display_source)

    return df


def clean_table_for_display(df: pd.DataFrame, table_type: str) -> pd.DataFrame:

    if df.empty:
        return df

    df = add_display_columns(df)

    if table_type == "recommendations":
        columns_map_en = {
            "display_service_category": "Service",
            "business_opportunity_score": "Opportunity",
            "feasibility_score": "Feasibility",
            "scalability_score": "Scalability",
            "testability_score": "Testability",
            "display_recommendation": "Status",
            "suggested_business_idea": "Business idea",
            "display_source": "Source",
        }
        columns_map_ar = {
            "display_service_category": "الخدمة",
            "business_opportunity_score": "درجة الفرصة",
            "feasibility_score": "قابلية التنفيذ",
            "scalability_score": "قابلية التوسع",
            "testability_score": "قابلية الاختبار",
            "display_recommendation": "الحالة",
            "suggested_business_idea": "فكرة المشروع",
            "display_source": "المصدر",
        }

    elif table_type == "region_needs":
        columns_map_en = {
            "display_region": "Region",
            "display_service_category": "Service",
            "response_count": "Responses",
            "avg_importance": "Importance",
            "avg_frequency": "Frequency",
            "avg_budget_aed": "Budget AED",
            "local_need_score": "Local need",
            "display_local_priority": "Priority",
            "top_occupation": "Top occupation",
        }
        columns_map_ar = {
            "display_region": "المنطقة",
            "display_service_category": "الخدمة",
            "response_count": "عدد الردود",
            "avg_importance": "الأهمية",
            "avg_frequency": "التكرار",
            "avg_budget_aed": "الميزانية",
            "local_need_score": "درجة الحاجة",
            "display_local_priority": "الأولوية",
            "top_occupation": "أبرز مهنة",
        }

    elif table_type == "segments":
        columns_map_en = {
            "display_service_category": "Service",
            "display_region": "Region",
            "display_occupation": "Occupation",
            "age_group": "Age",
            "response_count": "Responses",
            "pilot_readiness_score": "Pilot readiness",
            "display_pilot_priority": "Priority",
            "suggested_business_idea": "Business idea",
        }
        columns_map_ar = {
            "display_service_category": "الخدمة",
            "display_region": "المنطقة",
            "display_occupation": "المهنة",
            "age_group": "العمر",
            "response_count": "عدد الردود",
            "pilot_readiness_score": "جاهزية التجربة",
            "display_pilot_priority": "الأولوية",
            "suggested_business_idea": "فكرة المشروع",
        }

    elif table_type == "targeting":
        columns_map_en = {
            "target_type": "Type",
            "target_group": "Group",
            "score": "Score",
            "meaning": "Meaning",
        }
        columns_map_ar = {
            "target_type": "النوع",
            "target_group": "الفئة",
            "score": "الدرجة",
            "meaning": "المعنى",
        }

    elif table_type == "raw":
        columns_map_en = {
            "response_id": "ID",
            "age_group": "Age",
            "gender": "Gender",
            "display_region": "Region",
            "display_occupation": "Occupation",
            "display_service_category": "Service",
            "main_problem": "Problem",
            "needed_service": "Needed service",
            "opinion_text": "Opinion",
            "importance_score": "Importance",
            "frequency_of_problem": "Frequency",
            "monthly_budget": "Budget",
            "sentiment_label": "Sentiment",
        }
        columns_map_ar = {
            "response_id": "المعرف",
            "age_group": "العمر",
            "gender": "الجنس",
            "display_region": "المنطقة",
            "display_occupation": "المهنة",
            "display_service_category": "الخدمة",
            "main_problem": "المشكلة",
            "needed_service": "الخدمة المطلوبة",
            "opinion_text": "الرأي",
            "importance_score": "الأهمية",
            "frequency_of_problem": "التكرار",
            "monthly_budget": "الميزانية",
            "sentiment_label": "المشاعر",
        }

    else:
        return df

    columns_map = columns_map_ar if LANG == "ar" else columns_map_en
    existing = [col for col in columns_map if col in df.columns]
    display_df = df[existing].rename(columns=columns_map)

    if LANG == "ar":
        idea_col = "فكرة المشروع"
        if idea_col in display_df.columns and "service_category" in df.columns:
            translated_ideas = []
            categories = df["service_category"].tolist()
            original_ideas = display_df[idea_col].tolist()
            for index, original_idea in enumerate(original_ideas):
                category = categories[index] if index < len(categories) else ""
                translated_ideas.append(FALLBACK_IDEAS_AR.get(str(category), str(original_idea)))
            display_df[idea_col] = translated_ideas

        if "أبرز مهنة" in display_df.columns:
            display_df["أبرز مهنة"] = display_df["أبرز مهنة"].apply(display_occupation)

        if "المشاعر" in display_df.columns:
            display_df["المشاعر"] = display_df["المشاعر"].replace({
                "positive": "إيجابي",
                "neutral": "محايد",
                "negative": "سلبي",
            })

        if "الجنس" in display_df.columns:
            display_df["الجنس"] = display_df["الجنس"].replace({
                "male": "ذكر",
                "female": "أنثى",
                "prefer not to say": "أفضل عدم الإفصاح",
            })

        if "التكرار" in display_df.columns:
            display_df["التكرار"] = display_df["التكرار"].replace({
                "daily": "يومي",
                "weekly": "أسبوعي",
                "monthly": "شهري",
                "occasionally": "أحياناً",
                "rarely": "نادراً",
                "unknown": "غير معروف",
            })

    return display_df


def sidebar_choice(label, options, default, format_func):

    return st.sidebar.selectbox(
        label,
        options,
        index=options.index(default) if default in options else 0,
        format_func=format_func,
    )

def load_metadata(path: Path) -> dict:
    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def infer_dataset_type(metadata: dict, df: pd.DataFrame) -> str:
    metadata_text = " ".join(str(value).lower() for value in metadata.values())

    if "source" in df.columns:
        sources_text = " ".join(df["source"].dropna().astype(str).str.lower().unique().tolist())
    else:
        sources_text = ""

    combined_text = f"{metadata_text} {sources_text}"

    if "uploaded" in combined_text or "upload" in combined_text:
        return t("uploaded_dataset")

    if "demo" in combined_text or "synthetic" in combined_text or "generated" in combined_text:
        return t("synthetic_dataset")

    return t("loaded_dataset")


def safe_numeric_mean(df: pd.DataFrame, column: str, default: float = 0.0) -> float:
    if column not in df.columns or df.empty:
        return default

    values = pd.to_numeric(df[column], errors="coerce").dropna()

    if values.empty:
        return default

    return float(values.mean())


def safe_mode_value(df: pd.DataFrame, column: str, default: str = "—") -> str:
    if column not in df.columns or df.empty:
        return default

    values = df[column].dropna().astype(str)

    if values.empty:
        return default

    mode_values = values.mode()

    if mode_values.empty:
        return default

    return str(mode_values.iloc[0])


def safe_score(row, column: str, default: float = 0.0) -> float:
    try:
        value = row.get(column, default)
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def status_label(condition: bool) -> str:
    if condition:
        return f"{t('passed')}"
    return f"{t('needs_more_evidence')}"


def build_evidence_section(rec_df: pd.DataFrame, main_df: pd.DataFrame, metadata: dict):
    if rec_df.empty or main_df.empty:
        return

    top = rec_df.sort_values(
        "business_opportunity_score",
        ascending=False,
    ).iloc[0]

    top_category = str(top.get("service_category", ""))
    top_category_display = display_category(top_category)

    if "service_category" in main_df.columns:
        category_df = main_df[main_df["service_category"].astype(str) == top_category].copy()
    else:
        category_df = pd.DataFrame()

    total_responses = len(main_df)
    category_responses = len(category_df)
    response_share = (category_responses / total_responses * 100) if total_responses else 0

    avg_importance = safe_numeric_mean(category_df, "importance_score")
    avg_budget = safe_numeric_mean(category_df, "budget_midpoint_aed")

    top_region = display_region(safe_mode_value(category_df, "region"))
    top_occupation = display_occupation(safe_mode_value(category_df, "occupation"))

    unique_occupations = (
        category_df["occupation"].dropna().astype(str).nunique()
        if "occupation" in category_df.columns and not category_df.empty
        else 0
    )

    dataset_type = infer_dataset_type(metadata, main_df)

    st.header(t("evidence_title"))
    st.caption(t("evidence_subtitle"))

    st.warning(t("evidence_warning"))

    evidence_col1, evidence_col2, evidence_col3 = st.columns(3)

    evidence_col1.metric(t("dataset_type"), dataset_type)
    evidence_col2.metric(t("dataset_size"), f"{total_responses}")
    evidence_col3.metric(t("top_evidence_category"), top_category_display)

    st.subheader(t("evidence_for_recommendation"))

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

    metric_col1.metric(t("top_category_responses"), f"{category_responses}")
    metric_col2.metric(t("response_share"), f"{response_share:.1f}%")
    metric_col3.metric(t("avg_importance_evidence"), f"{avg_importance:.2f}/5")
    metric_col4.metric(t("avg_budget_evidence"), f"{avg_budget:.0f} AED")

    segment_col1, segment_col2 = st.columns(2)
    segment_col1.info(f"**{t('top_region_evidence')}:** {top_region}")
    segment_col2.info(f"**{t('top_segment_evidence')}:** {top_occupation}")

    st.subheader(t("scoring_formula"))
    st.write(t("scoring_formula_text"))

    score_rows = [
        (t("need_score"), safe_score(top, "need_score")),
        (t("payment_readiness"), safe_score(top, "payment_readiness_score")),
        (t("feasibility"), safe_score(top, "feasibility_score")),
        (t("scalability"), safe_score(top, "scalability_score")),
        (t("testability"), safe_score(top, "testability_score")),
        (t("opportunity_score"), safe_score(top, "business_opportunity_score")),
    ]

    score_df = pd.DataFrame(
        score_rows,
        columns=[t("component"), t("value")],
    )

    st.dataframe(
        score_df,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader(t("falsifiable_claim"))
    st.info(t("falsifiable_claim_text"))

    with st.expander(t("what_would_disprove"), expanded=True):
        if LANG == "ar":
            st.markdown(
                f"""
                <div class="rtl-bullet-list">
                    <div class="rtl-bullet-item"><span class="rtl-bullet-dot">•</span><span>{t("disprove_1")}</span></div>
                    <div class="rtl-bullet-item"><span class="rtl-bullet-dot">•</span><span>{t("disprove_2")}</span></div>
                    <div class="rtl-bullet-item"><span class="rtl-bullet-dot">•</span><span>{t("disprove_3")}</span></div>
                    <div class="rtl-bullet-item"><span class="rtl-bullet-dot">•</span><span>{t("disprove_4")}</span></div>
                    <div class="rtl-bullet-item"><span class="rtl-bullet-dot">•</span><span>{t("disprove_5")}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                - {t("disprove_1")}
                - {t("disprove_2")}
                - {t("disprove_3")}
                - {t("disprove_4")}
                - {t("disprove_5")}
                """
            )

    st.subheader(t("validation_tests"))

    response_word = "رداً" if LANG == "ar" else "responses"
    segment_word = "شرائح" if LANG == "ar" else "segments"

    validation_rows = [
        {
            t("test_name"): t("traceability_check"),
            t("test_result"): f"{category_responses} {response_word}",
            t("test_status"): status_label(category_responses > 0),
        },
        {
            t("test_name"): t("sample_size_check"),
            t("test_result"): f"{total_responses} {response_word}",
            t("test_status"): status_label(total_responses >= 30),
        },
        {
            t("test_name"): t("demand_threshold_check"),
            t("test_result"): f"{avg_importance:.2f} من 5" if LANG == "ar" else f"{avg_importance:.2f}/5",
            t("test_status"): status_label(avg_importance >= 3),
        },
        {
            t("test_name"): t("segment_diversity_check"),
            t("test_result"): f"{unique_occupations} {segment_word}",
            t("test_status"): status_label(unique_occupations >= 2),
        },
    ]

    st.dataframe(
        pd.DataFrame(validation_rows),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader(t("upload_to_disprove"))
    st.write(t("upload_to_disprove_text"))

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .bina-hero {
        background: linear-gradient(135deg, #0b132b 0%, #1a1a2e 45%, #16213e 100%);
        padding: 2rem;
        border-radius: 18px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(232, 201, 122, 0.25);
        box-shadow: 0 12px 30px rgba(0,0,0,0.18);
    }

    .bina-hero h1 {
        color: #e8c97a;
        margin: 0;
        font-size: 2.4rem;
    }

    .bina-hero p {
        color: #c9d1e8;
        margin: 0.6rem 0 0;
        font-size: 1.05rem;
        line-height: 1.6;
    }

    [data-testid="stExpander"] summary {
        padding-inline-end: 3rem !important;
    }

    [data-testid="stExpander"] details summary p {
        overflow-wrap: anywhere;
        word-break: normal;
    }

    div[data-testid="stAlert"] div {
        overflow-wrap: anywhere;
        word-break: normal;
        line-height: 1.8;
    }

    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
        margin-top: 1rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


if LANG == "ar":
    st.markdown(
        """
        <style>
        .main .block-container {
            direction: rtl;
            text-align: right;
        }

        [data-testid="stMarkdownContainer"] {
            direction: rtl;
            text-align: right;
        }

        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] li {
            direction: rtl;
            text-align: right;
        }

        .bina-hero,
        .bina-hero h1,
        .bina-hero p {
            direction: rtl;
            text-align: right;
        }

        [data-testid="stAlert"],
        [data-testid="stAlert"] div {
            direction: rtl;
            text-align: right;
            overflow-wrap: anywhere;
            line-height: 1.8;
        }

        [data-testid="stExpander"] {
            direction: rtl;
            text-align: right;
        }

        [data-testid="stExpander"] summary {
            direction: rtl;
            text-align: right;
            padding-left: 4rem !important;
            padding-right: 1rem !important;
        }

        [data-testid="stExpander"] summary p {
            overflow-wrap: anywhere;
            line-height: 1.8;
        }

        [data-testid="stSidebar"],
        [data-testid="stSidebar"] * {
            direction: rtl;
            text-align: right;
        }

        [data-testid="stMetric"],
        [data-testid="stMetric"] label,
        [data-testid="stMetric"] div {
            direction: rtl;
            text-align: right;
        }

        [data-testid="stFileUploader"],
        [data-testid="stFileUploader"] * {
            direction: rtl;
            text-align: right;
        }

        .stDataFrame,
        [data-testid="stDataFrame"],
        .stDataFrame *,
        [data-testid="stDataFrame"] * {
            direction: ltr;
            text-align: left;
        }

        div[role="dialog"],
        div[role="dialog"] *,
        [data-testid="stPopover"],
        [data-testid="stPopover"] *,
        [data-testid="stToolbar"],
        [data-testid="stToolbar"] * {
            direction: ltr !important;
            text-align: left !important;
        }

        button[aria-label="Close"],
        button[title="Close"] {
            z-index: 999999 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

if "started" not in st.session_state:
    st.session_state.started = False

if "last_upload_hash" not in st.session_state:
    st.session_state.last_upload_hash = None

if not st.session_state.started:
    landing_direction = "rtl" if LANG == "ar" else "ltr"

    st.markdown(
        f"""
        <div style='
            max-width:760px;
            margin:4rem auto;
            text-align:center;
            direction:{landing_direction};
            display:flex;
            flex-direction:column;
            align-items:center;
            justify-content:center;
        '>
            <h1 style='font-size:3.4rem;margin-bottom:0.5rem'>{t("hero_title")}</h1>
            <p style='font-size:1.2rem;color:gray;line-height:1.9;text-align:center'>
            {t("landing_subtitle")}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button(t("view_insights"), use_container_width=True):
            st.session_state.started = True
            st.rerun()

    st.stop()

@st.cache_data(show_spinner=False)
def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


def run_pipeline_with_upload(uploaded_file) -> tuple[bool, str]:
    uploaded_bytes = uploaded_file.getbuffer()
    upload_hash = hashlib.sha256(uploaded_bytes).hexdigest()

    if upload_hash == st.session_state.last_upload_hash:
        return True, t("already_analyzed")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = uploaded_file.name.replace(" ", "_")
    save_path = UPLOAD_DIR / f"{timestamp}_{safe_name}"

    with open(save_path, "wb") as file:
        file.write(uploaded_bytes)

    command = [
        sys.executable,
        str(PROJECT_ROOT / "run_pipeline.py"),
        "--input",
        str(save_path),
    ]

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return False, result.stderr or result.stdout

    st.session_state.last_upload_hash = upload_hash
    st.cache_data.clear()

    return True, result.stdout


def run_demo_pipeline() -> tuple[bool, str]:
    command = [
        sys.executable,
        str(PROJECT_ROOT / "run_pipeline.py"),
        "--demo",
    ]

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return False, result.stderr or result.stdout

    st.cache_data.clear()

    return True, result.stdout


def ensure_data_exists():
    if RECOMMENDATIONS_CSV.exists() and TABLEAU_EXPORT_CSV.exists():
        return

    with st.spinner(t("demo_running")):
        ok, message = run_demo_pipeline()

    if not ok:
        st.error(t("demo_failed"))
        st.code(message)
        st.stop()

st.markdown(
    f"""
    <div class='bina-hero'>
      <h1>{t("hero_title")}</h1>
      <p>{t("hero_subtitle")}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if LANG == "ar":
    st.caption(t("arabic_note"))

with st.expander(t("upload_title"), expanded=True):
    st.write(t("upload_help"))

    uploaded = st.file_uploader(
        t("upload_label"),
        type=["csv", "xlsx", "xls"],
    )

    if uploaded:
        with st.spinner(t("pipeline_running")):
            ok, message = run_pipeline_with_upload(uploaded)

        if ok:
            st.success(t("analysis_complete"))
        else:
            st.error(t("analysis_failed"))
            st.code(message)
            st.stop()

ensure_data_exists()

rec_df = load_csv(RECOMMENDATIONS_CSV)
main_df = load_csv(TABLEAU_EXPORT_CSV)

region_needs_df = (
    load_csv(REGION_NEEDS_CSV)
    if REGION_NEEDS_CSV.exists()
    else pd.DataFrame()
)

segments_df = (
    load_csv(SEGMENT_RECOMMENDATIONS_CSV)
    if SEGMENT_RECOMMENDATIONS_CSV.exists()
    else pd.DataFrame()
)

targeting_df = (
    load_csv(TARGETING_SUMMARY_CSV)
    if TARGETING_SUMMARY_CSV.exists()
    else pd.DataFrame()
)

rec_df = add_display_columns(rec_df)
main_df = add_display_columns(main_df)

if not region_needs_df.empty:
    region_needs_df = add_display_columns(region_needs_df)

if not segments_df.empty:
    segments_df = add_display_columns(segments_df)

if not targeting_df.empty:
    targeting_df = add_display_columns(targeting_df)

metadata = load_metadata(METADATA_JSON)

st.sidebar.header(t("filters"))

all_value = "__all__"

region_options = (
    [all_value] + sorted(main_df["region"].dropna().unique().tolist())
    if "region" in main_df.columns
    else [all_value]
)

selected_region = sidebar_choice(
    t("region"),
    region_options,
    default=all_value,
    format_func=lambda value: t("all") if value == all_value else display_region(value),
)

category_options = (
    [all_value] + sorted(main_df["service_category"].dropna().unique().tolist())
    if "service_category" in main_df.columns
    else [all_value]
)

selected_category = sidebar_choice(
    t("service_category"),
    category_options,
    default=all_value,
    format_func=lambda value: t("all") if value == all_value else display_category(value),
)

filtered_df = main_df.copy()

if selected_region != all_value and "region" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["region"] == selected_region]

if selected_category != all_value and "service_category" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["service_category"] == selected_category]

filtered_df = add_display_columns(filtered_df)

st.header(t("what_build"))

if not rec_df.empty:
    top = rec_df.iloc[0]

    top_category = display_category(top["service_category"])
    top_idea = display_business_idea(top)

    st.success(
        f"""
        **{top_category}** {t("strongest_opportunity")}

        {top_idea}

        **{t("start_here")}** {format_pilot_segment(top)}
        """
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        t("feasibility"),
        f"{top['feasibility_score']:.0f}/100",
        help=t("feasibility_help"),
    )

    col2.metric(
        t("scalability"),
        f"{top['scalability_score']:.0f}/100",
        help=t("scalability_help"),
    )

    col3.metric(
        t("testability"),
        f"{top['testability_score']:.0f}/100",
        help=t("testability_help"),
    )

else:
    st.warning(t("no_recommendations"))

build_evidence_section(rec_df, main_df, metadata)

st.header(t("overview"))

col1, col2, col3, col4 = st.columns(4)

col1.metric(t("responses"), len(filtered_df))

col2.metric(
    t("regions"),
    filtered_df["region"].nunique() if "region" in filtered_df.columns else 0,
)

col3.metric(
    t("categories"),
    filtered_df["service_category"].nunique() if "service_category" in filtered_df.columns else 0,
)

col4.metric(
    t("avg_budget"),
    f"{filtered_df['budget_midpoint_aed'].mean():.0f}"
    if "budget_midpoint_aed" in filtered_df.columns and not filtered_df.empty
    else "0",
)

st.header(t("top_opportunities"))

if "suggested_business_idea" in rec_df.columns:
    for _, row in rec_df.head(3).iterrows():
        category_display = display_category(row["service_category"])
        recommendation_display = display_recommendation(row["recommendation"])
        idea_display = display_business_idea(row)

        with st.expander(
            f"💡 {category_display} — {recommendation_display}",
            expanded=False,
        ):
            st.metric(t("opportunity_score"), f"{row['business_opportunity_score']:.1f}/100")

            c1, c2, c3 = st.columns(3)

            c1.metric(t("feasibility"), f"{row['feasibility_score']:.1f}")
            c2.metric(t("scalability"), f"{row['scalability_score']:.1f}")
            c3.metric(t("testability"), f"{row['testability_score']:.1f}")

            st.info(idea_display)
            st.caption(f"{t('best_pilot')}: {format_pilot_segment(row)}")
            st.caption(f"{t('why')}: {format_why(row)}")
            st.caption(f"{t('source')}: {display_source(row.get('recommendation_source', 'unknown'))}")

st.header(t("opportunity_ranking"))

score_columns = [
    "business_opportunity_score",
    "feasibility_score",
    "scalability_score",
    "testability_score",
]

available_score_columns = [col for col in score_columns if col in rec_df.columns]

if available_score_columns and not rec_df.empty:
    chart_df = rec_df.copy()

    fig = px.bar(
        chart_df,
        x="display_service_category" if "display_service_category" in chart_df.columns else "service_category",
        y="business_opportunity_score",
        hover_data=available_score_columns,
        title=t("opportunity_chart_title"),
        labels={
            "display_service_category": t("service_category"),
            "service_category": t("service_category"),
            "business_opportunity_score": t("opportunity_score"),
        },
    )

    fig.update_layout(
        xaxis_title=t("service_category"),
        yaxis_title=t("opportunity_score"),
        margin=dict(l=40, r=40, t=80, b=120),
    )

    if LANG == "ar":
        fig.update_layout(
            font=dict(size=14),
            title_x=0.98,
            title_xanchor="right",
        )

    st.plotly_chart(fig, use_container_width=True)


st.header(t("demand_category"))

if not filtered_df.empty and "service_category" in filtered_df.columns:
    group_column = "display_service_category" if "display_service_category" in filtered_df.columns else "service_category"

    category_counts = (
        filtered_df.groupby(group_column)
        .size()
        .reset_index(name="response_count")
        .sort_values("response_count", ascending=False)
    )

    fig2 = px.bar(
        category_counts,
        x=group_column,
        y="response_count",
        title=t("demand_category_chart_title"),
        labels={
            group_column: t("service_category"),
            "response_count": t("responses"),
        },
    )

    fig2.update_layout(
        xaxis_title=t("service_category"),
        yaxis_title=t("responses"),
        margin=dict(l=40, r=40, t=80, b=120),
    )

    if LANG == "ar":
        fig2.update_layout(title_x=0.98, title_xanchor="right")

    st.plotly_chart(fig2, use_container_width=True)


st.header(t("demand_region"))

if not filtered_df.empty and {"region", "service_category"}.issubset(filtered_df.columns):
    heatmap_group_column = "display_service_category" if "display_service_category" in filtered_df.columns else "service_category"
    region_column = "display_region" if "display_region" in filtered_df.columns else "region"

    heatmap_data = (
        filtered_df.groupby([region_column, heatmap_group_column])
        .size()
        .reset_index(name="response_count")
    )

    fig3 = px.density_heatmap(
        heatmap_data,
        x=heatmap_group_column,
        y=region_column,
        z="response_count",
        title=t("demand_region_chart_title"),
        labels={
            heatmap_group_column: t("service_category"),
            region_column: t("region"),
            "response_count": t("responses"),
        },
    )

    fig3.update_layout(
        xaxis_title=t("service_category"),
        yaxis_title=t("region"),
        margin=dict(l=60, r=60, t=80, b=120),
    )

    if LANG == "ar":
        fig3.update_layout(title_x=0.98, title_xanchor="right")

    st.plotly_chart(fig3, use_container_width=True)

matrix_columns = {
    "service_category",
    "feasibility_score",
    "scalability_score",
    "testability_score",
    "business_opportunity_score",
}

if not rec_df.empty and matrix_columns.issubset(rec_df.columns):
    from html import escape

    matrix_df = rec_df.copy()
    matrix_df["display_service_category"] = matrix_df["service_category"].apply(display_category)

    for column in [
        "feasibility_score",
        "scalability_score",
        "testability_score",
        "business_opportunity_score",
    ]:
        matrix_df[column] = pd.to_numeric(matrix_df[column], errors="coerce").fillna(0)

    matrix_direction = "rtl" if LANG == "ar" else "ltr"
    matrix_align = "right" if LANG == "ar" else "left"

    top_opportunity = matrix_df.sort_values("business_opportunity_score", ascending=False).iloc[0]
    top_feasibility = matrix_df.sort_values("feasibility_score", ascending=False).iloc[0]
    avg_scalability = matrix_df["scalability_score"].mean()
    avg_feasibility = matrix_df["feasibility_score"].mean()

    if LANG == "ar":
        kpi_cards = [
            {
                "label": "أعلى فرصة",
                "value": f"{top_opportunity['business_opportunity_score']:.0f}",
                "sub": display_category(top_opportunity["service_category"]),
            },
            {
                "label": "أعلى قابلية تنفيذ",
                "value": f"{top_feasibility['feasibility_score']:.0f}",
                "sub": display_category(top_feasibility["service_category"]),
            },
            {
                "label": "متوسط قابلية التوسع",
                "value": f"{avg_scalability:.0f}",
                "sub": "من 100",
            },
            {
                "label": "متوسط قابلية التنفيذ",
                "value": f"{avg_feasibility:.0f}",
                "sub": "من 100",
            },
        ]

        quadrant_labels = {
            "priority": "أولوية قصوى",
            "scale": "جاهزة للتوسع",
            "develop": "تحتاج تطوير",
            "review": "تحتاج مراجعة",
        }

        quadrant_descriptions = {
            "priority": "تنفيذ عالٍ · توسع عالٍ",
            "scale": "تنفيذ متوسط · توسع عالٍ",
            "develop": "تنفيذ منخفض · توسع متوسط",
            "review": "تنفيذ منخفض · توسع منخفض",
        }

        matrix_subtitle = "قابلية التنفيذ مقابل قابلية التوسع — حسب فئة الخدمة"
    else:
        kpi_cards = [
            {
                "label": "Top opportunity",
                "value": f"{top_opportunity['business_opportunity_score']:.0f}",
                "sub": display_category(top_opportunity["service_category"]),
            },
            {
                "label": "Highest feasibility",
                "value": f"{top_feasibility['feasibility_score']:.0f}",
                "sub": display_category(top_feasibility["service_category"]),
            },
            {
                "label": "Average scalability",
                "value": f"{avg_scalability:.0f}",
                "sub": "out of 100",
            },
            {
                "label": "Average feasibility",
                "value": f"{avg_feasibility:.0f}",
                "sub": "out of 100",
            },
        ]

        quadrant_labels = {
            "priority": "High priority",
            "scale": "Ready to scale",
            "develop": "Needs development",
            "review": "Needs review",
        }

        quadrant_descriptions = {
            "priority": "High feasibility · High scalability",
            "scale": "Medium feasibility · High scalability",
            "develop": "Low feasibility · Medium scalability",
            "review": "Low feasibility · Low scalability",
        }

        matrix_subtitle = "Feasibility vs scalability — by service category"

    st.markdown(
        """
        <style>
        .opportunity-matrix-shell {
            max-width: 1120px;
            margin: 2rem auto 1rem auto;
            padding: 0.25rem 0;
        }

        .opportunity-matrix-title {
            text-align: center;
            margin-bottom: 1.2rem;
        }

        .opportunity-matrix-title h2 {
            font-size: 2.15rem;
            margin: 0;
            font-weight: 800;
        }

        .opportunity-matrix-title p {
            margin: 0.35rem 0 0 0;
            color: #a9a9b2;
            font-size: 0.98rem;
        }

        .matrix-kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.85rem;
            margin-bottom: 1.3rem;
        }

        .matrix-kpi-card {
            background: rgba(255, 255, 255, 0.035);
            border: 1px solid rgba(255, 255, 255, 0.065);
            border-radius: 16px;
            padding: 1.05rem 1rem;
            min-height: 112px;
            box-shadow: 0 12px 30px rgba(0,0,0,0.18);
        }

        .matrix-kpi-card small {
            color: #b5b5bd;
            font-size: 0.83rem;
            display: block;
            margin-bottom: 0.3rem;
        }

        .matrix-kpi-card strong {
            color: #ffffff;
            font-size: 2.05rem;
            line-height: 1.1;
            display: block;
            letter-spacing: -0.03em;
        }

        .matrix-kpi-card span {
            color: #22c55e;
            font-size: 0.88rem;
            display: block;
            margin-top: 0.35rem;
            overflow-wrap: anywhere;
        }

        .matrix-chart-card {
            background: rgba(255, 255, 255, 0.028);
            border: 1px solid rgba(255, 255, 255, 0.055);
            border-radius: 18px;
            padding: 1rem 1.1rem 0.4rem 1.1rem;
            box-shadow: 0 15px 35px rgba(0,0,0,0.20);
        }

        .quadrant-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.85rem;
            margin-top: 1rem;
        }

        .quadrant-card {
            background: rgba(0, 0, 0, 0.38);
            border: 1px solid rgba(255,255,255,0.055);
            border-radius: 14px;
            padding: 0.9rem 1rem;
            min-height: 82px;
        }

        .quadrant-card strong {
            color: #ffffff;
            display: block;
            font-size: 0.98rem;
            margin-bottom: 0.25rem;
        }

        .quadrant-card span {
            color: #b9b9c3;
            display: block;
            font-size: 0.83rem;
        }

        .quadrant-card em {
            color: #22c55e;
            font-style: normal;
            display: block;
            margin-top: 0.35rem;
            font-size: 0.82rem;
        }

        @media (max-width: 900px) {
            .matrix-kpi-grid,
            .quadrant-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    kpi_html = ""
    for card in kpi_cards:
        kpi_html += f"""
        <div class="matrix-kpi-card">
            <small>{escape(card["label"])}</small>
            <strong>{escape(str(card["value"]))}</strong>
            <span>{escape(card["sub"])}</span>
        </div>
        """

    st.markdown(
        f"""
        <div class="opportunity-matrix-shell" dir="{matrix_direction}">
            <div class="opportunity-matrix-title">
                <h2>{escape(t("opportunity_matrix"))}</h2>
                <p>{escape(matrix_subtitle)}</p>
            </div>
            <div class="matrix-kpi-grid" style="text-align:{matrix_align}">
                {kpi_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    median_feasibility = float(matrix_df["feasibility_score"].median())
    median_scalability = float(matrix_df["scalability_score"].median())

    fig4 = px.scatter(
        matrix_df,
        x="feasibility_score",
        y="scalability_score",
        size="business_opportunity_score",
        color="display_service_category",
        hover_name="display_service_category",
        hover_data={
            "display_service_category": False,
            "feasibility_score": ":.1f",
            "scalability_score": ":.1f",
            "testability_score": ":.1f",
            "business_opportunity_score": ":.1f",
        },
        labels={
            "feasibility_score": t("feasibility"),
            "scalability_score": t("scalability"),
            "testability_score": t("testability"),
            "business_opportunity_score": t("opportunity_score"),
            "display_service_category": t("service_category"),
        },
        size_max=56,
    )

    fig4.add_shape(
        type="rect",
        x0=median_feasibility,
        x1=100,
        y0=median_scalability,
        y1=100,
        fillcolor="rgba(34,197,94,0.10)",
        line_width=0,
        layer="below",
    )
    fig4.add_shape(
        type="rect",
        x0=0,
        x1=median_feasibility,
        y0=median_scalability,
        y1=100,
        fillcolor="rgba(250,204,21,0.07)",
        line_width=0,
        layer="below",
    )
    fig4.add_shape(
        type="rect",
        x0=median_feasibility,
        x1=100,
        y0=0,
        y1=median_scalability,
        fillcolor="rgba(59,130,246,0.07)",
        line_width=0,
        layer="below",
    )
    fig4.add_shape(
        type="rect",
        x0=0,
        x1=median_feasibility,
        y0=0,
        y1=median_scalability,
        fillcolor="rgba(239,68,68,0.06)",
        line_width=0,
        layer="below",
    )

    fig4.add_vline(
        x=median_feasibility,
        line_dash="dash",
        line_color="rgba(255,255,255,0.35)",
        line_width=1,
    )

    fig4.add_hline(
        y=median_scalability,
        line_dash="dash",
        line_color="rgba(255,255,255,0.35)",
        line_width=1,
    )

    fig4.update_traces(
        marker=dict(opacity=0.88, line=dict(width=1.6, color="rgba(255,255,255,0.55)"))
    )

    fig4.update_layout(
        height=560,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.025)",
        font=dict(color="#f3f4f6", size=13),
        xaxis=dict(
            title=t("feasibility"),
            range=[0, 100],
            gridcolor="rgba(255,255,255,0.10)",
            zeroline=False,
        ),
        yaxis=dict(
            title=t("scalability"),
            range=[0, 100],
            gridcolor="rgba(255,255,255,0.10)",
            zeroline=False,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            title_text="",
        ),
        margin=dict(l=50, r=50, t=70, b=65),
    )

    if LANG == "ar":
        fig4.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.05,
                xanchor="center",
                x=0.5,
                title_text="",
            )
        )

    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

    def quadrant_key(row):
        feasibility = float(row["feasibility_score"])
        scalability = float(row["scalability_score"])

        if feasibility >= median_feasibility and scalability >= median_scalability:
            return "priority"

        if feasibility < median_feasibility and scalability >= median_scalability:
            return "develop"

        if feasibility >= median_feasibility and scalability < median_scalability:
            return "scale"

        return "review"

    matrix_df["quadrant_key"] = matrix_df.apply(quadrant_key, axis=1)

    quadrant_html = ""
    for key in ["priority", "scale", "develop", "review"]:
        subset = matrix_df[matrix_df["quadrant_key"] == key].sort_values(
            "business_opportunity_score",
            ascending=False,
        )

        if subset.empty:
            service = "—"
            score = "0"
        else:
            best_row = subset.iloc[0]
            service = display_category(best_row["service_category"])
            score = f"{float(best_row['business_opportunity_score']):.0f}"

        quadrant_html += f"""
        <div class="quadrant-card">
            <strong>{escape(quadrant_labels[key])}</strong>
            <span>{escape(quadrant_descriptions[key])}</span>
            <em>{escape(service)} · {escape(score)}/100</em>
        </div>
        """

    st.markdown(
        f"""
        <div class="opportunity-matrix-shell" dir="{matrix_direction}">
            <div class="quadrant-grid" style="text-align:{matrix_align}">
                {quadrant_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.header(t("details"))
st.dataframe(
    clean_table_for_display(rec_df, "recommendations"),
    use_container_width=True,
    hide_index=True,
)

if not region_needs_df.empty:
    st.header(t("local_needs"))
    st.dataframe(
        clean_table_for_display(region_needs_df, "region_needs"),
        use_container_width=True,
        hide_index=True,
    )

if not segments_df.empty:
    st.header(t("segments"))
    st.dataframe(
        clean_table_for_display(segments_df.head(25), "segments"),
        use_container_width=True,
        hide_index=True,
    )

if not targeting_df.empty:
    st.header(t("targeting"))
    st.dataframe(
        clean_table_for_display(targeting_df, "targeting"),
        use_container_width=True,
        hide_index=True,
    )

st.header(t("raw"))
st.dataframe(
    clean_table_for_display(filtered_df, "raw"),
    use_container_width=True,
    hide_index=True,
)
