import re


# =====================================================
# SINGLE VALUE EXTRACTION
# =====================================================
def extract_value(text, key=None):
    """
    Extracts a single value from messy input.
    Examples:
    - "city: Kochi" → Kochi
    - "Kochi" → Kochi
    """

    if not text:
        return ""

    text = text.strip()

    # Normalize spacing
    text = re.sub(r"\s+", " ", text)

    # Case 1: key:value format
    if key:
        pattern = rf"{key}\s*:\s*(.*)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Case 2: generic key:value
    if ":" in text:
        parts = text.split(":", 1)
        return parts[1].strip()

    # Case 3: plain text
    return text


# =====================================================
# TWO VALUE EXTRACTION
# =====================================================
def extract_two_values(text):
    """
    Extracts (value1, value2) from messy input.

    Handles:
    - "city: Kochi, interest: temples"
    - "Kochi, temples"
    - "Kochi temples"
    """

    if not text:
        return "", ""

    text = text.strip()
    text = re.sub(r"\s+", " ", text)

    # Case 1: structured key:value pairs
    pairs = re.findall(r"(\w+)\s*:\s*([^,]+)", text)

    if len(pairs) >= 2:
        return pairs[0][1].strip(), pairs[1][1].strip()

    # Case 2: comma-separated
    if "," in text:
        parts = [p.strip() for p in text.split(",")]
        if len(parts) >= 2:
            return parts[0], parts[1]

    # Case 3: space-separated fallback
    words = text.split()
    if len(words) >= 2:
        return words[0], " ".join(words[1:])

    return text, ""

def extract_preference(query):

    query = query.lower()

    preferences = {
        "budget": ["budget"],
        "location": ["location", "city", "destination"],
        "travel_date": ["date", "travel date"],
        "transport": ["flight", "train", "bus"]
    }

    for key, keywords in preferences.items():

        for word in keywords:

            if word in query:

                parts = query.split(word)

                if len(parts) > 1:

                    value = parts[1].replace("is", "").replace(":", "").strip()

                    return key, value

    return None, None