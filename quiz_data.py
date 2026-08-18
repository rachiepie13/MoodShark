TRAITS = [
    "Visionary", "Realist", "Cheerleader", "Daydreamer", "Curator",
    "Maverick", "Nurturer", "Strategist", "Seeker", "Challenger"
]

# Each question: text + list of (letter, option_text, {trait: points})
QUESTIONS = [
    {
        "question": "Pick a smell.",
        "options": [
            ("A", "Rain hitting hot pavement", {"Daydreamer": 3, "Curator": 1}),
            ("B", "Fresh coffee in a busy kitchen", {"Cheerleader": 2, "Nurturer": 2}),
            ("C", "Old paper in a vintage bookstore", {"Curator": 3, "Visionary": 1}),
            ("D", "Woodsmoke from a fire you built yourself", {"Seeker": 3, "Maverick": 1}),
            ("E", "The smell of an old map that's been folded away for years", {"Strategist": 2, "Challenger": 2}),
        ]
    },
    {
        "question": "Pick a song lyric that resonates the most with you.",
        "options": [
            ("A", "\u201cWe are always running for the thrill of it\u201d", {"Daydreamer": 3, "Maverick": 1}),
            ("B", "\u201cTell me what has become of my rights, am I invisible 'cause you ignore me?\u201d", {"Maverick": 3, "Challenger": 1}),
            ("C", "\u201cWhen my time comes around, lay me gently in the cold, dark earth, no grave can hold my body down. I'll crawl home to her.\u201d", {"Nurturer": 3, "Daydreamer": 1}),
            ("D", "\u201cWhen thunderclouds start pouring down, light a fire they can't put out, carve your name into those shining stars.\u201d", {"Seeker": 3, "Curator": 1}),
        ]
    },
    {
        "question": "Pick a place to spend an afternoon.",
        "options": [
            ("A", "A tiny bookstore where the shelves seem to go on forever.", {"Curator": 3, "Daydreamer": 1}),
            ("B", "A crowded street during a festival, with music coming from somewhere around every corner.", {"Cheerleader": 4}),
            ("C", "A quiet café with rain against the windows and absolutely nowhere you need to be.", {"Nurturer": 2, "Daydreamer": 2}),
            ("D", "A workshop where you can take something apart just to see how it works.", {"Strategist": 3, "Challenger": 1}),
            ("E", "A train station, but you don't know where the train is going.", {"Maverick": 3, "Challenger": 1}),
        ]
    },
    {
        "question": "If you were a mythical creature for a day, which would you be?",
        "options": [
            ("A", "A phoenix, rising from the ashes just to prove you could.", {"Challenger": 3, "Maverick": 1}),
            ("B", "A dragon guarding a hoard of secrets you're still cataloging.", {"Strategist": 3, "Visionary": 1}),
            ("C", "A unicorn wandering a forest no one else can find.", {"Daydreamer": 4}),
            ("D", "A griffin guarding its nest.", {"Nurturer": 3, "Cheerleader": 1}),
            ("E", "A kraken, mostly just enjoying being left alone.", {"Maverick": 3, "Realist": 1}),
        ]
    },
    {
        "question": "Pick an animal you'd want as a travel companion.",
        "options": [
            ("A", "An owl who always seems to know something you don't.", {"Visionary": 3, "Strategist": 1}),
            ("B", "A fox who takes the scenic route on purpose, always leading you somewhere new.", {"Seeker": 3, "Maverick": 1}),
            ("C", "A horse that never seems bothered by the journey, no matter how rough the road gets.", {"Realist": 3, "Strategist": 1}),
            ("D", "A cat who only comes along if it feels like it.", {"Maverick": 3, "Challenger": 1}),
            ("E", "An elephant who remembers every place you've been and every story you've told it.", {"Nurturer": 4}),
        ]
    },
    {
        "question": "At the end of a really good day, what makes you think, \u201cYeah. That was worth it\u201d?",
        "options": [
            ("A", "You discovered something you didn't know before.", {"Seeker": 3, "Visionary": 1}),
            ("B", "You made someone else's day a little better.", {"Nurturer": 3, "Cheerleader": 1}),
            ("C", "You finally did something you've been putting off.", {"Realist": 3, "Strategist": 1}),
            ("D", "You experienced something you'll probably think about for weeks.", {"Daydreamer": 3, "Curator": 1}),
            ("E", "You did something your usual self wouldn't have dared to do.", {"Maverick": 3, "Challenger": 1}),
        ]
    },
    {
        "question": "Pick something you'd want in your pocket.",
        "options": [
            ("A", "A compass that always points somewhere interesting.", {"Seeker": 3, "Visionary": 1}),
            ("B", "A diary written by someone who lived centuries ago.", {"Curator": 4}),
            ("C", "A pocket watch that runs a little fast.", {"Challenger": 3, "Strategist": 1}),
            ("D", "A single coin for good luck.", {"Cheerleader": 3, "Daydreamer": 1}),
            ("E", "A tiny multitool that fixes almost anything.", {"Realist": 3, "Strategist": 1}),
        ]
    },
    {
        "question": "Pick a sound that stops you in your tracks.",
        "options": [
            ("A", "Thunder rolling in somewhere far off.", {"Visionary": 3, "Seeker": 1}),
            ("B", "A room full of your loved ones laughing.", {"Cheerleader": 3, "Nurturer": 1}),
            ("C", "A pen scratching fast across paper.", {"Strategist": 3, "Realist": 1}),
            ("D", "Static clearing into a clean radio signal.", {"Challenger": 3, "Visionary": 1}),
            ("E", "Old floorboards creaking in an empty house.", {"Curator": 3, "Daydreamer": 1}),
        ]
    },
    {
        "question": "Which kind of story would you be more invested in?",
        "options": [
            ("A", "An adventure where the main character grows and discovers more about themselves through the experiences they encounter along the way.", {"Seeker": 3, "Nurturer": 1}),
            ("B", "A thriller where seemingly insignificant details gradually fall into place until everything suddenly makes sense.", {"Strategist": 3, "Curator": 1}),
            ("C", "A story where the character chooses a path nobody expected them to take.", {"Maverick": 3, "Challenger": 1}),
            ("D", "An open-ended story that leaves you wondering what happened long after you've finished it.", {"Daydreamer": 3, "Visionary": 1}),
            ("E", "A bittersweet story where a hero makes the ultimate sacrifice to save the world.", {"Nurturer": 3, "Cheerleader": 1}),
        ]
    },
    {
        "question": "You find a strange object at a flea market. What makes you pick it up?",
        "options": [
            ("A", "It looks like something from a future that hasn't happened yet.", {"Visionary": 4}),
            ("B", "You can already think of multiple ways to make use of it.", {"Realist": 3, "Curator": 1}),
            ("C", "You have absolutely no idea what it is, and now you need to know.", {"Challenger": 3, "Seeker": 1}),
            ("D", "It reminds you of something you can't quite remember.", {"Daydreamer": 3, "Nurturer": 1}),
            ("E", "The person selling it has a fascinating story about where it came from.", {"Curator": 3, "Seeker": 1}),
        ]
    },
    {
        "question": "You're told there's one rule in a strange new place: \u201cDon't touch the red door.\u201d What do you do?",
        "options": [
            ("A", "Immediately wonder why the door is red in the first place.", {"Challenger": 3, "Visionary": 1}),
            ("B", "Leave it alone. There is probably a very good reason, and you'd rather not create a problem for yourself.", {"Realist": 3, "Strategist": 1}),
            ("C", "Spend the rest of the day imagining what's behind it.", {"Daydreamer": 3, "Seeker": 1}),
            ("D", "Look for another way to find out what's behind it without opening it.", {"Strategist": 3, "Challenger": 1}),
            ("E", "Open it when nobody's looking. Obviously.", {"Maverick": 3, "Challenger": 1}),
        ]
    },
    {
        "question": "Pick a color you're drawn to right now.",
        "options": [
            ("A", "Deep forest green", {"Realist": 3, "Nurturer": 1}),
            ("B", "Electric blue", {"Visionary": 3, "Challenger": 1}),
            ("C", "Warm gold", {"Cheerleader": 3, "Daydreamer": 1}),
            ("D", "Slate gray", {"Strategist": 3, "Realist": 1}),
            ("E", "Deep burgundy", {"Curator": 3, "Maverick": 1}),
        ]
    },
    {
        "question": "You're stranded on an island with a few of your friends. What's the first thing you do?",
        "options": [
            ("A", "Take stock of what you have and start building a shelter before you need one.", {"Visionary": 3, "Strategist": 1}),
            ("B", "Start exploring the island, even if that means running into something dangerous.", {"Challenger": 3, "Maverick": 1}),
            ("C", "Focus on signaling for help; getting rescued matters more than settling in.", {"Realist": 4}),
            ("D", "Make sure everyone is okay first, then figure out how to make things as comfortable as possible for the group.", {"Nurturer": 4}),
            ("E", "Divide up the work: someone gathers resources, someone scouts, someone builds.", {"Strategist": 3, "Seeker": 1}),
        ]
    },
    {
        "question": "Which compliment would your friends give you?",
        "options": [
            ("A", "\u201cYou have a way of making everyone feel like they belong.\u201d", {"Cheerleader": 4}),
            ("B", "\u201cYou have a way of making impossible ideas sound possible.\u201d", {"Visionary": 4}),
            ("C", "\u201cI've never met anyone who sees the world quite the way you do.\u201d", {"Curator": 4}),
            ("D", "\u201cYou always know what to do when things go wrong.\u201d", {"Realist": 3, "Strategist": 1}),
            ("E", "\u201cYou ask the kind of questions that make people stop and think.\u201d", {"Challenger": 3, "Seeker": 1}),
        ]
    },
]

