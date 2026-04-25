import pandas as pd
import itertools

# Load the data
df = pd.read_csv('banner_sections_enriched.csv')

def time_to_min(t_str):
    """Helper to convert HH:MM to total minutes."""
    try:
        h, m = map(int, t_str.split(':'))
        return h * 60 + m
    except:
        return 0

# Pre-calculate minutes for the entire dataset
df['Start_Min'] = df['Start_Time'].apply(time_to_min)
df['End_Min'] = df['End_Time'].apply(time_to_min)

def check_conflict(s1, s2):
    """Returns True if two sections overlap in time and day."""
    days1 = set(s1['Meeting_Days'].split('/'))
    days2 = set(s2['Meeting_Days'].split('/'))
    
    if not days1.intersection(days2):
        return False
    
    # Check time overlap: (StartA < EndB) and (EndA > StartB)
    return s1['Start_Min'] < s2['End_Min'] and s1['End_Min'] > s2['Start_Min']

def score_schedule(schedule, prefs):
    """The Rule-Based AI Scoring Function."""
    score = 0
    
    # 1. Time Preferences (Morning vs Afternoon)
    time_pref = prefs.get('time_pref')
    for sec in schedule:
        if time_pref == 'Morning' and sec['Start_Min'] < 720: # Before 12 PM
            score += 5
        elif time_pref == 'Afternoon' and sec['Start_Min'] >= 720: # After 12 PM
            score += 5
            
        # 2. Instructor Preference
        if prefs.get('instructor') and sec['Instructor_Name'] == prefs['instructor']:
            score += 10
            
        # 3. Seat Availability (Weight: 10%)
        score += sec['Seat_Availability'] * 0.1
        
    # 4. Gap Penalty (Compactness)
    sorted_s = sorted(schedule, key=lambda x: x['Start_Min'])
    total_gap = 0
    for i in range(len(sorted_s) - 1):
        gap = sorted_s[i+1]['Start_Min'] - sorted_s[i]['End_Min']
        if gap > 0:
            total_gap += gap
    score -= (total_gap * 0.01)
    
    return round(score, 2)

def generate_and_rank(course_codes, preferences):
    """Main pipeline to find valid schedules and rank them."""
    # Filter only necessary courses
    sections_by_course = []
    for code in course_codes:
        course_sections = df[df['Course_Code'] == code].to_dict('records')
        if course_sections:
            sections_by_course.append(course_sections)

    if not sections_by_course:
        return []

    valid_results = []
    # Cartesian product finds every possible combination of sections
    for combination in itertools.product(*sections_by_course):
        has_overlap = False
        for i in range(len(combination)):
            for j in range(i + 1, len(combination)):
                if check_conflict(combination[i], combination[j]):
                    has_overlap = True
                    break
            if has_overlap: break
            
        if not has_overlap:
            score = score_schedule(combination, preferences)
            valid_results.append({
                "schedule": list(combination),
                "total_score": score
            })
            
    # Sort by highest score first
    return sorted(valid_results, key=lambda x: x['total_score'], reverse=True)