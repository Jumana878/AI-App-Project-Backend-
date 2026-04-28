import pandas as pd
import itertools
import os

# =========================================
# Load Dataset Safely
# =========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, 'data/banner_sections_enriched.csv')

df = pd.read_csv(file_path)

# =========================================
# Preprocessing
# =========================================
def time_to_min(t_str):
    try:
        h, m = map(int, t_str.split(':'))
        return h * 60 + m
    except:
        return 0

df['Start_Min'] = df['Start_Time'].apply(time_to_min)
df['End_Min'] = df['End_Time'].apply(time_to_min)

# =========================================
# Conflict Detection
# =========================================
def check_conflict(s1, s2):
    days1 = set(s1['Meeting_Days'].split('/'))
    days2 = set(s2['Meeting_Days'].split('/'))

    if not days1.intersection(days2):
        return False

    return s1['Start_Min'] < s2['End_Min'] and s1['End_Min'] > s2['Start_Min']

# =========================================
# Clean Output for JSON
# =========================================
def clean_section(sec):
    return {
        "course_code": sec["Course_Code"],
        "course_name": sec["Course_Name"],
        "section": sec["Section_Number"],
        "days": sec["Meeting_Days"],
        "start": sec["Start_Time"],
        "end": sec["End_Time"],
        "instructor": sec["Instructor_Name"],
        "seat_availability": sec["Seat_Availability"]
    }

# =========================================
# Scoring Function (Unified Preferences)
# =========================================
def score_schedule(schedule, prefs):
    score = 0

    for sec in schedule:

        # Avoid morning
        if prefs.get("avoid_morning") and sec['Start_Min'] < 720:
            score -= 5

        # Prefer morning
        if prefs.get("prefer_morning") and sec['Start_Min'] < 720:
            score += 5

        # Preferred instructor (partial match)
        if prefs.get("instructor"):
            if prefs["instructor"].lower() in sec["Instructor_Name"].lower():
                score += 10

        # Seat availability weight
        score += sec["Seat_Availability"] * 0.1

    # Gap penalty (compactness)
    sorted_s = sorted(schedule, key=lambda x: x['Start_Min'])
    total_gap = 0

    for i in range(len(sorted_s) - 1):
        gap = sorted_s[i+1]['Start_Min'] - sorted_s[i]['End_Min']
        if gap > 0:
            total_gap += gap

    score -= total_gap * 0.01

    return round(score, 2)

# =========================================
# Main Scheduling Pipeline
# =========================================
def generate_and_rank(course_codes, preferences):

    # Remove duplicates
    course_codes = list(set(course_codes))

    sections_by_course = []

    for code in course_codes:
        course_sections = df[df['Course_Code'] == code].to_dict('records')

        # If any course has no sections → stop
        if not course_sections:
            return []

        sections_by_course.append(course_sections)

    valid_results = []

    # Generate all combinations
    for combination in itertools.product(*sections_by_course):

        has_overlap = False

        for i in range(len(combination)):
            for j in range(i + 1, len(combination)):
                if check_conflict(combination[i], combination[j]):
                    has_overlap = True
                    break
            if has_overlap:
                break

        if not has_overlap:
            score = score_schedule(combination, preferences)

            valid_results.append({
                "schedule": [clean_section(s) for s in combination],
                "total_score": score
            })

    # Sort by score descending
    return sorted(valid_results, key=lambda x: x['total_score'], reverse=True)
