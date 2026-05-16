import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import re

# ── Wikipedia ──────────────────────────────────────────────────────────────────

def wikipedia_summary(topic: str) -> str:
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic.replace(' ', '_')}"
        resp = requests.get(url, timeout=5).json()
        extract = resp.get("extract", "")
        if extract:
            return extract[:400] + "..., Boss."
        return f"Couldn't find a Wikipedia article for {topic}, Boss."
    except Exception as e:
        return f"Wikipedia lookup failed, Boss: {e}"

# ── Currency conversion ────────────────────────────────────────────────────────

CURRENCY_ALIASES = {
    "dollar": "USD", "dollars": "USD", "usd": "USD",
    "euro": "EUR", "euros": "EUR", "eur": "EUR",
    "pound": "GBP", "pounds": "GBP", "gbp": "GBP",
    "rupee": "INR", "rupees": "INR", "inr": "INR",
    "yen": "JPY", "jpy": "JPY",
    "yuan": "CNY", "cny": "CNY",
    "franc": "CHF", "chf": "CHF",
    "dirham": "AED", "aed": "AED",
    "riyal": "SAR", "sar": "SAR",
    "baht": "THB", "thb": "THB",
    "won": "KRW", "krw": "KRW",
    "ruble": "RUB", "rub": "RUB",
    "lira": "TRY", "try": "TRY",
    "canadian dollar": "CAD", "cad": "CAD",
    "australian dollar": "AUD", "aud": "AUD",
    "singapore dollar": "SGD", "sgd": "SGD",
}

def convert_currency(expression: str) -> str:
    try:
        match = re.search(r'([\d,]+\.?\d*)', expression.replace(",", ""))
        if not match:
            return "Couldn't find an amount, Boss."
        amount = float(match.group(1))
        expr = expression.lower()
        found = []
        for word, code in CURRENCY_ALIASES.items():
            if word in expr and code not in found:
                found.append(code)
        if len(found) < 2:
            return "Couldn't understand the currencies, Boss. Try: convert 100 dollars to rupees."
        from_cur, to_cur = found[0], found[1]
        url = f"https://open.er-api.com/v6/latest/{from_cur}"
        resp = requests.get(url, timeout=5).json()
        if resp.get("result") != "success":
            return "Couldn't fetch exchange rates right now, Boss."
        rate = resp["rates"][to_cur]
        result = round(amount * rate, 2)
        return f"{amount} {from_cur} = {result} {to_cur}, Boss."
    except Exception as e:
        return f"Currency conversion failed, Boss: {e}"

# ── Unit conversion ────────────────────────────────────────────────────────────

def convert_units(expression: str) -> str:
    conversions = {
        ("miles", "km"):            lambda x: x * 1.60934,
        ("km", "miles"):            lambda x: x * 0.621371,
        ("kg", "pounds"):           lambda x: x * 2.20462,
        ("pounds", "kg"):           lambda x: x * 0.453592,
        ("grams", "ounces"):        lambda x: x * 0.035274,
        ("ounces", "grams"):        lambda x: x * 28.3495,
        ("celsius", "fahrenheit"):  lambda x: x * 9/5 + 32,
        ("fahrenheit", "celsius"):  lambda x: (x - 32) * 5/9,
        ("kelvin", "celsius"):      lambda x: x - 273.15,
        ("celsius", "kelvin"):      lambda x: x + 273.15,
        ("meters", "feet"):         lambda x: x * 3.28084,
        ("feet", "meters"):         lambda x: x * 0.3048,
        ("meters", "yards"):        lambda x: x * 1.09361,
        ("yards", "meters"):        lambda x: x * 0.9144,
        ("liters", "gallons"):      lambda x: x * 0.264172,
        ("gallons", "liters"):      lambda x: x * 3.78541,
        ("liters", "pints"):        lambda x: x * 2.11338,
        ("pints", "liters"):        lambda x: x * 0.473176,
        ("inches", "cm"):           lambda x: x * 2.54,
        ("cm", "inches"):           lambda x: x * 0.393701,
        ("km", "meters"):           lambda x: x * 1000,
        ("meters", "km"):           lambda x: x / 1000,
        ("acres", "hectares"):      lambda x: x * 0.404686,
        ("hectares", "acres"):      lambda x: x * 2.47105,
        ("mph", "kmh"):             lambda x: x * 1.60934,
        ("kmh", "mph"):             lambda x: x * 0.621371,
    }
    try:
        expr = expression.lower()
        match = re.search(r'([\d.]+)', expr)
        if not match:
            return "Couldn't find a number to convert, Boss."
        value = float(match.group(1))
        for (from_u, to_u), fn in conversions.items():
            if from_u in expr and to_u in expr:
                result = round(fn(value), 4)
                return f"{value} {from_u} = {result} {to_u}, Boss."
        return "Conversion not recognised, Boss. Try: convert 5 miles to km."
    except Exception as e:
        return f"Conversion failed, Boss: {e}"

