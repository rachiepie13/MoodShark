from db import users_collection, activities_collection

PERSONALITY_TYPES = [
    "Visionary", "Realist", "Cheerleader", "Daydreamer", "Curator",
    "Maverick", "Nurturer", "Strategist", "Seeker", "Challenger",
]

PERSONALITY_WEIGHT = 0.4
MOOD_WEIGHT = 0.6


def get_user(username):
    return users_collection.find_one({"username": username})


def load_activities():
    return list(activities_collection.find())


def personality_match_score(activity, user_personality):
    total_weight = sum(user_personality.values())

    if total_weight == 0:
        return 0

    personality_scores = activity.get("personalityScores", {})

    weighted_sum = 0

    for ptype in PERSONALITY_TYPES:
        activity_score = float(personality_scores.get(ptype, 0) or 0)
        user_weight = user_personality.get(ptype, 0)

        weighted_sum += activity_score * user_weight

    return weighted_sum / total_weight


def mood_match_score(activity, todays_moods):
    if not todays_moods:
        return 0

    mood_scores = activity.get("moodScores", {})

    total = 0

    for mood in todays_moods:
        total += float(mood_scores.get(mood, 0) or 0)

    return total / len(todays_moods)


def score_activities(activities, user_personality, todays_moods):
    scored = []

    for activity in activities:
        p_score = personality_match_score(
            activity,
            user_personality
        )

        m_score = mood_match_score(
            activity,
            todays_moods
        )

        final_score = (
            (p_score * PERSONALITY_WEIGHT)
            + (m_score * MOOD_WEIGHT)
        )

        scored.append((final_score, activity))

    scored.sort(key=lambda pair: pair[0], reverse=True)

    return scored


def print_top(scored, n=10):
    print(f"{'Score':>6}  title")
    print("-" * 50)

    for score, activity in scored[:n]:
        print(f"{score:6.2f}  {activity.get('title', 'Unknown Activity')}")


if __name__ == "__main__":

    username = input("Enter username: ").strip()

    user = get_user(username)

    if not user:
        print("User not found.")
        exit()

    personality_data = user.get("personality", {})
    user_personality = personality_data.get("percentages", {})

    daily_mood = user.get("daily_mood", {})

    todays_moods = []

    if isinstance(daily_mood, dict):
        primary_mood = daily_mood.get("mood")
        secondary_mood = daily_mood.get("secondary_mood")

        if primary_mood:
            todays_moods.append(primary_mood)

        if secondary_mood:
            todays_moods.append(secondary_mood)

    activities = load_activities()

    scored = score_activities(
        activities,
        user_personality,
        todays_moods
    )

    print()
    print(f"Activity Recommendations for {username}")
    print()

    print_top(scored, n=10)