# -*- coding: utf-8 -*-
"""
LocalBiz AI – Social Media Post Generator
Flask backend with Ollama integration.
"""

import os
import json
import time
import logging
import requests
from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import io
from werkzeug.utils import secure_filename

# ---------------------------------------------------------------------------
# App configuration
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "localbiz-ai-secret-2024")

# Ollama configuration – change OLLAMA_MODEL to any model you have pulled
OLLAMA_HOST  = os.environ.get("OLLAMA_HOST",  "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "120"))
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "caption": {"type": "string"},
        "short_description": {"type": "string"},
        "hashtags": {"type": "string"},
        "call_to_action": {"type": "string"},
        "whatsapp_message": {"type": "string"},
    },
    "required": [
        "caption",
        "short_description",
        "hashtags",
        "call_to_action",
        "whatsapp_message",
    ],
    "additionalProperties": False,
}

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def build_prompt(data: dict) -> str:
    business_name   = _get_text(data, "business_name")
    product_name    = _get_text(data, "product_name")
    description     = _get_text(data, "description")
    price           = _get_text(data, "price")
    target_audience = _get_text(data, "target_audience")
    platform        = _get_text(data, "platform", "Instagram")
    language        = _get_text(data, "language", "English")
    tone            = _get_text(data, "tone", "Professional")
    cta             = _get_text(data, "cta")

    price_line = f"Price: {price}" if price else "Price: Not specified"
    cta_line   = (f"Call to action preferred by the owner: {cta}"
                  if cta else "Call to action: Generate a suitable one.")

    lang_instruction = {
        "Hindi":    "Write EVERYTHING in Hindi (Devanagari script). Only JSON keys in English.",
        "Hinglish": "Write EVERYTHING in Hinglish (mix of Hindi and English). Only JSON keys in English.",
        "English":  "Write everything in clear, natural English.",
    }.get(language, "Write everything in clear, natural English.")

    tone_desc = {
        "Professional": "formal, polished, and business-like",
        "Friendly":     "warm, conversational, and approachable",
        "Promotional":  "exciting, persuasive, and sales-focused",
    }.get(tone, "professional")

    platform_note = {
        "Instagram": "Instagram (use emojis, 2200-char limit, hashtag-friendly)",
        "Facebook":  "Facebook (slightly longer, story-driven, community focus)",
        "WhatsApp":  "WhatsApp (concise, personal, short paragraphs)",
    }.get(platform, platform)

    prompt = f"""You are an expert social media copywriter for small businesses in India.
A business owner has given you the following information. Create compelling promotional content for their {platform_note} page.

--- BUSINESS DETAILS ---
Business Name   : {business_name}
Product/Service : {product_name}
Description     : {description}
{price_line}
Target Audience : {target_audience}
Tone            : {tone_desc}
{cta_line}
Language        : {language}
{lang_instruction}

--- YOUR TASK ---
Return ONLY a valid JSON object (no markdown, no extra text, no code fences).
Use exactly these keys:

{{
  "caption": "<An attractive {platform} promotional caption with emojis where appropriate>",
  "short_description": "<A short 2-3 sentence product/service description>",
  "hashtags": "<10-15 relevant hashtags separated by spaces>",
  "call_to_action": "<A punchy one-liner call to action>",
  "whatsapp_message": "<A short WhatsApp promotional message under 300 characters>"
}}

Rules:
- Never add any text outside the JSON.
- Do not wrap the JSON in markdown code fences.
- All values must be non-empty strings.
- Hashtags must start with #.
- WhatsApp message must be under 300 characters.
"""
    return prompt


def _get_text(data: dict, key: str, default: str = "") -> str:
    value = data.get(key, default)
    return value.strip() if isinstance(value, str) else default


# ---------------------------------------------------------------------------
# Ollama helper
# ---------------------------------------------------------------------------

