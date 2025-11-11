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
    # Safer general tech-repair tutorials (placeholders; replace with your curated picks)
    "Laptop/PC": "xQZ8dS2o3kI",
    "Smartphone": "Gv0R0bS3W8M",
    "Tablet": "2u5YxX1Q7nA",
    "Router/Modem": "Zk8Q5h4nE1c",
    "Game Console": "Wq3J6l9T0pU",
    "Printer": "Hk9L2d3S4mN",
    "Smart TV": "Qp7R8s1V2xY",
    "Other": "xQZ8dS2o3kI",
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

NEGATIVE_TERMS = ["official video", "lyrics", "music", "song", "remix", "cover"]
POSITIVE_TERMS = ["fix", "repair", "troubleshoot", "how to", "guide", "tutorial"]

def build_query(product_type: str, brand: str, model: str, keywords: List[str]) -> str:
    base_terms = [product_type, brand, model] + keywords + POSITIVE_TERMS
    filtered = [t for t in base_terms if t]
    search_core = " ".join(filtered)
    return search_core

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
        resp = yt.search().list(q=query, part="snippet", type="video", maxResults=6, safeSearch="moderate").execute()
        items = resp.get("items", [])
        ids = [it["id"]["videoId"] for it in items if it.get("id", {}).get("videoId")]
        videos: List[Dict[str, str]] = []
        if ids:
            detail = yt.videos().list(part="contentDetails,snippet", id=",".join(ids)).execute()
            for it in detail.get("items", []):
                vid = it.get("id", "")
                sn = it.get("snippet", {})
                title = sn.get("title", "Untitled")
                channel = sn.get("channelTitle", "")
                duration = it.get("contentDetails", {}).get("duration", "PT10M")
                videos.append(YouTubeVideo(vid, title, channel, duration).to_dict())

        # Rerank: prefer repair-related titles and those matching device terms; penalize music-y titles
        def score(v: Dict[str, str]) -> int:
            t = (v.get("title") or "").lower()
            s = 0
            for term in POSITIVE_TERMS:
                if term in t:
                    s += 3
            for term in [product_type.lower(), (brand or "").lower(), (model or "").lower()]:
                if term and term in t:
                    s += 2
            for bad in NEGATIVE_TERMS:
                if bad in t:
                    s -= 5
            return s

        videos = sorted(videos, key=score, reverse=True)[:3]

        if not videos:
            default_id = CURATED_DEFAULTS.get(product_type, CURATED_DEFAULTS["Other"])
            videos = [YouTubeVideo(default_id, f"{product_type} basic troubleshooting", "Curated", "PT10M").to_dict()]
        return {"query": query, "videos": videos, "fallback": False}
    except Exception:
        default_id = CURATED_DEFAULTS.get(product_type, CURATED_DEFAULTS["Other"])
        videos = [YouTubeVideo(default_id, f"{product_type} basic troubleshooting", "Curated", "PT10M").to_dict()]
        return {"query": query, "videos": videos, "fallback": True}