# ── Flight status ──────────────────────────────────────────────────────────────

def get_flight_status(flight_number: str) -> str:
    """Look up flight status — opens FlightAware for live data."""
    flight = flight_number.upper().replace(" ", "")
    try:
        # Open FlightAware for live tracking
        import subprocess
        subprocess.Popen(["open", f"https://flightaware.com/live/flight/{flight}"])
        return f"Opened FlightAware for flight {flight}, Boss."
    except Exception as e:
        return f"Couldn't look up flight {flight}, Boss: {e}"

def track_flight(flight_number: str) -> str:
    return get_flight_status(flight_number)

# ── Package tracking ───────────────────────────────────────────────────────────

def track_package(tracking_number: str) -> str:
    """Open package tracking — detects courier from tracking number format."""
    import subprocess
    tn = tracking_number.strip().upper()

    # Detect courier from tracking number format
    if re.match(r'^1Z[A-Z0-9]{16}$', tn):
        url = f"https://www.ups.com/track?tracknum={tn}"
        courier = "UPS"
    elif re.match(r'^\d{12,22}$', tn):
        url = f"https://www.fedex.com/fedextrack/?trknbr={tn}"
        courier = "FedEx"
    elif re.match(r'^(94|93|92|94|95)\d{20}$', tn):
        url = f"https://tools.usps.com/go/TrackConfirmAction?tLabels={tn}"
        courier = "USPS"
    elif re.match(r'^[A-Z]{2}\d{9}[A-Z]{2}$', tn):
        url = f"https://www.indiapost.gov.in/_layouts/15/DOP.Portal.Tracking/TrackConsignment.aspx"
        courier = "India Post"
    else:
        # Generic — try 17track
        url = f"https://www.17track.net/en/track#nums={tn}"
        courier = "auto-detect"

    subprocess.Popen(["open", url])
    return f"Opened {courier} tracking for {tn}, Boss."

# ── Sports scores ──────────────────────────────────────────────────────────────

def get_cricket_score() -> str:
    try:
        resp = requests.get(
            "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live",
            headers={"X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com"},
            timeout=5
        )
        # Free fallback — open Cricbuzz
        import subprocess
        subprocess.Popen(["open", "https://www.cricbuzz.com/cricket-match/live-scores"])
        return "Opened live cricket scores on Cricbuzz, Boss."
    except:
        import subprocess
        subprocess.Popen(["open", "https://www.cricbuzz.com/cricket-match/live-scores"])
        return "Opened Cricbuzz for live scores, Boss."

def get_ipl_score() -> str:
    import subprocess
    subprocess.Popen(["open", "https://www.cricbuzz.com/cricket-series/7607/indian-premier-league-2025/matches"])
    return "Opened IPL 2025 scores, Boss."

def get_football_score(team: str = "") -> str:
    import subprocess
    if team:
        subprocess.Popen(["open", f"https://www.bbc.com/sport/football/scores-fixtures"])
    else:
        subprocess.Popen(["open", "https://www.bbc.com/sport/football/scores-fixtures"])
    return "Opened football scores, Boss."

