import json
import textwrap
from typing import Optional, Tuple

from .search_service import SearchService
from .models import TroubleshootResult, SearchError, SearchOptions


def _build_prompt(product_type: str, brand: str, model: str, issue_summary: str, advanced_details: str) -> str:
    contract = textwrap.dedent(
        """
        You are a senior device repair technician with extensive experience. 
        
        IMPORTANT: Carefully analyze ALL the information provided below. Take your time to:
        1. Read and understand the product type, brand, model
        2. Thoroughly analyze the issue summary and all advanced details
        3. Consider the specific device characteristics and common failure modes
        4. Research known issues for this specific device model if applicable
        5. Generate a comprehensive, device-specific troubleshooting plan
        
        Produce a strictly valid JSON object matching this TypeScript type:

        type TroubleshootResult = {
          productType: string;
          brand: string;
          model: string;
          issueSummary: string;
          observations: string[];        // detailed, confirmable checks specific to THIS device
          hypothesis: string;            // detailed, testable cause based on the PROVIDED information
          probableCauses?: string[];     // ordered by likelihood based on the symptoms described
          actionPlan: string[];          // comprehensive, safe-first, numbered steps tailored to THIS issue
          escalationCriteria: string[];  // concrete stop/seek-help triggers relevant to this specific problem
          warnings?: string[];           // safety/warranty/data-loss warnings relevant to this device/issue
          suggestedKeywords: string[];   // specific search terms for THIS device and issue
        };

        Rules:
        - Output JSON only, no markdown, no prose, no code fences.
        - ANALYZE the provided details carefully - don't give generic advice
        - Observations should reference the ACTUAL symptoms and details provided
        - Hypothesis should explain the SPECIFIC issue described, not generic problems
        - Action plan should be tailored to the EXACT device and problem described
        - Include device-specific commands, settings, or procedures when applicable
        - Escalation criteria should be specific to the described symptoms
        - suggestedKeywords should include the ACTUAL brand, model, and specific issue terms
        """
    ).strip()

    context = {
        "productType": product_type,
        "brand": brand,
        "model": model,
        "issueSummary": issue_summary,
        "advancedDetails": advanced_details or "",
    }

    return contract + "\n\nUser Input to Analyze:\n" + json.dumps(context, indent=2)


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
