"""
recommendations.py

Orchestrates the six existing recommend_*.py scripts into one place the
Home screen can call. Does NOT change how anything is scored — it only
calls the score_* / load_* functions that already exist in each file.

What it adds on top of those files:
  1. A single entry point: get_recommendations(username)
  2. Two rankings per category, both using the SAME existing score_*()
     function, just with different mood inputs:
       - "personality" list (top 10): score_*() called with todays_moods=[]
         so the mood half of the formula contributes 0 (that behavior
         already exists in every recommend_*.py file).
       - "mood" list (top 3): score_*() called with the real mood(s).
  3. Caching: only the item IDs (not full documents) are stored on the
     user's MongoDB document, alongside when they were generated. The
     personality list only regenerates every 3 days (or immediately if
     the user retook the quiz). The mood list regenerates whenever
     today's mood check-in result is newer than what's cached.

None of the six recommend_*.py files are modified.
"""

from datetime import datetime, timedelta, timezone
from bson import ObjectId

from db import users_collection

import recommend_movies
import recommend_tv
import recommend_books
import recommend_music
import recommend_podcast
import recommend_activities

REFRESH_INTERVAL_DAYS = 3

# One entry per recommendation category. Each just points at the load/score
# functions and collection that already exist in that category's file.
CATEGORY_CONFIG = {
    "movies": {
        "label": "Movies",
        "load": recommend_movies.load_movies,
        "score": recommend_movies.score_movies,
        "collection": recommend_movies.movies_collection,
    },
    "tv_shows": {
        "label": "TV Shows",
        "load": recommend_tv.load_tv_shows,
        "score": recommend_tv.score_tv_shows,
        "collection": recommend_tv.tv_shows_collection,
    },
    "books": {
        "label": "Books",
        "load": recommend_books.load_books,
        "score": recommend_books.score_books,
        "collection": recommend_books.books_collection,
    },
    "music": {
        "label": "Music",
        "load": recommend_music.load_music,
        "score": recommend_music.score_music,
        "collection": recommend_music.music_collection,
    },
    "podcasts": {
        "label": "Podcasts",
        "load": recommend_podcast.load_podcasts,
        "score": recommend_podcast.score_podcasts,
        "collection": recommend_podcast.podcasts_collection,
    },
    "activities": {
        "label": "Activities",
        "load": recommend_activities.load_activities,
        "score": recommend_activities.score_activities,
        "collection": recommend_activities.activities_collection,
    },
}


def _get_todays_moods(user):
    daily_mood = user.get("daily_mood", {})
    moods = []
    if isinstance(daily_mood, dict):
        primary = daily_mood.get("mood")
        secondary = daily_mood.get("secondary_mood")
        if primary:
            moods.append(primary)
        if secondary:
            moods.append(secondary)
    return moods, daily_mood.get("date")


def _needs_personality_refresh(cache, current_percentages):
    if not cache or not cache.get("generated_at"):
        return True
    if cache.get("personality_source") != current_percentages:
        return True  # any change in the quiz result — not just a top-trait
        # swap — means old picks no longer reflect the current personality
    try:
        generated_at = datetime.fromisoformat(cache["generated_at"])
    except (KeyError, ValueError, TypeError):
        return True
    if generated_at.tzinfo is None:
        # cached before this file switched to timezone-aware timestamps —
        # those were always UTC under the hood (utcnow()), so just label them
        generated_at = generated_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - generated_at >= timedelta(days=REFRESH_INTERVAL_DAYS)


def _build_personality_lists(user_personality, top_traits):
    lists = {}
    for key, cfg in CATEGORY_CONFIG.items():
        items = cfg["load"]()
        scored = cfg["score"](items, user_personality, [])
        lists[key] = [str(item["_id"]) for _, item in scored[:10]]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "personality_source": dict(user_personality),
        "top_traits_at_generation": top_traits,  # kept for debugging/display only
        "lists": lists,
    }


def _build_mood_lists(user_personality, todays_moods, mood_date):
    lists = {}
    for key, cfg in CATEGORY_CONFIG.items():
        if not todays_moods:
            lists[key] = []
            continue
        items = cfg["load"]()
        scored = cfg["score"](items, user_personality, todays_moods)
        lists[key] = [str(item["_id"]) for _, item in scored[:3]]
    return {"mood_source_date": mood_date, "lists": lists}


def _fetch_by_ids(collection, id_strings):
    if not id_strings:
        return []
    try:
        object_ids = [ObjectId(i) for i in id_strings]
    except Exception:
        return []
    found = {str(doc["_id"]): doc for doc in collection.find({"_id": {"$in": object_ids}})}
    # preserve the ranked order the cache stored, not Mongo's return order
    return [found[i] for i in id_strings if i in found]


def get_recommendations(username, force_refresh=False):
    """
    Returns a dict shaped for Home to render directly:

    {
        "user": <full mongo user document>,
        "top_traits": [...],
        "personality_percentages": {...},
        "todays_moods": [...],
        "personality": {category_key: [up to 10 full item docs]},
        "mood": {category_key: [up to 3 full item docs]},
    }

    Returns None if the username doesn't exist.
    """
    user = users_collection.find_one({"username": username})
    if not user:
        return None

    personality_data = user.get("personality", {})
    user_personality = personality_data.get("percentages", {})
    top_traits = personality_data.get("top_traits", [])

    todays_moods, mood_date = _get_todays_moods(user)

    cache = user.get("recommendations_cache", {})
    personality_cache = cache.get("personality")
    mood_cache = cache.get("mood")

    updates = {}

    if force_refresh or _needs_personality_refresh(personality_cache, user_personality):
        personality_cache = _build_personality_lists(user_personality, top_traits)
        updates["recommendations_cache.personality"] = personality_cache

    if not mood_cache or mood_cache.get("mood_source_date") != mood_date:
        mood_cache = _build_mood_lists(user_personality, todays_moods, mood_date)
        updates["recommendations_cache.mood"] = mood_cache

    if updates:
        users_collection.update_one({"username": username}, {"$set": updates})

    result = {
        "user": user,
        "top_traits": top_traits,
        "personality_percentages": user_personality,
        "todays_moods": todays_moods,
        "personality": {},
        "mood": {},
    }

    for key, cfg in CATEGORY_CONFIG.items():
        result["personality"][key] = _fetch_by_ids(cfg["collection"], personality_cache["lists"].get(key, []))
        result["mood"][key] = _fetch_by_ids(cfg["collection"], mood_cache["lists"].get(key, []))

    return result


if __name__ == "__main__":
    test_username = input("Enter username: ").strip()
    data = get_recommendations(test_username)
    if not data:
        print("User not found.")
    else:
        print(f"\nTop traits: {data['top_traits']}")
        print(f"Today's moods: {data['todays_moods']}\n")
        for key, cfg in CATEGORY_CONFIG.items():
            print(f"--- {cfg['label']} (personality, top {len(data['personality'][key])}) ---")
            for item in data["personality"][key]:
                print(f"  {item.get('title', 'Unknown')}")
            print(f"--- {cfg['label']} (today's mood, top {len(data['mood'][key])}) ---")
            for item in data["mood"][key]:
                print(f"  {item.get('title', 'Unknown')}")
            print()