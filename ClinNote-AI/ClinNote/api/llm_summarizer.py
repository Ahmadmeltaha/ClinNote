"""
ClinNote — LLM Clinical Summary Generator

Uses meta-llama/Llama-3.2-3B-Instruct (HuggingFace) to generate context-aware
clinical summaries for 3 patient scenarios:

  Case 1: Existing patient, no new data → historical past-tense summary
  Case 2: Existing patient + new data   → change-focused summary (old → new risk)
  Case 3: New patient                   → full clinical picture from scratch

Falls back to the template-based summary from PatientSummaryBuilder if the
LLM is unavailable or fails (no crash guaranteed).

Usage:
    from api.llm_summarizer import load_llm, generate_summary
    load_llm()   # called once at app startup
    text = generate_summary(case=1, context={...})
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_pipe = None      # tokenizer + model tuple: (_tokenizer, _model), loaded once at startup


def load_llm(hf_token: Optional[str] = None) -> bool:
    """
    Load Phi-3.5-mini-instruct from HuggingFace using model+tokenizer directly.
    Returns True if loaded successfully, False otherwise.
    Call once at app startup.
    """
    global _pipe
    if _pipe is not None:
        return True

    token = hf_token or os.environ.get("HF_TOKEN", "")
    if not token:
        logger.warning("HF_TOKEN not set — LLM summaries will use fallback template")
        return False

    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM
        from transformers.cache_utils import DynamicCache

        # Phi-3.5 modeling code calls cache.seen_tokens which was removed in transformers 4.45+.
        # Patch it back as a property so use_cache=True (fast KV-cache inference) works correctly.
        if not hasattr(DynamicCache, "seen_tokens"):
            DynamicCache.seen_tokens = property(
                lambda self: self.get_seq_length()
            )

        model_id = "microsoft/Phi-3.5-mini-instruct"
        logger.info("Loading %s from HuggingFace ...", model_id)

        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        tokenizer = AutoTokenizer.from_pretrained(
            model_id, token=token, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            token=token,
            torch_dtype=dtype,
            device_map="auto",
            trust_remote_code=True,
            attn_implementation="eager",
        )
        model.eval()
        _pipe = (tokenizer, model)
        logger.info("LLM loaded successfully")
        return True

    except Exception as e:
        logger.warning("Failed to load LLM (%s) — using template fallback", e)
        _pipe = None
        return False


def generate_summary(case: int, context: dict) -> str:
    """
    Generate a clinical summary using the LLM.

    Parameters
    ----------
    case : int
        1 = existing patient, no new data (historical)
        2 = existing patient + new data (change-focused)
        3 = new patient (first assessment)
    context : dict
        Keys vary by case — see _build_prompt() for expected keys.

    Returns
    -------
    str
        3-sentence clinical summary. Falls back to template if LLM unavailable.
    """
    if _pipe is None:
        return _template_fallback(context)

    try:
        import torch
        tokenizer, model = _pipe
        messages = _build_prompt(case, context)

        # Apply chat template to get the formatted prompt string
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=220,
                do_sample=False,
                repetition_penalty=1.1,
                pad_token_id=tokenizer.eos_token_id,
                use_cache=True,
            )

        # Decode only the newly generated tokens (skip the prompt)
        new_tokens = output_ids[0][inputs["input_ids"].shape[1]:]
        text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
        logger.info("LLM summary (first 200): %s", text[:200])
        summary = _trim_to_sentences(text, 12)
        return summary.strip()

    except Exception as e:
        logger.warning("LLM generation failed (%s) — using template fallback", e)
        return _template_fallback(context)


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _build_prompt(case: int, ctx: dict) -> str:
    if case == 1:
        return _prompt_case1(ctx)
    elif case == 2:
        return _prompt_case2(ctx)
    else:
        return _prompt_case3(ctx)


def _make_messages(system: str, user: str) -> list[dict]:
    return [
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ]

_SYSTEM = (
    "You are a clinical decision support AI writing brief narrative summaries for attending physicians. "
    "The physician already sees the detailed tables of labs, vitals, and alerts. "
    "Your job is to synthesize the data into a concise clinical story — not repeat numbers. "
    "Focus on: what is the overall clinical picture, what are the most concerning findings, "
    "what organ systems are affected, and what is the risk level. "
    "Write 3 to 4 sentences maximum. Be direct and clinically useful."
)


def _prompt_case1(ctx: dict) -> list[dict]:
    age = ctx.get("age", "unknown")
    gender = ctx.get("gender", "unknown")
    prob = ctx.get("probability", 0.0)
    risk = ctx.get("risk_level", "UNKNOWN")
    labs = ctx.get("lab_summary", "none")
    vitals = ctx.get("vital_summary", "none")
    note = ctx.get("note_excerpt", "")
    user = (
        f"Summarize this patient's clinical picture in 3–4 sentences for the attending physician.\n"
        f"Do NOT list numbers or repeat the data — synthesize it into a clinical narrative.\n\n"
        f"Patient: {age}-year-old {gender}, {risk} mortality risk ({prob:.0f}%)\n"
        f"Key abnormal labs: {labs}\n"
        f"Key abnormal vitals: {vitals}\n"
        f"Note excerpt: {note[:300] if note else 'not available'}\n\n"
        f"Write a 3–4 sentence narrative: what is the overall picture, which organ systems are involved, "
        f"how serious is this patient, and what deserves immediate attention."
    )
    return _make_messages(_SYSTEM, user)


def _prompt_case2(ctx: dict) -> list[dict]:
    age = ctx.get("age", "unknown")
    gender = ctx.get("gender", "unknown")
    old_prob = ctx.get("old_probability", 0.0)
    new_prob = ctx.get("new_probability", 0.0)
    new_labs = ctx.get("new_lab_summary", "none")
    new_vitals = ctx.get("new_vital_summary", "none")
    new_note = ctx.get("new_note_excerpt", "")
    direction = "worsened" if new_prob > old_prob else "improved" if new_prob < old_prob else "unchanged"
    user = (
        f"New clinical data was just uploaded for this patient. Summarize the update in 3–4 sentences.\n"
        f"Do NOT list numbers — synthesize into a clinical narrative about what changed.\n\n"
        f"Patient: {age}-year-old {gender}\n"
        f"Mortality risk has {direction}: {old_prob:.0f}% → {new_prob:.0f}%\n"
        f"New abnormal labs: {new_labs}\n"
        f"New abnormal vitals: {new_vitals}\n"
        f"New note: {new_note[:300] if new_note else 'not available'}\n\n"
        f"Write 3–4 sentences: what changed clinically, whether the patient is improving or deteriorating, "
        f"which new findings are most concerning, and what action is most urgent."
    )
    return _make_messages(_SYSTEM, user)


def _prompt_case3(ctx: dict) -> list[dict]:
    age = ctx.get("age", "unknown")
    gender = ctx.get("gender", "unknown")
    prob = ctx.get("probability", 0.0)
    risk = ctx.get("risk_level", "UNKNOWN")
    labs = ctx.get("lab_summary", "none")
    vitals = ctx.get("vital_summary", "none")
    note = ctx.get("note_excerpt", "")
    user = (
        f"Summarize this newly admitted patient's clinical picture in 3–4 sentences for the attending physician.\n"
        f"Do NOT list numbers — synthesize into a clinical narrative.\n\n"
        f"Patient: {age}-year-old {gender}, {risk} mortality risk ({prob:.0f}%)\n"
        f"Key abnormal labs: {labs}\n"
        f"Key abnormal vitals: {vitals}\n"
        f"Note excerpt: {note[:300] if note else 'not available'}\n\n"
        f"Write 3–4 sentences: what is the overall clinical picture on admission, which organ systems are affected, "
        f"how urgent is this patient, and what requires immediate clinical attention."
    )
    return _make_messages(_SYSTEM, user)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_response(generated, max_sentences: int = 12) -> str:
    """Extract the assistant reply from pipeline output."""
    if isinstance(generated, list):
        for msg in reversed(generated):
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                text = msg.get("content", "").strip()
                return _trim_to_sentences(text, max_sentences)
        text = " ".join(m.get("content", "") for m in generated if isinstance(m, dict))
        return _trim_to_sentences(text, max_sentences)

    text = str(generated).strip()
    return _trim_to_sentences(text, max_sentences)


def _trim_to_sentences(text: str, n: int) -> str:
    sentences = []
    for part in text.replace("\n", " ").split("."):
        part = part.strip()
        if part:
            sentences.append(part + ".")
        if len(sentences) >= n:
            break
    return " ".join(sentences) if sentences else text[:1200]


def _template_fallback(ctx: dict) -> str:
    """Template summary used when LLM is unavailable."""
    age = ctx.get("age", "unknown")
    gender = ctx.get("gender", "unknown")
    prob = ctx.get("probability") or ctx.get("new_probability", 0.0)
    risk = ctx.get("risk_level", "UNKNOWN")
    labs = ctx.get("lab_summary") or ctx.get("new_lab_summary", "none")
    vitals = ctx.get("vital_summary") or ctx.get("new_vital_summary", "none")

    risk_sentence = (
        f"This {age}-year-old {gender} patient carries a {risk.lower()} in-hospital mortality risk."
    )
    lab_sentence = (
        f"Laboratory findings are notable for {labs}." if labs and labs != "none"
        else "No significant laboratory abnormalities were identified."
    )
    vital_sentence = (
        f"Vital sign monitoring reveals {vitals}." if vitals and vitals != "none"
        else "Vital signs are within acceptable limits."
    )
    return f"{risk_sentence} {lab_sentence} {vital_sentence} Please review the detailed panels below for full assessment."


def build_summary_context(case: int, summary: dict,
                           old_summary: Optional[dict] = None) -> dict:
    """
    Build the context dict to pass to generate_summary() from a pipeline summary dict.

    Parameters
    ----------
    case : int
    summary : dict  — current/new dashboard summary dict
    old_summary : dict | None  — previous summary dict (Case 2 only)
    """
    prob = summary.get("predicted_mortality", {}).get("probability", 0.0)
    risk = summary.get("predicted_mortality", {}).get("risk_level", "UNKNOWN")
    age = summary.get("demographics", {}).get("age", "unknown")
    gender = summary.get("demographics", {}).get("gender", "unknown")

    # Build concise lab summary — unique names + direction only, no raw numbers
    top_labs = summary.get("lab_summary", {}).get("top_abnormal", [])
    if top_labs:
        seen = set()
        high, low = [], []
        for l in top_labs:
            name = l.get("label") or l.get("name", "?")
            if name in seen:
                continue
            seen.add(name)
            if l.get("direction") == "HIGH":
                high.append(name)
            else:
                low.append(name)
        parts = []
        if high:
            parts.append(f"elevated: {', '.join(high[:5])}")
        if low:
            parts.append(f"low: {', '.join(low[:5])}")
        lab_str = "; ".join(parts) if parts else "none"
    else:
        lab_str = "none"

    # Build concise vitals summary — names + status + trend only
    vital_alerts = summary.get("vital_summary", {}).get("alerts", [])
    if vital_alerts:
        vital_parts = []
        for v in vital_alerts:
            name   = v.get("vital_name", "?").replace("_", " ")
            status = v.get("status", "")
            trend  = v.get("trend", "STABLE")
            trend_str = f" and {trend.lower()}" if trend != "STABLE" else ""
            vital_parts.append(f"{name} {status.lower()}{trend_str}")
        vital_str = ", ".join(vital_parts)
    else:
        vital_str = "none"

    # Note excerpt — stored in JSON as note_excerpt (permanent) or _note_text (runtime only)
    note_text = summary.get("note_excerpt") or summary.get("_note_text", "")

    if case == 2 and old_summary:
        old_prob = old_summary.get("predicted_mortality", {}).get("probability", 0.0)
        return {
            "age": age, "gender": gender,
            "old_probability": old_prob * 100,
            "new_probability": prob * 100,
            "new_lab_summary": lab_str,
            "new_vital_summary": vital_str,
            "new_note_excerpt": note_text,
        }

    return {
        "age": age, "gender": gender,
        "probability": prob * 100,
        "risk_level": risk,
        "lab_summary": lab_str,
        "vital_summary": vital_str,
        "note_excerpt": note_text,
    }
