"""Thin provider wrappers: Gemini for generation, Perplexity for search."""

import json
import os

import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

_GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
_client: genai.Client | None = None


def _gemini_client() -> genai.Client:
    global _client
    if _client is None:
        if not _GEMINI_KEY:
            raise RuntimeError("GEMINI_API_KEY not set")
        _client = genai.Client(api_key=_GEMINI_KEY)
    return _client


GEMINI_FAST = "gemini-2.5-flash"
GEMINI_QUALITY = "gemini-2.5-pro"


def gemini_json(prompt: str, *, model: str = GEMINI_FAST, system: str | None = None, max_tokens: int = 1024) -> dict:
    """Call Gemini and parse a JSON response. Raises on failure."""
    client = _gemini_client()
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        max_output_tokens=max_tokens,
        temperature=0.7,
        system_instruction=system,
    )
    resp = client.models.generate_content(model=model, contents=prompt, config=config)
    text = (resp.text or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)


PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"


def perplexity_search(query: str, *, model: str = "sonar", max_tokens: int = 1500) -> dict:
    """Query Perplexity Sonar. Returns parsed JSON content + citations."""
    key = os.environ.get("PERPLEXITY_API_KEY", "")
    if not key:
        raise RuntimeError("PERPLEXITY_API_KEY not set")

    system = (
        "You are a job search assistant. Return ONLY valid JSON matching the requested schema. "
        "No prose, no markdown fences."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": query},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    resp = requests.post(PERPLEXITY_URL, json=payload, headers=headers, timeout=45)
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    citations = data.get("citations", []) or data.get("search_results", [])
    return {"content": json.loads(content), "citations": citations}
