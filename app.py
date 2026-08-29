from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
import json

app = FastAPI()

client = genai.Client()


# Load university database
with open("database/universities.json", "r") as file:
    universities = json.load(file)

# Load industry database
with open("database/industries.json", "r") as file:
    industries = json.load(file)


# User input
class Problem(BaseModel):
    problem: str


# Gemini AI analysis
def analyze_problem(problem):

    prompt = f"""
Analyze this citizen problem:

{problem}

Identify the main technical domain responsible for solving this problem.

Return ONLY valid JSON in exactly this format:

{{
    "category": "...",
    "domain": "...",
    "severity": "Low/Medium/High",
    "required_expertise": "...",
    "recommended_department": "...",
    "priority": "Low/Medium/High",
    "reason": "..."
}}

The "domain" should preferably be one of these:

- Civil Engineering
- Electrical Engineering
- Computer Science
- Mechanical Engineering
- Environmental Engineering
- Electronics Engineering

Examples:

Pothole or damaged road
→ Civil Engineering

Damaged traffic signal
→ Electrical Engineering

Software or digital system problem
→ Computer Science

Pollution or waste management
→ Environmental Engineering

Do not add any explanation or markdown.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return json.loads(response.text)


# Match with database
def find_matches(analysis):

    domain = analysis["domain"].lower()

    matched_universities = []
    matched_industries = []


    # University matching
    for university in universities:

        if university["domain"].lower() == domain:
            matched_universities.append(university)


    # Industry matching
    for industry in industries:

        if industry["domain"].lower() == domain:
            matched_industries.append(industry)


    return {
        "analysis": analysis,
        "suitable_universities": matched_universities,
        "suitable_industries": matched_industries
    }


# API endpoint
@app.post("/analyze")
def analyze(data: Problem):

    analysis = analyze_problem(data.problem)

    result = find_matches(analysis)

    return result