from datetime import datetime, timedelta
import random
import pandas as pd


AGE_GROUPS = [
    "18-24",
    "25-34",
    "35-44",
    "45-54",
    "55+"
]

GENDER_OPTIONS = [
    "Male",
    "Female",
    "Prefer not to say"
]

REGIONS = [
    "Hatta",
    "Al Ain outskirts",
    "Masfout",
    "Al Madam",
    "Dibba",
    "Liwa",
    "Ghayathi",
    "Kalba",
    "Khor Fakkan outskirts",
    "Ras Al Khaimah rural area"
]

OCCUPATIONS = [
    "Student",
    "Farmer",
    "Shop owner",
    "Teacher",
    "Driver",
    "Homemaker",
    "Employee",
    "Retired",
    "Unemployed",
    "Tourism worker",
    "Small business owner"
]

SOURCES = [
    "paper_form",
    "qr_survey",
    "voice_note",
    "interview",
    "shop_owner_note"
]

SERVICE_CATEGORIES = {
    "Delivery": {
        "problems": [
            "Poor delivery access",
            "Slow grocery delivery",
            "No pharmacy delivery",
            "Difficulty receiving online orders"
        ],
        "services": [
            "Grocery delivery",
            "Pharmacy delivery",
            "Local delivery service",
            "Home delivery from local shops"
        ],
        "opinions": [
            "We need faster delivery because shops are far from our homes.",
            "Many families cannot always drive to buy groceries.",
            "A local delivery service would help elderly people and busy families.",
            "Online delivery is not always available in this area."
        ],
        "current_solutions": [
            "Ask family member",
            "Drive to city",
            "Wait until weekend",
            "No solution"
        ]
    },

    "Education": {
        "problems": [
            "No nearby tutoring center",
            "Limited after-school support",
            "Students need exam preparation",
            "Lack of affordable learning support"
        ],
        "services": [
            "Student tutoring",
            "Exam preparation center",
            "English and math tutoring",
            "After-school learning support"
        ],
        "opinions": [
            "Many students need affordable tutoring nearby, especially for math and English.",
            "Parents travel far to find good tutoring centers.",
            "A small learning center would help students after school.",
            "Online videos are not enough for some students."
        ],
        "current_solutions": [
            "Online videos",
            "Ask relatives",
            "Travel to city",
            "Private tutor"
        ]
    },

    "Transport": {
        "problems": [
            "Limited transport",
            "No regular local bus",
            "Difficult transport for appointments",
            "Expensive taxi access"
        ],
        "services": [
            "Local transport",
            "Community shuttle",
            "Shared taxi service",
            "Appointment transport service"
        ],
        "opinions": [
            "Transport is difficult for families without a second car.",
            "A small community shuttle would help people reach clinics and shops.",
            "Some people depend on relatives for transport.",
            "Taxi services are expensive or not always available."
        ],
        "current_solutions": [
            "Ask relatives",
            "Use taxi",
            "Wait for someone to help",
            "Cancel trip"
        ]
    },

    "Agriculture": {
        "problems": [
            "Lack of farm marketing",
            "Farmers struggle to sell directly",
            "Low visibility for local produce",
            "No simple ordering system for farms"
        ],
        "services": [
            "Farm-to-home ordering",
            "Local produce delivery",
            "Farm product marketplace",
            "Weekly farm box service"
        ],
        "opinions": [
            "Small farms need a simple way to sell dates and vegetables directly to customers.",
            "People would buy more local produce if ordering was easier.",
            "Farmers depend too much on word of mouth.",
            "A WhatsApp ordering system for local farms would be useful."
        ],
        "current_solutions": [
            "Sell through relatives",
            "Use WhatsApp groups",
            "Sell at local market",
            "No clear solution"
        ]
    },

    "Repair": {
        "problems": [
            "Few repair services",
            "No nearby appliance repair",
            "Hard to find trusted technicians",
            "Repair services take too long"
        ],
        "services": [
            "Home appliance repair",
            "Mobile repair technician",
            "AC repair service",
            "Local maintenance service"
        ],
        "opinions": [
            "It is hard to find someone nearby to repair appliances.",
            "People wait too long for repair workers to come from the city.",
            "A trusted local technician service would be useful.",
            "Home maintenance is expensive because providers are far away."
        ],
        "current_solutions": [
            "Call city technician",
            "Ask neighbors",
            "Wait several days",
            "Replace item"
        ]
    },

    "Tourism": {
        "problems": [
            "Limited tourism information",
            "No easy booking for local experiences",
            "Tourists do not know local activities",
            "Local guides are not visible"
        ],
        "services": [
            "Rural tourism guide",
            "Local experience booking",
            "Farm visit booking",
            "Weekend tourism platform"
        ],
        "opinions": [
            "Visitors ask about local food, farms, and activities.",
            "A simple guide for tourists would help small local businesses.",
            "Local families could offer farm visits or cultural experiences.",
            "Tourists come on weekends but do not know where to go."
        ],
        "current_solutions": [
            "Ask locals",
            "Search online",
            "Use Instagram",
            "No organized option"
        ]
    }
}