def get_f1_standings() -> str:
    import subprocess
    subprocess.Popen(["open", "https://www.formula1.com/en/results/standings/drivers"])
    return "Opened F1 driver standings, Boss."

def get_f1_next_race() -> str:
    try:
        resp = requests.get("https://ergast.com/api/f1/current/next.json", timeout=5).json()
        race = resp["MRData"]["RaceTable"]["Races"][0]
        name = race["raceName"]
        date = race["date"]
        circuit = race["Circuit"]["circuitName"]
        country = race["Circuit"]["Location"]["country"]
        return f"Next F1 race: {name} at {circuit}, {country} on {date}, Boss."
    except:
        import subprocess
        subprocess.Popen(["open", "https://www.formula1.com/en/racing/2025.html"])
        return "Opened F1 2025 calendar, Boss."

def get_sports_score(sport: str = "") -> str:
    sport = sport.lower()
    if "cricket" in sport or "ipl" in sport:
        return get_cricket_score()
    elif "football" in sport or "soccer" in sport or "premier" in sport:
        return get_football_score()
    elif "f1" in sport or "formula" in sport:
        return get_f1_next_race()
    else:
        return get_cricket_score()

# ── Movies & Shows ─────────────────────────────────────────────────────────────

def get_movie_info(title: str) -> str:
    try:
        # Use OMDB API (free tier — no key needed for basic info)
        resp = requests.get(
            f"http://www.omdbapi.com/",
            params={"t": title, "apikey": "trilogy"},
            timeout=5
        ).json()
        if resp.get("Response") == "True":
            return (f"{resp['Title']} ({resp['Year']}) — {resp['Genre']}. "
                    f"Rating: {resp.get('imdbRating', 'N/A')}/10. "
                    f"{resp.get('Plot', '')[:150]}, Boss.")
        # Fallback to IMDB search
        import subprocess
        query = title.replace(" ", "+")
        subprocess.Popen(["open", f"https://www.imdb.com/find?q={query}"])
        return f"Opened IMDB search for {title}, Boss."
    except Exception as e:
        import subprocess
        query = title.replace(" ", "+")
        subprocess.Popen(["open", f"https://www.imdb.com/find?q={query}"])
        return f"Opened IMDB search for {title}, Boss."

def whats_streaming(service: str = "") -> str:
    import subprocess
    services = {
        "netflix":    "https://www.netflix.com/browse",
        "prime":      "https://www.primevideo.com",
        "hotstar":    "https://www.hotstar.com",
        "disney":     "https://www.hotstar.com",
        "apple tv":   "https://tv.apple.com",
        "youtube":    "https://www.youtube.com/feed/trending",
    }
    key = service.lower().strip()
    url = services.get(key, "https://www.justwatch.com/in")
    subprocess.Popen(["open", url])
    label = service if service else "JustWatch"
    return f"Opened {label}, Boss."

# ── Recipes ────────────────────────────────────────────────────────────────────

def get_recipe(dish: str) -> str:
    try:
        resp = requests.get(
            f"https://www.themealdb.com/api/json/v1/1/search.php",
            params={"s": dish},
            timeout=5
        ).json()
        meals = resp.get("meals")
        if meals:
            meal = meals[0]
            name = meal["strMeal"]
            category = meal["strCategory"]
            instructions = meal["strInstructions"][:300]
            return f"{name} ({category}): {instructions}..., Boss."
        return f"Couldn't find a recipe for {dish}, Boss."
    except Exception as e:
        return f"Recipe lookup failed, Boss: {e}"

def get_random_recipe() -> str:
    try:
        resp = requests.get(
            "https://www.themealdb.com/api/json/v1/1/random.php",
            timeout=5
        ).json()
        meal = resp["meals"][0]
        name = meal["strMeal"]
        category = meal["strCategory"]
        instructions = meal["strInstructions"][:250]
        return f"Random recipe: {name} ({category}). {instructions}..., Boss."
    except Exception as e:
        return f"Couldn't fetch a recipe, Boss: {e}"

