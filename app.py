# from fastapi import FastAPI
# from pydantic import BaseModel
# from google import genai
# import json

# app = FastAPI()

# client = genai.Client()


# # Load university database
# with open("database/universities.json", "r") as file:
#     universities = json.load(file)

# # Load industry database
# with open("database/industries.json", "r") as file:
#     industries = json.load(file)


# # User input
# class Problem(BaseModel):
#     problem: str


# # Gemini AI analysis
# def analyze_problem(problem):

#     prompt = f"""Analyze this citizen problem:{problem}
# Identify the main technical domain responsible for solving this problem.
# Return ONLY valid JSON in exactly this format:
# {{
#     "category": "...",
#     "domain": "...",
#     "severity": "Low/Medium/High",
#     "required_expertise": "...",
#     "recommended_department": "...",
#     "priority": "Low/Medium/High",
#     "reason": "..."
# }}
# The "domain" should preferably be one of these:

# - Civil Engineering
# - Electrical Engineering
# - Computer Science
# - Mechanical Engineering
# - Environmental Engineering
# - Electronics Engineering

# Examples:

# Pothole or damaged road
# → Civil Engineering

# Damaged traffic signal
# → Electrical Engineering

# Software or digital system problem
# → Computer Science

# Pollution or waste management
# → Environmental Engineering

# Do not add any explanation or markdown.
# """

#     response = client.models.generate_content(
#         model="gemini-3.6-flash",
#         contents=prompt
#     )

#     return json.loads(response.text)


# # Match with database
# def find_matches(analysis):

#     domain = analysis["domain"].lower()

#     matched_universities = []
#     matched_industries = []


#     # University matching
#     for university in universities:

#         if university["domain"].lower() == domain:
#             matched_universities.append(university)


#     # Industry matching
#     for industry in industries:

#         if industry["domain"].lower() == domain:
#             matched_industries.append(industry)


#     return {
#         "analysis": analysis,
#         "suitable_universities": matched_universities,
#         "suitable_industries": matched_industries
#     }


# # API endpoint
# @app.post("/analyze")
# def analyze(data: Problem):

#     analysis = analyze_problem(data.problem)

#     result = find_matches(analysis)

#     return result


from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
import json
import re

app = FastAPI()

client = genai.Client()


# -----------------------------
# LOAD DATABASE
# -----------------------------

with open("database/universities.json", "r") as file:
    universities = json.load(file)

with open("database/industries.json", "r") as file:
    industries = json.load(file)


# -----------------------------
# USER INPUT
# -----------------------------

class Problem(BaseModel):
    problem: str


# -----------------------------
# GEMINI AI ANALYSIS
# -----------------------------

