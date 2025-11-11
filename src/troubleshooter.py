import json
import textwrap
from typing import Optional, Tuple

from .search_service import SearchService
from .models import TroubleshootResult, SearchError, SearchOptions


def _build_prompt(product_type: str, brand: str, model: str, issue_summary: str, advanced_details: str) -> str:
    contract = textwrap.dedent(
        """
        You are a senior device repair technician. Produce a strictly valid JSON object matching this TypeScript type:

        type TroubleshootResult = {
          productType: string;
          brand: string;
          model: string;
          issueSummary: string;
          observations: string[];        // confirmable checks
          hypothesis: string;            // concise, testable cause
          probableCauses?: string[];     // optional, ordered
          actionPlan: string[];          // safe-first, numbered steps
          escalationCriteria: string[];  // concrete stop/seek-help triggers
          warnings?: string[];           // safety/warranty/data-loss
          suggestedKeywords: string[];   // for YouTube query enrichment
        };

        Rules:
        - Output JSON only, no markdown, no prose, no code fences.
        - Keep hypothesis to 1–2 sentences.
        - Action plan must start with safe, non-destructive steps.
        - Use short, checkable observations (LED codes, messages, noises).
        - Provide concrete escalation criteria (battery swelling, thermal >95C, clicking drive, no POST, warranty issues, liquid damage, repeated shutdowns).
        - suggestedKeywords should be compact search terms to find tutorials.
        """
    ).strip()

    context = {
        "productType": product_type,
        "brand": brand,
        "model": model,
        "issueSummary": issue_summary,
        "advancedDetails": advanced_details or "",
    }

    return contract + "\n\n" + json.dumps(context)


def generate_troubleshoot_result(
    service: SearchService,
    product_type: str,
    brand: str,
    model: str,
    issue_summary: str,
    advanced_details: str,
    model_name: Optional[str] = None,
    reasoning_effort: str = "low",
) -> Tuple[TroubleshootResult, str]:
    """
    Calls the LLM to produce a TroubleshootResult JSON and validates it.
    Returns (result, raw_text).
    """
    prompt = _build_prompt(product_type, brand, model, issue_summary, advanced_details)
    options = SearchOptions(model=model_name or "gpt-4o-mini", reasoning_effort=reasoning_effort)

    raw_text = ""
    try:
        result = service.search(prompt, options)
        raw_text = result.text.strip()
    except SearchError as e:
        raise

    # Try to extract JSON from the response
    json_str = raw_text
    # If model returned fences, strip them
    if json_str.startswith("```") or json_str.startswith("```json"):
        json_str = json_str.strip("`\n ")
        if json_str.lower().startswith("json"):
            json_str = json_str[4:].strip()

    # Try parse, with fallback minimal fill
    try:
        data = json.loads(json_str)
        ts = TroubleshootResult(**data)
        return ts, raw_text
    except Exception:
        # Minimal fallback
        fallback = TroubleshootResult(
            productType=product_type,
            brand=brand,
            model=model,
            issueSummary=issue_summary,
            observations=["Record exact symptoms and any error codes/messages."],
            hypothesis="Insufficient details: gather more observations to isolate root cause.",
            probableCauses=["Configuration issue", "Driver/firmware problem", "Hardware degradation"],
            actionPlan=[
                "Reproduce the issue and note exact conditions.",
                "Collect error messages/screenshots and LED/beep codes.",
                "Check power, connections, and basic settings.",
            ],
            escalationCriteria=[
                "Battery swelling or burning smell.",
                "Repeated shutdowns or no POST.",
                "SMART failing or clicking drive.",
                "Temps > 95C sustained under light load.",
                "Liquid damage or under warranty cases.",
            ],
            warnings=["Back up data before risky operations.", "Observe ESD safety."],
            suggestedKeywords=[issue_summary, brand, model, product_type, "troubleshoot", "repair", "fix"],
        )
        return fallback, raw_text