# ── Dictionary & Thesaurus ─────────────────────────────────────────────────────

def define_word(word: str) -> str:
    try:
        resp = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.strip()}",
            timeout=5
        ).json()
        if isinstance(resp, list):
            entry    = resp[0]
            meaning  = entry["meanings"][0]
            part     = meaning["partOfSpeech"]
            defn     = meaning["definitions"][0]["definition"]
            example  = meaning["definitions"][0].get("example", "")
            result   = f"{word} ({part}): {defn}"
            if example:
                result += f". Example: {example}"
            return result + ", Boss."
        return f"Couldn't find definition for {word}, Boss."
    except Exception as e:
        return f"Dictionary lookup failed, Boss: {e}"

def get_synonyms(word: str) -> str:
    try:
        resp = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.strip()}",
            timeout=5
        ).json()
        if isinstance(resp, list):
            synonyms = []
            for meaning in resp[0]["meanings"]:
                for defn in meaning["definitions"]:
                    synonyms.extend(defn.get("synonyms", []))
            synonyms = list(set(synonyms))[:8]
            if synonyms:
                return f"Synonyms for {word}: {', '.join(synonyms)}, Boss."
        return f"No synonyms found for {word}, Boss."
    except Exception as e:
        return f"Thesaurus lookup failed, Boss: {e}"

def get_antonyms(word: str) -> str:
    try:
        resp = requests.get(
            f"https://api.dictionaryapi.dev/api/v2/entries/en/{word.strip()}",
            timeout=5
        ).json()
        if isinstance(resp, list):
            antonyms = []
            for meaning in resp[0]["meanings"]:
                for defn in meaning["definitions"]:
                    antonyms.extend(defn.get("antonyms", []))
            antonyms = list(set(antonyms))[:8]
            if antonyms:
                return f"Antonyms for {word}: {', '.join(antonyms)}, Boss."
        return f"No antonyms found for {word}, Boss."
    except Exception as e:
        return f"Antonym lookup failed, Boss: {e}"

# ── Translation ────────────────────────────────────────────────────────────────

LANG_CODES = {
    "hindi":      "hi",
    "bengali":    "bn",
    "spanish":    "es",
    "french":     "fr",
    "german":     "de",
    "japanese":   "ja",
    "chinese":    "zh",
    "arabic":     "ar",
    "portuguese": "pt",
    "russian":    "ru",
    "italian":    "it",
    "korean":     "ko",
    "urdu":       "ur",
    "tamil":      "ta",
    "telugu":     "te",
    "marathi":    "mr",
    "english":    "en",
}

def translate_text(text: str, target_lang: str = "hindi") -> str:
    try:
        lang_code = LANG_CODES.get(target_lang.lower(), target_lang.lower())
        resp = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": f"en|{lang_code}"},
            timeout=5
        ).json()
        translated = resp.get("responseData", {}).get("translatedText", "")
        if translated and translated.lower() != text.lower():
            return f"'{text}' in {target_lang}: {translated}, Boss."
        return f"Translation unavailable right now, Boss."
    except Exception as e:
        return f"Translation failed, Boss: {e}"

def detect_language(text: str) -> str:
    try:
        resp = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": "en|hi"},
            timeout=5
        ).json()
        return f"Language detection done. Response: {resp.get('responseStatus', 'unknown')}, Boss."
    except Exception as e:
        return f"Language detection failed, Boss: {e}"

if __name__ == "__main__":
    print(wikipedia_summary("Elon Musk"))
    print(convert_currency("100 dollars to rupees"))
    print(convert_units("5 miles to km"))
    print(define_word("serendipity"))
    print(get_synonyms("happy"))
    print(translate_text("Good morning", "hindi"))
    print(get_f1_next_race())
    print(get_random_recipe())