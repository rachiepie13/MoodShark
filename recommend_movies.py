from db import users_collection, movies_collection

PERSONALITY_TYPES = [
    "Visionary", "Realist", "Cheerleader", "Daydreamer", "Curator",
    "Maverick", "Nurturer", "Strategist", "Seeker", "Challenger",
]

PERSONALITY_WEIGHT = 0.4
MOOD_WEIGHT = 0.6


def get_user(username):
    return users_collection.find_one({"username": username})


def load_movies():
    return list(movies_collection.find())


def personality_match_score(movie, user_personality):
    total_weight = sum(user_personality.values())

    if total_weight == 0:
        return 0

    personality_scores = movie.get("personalityScores", {})

    weighted_sum = 0

    for ptype in PERSONALITY_TYPES:
        movie_score = float(personality_scores.get(ptype, 0) or 0)
        user_weight = user_personality.get(ptype, 0)

        weighted_sum += movie_score * user_weight

    return weighted_sum / total_weight


def mood_match_score(movie, todays_moods):
    if not todays_moods:
        return 0

    mood_scores = movie.get("moodScores", {})

    total = 0

    for mood in todays_moods:
        total += float(mood_scores.get(mood, 0) or 0)

    return total / len(todays_moods)


def score_movies(movies, user_personality, todays_moods):
    scored = []

    for movie in movies:
        p_score = personality_match_score(
            movie,
            user_personality
        )

        m_score = mood_match_score(
            movie,
            todays_moods
        )

        final_score = (
            (p_score * PERSONALITY_WEIGHT)
            + (m_score * MOOD_WEIGHT)
        )

        scored.append((final_score, movie))

    scored.sort(key=lambda pair: pair[0], reverse=True)

    return scored


def print_top(scored, n=10):
    print(f"{'Score':>6}  title")
    print("-" * 50)

    for score, movie in scored[:n]:
        print(f"{score:6.2f}  {movie.get('title', 'Unknown Title')}")


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

    movies = load_movies()

    scored = score_movies(
        movies,
        user_personality,
        todays_moods
    )

    print()
    print(f"Recommendations for {username}")
    print()

    print_top(scored, n=10)