def call_ollama(prompt: str) -> dict:
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model":  OLLAMA_MODEL,
        "prompt": prompt,
        "format": RESPONSE_SCHEMA,
        "stream": False,
        "options": {
            "temperature": 0.4,
            "top_p":       0.9,
            "num_predict": 900,
        },
    }

    try:
        resp = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"Cannot connect to Ollama at {OLLAMA_HOST}. Make sure Ollama is running. Run: ollama serve"
        )
    except requests.exceptions.Timeout:
        raise TimeoutError(
            "Ollama took too long to respond. The model may still be loading. Please wait and try again."
        )
    except requests.exceptions.HTTPError as e:
        if resp.status_code == 404:
            raise ValueError(f"Model '{OLLAMA_MODEL}' not found. Run: ollama pull {OLLAMA_MODEL}")
        raise ValueError(f"Ollama returned an error: {e}")

    try:
        response_body = resp.json()
    except ValueError as e:
        raise ValueError("Ollama returned an invalid JSON response.") from e
    if not isinstance(response_body, dict):
        raise ValueError("Ollama returned an invalid response.")

    raw_response = response_body.get("response")
    if not isinstance(raw_response, str) or not raw_response.strip():
        raise ValueError("Ollama returned an empty response. Try regenerating.")
    raw_text = raw_response.strip()
    logger.info("Raw Ollama response (first 300 chars): %s", raw_text[:300])

    # Strip markdown code fences if the model added them
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw_text = "\n".join(lines).strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("{")
        end   = raw_text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                parsed = json.loads(raw_text[start:end])
            except json.JSONDecodeError:
                raise ValueError("The AI model did not return valid JSON. Try regenerating or use a different model.")
        else:
            raise ValueError("The AI model did not return valid JSON. Try regenerating or use a different model.")

    if not isinstance(parsed, dict):
        raise ValueError("The AI model response must be a JSON object. Try regenerating.")

    required_keys = ["caption", "short_description", "hashtags", "call_to_action", "whatsapp_message"]
    missing = [k for k in required_keys if k not in parsed]
    if missing:
        raise ValueError(f"AI response is missing fields: {missing}. Try regenerating.")
    invalid = [k for k in required_keys if not isinstance(parsed[k], str) or not parsed[k].strip()]
    if invalid:
        raise ValueError(f"AI response has empty or invalid fields: {invalid}. Try regenerating.")

    return parsed


# ---------------------------------------------------------------------------
# Demo mode
# ---------------------------------------------------------------------------

DEMO_RESPONSES = {
    "English": {
        "caption": "✨ Introducing {product_name} by {business_name}! 🚀\n\n{description}\n\nPerfect for {target_audience}. Don't miss out on this incredible opportunity! 💯\n\n#SmallBusiness #LocalBusiness #NewProduct",
        "short_description": "{product_name} by {business_name} is designed specifically for {target_audience}. {description} Experience quality you can trust at an unbeatable price.",
        "hashtags": "#SmallBusiness #LocalBusiness #SupportLocal #NewLaunch #MadeInIndia #ShopLocal #BestDeals #QualityFirst #CustomerFirst #IndianBusiness #ShopNow #Trending",
        "call_to_action": "Order now and get it delivered to your doorstep! 📦",
        "whatsapp_message": "Hi! 👋 Check out {product_name} from {business_name}. Great for {target_audience}. Contact us to order today! 🛒",
    },
    "Hindi": {
        "caption": "✨ {business_name} की तरफ से लाइए {product_name}! 🚀\n\n{description}\n\n{target_audience} के लिए एकदम सही! अभी ऑर्डर करें! 💯",
        "short_description": "{business_name} का {product_name} {target_audience} के लिए खास बनाया गया है। {description} उत्कृष्ट गुणवत्ता का अनुभव करें।",
        "hashtags": "#लोकलबिज़नेस #भारतीयव्यापार #नयाउत्पाद #मेडइनइंडिया #सपोर्टलोकल #शॉपलोकल #बेस्टडील #गुणवत्ता #ग्राहकसेवा #भारत #शॉपनाउ",
        "call_to_action": "अभी ऑर्डर करें और घर पर पाएं! 📦",
        "whatsapp_message": "नमस्ते! 👋 {business_name} से {product_name} देखें। {target_audience} के लिए बढ़िया। आज ही ऑर्डर करें! 🛒",
    },
    "Hinglish": {
        "caption": "✨ {business_name} ka {product_name} aa gaya! 🚀\n\n{description}\n\n{target_audience} ke liye bilkul perfect! Abhi order karo! 💯",
        "short_description": "{business_name} ka {product_name} {target_audience} ke liye specially banaya gaya hai. {description} Ekdum zabardast quality!",
        "hashtags": "#LocalBusiness #DesiStyle #NewLaunch #MadeInIndia #SupportLocal #BestDeal #ZabardastOffer #Desi #IndianBrand #ShopNow #Trending #MustBuy",
        "call_to_action": "Abhi order karo aur ghar pe pao! 📦",
        "whatsapp_message": "Arre yaar! 👋 {business_name} ka {product_name} dekho. {target_audience} ke liye best hai. Aaj hi order karo! 🛒",
    },
}


def get_demo_response(data: dict) -> dict:
    language = _get_text(data, "language", "English")
    template = DEMO_RESPONSES.get(language, DEMO_RESPONSES["English"])
    fmt = {
        "business_name":   _get_text(data, "business_name", "Your Business"),
        "product_name":    _get_text(data, "product_name", "Our Product"),
        "description":     _get_text(data, "description", "Amazing product for you"),
        "target_audience": _get_text(data, "target_audience", "everyone"),
    }
    return {key: val.format(**fmt) for key, val in template.items()}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html", model=OLLAMA_MODEL, ollama_host=OLLAMA_HOST)