# title + description for the result screen
PERSONALITY_DESCRIPTIONS = {
    "Visionary": {
        "text": "You see possibilities where other people see blank spaces. You're drawn to new ideas, unusual possibilities, and imagining what could exist next. You don't need everything to make sense right away; sometimes the most interesting ideas are the ones that haven't been figured out yet.",
        "likes": "imaginative worlds, original ideas, unexpected concepts, and stories that make you wonder, \u201cHow did someone even think of this?\u201d"
    },
    "Realist": {
        "text": "You appreciate things that feel real. You don't need something to be flashy or complicated to enjoy it; if it has substance, feels genuine, and gives you something worth taking away, you've got a reason to stick around. When all your friends are getting carried away with an idea, you're probably somewhere nearby thinking, \u201cOkay, but does this actually work?\u201d",
        "likes": "authentic characters, grounded stories, practical ideas, and things that leave you feeling like your time was well spent."
    },
    "Cheerleader": {
        "text": "You are the human representation of the \u201csunshine\u201d in the grumpy x sunshine cringe rom-com trope, even though you probably won't like hearing this. You have a way of making ordinary moments feel a little more exciting. You love the kind of things that make you smile without having to work too hard for it. You probably enjoy sharing good experiences just as much as having them yourself. After all, what's the point of finding something wonderful if you can't drag everyone you love into it too?",
        "likes": "feel-good stories, infectious music, lovable characters, fun adventures, and anything that leaves you with an inexplicably good mood."
    },
    "Daydreamer": {
        "text": "Your imagination is basically its own little universe, and you visit often. You overthink everything, good or bad, replaying moments until they turn into something bigger than they were. You have the imagination of a movie director and the heart of a hopeless romantic. The stuff that actually gets you isn't always the stuff that makes the most sense; it's the stuff that lingers.",
        "likes": "dreamy worlds, emotional stories, atmospheric music, impossible romances, and anything that feels a little bit like escaping into another universe."
    },
    "Curator": {
        "text": "You're always looking for the meaning behind things. To you, almost anything can be art if you look at it the right way, and you're probably the friend with the most random knowledge about the most random things. You notice details other people miss, remember oddly specific facts, and somehow always have a song, movie, book, or obscure piece of history to recommend. And yes, you might get a little aggressive about gatekeeping the things you love, especially when you found them first.",
        "likes": "beautiful cinematography, distinctive aesthetics, atmospheric music, indie records, and stories with details worth noticing twice."
    },
    "Maverick": {
        "text": "You've never understood the appeal of choosing something just because everyone else did. You like having your own taste, your own opinions, and occasionally, your own questionable decisions. You can probably take being stabbed once or twice, but definitely not being bored. You're drawn to anything with a little edge and a refusal to follow the rules. You'll probably be the uncle who brings politics to the family dinner.",
        "likes": "unconventional characters, rebellious stories, bold music, unexpected endings, and anything that feels like it was made for people who don't like following the crowd."
    },
    "Nurturer": {
        "text": "You tend to notice how people are feeling, even when they haven't said anything. You value the little moments that make people feel understood, remembered, or cared for. You're probably the least controversial friend in every friend group, and somehow know everyone's birthday, cafeteria order, and family lore. Basically, the unpaid therapist and single mother of the entire friend group.",
        "likes": "heartfelt stories, unforgettable friendships, meaningful romances, emotional music, and characters you'll end up caring about far more than you intended."
    },
    "Strategist": {
        "text": "You enjoy the feeling of slowly figuring something out. Give you a complicated situation, a few suspicious details, and suddenly you're connecting the dots. You probably predict the ending of a movie before anyone else and then accidentally spoil it for your friends. I wouldn't be surprised if you used to watch escape room videos on YouTube growing up.",
        "likes": "clever plots, mysteries, intricate worlds, strategic characters, hidden clues, and those wonderfully satisfying moments when everything finally clicks."
    },
    "Seeker": {
        "text": "You're incredibly self-aware and always curious about yourself, other people, and the world around you. You like experiences that leave you with something to think about. If you don't journal, you've probably read at least 2\u20133 self-help books in your lifetime. Please stop trying to diagnose and psychoanalyze your friends every time they ask you for suggestions.",
        "likes": "coming-of-age stories, personal journeys, thought-provoking music, adventures, and anything that leaves you feeling like you've discovered something new about yourself."
    },
    "Challenger": {
        "text": "You have a difficult relationship with the phrase \u201cbecause that's just how it is.\u201d You like questions, contradictions, strange ideas, and anything that gives your brain something to chew on. You're curious enough to keep digging when everyone else has already accepted the obvious answer, and you probably enjoy a good debate more than you admit.",
        "likes": "mysteries, psychological stories, complex ideas, clever twists, alternative and indie music, and anything that keeps you thinking."
    },
}