IMPORTANCE_LEVELS = [
    "Low",
    "Medium",
    "High"
]

SATISFACTION_LEVELS = [
    "Very dissatisfied",
    "Dissatisfied",
    "Neutral",
    "Satisfied",
    "Very satisfied"
]

WOULD_PAY_OPTIONS = [
    "Yes",
    "Maybe",
    "No"
]

MONTHLY_BUDGET_OPTIONS = [
    "0 AED",
    "10-30 AED",
    "31-50 AED",
    "51-100 AED",
    "100+ AED"
]

URGENCY_LEVELS = [
    "Not urgent",
    "Soon",
    "Very urgent"
]

FREQUENCY_OPTIONS = [
    "Rarely",
    "Monthly",
    "Weekly",
    "Daily"
]

PREFERRED_SOLUTION_TYPES = [
    "WhatsApp",
    "Phone call",
    "In-person service",
    "Mobile app",
    "Website",
    "Community center",
    "Delivery service"
]


def choose_weighted(options, weights):
    """
    Choose one item from a list using weighted probabilities.
    """
    return random.choices(options, weights=weights, k=1)[0]


def create_demo_dataset(rows=250):
    """
    Create a synthetic dataset that simulates community opinion data.

    This dataset represents opinions collected from rural or smaller UAE communities
    through low-tech and assisted methods such as paper forms, interviews, QR surveys,
    voice notes, and shop-owner notes.

    Parameters:
        rows:
            Number of responses to generate.

    Returns:
        pandas DataFrame
    """

    data = []

    start_date = datetime.today() - timedelta(days=90)

    for response_id in range(1, rows + 1):
        service_category = random.choice(list(SERVICE_CATEGORIES.keys()))
        category_data = SERVICE_CATEGORIES[service_category]

        main_problem = random.choice(category_data["problems"])
        needed_service = random.choice(category_data["services"])
        opinion_text = random.choice(category_data["opinions"])
        current_solution = random.choice(category_data["current_solutions"])

        importance_level = choose_weighted(
            IMPORTANCE_LEVELS,
            weights=[0.15, 0.35, 0.50]
        )

        urgency_level = choose_weighted(
            URGENCY_LEVELS,
            weights=[0.20, 0.40, 0.40]
        )

        frequency_of_problem = choose_weighted(
            FREQUENCY_OPTIONS,
            weights=[0.10, 0.25, 0.40, 0.25]
        )

        satisfaction_level = choose_weighted(
            SATISFACTION_LEVELS,
            weights=[0.20, 0.35, 0.25, 0.15, 0.05]
        )

        would_pay = choose_weighted(
            WOULD_PAY_OPTIONS,
            weights=[0.45, 0.40, 0.15]
        )

        if would_pay == "No":
            monthly_budget = "0 AED"
        else:
            monthly_budget = choose_weighted(
                MONTHLY_BUDGET_OPTIONS,
                weights=[0.05, 0.30, 0.35, 0.20, 0.10]
            )

        random_days = random.randint(0, 90)
        date_collected = start_date + timedelta(days=random_days)

        row = {
            "response_id": response_id,
            "age_group": random.choice(AGE_GROUPS),
            "gender": random.choice(GENDER_OPTIONS),
            "region": random.choice(REGIONS),
            "occupation": random.choice(OCCUPATIONS),
            "source": random.choice(SOURCES),
            "main_problem": main_problem,
            "needed_service": needed_service,
            "service_category": service_category,
            "importance_level": importance_level,
            "current_solution": current_solution,
            "satisfaction_level": satisfaction_level,
            "would_pay": would_pay,
            "monthly_budget": monthly_budget,
            "urgency_level": urgency_level,
            "frequency_of_problem": frequency_of_problem,
            "preferred_solution_type": random.choice(PREFERRED_SOLUTION_TYPES),
            "opinion_text": opinion_text,
            "date_collected": date_collected.strftime("%Y-%m-%d")
        }

        data.append(row)

    df = pd.DataFrame(data)

    return df