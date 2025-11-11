"""YouTube search and fallback embedding logic.

If YOUTUBE_API_KEY is set, use YouTube Data API v3 to fetch top 3 tutorial videos.
Otherwise, return curated defaults based on product type and a query link.
"""
from typing import List, Dict, Optional
import os

try:
    from googleapiclient.discovery import build  # type: ignore
except Exception:  # pragma: no cover
    build = None  # Fallback when library missing

CURATED_DEFAULTS: Dict[str, str] = {
    "Laptop/PC": "dQw4w9WgXcQ",  # Placeholder demo video id
    "Smartphone": "fC7oUOUEEi4",
    "Tablet": "fC7oUOUEEi4",
    "Router/Modem": "XQ9NeR3Qdm0",
    "Game Console": "1x6mZ8v9zjY",
    "Printer": "IcrbM1l_BoI",
    "Smart TV": "q1LCVnE2YFE",
    "Other": "dQw4w9WgXcQ",
}

class YouTubeVideo:
    def __init__(self, video_id: str, title: str, channel: str, duration: str):
        self.video_id = video_id
        self.title = title
        self.channel = channel
        self.duration = duration

    def to_dict(self):
        return {
            "videoId": self.video_id,
            "title": self.title,
            "channel": self.channel,
            "duration": self.duration,
        }

def build_query(product_type: str, brand: str, model: str, keywords: List[str]) -> str:
    base_terms = [product_type, brand, model] + keywords
    filtered = [t for t in base_terms if t]
    search_core = " ".join(filtered)
    # Append fix/troubleshoot modifiers
    return f"{search_core} fix troubleshoot repair"

def search_youtube(product_type: str, brand: str, model: str, keywords: List[str]) -> Dict[str, List[Dict[str, str]]]:
    api_key = os.getenv("YOUTUBE_API_KEY")
    query = build_query(product_type, brand, model, keywords)

    if not api_key or not build:
        # Fallback: just return curated default + query link
        default_id = CURATED_DEFAULTS.get(product_type, CURATED_DEFAULTS["Other"])
        videos = [
            YouTubeVideo(default_id, f"{product_type} basic troubleshooting", "Curated", "PT10M").to_dict(),
        ]
        return {"query": query, "videos": videos, "fallback": True}

    try:
        yt = build("youtube", "v3", developerKey=api_key)
        resp = yt.search().list(q=query, part="snippet", type="video", maxResults=3).execute()
        items = resp.get("items", [])
        videos: List[Dict[str, str]] = []
        for it in items:
            vid = it["id"]["videoId"]
            snippet = it["snippet"]
            title = snippet.get("title", "Untitled")
            channel = snippet.get("channelTitle", "")
            # Duration requires videos.list; keep placeholder for minimal call
            videos.append(YouTubeVideo(vid, title, channel, "PT10M").to_dict())
        if not videos:
            default_id = CURATED_DEFAULTS.get(product_type, CURATED_DEFAULTS["Other"])
            videos = [YouTubeVideo(default_id, f"{product_type} basic troubleshooting", "Curated", "PT10M").to_dict()]
        return {"query": query, "videos": videos, "fallback": False}
    except Exception:
        default_id = CURATED_DEFAULTS.get(product_type, CURATED_DEFAULTS["Other"])
        videos = [YouTubeVideo(default_id, f"{product_type} basic troubleshooting", "Curated", "PT10M").to_dict()]
        return {"query": query, "videos": videos, "fallback": True}