# How close the top two traits need to be (percentage points) to show a
# "top two" result instead of a single trait. Kept low on purpose — a mix
# result should be the exception (a genuine near-tie), not the default
# outcome for most quiz-takers.
MIX_THRESHOLD = 4


def calculate_scores(answers):
    """
    answers: list of dicts, one per question answered, each the trait-points
    dict for the option they picked, e.g. {"Daydreamer": 3, "Curator": 1}

    Returns (raw_totals, percentages) both as {trait: number} dicts.
    """
    raw_totals = {t: 0 for t in TRAITS}
    for answer in answers:
        for trait, points in answer.items():
            raw_totals[trait] += points

    total_points = sum(raw_totals.values()) or 1  # avoid divide-by-zero
    percentages = {
        t: round((raw_totals[t] / total_points) * 100, 1)
        for t in TRAITS
    }
    return raw_totals, percentages


def get_result_summary(percentages):
    """
    Returns a dict describing the result:
    { "type": "single" or "mix", "traits": [trait, ...], "percentages": {...} }
    """
    ranked = sorted(percentages.items(), key=lambda x: x[1], reverse=True)
    top_trait, top_pct = ranked[0]
    second_trait, second_pct = ranked[1]

    if (top_pct - second_pct) <= MIX_THRESHOLD:
        return {
            "type": "mix",
            "traits": [top_trait, second_trait],
            "percentages": percentages,
            "ranked": ranked
        }
    else:
        return {
            "type": "single",
            "traits": [top_trait],
            "percentages": percentages,
            "ranked": ranked
        }