@app.route("/health")
def health():
    try:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        resp.raise_for_status()
        body = resp.json()
        if not isinstance(body, dict):
            raise ValueError("Ollama returned an invalid tags response.")
        model_entries = body.get("models", [])
        if not isinstance(model_entries, list):
            raise ValueError("Ollama returned an invalid models list.")
        models = [
            model["name"] for model in model_entries
            if isinstance(model, dict) and isinstance(model.get("name"), str)
        ]
        model_ready = any(
            name == OLLAMA_MODEL
            or (":" not in OLLAMA_MODEL and name.startswith(f"{OLLAMA_MODEL}:"))
            for name in models
        )
        return jsonify({
            "ollama_running":   True,
            "model_available":  model_ready,
            "model_name":       OLLAMA_MODEL,
            "available_models": models,
        })
    except (requests.exceptions.RequestException, ValueError) as e:
        logger.warning("Ollama health check failed: %s", e)
        return jsonify({
            "ollama_running":   False,
            "model_available":  False,
            "model_name":       OLLAMA_MODEL,
            "available_models": [],
        })


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"success": False, "error": "Request body must be a JSON object."}), 400
    demo_mode = data.get("demo_mode") is True

    # Input validation
    errors = {}
    required_fields = {
        "business_name": "Business name is required.",
        "product_name": "Product / service name is required.",
        "description": "Product description is required.",
        "target_audience": "Target audience is required.",
    }
    for field, message in required_fields.items():
        if not _get_text(data, field):
            errors[field] = message

    if errors:
        return jsonify({"success": False, "errors": errors}), 422

    if demo_mode:
        logger.info("Demo mode request.")
        result = get_demo_response(data)
        return jsonify({"success": True, "result": result, "demo": True})

    prompt = build_prompt(data)
    logger.info("Sending prompt to Ollama model: %s", OLLAMA_MODEL)
    start = time.time()

    try:
        result  = call_ollama(prompt)
        elapsed = round(time.time() - start, 2)
        logger.info("Generation complete in %ss", elapsed)
        return jsonify({"success": True, "result": result, "elapsed": elapsed, "demo": False})

    except ConnectionError as e:
        return jsonify({
            "success": False, "error": str(e), "error_type": "connection",
            "setup_steps": [
                "1. Download Ollama from https://ollama.com/download",
                f"2. Run: ollama pull {OLLAMA_MODEL}",
                "3. Start Ollama: ollama serve",
                "4. Refresh this page and try again",
            ],
        }), 503

    except TimeoutError as e:
        return jsonify({"success": False, "error": str(e), "error_type": "timeout"}), 504

    except ValueError as e:
        return jsonify({"success": False, "error": str(e), "error_type": "model_error"}), 500

    except Exception as e:
        logger.exception("Unexpected error")
        return jsonify({"success": False, "error": f"Unexpected error: {e}", "error_type": "unknown"}), 500


@app.route("/download", methods=["POST"])
def download():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400
    result = data.get("result", {})
    meta   = data.get("meta", {})
    if not isinstance(result, dict) or not isinstance(meta, dict):
        return jsonify({"error": "Result and metadata must be JSON objects."}), 400

    lines = [
        "=" * 60,
        "  LocalBiz AI – Social Media Post Generator",
        "=" * 60,
        f"Generated On : {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
        f"Business     : {_get_text(meta, 'business_name')}",
        f"Product      : {_get_text(meta, 'product_name')}",
        f"Platform     : {_get_text(meta, 'platform')}",
        f"Language     : {_get_text(meta, 'language')}",
        f"Tone         : {_get_text(meta, 'tone')}",
        "",
        "─" * 60,
        "CAPTION",
        "─" * 60,
        _get_text(result, "caption"),
        "",
        "─" * 60,
        "SHORT DESCRIPTION",
        "─" * 60,
        _get_text(result, "short_description"),
        "",
        "─" * 60,
        "HASHTAGS",
        "─" * 60,
        _get_text(result, "hashtags"),
        "",
        "─" * 60,
        "CALL TO ACTION",
        "─" * 60,
        _get_text(result, "call_to_action"),
        "",
        "─" * 60,
        "WHATSAPP MESSAGE",
        "─" * 60,
        _get_text(result, "whatsapp_message"),
        "",
        "=" * 60,
        "  Generated by LocalBiz AI",
        "  https://github.com/your-username/LocalBiz-AI",
        "=" * 60,
    ]

    content  = "\n".join(lines)
    buf      = io.BytesIO(content.encode("utf-8"))
    business_name = _get_text(meta, "business_name", "post")
    business_slug = secure_filename(business_name) or "post"
    filename = f"localbiz_ai_{business_slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    return send_file(buf, as_attachment=True, download_name=filename,
                     mimetype="text/plain; charset=utf-8")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys, io
    # Ensure stdout is UTF-8 on Windows so the banner prints correctly
    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print("\n" + "=" * 55)
    print("  [*]  LocalBiz AI - Social Media Post Generator")
    print("=" * 55)
    print(f"  Ollama Host  : {OLLAMA_HOST}")
    print(f"  Model        : {OLLAMA_MODEL}")
    print(f"  App URL      : http://127.0.0.1:5000")
    print("  Demo Mode    : Available (no Ollama needed)")
    print("=" * 55 + "\n")
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