def analyze_problem(problem):

    prompt = f"""
Analyze this citizen problem:

{problem}

Identify the MAIN technical domain required to solve the problem.

Choose the domain carefully.

Possible engineering domains are:

- Civil Engineering
- Electrical Engineering
- Computer Science
- Mechanical Engineering
- Environmental Engineering
- Electronics Engineering

If the problem is NOT an engineering/technical problem
(for example law enforcement, crime, medical emergency,
police matter, legal issue, etc.), do NOT force it into
an engineering domain.

Return ONLY valid JSON in exactly this format:

{{
    "category": "...",
    "domain": "...",
    "location": "...",
    "severity": "Low/Medium/High",
    "required_expertise": "...",
    "recommended_department": "...",
    "priority": "Low/Medium/High",
    "reason": "..."
}}

Examples:
Identify the city/location of the problem if a city or specific geographic location is explicitly mentioned.

Examples:
- "Pothole in Pune near a school" → "Pune"
- "Broken traffic signal in Mumbai" → "Mumbai"
- "Garbage problem in Kothrud, Pune" → "Pune"
- "There is a pothole near a school" → "Unknown"

Do NOT use descriptions such as "near school", "near market", "near hospital" as the location.
If no city/location is mentioned, return "Unknown".

Pothole / damaged road
→ Civil Engineering

Damaged traffic signal
→ Electrical Engineering

Software / website / digital system problem
→ Computer Science

Garbage / pollution / waste management
→ Environmental Engineering

Broken machine
→ Mechanical Engineering

Electronic device / sensor problem
→ Electronics Engineering

Police / crime / law enforcement problem
→ domain can be "Law Enforcement"

Do not add any explanation or markdown.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return json.loads(response.text)


# -----------------------------
# TEXT NORMALIZATION
# -----------------------------

def normalize(text):

    text = text.lower()

    # Remove special characters
    text = re.sub(r"[^a-z0-9 ]", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# -----------------------------
# MATCHING FUNCTION
# -----------------------------

def calculate_score(analysis, item):

    score = 0

    problem_domain = normalize(analysis.get("domain", ""))
    required_expertise = normalize(
        analysis.get("required_expertise", "")
    )
    recommended_department = normalize(
        analysis.get("recommended_department", "")
    )
    category = normalize(
        analysis.get("category", "")
    )

    item_domain = normalize(item.get("domain", ""))
    item_department = normalize(item.get("department", ""))
    item_location = normalize(item.get("location", ""))

    # --------------------------------
    # DOMAIN MATCH
    # --------------------------------

    if problem_domain == item_domain:
        score += 40

    elif problem_domain in item_domain or item_domain in problem_domain:
        score += 25

    # --------------------------------
    # LOCATION MATCH
    # --------------------------------

    problem_location = normalize(
    analysis.get("location", "")
    )

    if (
    problem_location != ""
    and problem_location != "unknown"
    and problem_location == item_location
    ):
        score += 20

    # --------------------------------
    # DEPARTMENT MATCH
    # --------------------------------

    expertise_words = set(required_expertise.split())
    department_words = set(item_department.split())

    common_words = expertise_words.intersection(department_words)

    score += len(common_words) * 3

    # --------------------------------
    # RECOMMENDED DEPARTMENT MATCH
    # --------------------------------

    recommended_words = set(
        recommended_department.split()
    )

    common_department_words = recommended_words.intersection(
        department_words
    )

    score += len(common_department_words) * 4

    # --------------------------------
    # CATEGORY / DOMAIN WORD MATCH
    # --------------------------------

    category_words = set(category.split())
    domain_words = set(item_domain.split())

    common_domain_words = category_words.intersection(
        domain_words
    )

    score += len(common_domain_words) * 2

    return score


# -----------------------------
# FIND BEST MATCHES
# -----------------------------

def find_matches(analysis):

    university_results = []
    industry_results = []

    # --------------------------------
    # UNIVERSITY MATCHING
    # --------------------------------

    for university in universities:

        score = calculate_score(
            analysis,
            university
        )

        if score >= 40:

            university_copy = university.copy()

            university_copy["match_score"] = score
            university_copy["match_reason"] = (
                f"Domain matches: {university['domain']}. "
                f"Department: {university['department']}. "
                f"Location matches: {university['location']}."
            )

            university_results.append(
                university_copy
            )

    # --------------------------------
    # INDUSTRY MATCHING
    # --------------------------------

    for industry in industries:

        score = calculate_score(
            analysis,
            industry
        )

        if score >= 40:

            industry_copy = industry.copy()

            industry_copy["match_score"] = score
            industry_copy["match_reason"] = (
                f"Domain matches: {industry['domain']}. "
                f"Department: {industry['department']}. "
                f"Location matches: {industry['location']}."
            )

            industry_results.append(
                industry_copy
            )

    # --------------------------------
    # SORT BY BEST SCORE
    # --------------------------------

    university_results.sort(
        key=lambda x: x["match_score"],
        reverse=True
    )

    industry_results.sort(
        key=lambda x: x["match_score"],
        reverse=True
    )

    return {
        "analysis": analysis,

        "matching": {
            "mapped_category": analysis.get("category"),

            "suitable_universities": university_results,

            "suitable_industries": industry_results
        }
    }


# -----------------------------
# API ENDPOINT
# -----------------------------

@app.post("/analyze")
def analyze(data: Problem):

    analysis = analyze_problem(
        data.problem
    )

    result = find_matches(
        analysis
    )

    return result