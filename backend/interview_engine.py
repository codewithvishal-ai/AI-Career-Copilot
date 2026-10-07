import os
import json
import uuid
import re
import base64
import threading
import time
from datetime import datetime
from urllib.request import Request as URLRequest, urlopen
from urllib.error import HTTPError, URLError

from flask import request, jsonify
from mongo_store import load_record, load_records, save_record

try:
    from google import genai
except ImportError:
    genai = None

# ============================================================
# CONFIG
# ============================================================


def _env_int(name, default, minimum=None, maximum=None):
    try:
        value = int(os.getenv(name, str(default)).strip())
    except (TypeError, ValueError):
        value = default

    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


INTERVIEW_SESSIONS = {}
SESSION_LOCK = threading.RLock()
QUESTION_COUNT = _env_int("INTERVIEW_QUESTION_COUNT", 8, minimum=1, maximum=20)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "").strip()
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2").strip()
ELEVENLABS_STT_MODEL_ID = os.getenv("ELEVENLABS_STT_MODEL_ID", "scribe_v2").strip()
ELEVENLABS_OUTPUT_FORMAT = os.getenv("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128").strip()

GEMINI_CLIENT = None
GEMINI_DISABLED_UNTIL = 0.0
GEMINI_DISABLE_SECONDS = _env_int("GEMINI_QUOTA_COOLDOWN_SECONDS", 900, minimum=30, maximum=86400)
ELEVENLABS_TTS_DISABLED_UNTIL = 0.0
ELEVENLABS_STT_DISABLED_UNTIL = 0.0
ELEVENLABS_DISABLE_SECONDS = _env_int("ELEVENLABS_QUOTA_COOLDOWN_SECONDS", 3600, minimum=60, maximum=86400)
if genai and GEMINI_API_KEY:
    try:
        GEMINI_CLIENT = genai.Client(api_key=GEMINI_API_KEY)
        print(f"[INTERVIEW] Gemini client initialized: {GEMINI_MODEL}")
    except Exception as error:
        print(f"[INTERVIEW] Gemini initialization failed: {error}")
else:
    if not genai:
        print("[INTERVIEW] google-genai package is not installed.")
    if not GEMINI_API_KEY:
        print("[INTERVIEW] GEMINI_API_KEY is not configured.")


def _text(value, default=""):
    if value is None:
        return default
    value = str(value).strip()
    return value if value else default


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _language_text(language, english, hindi):
    return hindi if language == "HINDI" else english


def _interview_type_label(interview_type, language="ENGLISH"):
    if language == "HINDI":
        return {
            "technical": "तकनीकी दौर",
            "project_resume": "परियोजना और रिज़्यूमे दौर",
            "hr": "एचआर साक्षात्कार",
            "mixed": "सामान्य साक्षात्कार",
        }.get(interview_type, "साक्षात्कार")
    return INTERVIEW_TYPES.get(interview_type, INTERVIEW_TYPES["mixed"])["label"]


INTERVIEW_MESSAGES = {
    "mode_set": ("Perfect. We'll use {mode} mode. Let's begin.", "ठीक है। हम {mode} मोड में आगे बढ़ेंगे। शुरू करते हैं।"),
    "ready": ("Great. Before we begin, would you like to take this interview in voice mode or chat mode?", "बहुत अच्छा। शुरू करने से पहले बताइए, आप वॉइस मोड में साक्षात्कार देना चाहेंगे या चैट मोड में?"),
    "not_ready": ("No problem. Take your time. Whenever you're ready, just say 'yes' or tell me that you're ready to begin.", "कोई बात नहीं। आराम से समय लें। तैयार होने पर बताइए, फिर हम शुरू करेंगे।"),
    "ready_check": ("Before we begin, I just need to know whether you're ready to start the interview.", "शुरू करने से पहले बस बताइए कि क्या आप साक्षात्कार शुरू करने के लिए तैयार हैं।"),
    "mode_prompt": ("Would you prefer voice mode, where you speak your answers, or chat mode, where you type them?", "आप वॉइस मोड पसंद करेंगे, जिसमें आप बोलकर उत्तर देंगे, या चैट मोड, जिसमें आप लिखकर उत्तर देंगे?"),
    "clarification": ("Of course. What I'm asking is: {question} I want to understand your own experience, reasoning or approach here.", "बिल्कुल। मेरा प्रश्न है: {question} मैं यहाँ आपका अपना अनुभव, तर्क या तरीका समझना चाहता हूँ।"),
    "explanation": ("Absolutely. {explanation} Does that make sense?", "ज़रूर। {explanation} क्या यह स्पष्ट है?"),
    "question_back": ("That's a fair question. For this part of the interview, I'd like you to answer from your own experience first. Let's return to the question: {question}", "यह उचित सवाल है। इस हिस्से में पहले मैं चाहूँगा कि आप अपने अनुभव के आधार पर उत्तर दें। आइए प्रश्न पर लौटें: {question}"),
    "off_topic": ("I understand. Let's keep this focused on the interview. Coming back to my question: {question}", "समझ गया। आइए बातचीत को साक्षात्कार पर केंद्रित रखें। मेरे प्रश्न पर लौटते हैं: {question}"),
    "yes_continue": ("Yes, let's continue. Please answer the interview question above in your own words.", "हाँ, आगे बढ़ते हैं। कृपया ऊपर दिए गए प्रश्न का उत्तर अपने शब्दों में दें।"),
    "continue": ("Hi {name}. Let's continue. {question}", "नमस्ते {name}। आगे बढ़ते हैं। {question}"),
    "retry": ("Great. Let me ask that idea again in a slightly simpler way.", "अच्छा। मैं वही बात थोड़े सरल तरीके से फिर पूछता हूँ।"),
    "explain_again": ("No problem. Let me explain it another way. {explanation} Does that make sense now?", "कोई बात नहीं। मैं इसे दूसरे तरीके से समझाता हूँ। {explanation} क्या अब यह स्पष्ट है?"),
    "explain_clearer": ("Let me make it even clearer. {explanation} Does that make sense now?", "मैं इसे और सरल करके बताता हूँ। {explanation} क्या अब यह स्पष्ट है?"),
    "dont_know": ("That's okay. Would you like me to explain the concept briefly and then let you try the question again?", "कोई बात नहीं। क्या आप चाहेंगे कि मैं अवधारणा संक्षेप में समझाऊँ और फिर आपको दोबारा उत्तर देने का मौका दूँ?"),
    "guidance_yes": ("Absolutely. {explanation} Does that make sense?", "ज़रूर। {explanation} क्या यह स्पष्ट है?"),
    "move_on": ("No problem. Let's move on.", "कोई बात नहीं। अगले प्रश्न पर चलते हैं।"),
    "guidance_prompt": ("Would you like me to explain it briefly, or would you prefer to move on?", "क्या आप चाहेंगे कि मैं इसे संक्षेप में समझाऊँ, या आप अगले प्रश्न पर जाना पसंद करेंगे?"),
    "feedback_followup": ("Thank you. Let me go a little deeper into that.", "धन्यवाद। आइए इस बात को थोड़ा और विस्तार से समझते हैं।"),
    "thanks": ("Thank you.", "धन्यवाद।"),
    "continue_next": ("Thank you. Let's continue.", "धन्यवाद। आगे बढ़ते हैं।"),
}


def _interview_message(language, key, **values):
    english, hindi = INTERVIEW_MESSAGES[key]
    template = hindi if language == "HINDI" else english
    return template.format(**values)


def _gemini_available():
    return GEMINI_CLIENT is not None and time.time() >= GEMINI_DISABLED_UNTIL


def _mark_gemini_quota_exhausted(error):
    global GEMINI_DISABLED_UNTIL
    message = str(error).lower()
    if "429" in message or "resource_exhausted" in message or "quota" in message or "rate limit" in message:
        GEMINI_DISABLED_UNTIL = time.time() + GEMINI_DISABLE_SECONDS
        print(f"[INTERVIEW] Gemini quota/rate limit detected. Adaptive mode disabled for {GEMINI_DISABLE_SECONDS}s; fallback mode is active.")
        return True
    return False


# ============================================================
# RESUME CONTEXT
# ============================================================

def _latest_resume(resume_manager, username):
    try:
        data = resume_manager.get_latest_analysis(username)
        return data if isinstance(data, dict) else {}
    except Exception as error:
        print(f"[INTERVIEW] Resume lookup error: {error}")
        return {}


def _resume_context(analysis):
    if not isinstance(analysis, dict):
        return "{}"
    allowed = {
        "name": analysis.get("name", ""),
        "email": analysis.get("email", ""),
        "skills": analysis.get("skills", []),
        "sections": analysis.get("sections", []),
        "projects": analysis.get("projects", []),
        "experience": analysis.get("experience", []),
        "education": analysis.get("education", []),
        "certifications": analysis.get("certifications", []),
        "summary": analysis.get("summary", ""),
    }
    try:
        return json.dumps(allowed, ensure_ascii=False, default=str)[:30000]
    except Exception:
        return "{}"


def _role_from_resume(analysis):
    if not isinstance(analysis, dict):
        return "Software Developer"
    text = " ".join([
        " ".join(str(x).lower() for x in analysis.get("skills", []) if x),
        str(analysis.get("summary", "")).lower(),
        json.dumps(analysis.get("experience", []), ensure_ascii=False, default=str).lower(),
    ])
    if any(x in text for x in ("machine learning", "deep learning", "computer vision", "pytorch", "tensorflow", "artificial intelligence", "generative ai", "llm")):
        return "AI / ML Engineer"
    if any(x in text for x in ("pandas", "numpy", "power bi", "tableau", "data analysis", "data science", "statistics")):
        return "Data Scientist / Data Analyst"
    if any(x in text for x in ("fastapi", "flask", "django", "rest api", "backend", "postgresql", "mysql", "mongodb")):
        return "Backend Developer"
    if any(x in text for x in ("react", "javascript", "typescript", "html", "css", "next.js", "nextjs")):
        return "Full Stack Developer"
    if any(x in text for x in ("flutter", "dart", "android", "ios", "mobile development")):
        return "Flutter / Mobile Developer"
    return "Software Developer"


# ============================================================
# GEMINI
# ============================================================

def _gemini_generate_json(prompt, schema, system_instruction, temperature=0.25):
    if not _gemini_available():
        return None
    try:
        from google.genai import types
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=schema,
            temperature=temperature,
        )
        response = GEMINI_CLIENT.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=config,
        )
        raw = (getattr(response, "text", "") or "").strip()
        raw = re.sub(r"^```json\s*", "", raw, flags=re.I)
        raw = re.sub(r"\s*```$", "", raw, flags=re.I).strip()
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else None
    except Exception as error:
        _mark_gemini_quota_exhausted(error)
        print(f"[INTERVIEW] Gemini API error: {error}")
        return None


def _fallback_language(text):
    text = _text(text).lower()
    if not text:
        return "ENGLISH"
    if re.search(r"[\u0900-\u097f]", text):
        return "HINDI"
    hindi = ("haan", "han", "nahi", "nahin", "mujhe", "mera", "meri", "mere", "aap", "kya", "kyu", "kyun", "hai", "hain", "hoon", "hu", "karna", "karta", "karti", "batao", "bataye", "samajh", "samjha", "pata", "accha", "achha", "theek", "kaise", "kyunki", "lekin", "aur")
    hits = sum(1 for x in hindi if re.search(rf"\b{re.escape(x)}\b", text))
    english = sum(1 for x in ("the", "is", "are", "because", "project", "experience", "using", "built", "developed", "role") if re.search(rf"\b{re.escape(x)}\b", text))
    if hits >= 2 and english >= 1:
        return "HINGLISH"
    if hits >= 2:
        return "HINGLISH"
    return "ENGLISH"


def _fallback_intent(text, state):
    text_l = _text(text).lower()
    lang = _fallback_language(text)
    if not text_l:
        return {"intent": "EMPTY", "language": lang, "confidence": 1.0}

    # These are conversational/setup messages, never scored as interview answers.
    if any(x in text_l for x in (
        "ask me questions", "ask questions", "you can ask me",
        "question please", "questions please", "start asking",
        "go ahead and ask", "poochho", "sawal pooch", "sawaal pooch"
    )):
        return {"intent": "QUESTION_TO_INTERVIEWER", "language": lang, "confidence": .98}

    if re.fullmatch(r"(?:yes|yeah|yep|yup|sure|okay|ok|haan|han|bilkul|yes please|go ahead)[.!\s]*", text_l):
        return {"intent": "YES", "language": lang, "confidence": .98}

    if any(x in text_l for x in ("i don't know", "i dont know", "not sure", "no idea", "can't answer", "cannot answer", "pata nahi", "mujhe nahi pata")):
        return {"intent": "DONT_KNOW", "language": lang, "confidence": .95}
    if any(x in text_l for x in ("what do you mean", "could you clarify", "please clarify", "samajh nahi", "question samjha nahi", "thoda explain", "explain the question", "what does that mean")):
        return {"intent": "CLARIFICATION", "language": lang, "confidence": .92}
    if any(x in text_l for x in ("explain", "samjha do", "samjha dein", "can you explain", "please explain")):
        return {"intent": "ASK_EXPLANATION", "language": lang, "confidence": .92}
    if any(x in text_l for x in ("no", "not really", "nahi", "nahin", "not clear")) and state in ("EXPLANATION_CHECK", "GUIDANCE_OFFER"):
        return {"intent": "NO", "language": lang, "confidence": .95}
    if any(x in text_l for x in ("voice", "audio", "speak", "bolkar", "bol ke", "by voice")) and state == "MODE_SELECT":
        return {"intent": "VOICE_MODE", "language": lang, "confidence": .95}
    if any(x in text_l for x in ("chat", "text", "type", "typing", "likh")) and state == "MODE_SELECT":
        return {"intent": "CHAT_MODE", "language": lang, "confidence": .95}
    return {"intent": "ANSWER", "language": lang, "confidence": .65}


def _classify_intent(text, session):
    schema = {
        "type": "object",
        "properties": {
            "intent": {"type": "string", "enum": ["READY", "NOT_READY", "VOICE_MODE", "CHAT_MODE", "ANSWER", "DONT_KNOW", "CLARIFICATION", "ASK_EXPLANATION", "YES", "NO", "QUESTION_TO_INTERVIEWER", "OFF_TOPIC", "GREETING", "EMPTY"]},
            "language": {"type": "string", "enum": ["ENGLISH", "HINDI", "HINGLISH"]},
            "confidence": {"type": "number"},
        },
        "required": ["intent", "language", "confidence"],
    }
    prompt = f"""
Classify the candidate's latest message in a live one-to-one interview.
State: {session.get('state')}
Current question: {json.dumps(session.get('question', {}), ensure_ascii=False)}
Candidate message: {text}

Rules:
- Understand English, Hindi, Hinglish and mixed language.
- READY/NOT_READY are only for the opening readiness check. YES by itself, "ask me questions", greetings, and setup chatter are never substantive answers to a question.
- VOICE_MODE/CHAT_MODE are only for mode selection.
- DONT_KNOW means the candidate cannot answer.
- CLARIFICATION means the candidate wants the wording/question clarified.
- ASK_EXPLANATION means they explicitly want the concept/answer explained.
- YES/NO are confirmations to the immediately previous interviewer request.
- ANSWER is any substantive answer, even if short or partially correct. A one-word confirmation such as "yes" is not an answer unless it is clearly the substantive content requested by the current question.
- QUESTION_TO_INTERVIEWER is a genuine question asked back to the interviewer.
- OFF_TOPIC means the message does not meaningfully answer or progress the interview.
- Do not call a substantive answer a greeting.
"""
    result = _gemini_generate_json(prompt, schema, "You are a precise conversational intent classifier for a professional AI interviewer.", .05)
    if isinstance(result, dict) and result.get("intent"):
        return result
    return _fallback_intent(text, session.get("state", "QUESTION"))


# ============================================================
# INTERVIEW CONTENT
# ============================================================

INTERVIEW_TYPES = {
    "technical": {
        "label": "Round 1: Technical",
        "categories": ("TECHNICAL", "SCENARIO"),
        "focus": "Assess role-relevant technical knowledge, problem solving, debugging, and engineering trade-offs. Prioritize skills verified in the resume.",
        "scoring": "Prioritize technical correctness, reasoning, trade-offs, and clear problem-solving steps.",
    },
    "project_resume": {
        "label": "Round 2: Project and Resume",
        "categories": ("PROJECT", "RESUME"),
        "focus": "Deep-dive only into projects, responsibilities, experience, education, and skills actually present in the verified resume. Probe the candidate's personal contribution and evidence; do not invent details.",
        "scoring": "Prioritize specific ownership, decisions, evidence, outcomes, and consistency with the verified resume.",
    },
    "hr": {
        "label": "HR Interview",
        "categories": ("HR", "BEHAVIORAL"),
        "focus": "Assess motivation, communication, collaboration, self-awareness, and behavioral examples. Keep questions professional and avoid sensitive personal topics.",
        "scoring": "Prioritize clear communication, reflection, professional judgment, and structured behavioral examples over technical jargon.",
    },
    "mixed": {
        "label": "General Interview",
        "categories": ("HR", "RESUME", "PROJECT", "TECHNICAL", "SCENARIO", "BEHAVIORAL", "FINAL"),
        "focus": "Run a balanced interview grounded in the candidate's verified resume.",
        "scoring": "Judge the answer against the question and the candidate's role.",
    },
}


def _localize_fallback_questions(questions, language, project_name, skill, role):
    if language != "HINDI":
        return questions

    translations = {
        "resume-skill": f"आपके रिज़्यूमे में {skill} का उल्लेख है। इसकी मूल अवधारणा क्या है और आप इसे कब चुनेंगे?",
        "debugging": "यदि कोई सुविधा स्थानीय वातावरण में सही चले लेकिन प्रोडक्शन में विफल हो, तो आप सबसे पहले क्या जाँचेंगे और क्यों?",
        "implementation": f"इस भूमिका की किसी वास्तविक समस्या को हल करने के लिए आप {skill} का उपयोग कैसे करेंगे?",
        "problem-solving": "यदि किसी धीमे API का मुख्य कारण अभी पता न हो, तो आप जाँच कहाँ से शुरू करेंगे?",
        "tradeoffs": "ऐसे तकनीकी निर्णय का उदाहरण दें जिसमें आपने दो विकल्पों की तुलना की। आपके निर्णय को किन समझौतों ने प्रभावित किया?",
        "reliability": "यदि कोई निर्भर सेवा अस्थिर हो जाए, तो आप सिस्टम को अधिक भरोसेमंद कैसे बनाएँगे?",
        "testing": "आप कैसे तय करते हैं कि किस हिस्से के लिए यूनिट टेस्ट, इंटीग्रेशन टेस्ट या मैन्युअल जाँच चाहिए?",
        "technical-communication": "किसी गैर-तकनीकी हितधारक को जटिल तकनीकी सीमा कैसे समझाएँगे?",
        "security": "नया API endpoint सार्वजनिक करने से पहले कौन-से सुरक्षा जोखिम जाँचेंगे और उन्हें कैसे घटाएँगे?",
        "data-quality": "सिस्टम में आने वाले अमान्य या अधूरे डेटा को आप कैसे पहचानेंगे और संभालेंगे?",
        "project-overview": f"आपके रिज़्यूमे में उल्लिखित {project_name} किस समस्या को हल करता था और इसके उपयोगकर्ता कौन थे?",
        "personal-contribution": "इस काम का कौन-सा हिस्सा आपने स्वयं संभाला, और मुख्य निर्णय आपने कैसे लिए?",
        "architecture": f"आपने {project_name} में रिज़्यूमे में उल्लिखित कौन-सी तकनीकें इस्तेमाल कीं और वे क्यों उपयुक्त थीं?",
        "challenge": "इस काम की सबसे कठिन बाधा क्या थी और आपने उसे कैसे दूर किया?",
        "evidence": "कौन-सा प्रमाण या परिणाम दिखाता है कि आपका योगदान सफल रहा? यदि मापा नहीं था, तो अब क्या मापेंगे?",
        "improvement": "यदि इस प्रोजेक्ट पर एक और सप्ताह मिलता, तो पहले क्या सुधारते और उसका क्या असर होता?",
        "skill-evidence": f"अपने अनुभव का एक ठोस उदाहरण दें जो {skill} में आपकी क्षमता दिखाता हो।",
        "learning": "इस प्रोजेक्ट से आपने क्या सीखा जिसने बाद में काम करने का आपका तरीका बदला?",
        "collaboration": "इस काम में और कौन शामिल था, और आपने जिम्मेदारियों या असहमति को कैसे संभाला?",
        "introduction": "अपना संक्षिप्त परिचय दें और बताएँ कि आपके अनुभव ने आपको इस भूमिका के लिए कैसे तैयार किया।",
        "motivation": f"{role} की इस भूमिका में आपकी रुचि क्यों है, और आप टीम में क्या योगदान देना चाहेंगे?",
        "teamwork": "ऐसे समय के बारे में बताएँ जब किसी सहकर्मी का काम करने का तरीका आपसे अलग था। आपने काम आगे कैसे बढ़ाया?",
        "strengths": "आपके अनुभव की कौन-सी ताकत इस टीम के लिए सबसे उपयोगी होगी? एक उदाहरण दें।",
        "feedback": "ऐसे सुझाव के बारे में बताएँ जिसे सुनना कठिन था। आपने उस पर कैसे प्रतिक्रिया दी?",
        "growth": "आप अभी किस कौशल को बेहतर बना रहे हैं और उसका अभ्यास कैसे कर रहे हैं?",
        "candidate-questions": "समाप्त करने से पहले आप टीम या भूमिका के बारे में क्या जानना चाहेंगे?",
        "priorities": "कई कामों की समय-सीमा एक साथ होने पर आपने प्राथमिकता कैसे तय की और बदलावों के बारे में कैसे बताया?",
        "work-style": "किस तरह का टीम वातावरण आपको अच्छा काम करने में मदद करता है, और आप उसमें क्या योगदान देते हैं?",
    }

    for question in questions:
        question["question"] = translations.get(
            question.get("topic"),
            question["question"],
        )

    return questions


def _fallback_questions(session_or_analysis, role="Software Developer", interview_type="mixed", language="ENGLISH"):
    analysis = session_or_analysis if isinstance(session_or_analysis, dict) else {}
    projects = analysis.get("projects") or []
    skills = analysis.get("skills") or []
    project_name = "your main project"
    if projects:
        first = projects[0]
        if isinstance(first, dict):
            project_name = _text(first.get("name") or first.get("title"), project_name)
        else:
            project_name = _text(first, project_name)
    skill = _text(skills[0] if skills else "a technology you know", "a technology you know")

    if interview_type == "technical":
        return _localize_fallback_questions([
            {"category": "TECHNICAL", "difficulty": "Easy", "topic": "resume-skill", "question": f"Your resume lists {skill}. Explain its core idea and when you would choose it."},
            {"category": "SCENARIO", "difficulty": "Medium", "topic": "debugging", "question": "A feature passes locally but fails in production. What would you check first, and why?"},
            {"category": "TECHNICAL", "difficulty": "Medium", "topic": "implementation", "question": f"Describe how you would use {skill} to solve a realistic problem in this role."},
            {"category": "SCENARIO", "difficulty": "Medium", "topic": "problem-solving", "question": "How would you investigate a slow API endpoint when you do not yet know the bottleneck?"},
            {"category": "TECHNICAL", "difficulty": "Hard", "topic": "tradeoffs", "question": "Describe a technical decision where you compared two approaches. What trade-offs guided your choice?"},
            {"category": "SCENARIO", "difficulty": "Hard", "topic": "reliability", "question": "How would you make a service more resilient when one of its dependencies becomes unreliable?"},
            {"category": "TECHNICAL", "difficulty": "Medium", "topic": "testing", "question": "How do you decide what to unit test, integration test, and verify manually?"},
            {"category": "SCENARIO", "difficulty": "Medium", "topic": "technical-communication", "question": "How would you explain a complex technical limitation to a non-technical stakeholder?"},
            {"category": "TECHNICAL", "difficulty": "Hard", "topic": "security", "question": "What security risks would you review before exposing a new API endpoint, and how would you reduce them?"},
            {"category": "SCENARIO", "difficulty": "Medium", "topic": "data-quality", "question": "How would you detect and handle invalid or incomplete data entering a system?"},
        ], language, project_name, skill, role)

    if interview_type == "project_resume":
        return _localize_fallback_questions([
            {"category": "PROJECT", "difficulty": "Easy", "topic": "project-overview", "question": f"Your resume mentions {project_name}. What problem did it address, and who was it for?"},
            {"category": "RESUME", "difficulty": "Medium", "topic": "personal-contribution", "question": "Which part of that work did you personally own, and how did you make the key decisions?"},
            {"category": "PROJECT", "difficulty": "Medium", "topic": "architecture", "question": f"Which technologies from your resume did you use in {project_name}, and why were they suitable?"},
            {"category": "PROJECT", "difficulty": "Medium", "topic": "challenge", "question": "What was the most difficult obstacle in this work, and how did you resolve it?"},
            {"category": "RESUME", "difficulty": "Hard", "topic": "evidence", "question": "What evidence or result best shows that your contribution worked? If you did not measure it, what would you measure now?"},
            {"category": "PROJECT", "difficulty": "Hard", "topic": "improvement", "question": "If you had another week on this project, what would you improve first and what would that change?"},
            {"category": "RESUME", "difficulty": "Medium", "topic": "skill-evidence", "question": f"Give a specific example from your experience that demonstrates your {skill} skill."},
            {"category": "PROJECT", "difficulty": "Medium", "topic": "learning", "question": "What did this project teach you that changed how you approach later work?"},
            {"category": "RESUME", "difficulty": "Medium", "topic": "collaboration", "question": "Who else contributed to this work, and how did you coordinate responsibilities or resolve disagreements?"},
            {"category": "PROJECT", "difficulty": "Hard", "topic": "reliability", "question": "What could fail after launch, and how would you monitor or support this project in production?"},
        ], language, project_name, skill, role)

    if interview_type == "hr":
        return _localize_fallback_questions([
            {"category": "HR", "difficulty": "Easy", "topic": "introduction", "question": "Could you introduce yourself and summarize the experiences that have prepared you for this role?"},
            {"category": "HR", "difficulty": "Medium", "topic": "motivation", "question": f"What interests you about this {role} role, and what would you hope to contribute?"},
            {"category": "BEHAVIORAL", "difficulty": "Medium", "topic": "teamwork", "question": "Tell me about a time you worked with someone who had a different approach. How did you move the work forward?"},
            {"category": "BEHAVIORAL", "difficulty": "Medium", "topic": "challenge", "question": "Describe a professional setback or mistake. What did you learn and change afterward?"},
            {"category": "HR", "difficulty": "Medium", "topic": "strengths", "question": "Which strength from your experience would be most useful to this team? Please give an example."},
            {"category": "BEHAVIORAL", "difficulty": "Hard", "topic": "feedback", "question": "Tell me about feedback that was difficult to hear. How did you respond?"},
            {"category": "HR", "difficulty": "Medium", "topic": "growth", "question": "What skill are you currently working to improve, and how are you practicing it?"},
            {"category": "HR", "difficulty": "Easy", "topic": "candidate-questions", "question": "What would you like to know about the team or the role before we finish?"},
            {"category": "BEHAVIORAL", "difficulty": "Medium", "topic": "priorities", "question": "Tell me about a time you had competing deadlines. How did you prioritize and communicate the trade-offs?"},
            {"category": "HR", "difficulty": "Medium", "topic": "work-style", "question": "What kind of team environment helps you do your best work, and how do you contribute to it?"},
        ], language, project_name, skill, role)

    return [
        {"category":"HR","difficulty":"Easy","topic":"introduction","question":"Could you briefly walk me through your background and what has prepared you for this role?"},
        {"category":"RESUME","difficulty":"Easy","topic":"resume","question":f"Looking at your resume, which project or experience best represents your current technical ability, and why?"},
        {"category":"PROJECT","difficulty":"Medium","topic":"project-deep-dive","question":f"Tell me about {project_name}. What problem were you solving, and what was your personal contribution?"},
        {"category":"TECHNICAL","difficulty":"Medium","topic":"technical-foundation","question":f"How would you explain {skill} to someone who understands programming but has never used it?"},
        {"category":"SCENARIO","difficulty":"Medium","topic":"debugging","question":"Suppose a feature works locally but fails in production. How would you investigate the problem step by step?"},
        {"category":"BEHAVIORAL","difficulty":"Medium","topic":"challenge","question":"Tell me about a technical challenge or mistake you faced. What did you do, and what did you learn from it?"},
        {"category":"TECHNICAL","difficulty":"Hard","topic":"tradeoffs","question":"Describe a technical decision where you had to choose between two approaches. What trade-offs did you consider?"},
        {"category":"FINAL","difficulty":"Medium","topic":"closing","question":"If you joined this role, what technical area would you want to improve first, and how would you approach it?"},
    ]


def _first_question(analysis, role, language="ENGLISH", interview_type="mixed"):
    interview = INTERVIEW_TYPES.get(interview_type, INTERVIEW_TYPES["mixed"])
    schema = {
        "type": "object",
        "properties": {
            "category": {"type": "string", "enum": ["HR", "RESUME", "PROJECT", "TECHNICAL", "SCENARIO", "BEHAVIORAL"]},
            "difficulty": {"type": "string", "enum": ["Easy", "Medium", "Hard"]},
            "question": {"type": "string"},
            "topic": {"type": "string"},
        },
        "required": ["category", "difficulty", "question", "topic"],
    }
    prompt = f"""
Start a realistic one-to-one interview for the target role: {role}.
Interview track: {interview['label']}.
Track focus: {interview['focus']}
Candidate language: {language}.
Verified resume:
{_resume_context(analysis)}

Ask exactly one natural opening interview question. It must fit the selected track and use only verified resume facts. Do not invent facts. Do not add feedback.
"""
    result = _gemini_generate_json(prompt, schema, "You are an experienced human interviewer beginning a real interview.", .35)
    if isinstance(result, dict) and result.get("question") and result.get("category") in interview["categories"]:
        return result
    return _fallback_questions(analysis, role, interview_type, language)[0]


def _next_question(session, last_answer="", evaluation=None):
    analysis = session["analysis"]
    history = session.get("history", [])
    language = session.get("preferred_language", "ENGLISH")
    interview_type = session.get("interview_type", "mixed")
    interview = INTERVIEW_TYPES.get(interview_type, INTERVIEW_TYPES["mixed"])
    recent = []
    for item in history[-10:]:
        recent.append({
            "question": item.get("question", {}).get("question", ""),
            "category": item.get("question", {}).get("category", ""),
            "answer": item.get("answer", ""),
            "score": item.get("evaluation", {}).get("score", 0),
            "attempt": item.get("attempt", 1),
        })
    schema = {
        "type": "object",
        "properties": {
            "category": {"type": "string", "enum": ["HR", "RESUME", "PROJECT", "TECHNICAL", "SCENARIO", "BEHAVIORAL", "FINAL"]},
            "difficulty": {"type": "string", "enum": ["Easy", "Medium", "Hard"]},
            "question": {"type": "string"},
            "topic": {"type": "string"},
        },
        "required": ["category", "difficulty", "question", "topic"],
    }
    prompt = f"""
You are continuing a real one-to-one interview.
Target role: {session['role']}
Interview track: {interview['label']}.
Track focus: {interview['focus']}
Main question number: {session['question_index'] + 1} of {session['question_count']}
Candidate language: {language}

VERIFIED RESUME:
{_resume_context(analysis)}

PREVIOUS QUESTION:
{json.dumps(session.get('question', {}), ensure_ascii=False)}

CANDIDATE'S LATEST ANSWER:
{last_answer}

LATEST EVALUATION:
{json.dumps(evaluation or {}, ensure_ascii=False)}

RECENT INTERVIEW MEMORY:
{json.dumps(recent, ensure_ascii=False, default=str)}

Interview rules:
1. Behave like a human interviewer, not a question bank.
2. React to the candidate's actual latest answer. If they named a technology, project, decision, challenge, result or claim, probe it naturally when useful.
3. Use verified resume facts only. Never invent a company, project, skill, metric or responsibility.
4. Do not repeat a previous question or ask the same thing with superficial wording.
5. Keep every question within the selected track categories: {", ".join(interview['categories'])}.
6. If the candidate is strong, increase depth/difficulty naturally.
7. Keep the question concise and speakable, normally under 45 words.
8. Ask exactly one question. No feedback, no explanation.
"""
    result = _gemini_generate_json(prompt, schema, "You are an elite human interviewer with strong conversational memory and resume grounding.", .35)
    if isinstance(result, dict) and result.get("question") and result.get("category") in interview["categories"]:
        result["question"] = _text(result["question"])[:800]
        return result
    questions = _fallback_questions(
        session["analysis"],
        session["role"],
        interview_type,
        language,
    )
    idx = min(max(_safe_int(session.get("question_index"), 0), 0), len(questions) - 1)
    return questions[idx]


def _rephrase_question(session, question, language):
    schema = {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]}
    prompt = f"""
Rephrase this interview question so the candidate can try the SAME underlying competency again.
Role: {session['role']}
Interview track: {INTERVIEW_TYPES.get(session.get('interview_type'), INTERVIEW_TYPES['mixed'])['label']}
Language: {language}
Original question: {json.dumps(question, ensure_ascii=False)}
Resume: {_resume_context(session['analysis'])}

Keep the same subject and difficulty, but make the wording clearer and slightly easier to understand. Ask one question only. Do not answer it and do not introduce a new topic.
"""
    result = _gemini_generate_json(prompt, schema, "You are a supportive but realistic interviewer. Rephrase without changing the competency.", .25)
    if isinstance(result, dict) and result.get("question"):
        return _text(result["question"])[:800]
    return _text(question.get("question"), "Could you explain the same idea in your own words?")


def _explain_question(session, question, language, candidate_request=""):
    schema = {"type": "object", "properties": {"explanation": {"type": "string"}}, "required": ["explanation"]}
    prompt = f"""
Explain the current interview question to the candidate because they asked for help.
Role: {session['role']}
Language: {language}
Question: {json.dumps(question, ensure_ascii=False)}
Candidate request: {candidate_request}
Resume: {_resume_context(session['analysis'])}

Explain what the interviewer is trying to assess, what the key concept means, and how a strong answer could be structured. Do not falsely claim the candidate did something. Keep it concise and conversational. Technical terms may remain in English.
"""
    result = _gemini_generate_json(prompt, schema, "You are a patient interview coach. Teach without sounding like a lecture.", .3)
    return _text(result.get("explanation") if isinstance(result, dict) else "") or "Let me simplify what I am looking for. I want you to explain the main idea, your reasoning, and, if possible, connect it to something you have actually worked on."


def _evaluate_answer(session, answer):
    question = session.get("question", {})
    language = session.get("preferred_language", "ENGLISH")
    interview = INTERVIEW_TYPES.get(session.get("interview_type"), INTERVIEW_TYPES["mixed"])
    recent = [{"question": x.get("question", {}).get("question", ""), "answer": x.get("answer", ""), "score": x.get("evaluation", {}).get("score", 0)} for x in session.get("history", [])[-6:]]
    schema = {
        "type": "object",
        "properties": {
            "score": {"type": "integer", "minimum": 0, "maximum": 100},
            "label": {"type": "string", "enum": ["STRONG", "GOOD", "PARTIAL", "WEAK", "INCORRECT"]},
            "feedback": {"type": "string"},
            "strengths": {"type": "array", "items": {"type": "string"}},
            "improvements": {"type": "array", "items": {"type": "string"}},
            "missing_points": {"type": "array", "items": {"type": "string"}},
            "technical_accuracy": {"type": "integer", "minimum": 0, "maximum": 100},
            "clarity": {"type": "integer", "minimum": 0, "maximum": 100},
            "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
            "relevance": {"type": "integer", "minimum": 0, "maximum": 100},
            "should_follow_up": {"type": "boolean"},
            "follow_up_question": {"type": "string"},
            "follow_up_reason": {"type": "string"},
        },
        "required": ["score", "label", "feedback", "strengths", "improvements", "missing_points", "technical_accuracy", "clarity", "confidence", "relevance", "should_follow_up", "follow_up_question", "follow_up_reason"],
    }
    prompt = f"""
Evaluate the candidate's actual answer as a human interviewer.
Role: {session['role']}
Interview track: {interview['label']}
Scoring focus: {interview['scoring']}
Language: {language}
Current question: {json.dumps(question, ensure_ascii=False)}
Candidate answer: {answer}
Resume: {_resume_context(session['analysis'])}
Recent context: {json.dumps(recent, ensure_ascii=False, default=str)}

Rules:
- Judge this exact answer against this exact question.
- A concise correct answer can score highly; irrelevant length is not rewarded.
- For HR/behavioral questions, judge reasoning and evidence rather than technical jargon.
- For technical questions, technical correctness matters.
- If the candidate mentioned a specific resume project/technology/decision, reference it in feedback or follow-up when relevant.
- Never use canned feedback repeatedly.
- If the answer is incomplete but promising, create a specific follow-up that probes the missing part.
- If the answer is clearly wrong, do not pretend it is correct.
- Follow-up must be contextual, never a generic 'give an example'.
- Keep feedback natural enough to be spoken aloud.
"""
    result = _gemini_generate_json(prompt, schema, "You are a fair senior interviewer evaluating a live candidate.", .2)
    if isinstance(result, dict) and "score" in result:
        result["score"] = max(0, min(100, _safe_int(result.get("score"))))
        return result
    words = len(_text(answer).split())
    qtext = _text(question.get("question"))
    score = min(88, 35 + (10 if words >= 8 else 0) + (10 if words >= 18 else 0) + (10 if words >= 35 else 0) + (10 if any(k in _text(answer).lower() for k in ("because", "example", "built", "developed", "implemented", "tested", "result", "learned")) else 0))
    label = "STRONG" if score >= 80 else "GOOD" if score >= 65 else "PARTIAL" if score >= 50 else "WEAK"
    follow = score < 68 and session.get("retry_count", 0) < 2
    if language == "HINDI":
        return {
            "score": score,
            "label": label,
            "feedback": "अच्छा। चलिए इसे आगे बढ़ाते हैं।" if score >= 65 else "धन्यवाद। आपके उत्तर का आकलन करने के लिए मुझे थोड़ा और विवरण चाहिए।",
            "strengths": ["उत्तर सीधे प्रश्न से जुड़ा है।"] if score >= 65 else [],
            "improvements": ["अपना तर्क और परिणाम बताते हुए एक ठोस उदाहरण दें।"] if score < 80 else ["उत्तर को स्पष्ट और विशिष्ट रखें।"],
            "missing_points": [],
            "technical_accuracy": score,
            "clarity": score,
            "confidence": score,
            "relevance": score,
            "should_follow_up": follow,
            "follow_up_question": "आपने यह निर्णय क्यों लिया और इसका क्या परिणाम हुआ?",
            "follow_up_reason": "उत्तर में उम्मीदवार के तर्क और परिणाम के बारे में और जानकारी चाहिए।",
        }
    return {"score": score, "label": label, "feedback": "Good. Let’s build on that." if score >= 65 else "Thanks. I need a little more detail to assess that answer.", "strengths": ["The answer directly engages with the question."] if score >= 65 else [], "improvements": ["Add a concrete example, your reasoning, and the result."] if score < 80 else ["Keep the answer structured and specific."], "missing_points": [], "technical_accuracy": score, "clarity": score, "confidence": score, "relevance": score, "should_follow_up": follow, "follow_up_question": "What was your specific reasoning or contribution, and what was the result?", "follow_up_reason": "The fallback evaluator needs more evidence from the candidate."}


# ============================================================
# ELEVENLABS
# ============================================================

def _elevenlabs_available():
    return bool(ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID and time.time() >= ELEVENLABS_TTS_DISABLED_UNTIL)


def _elevenlabs_stt_available():
    return bool(ELEVENLABS_API_KEY and time.time() >= ELEVENLABS_STT_DISABLED_UNTIL)


def _elevenlabs_audio(text):
    if not text or not _elevenlabs_available():
        return None
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}?output_format={ELEVENLABS_OUTPUT_FORMAT}"
    payload = json.dumps({
        "text": _text(text)[:2500],
        "model_id": ELEVENLABS_MODEL_ID,
        "voice_settings": {"stability": 0.45, "similarity_boost": 0.80, "style": 0.20, "speed": 0.98},
    }).encode("utf-8")
    req = URLRequest(url, data=payload, method="POST", headers={"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json", "Accept": "audio/mpeg", "User-Agent": "AI-Career-Copilot/2.0"})
    try:
        with urlopen(req, timeout=45) as response:
            return response.read()
    except HTTPError as error:
        try:
            detail = error.read().decode("utf-8", "replace")
        except Exception:
            detail = str(error)
        if error.code in (401, 402, 403, 429):
            global ELEVENLABS_TTS_DISABLED_UNTIL
            ELEVENLABS_TTS_DISABLED_UNTIL = time.time() + ELEVENLABS_DISABLE_SECONDS
            print(f"[INTERVIEW] ElevenLabs TTS quota/auth error ({error.code}). Browser TTS fallback will be used for {ELEVENLABS_DISABLE_SECONDS}s.")
        print(f"[INTERVIEW] ElevenLabs TTS HTTP {error.code}: {detail}")
        return None
    except (URLError, TimeoutError, ValueError) as error:
        print(f"[INTERVIEW] ElevenLabs TTS error: {error}")
        return None


def _elevenlabs_audio_b64(text):
    audio = _elevenlabs_audio(text)
    if not audio:
        return None
    try:
        return base64.b64encode(audio).decode("ascii")
    except Exception:
        return None


def _elevenlabs_transcribe(audio_bytes, filename="answer.webm", mime_type="audio/webm"):
    if not audio_bytes or not _elevenlabs_stt_available():
        return None
    boundary = "----AICareerCopilotBoundary" + uuid.uuid4().hex
    body = bytearray()

    def field(name, value):
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.extend(str(value).encode())
        body.extend(b"\r\n")

    field("model_id", ELEVENLABS_STT_MODEL_ID)
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: {mime_type}\r\n\r\n'.encode())
    body.extend(audio_bytes)
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode())

    req = URLRequest("https://api.elevenlabs.io/v1/speech-to-text", data=bytes(body), method="POST", headers={"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": f"multipart/form-data; boundary={boundary}", "Accept": "application/json", "User-Agent": "AI-Career-Copilot/2.0"})
    try:
        with urlopen(req, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        text = _text(payload.get("text"))
        return {"text": text, "language_code": _text(payload.get("language_code"), "unknown"), "language_probability": _safe_float(payload.get("language_probability"), 0.0)} if text else None
    except HTTPError as error:
        if error.code in (401, 402, 403, 429):
            global ELEVENLABS_STT_DISABLED_UNTIL
            ELEVENLABS_STT_DISABLED_UNTIL = time.time() + ELEVENLABS_DISABLE_SECONDS
        print(f"[INTERVIEW] ElevenLabs STT HTTP {error.code}: {error}")
        return None
    except (URLError, TimeoutError, ValueError) as error:
        print(f"[INTERVIEW] ElevenLabs STT error: {error}")
        return None


def _attach_audio(payload):
    # Do not synthesize audio during every API response. The browser requests
    # TTS only when it actually needs to speak, which prevents duplicate
    # ElevenLabs quota consumption and makes the browser fallback reliable.
    return payload


def _respond(payload, status=200):
    session_id = _text(payload.get("session_id"))
    if not session_id:
        request_data = request.get_json(silent=True) or {}
        session_id = _text(request_data.get("session_id"))

    if session_id:
        with SESSION_LOCK:
            session = INTERVIEW_SESSIONS.get(session_id)
        if session:
            save_record("interview_session", session_id, session)

    return jsonify(_attach_audio(payload)), status


# ============================================================
# REPORT
# ============================================================

def _valid_answer_count(session):
    return sum(1 for item in session.get("history", []) if item.get("count_for_score", False) and item.get("intent", "ANSWER") == "ANSWER")


def _average_score(session):
    scored = [x for x in session.get("history", []) if x.get("count_for_score", True) and x.get("evaluation")]
    values = [_safe_float(x.get("evaluation", {}).get("score", 0)) for x in scored]
    return round(sum(values) / len(values)) if values else 0


def _generate_report(session):
    scored = [x for x in session.get("history", []) if x.get("count_for_score", True) and x.get("evaluation")]
    if not scored:
        return {"overall_score": 0, "summary": "No scored interview answers were recorded.", "strengths": [], "improvements": [], "recommendations": [], "category_scores": {}, "performance_metrics": {}, "question_breakdown": []}

    scores = [_safe_float(x["evaluation"].get("score", 0)) for x in scored]
    metrics = {k: [] for k in ("technical_accuracy", "clarity", "confidence", "relevance")}
    categories = {}
    strengths, improvements, breakdown = [], [], []
    for item in scored:
        ev = item.get("evaluation", {})
        q = item.get("question", {})
        cat = _text(q.get("category"), "GENERAL")
        categories.setdefault(cat, []).append(_safe_float(ev.get("score", 0)))
        for k in metrics:
            metrics[k].append(_safe_float(ev.get(k, ev.get("score", 0))))
        for x in ev.get("strengths", []):
            if x not in strengths:
                strengths.append(x)
        for x in ev.get("improvements", []):
            if x not in improvements:
                improvements.append(x)
        breakdown.append({"question_number": item.get("main_question_number"), "question": q.get("question", ""), "category": cat, "difficulty": q.get("difficulty", ""), "answer": item.get("answer", ""), "score": _safe_float(ev.get("score", 0)), "label": ev.get("label", ""), "feedback": ev.get("feedback", "")})

    overall = round(sum(scores) / len(scores))
    summary = "Excellent interview performance." if overall >= 85 else "Solid interview performance with room to deepen your reasoning." if overall >= 70 else "Developing interview performance. Focus on specific evidence and structured answers." if overall >= 50 else "More preparation is needed. Review your resume, projects and core technical concepts."
    return {
        "overall_score": overall,
        "summary": summary,
        "strengths": strengths[:8],
        "improvements": improvements[:8],
        "recommendations": [
            "Use specific evidence from your real projects.",
            "Clearly separate what the team did from what you personally did.",
            "Explain why you chose a technology or approach.",
            "Finish important answers with a result, learning or trade-off.",
            "Practice weak technical areas identified in the interview.",
        ],
        "category_scores": {k: round(sum(v) / len(v)) for k, v in categories.items() if v},
        "performance_metrics": {k: round(sum(v) / len(v)) if v else overall for k, v in metrics.items()},
        "question_breakdown": breakdown,
    }


# ============================================================
# ROUTES
# ============================================================

def register_interview_routes(app, resume_manager, require_auth, get_authenticated_username):

    def _get_owned_session(session_id):
        authenticated_username = get_authenticated_username()
        if not authenticated_username:
            return None, jsonify({
                "success": False,
                "message": "Authentication required. Please login again."
            }), 401

        session_id = _text(session_id)
        if not session_id:
            return None, jsonify({
                "success": False,
                "message": "Session ID is required."
            }), 400

        with SESSION_LOCK:
            session = INTERVIEW_SESSIONS.get(session_id)

        if not session:
            session = load_record("interview_session", session_id)
            if session:
                with SESSION_LOCK:
                    INTERVIEW_SESSIONS[session_id] = session

        if not session:
            return None, jsonify({
                "success": False,
                "message": "Interview session expired. Please restart."
            }), 404

        owner = _text(session.get("username"))
        if owner.lower() != authenticated_username.lower():
            return None, jsonify({
                "success": False,
                "message": "You are not authorized to access this interview session."
            }), 403

        return session, None, None

    @app.route("/api/interview/start", methods=["POST"])
    @require_auth
    def interview_start():
        try:
            data = request.get_json(silent=True) or {}
            username = _text(data.get("username"))
            role = _text(data.get("target_role"))
            interview_type = _text(data.get("interview_type"), "technical").lower()
            language = _text(data.get("language"), "ENGLISH").upper()
            if not username:
                return jsonify({"success": False, "message": "Username is required."}), 400
            if interview_type not in INTERVIEW_TYPES or interview_type == "mixed":
                return jsonify({"success": False, "message": "Choose technical, project_resume, or hr interview type."}), 400
            if language not in ("ENGLISH", "HINDI"):
                return jsonify({"success": False, "message": "Choose English or Hindi for the interview."}), 400

            analysis = _latest_resume(resume_manager, username)
            if not analysis:
                return jsonify({"success": False, "message": "Please analyze your resume before starting interview preparation."}), 404

            role = role or _role_from_resume(analysis)
            name = _text(analysis.get("name"), username)
            session_id = uuid.uuid4().hex
            session = {
                "session_id": session_id,
                "username": username,
                "candidate_name": name,
                "role": role,
                "interview_type": interview_type,
                "analysis": analysis,
                "question_index": 0,
                "question_count": min(
                    QUESTION_COUNT,
                    len(_fallback_questions(analysis, role, interview_type, language)),
                ),
                "question": None,
                "history": [],
                "state": "QUESTION",
                "answer_mode": "CHAT",
                "preferred_language": language,
                "retry_count": 0,
                "guidance_round": 0,
                "conversation_turns": [],
                "topics_covered": [],
                "started_at": _now(),
                "finished_at": None,
                "report": None,
            }
            with SESSION_LOCK:
                INTERVIEW_SESSIONS[session_id] = session

            if language == "HINDI":
                greeting = (
                    f"नमस्ते {name}, आपके {_interview_type_label(interview_type, language)} में आपका स्वागत है। "
                    "मैंने आपका रिज़्यूमे देखा है और प्रश्न आपके वास्तविक कौशल, परियोजनाओं और अनुभव पर आधारित होंगे। आइए शुरू करें।"
                )
            else:
                greeting = (
                    f"Hi {name}, welcome to your {_interview_type_label(interview_type, language)} interview. I'm your AI interviewer. "
                    "I've reviewed your resume and will base the questions on your actual skills, projects, and experience. Let's begin."
                )
            session["question"] = _first_question(analysis, role, language, interview_type)
            return _respond({
                "success": True,
                "session_id": session_id,
                "candidate_name": name,
                "target_role": role,
                "interview_type": interview_type,
                "interview_type_label": _interview_type_label(interview_type, language),
                "preferred_language": language,
                "question_number": 1,
                "question_count": session["question_count"],
                "question": session["question"],
                "greeting": greeting,
                "speech_text": greeting,
                "state": "QUESTION",
                "answer_mode": "CHAT",
                "gemini_enabled": _gemini_available(),
                "elevenlabs_enabled": _elevenlabs_available(),
                "elevenlabs_stt_enabled": bool(ELEVENLABS_API_KEY),
                "voice_provider": "elevenlabs" if _elevenlabs_available() else "browser_fallback",
            })
        except Exception as error:
            print(f"[INTERVIEW] Start error: {error}")
            return jsonify({"success": False, "message": "Unable to start the interview."}), 500

    @app.route("/api/interview/mode", methods=["POST"])
    @require_auth
    def interview_mode():
        data = request.get_json(silent=True) or {}
        session_id = _text(data.get("session_id"))
        mode = _text(data.get("answer_mode")).upper()
        if mode in ("TEXT", "CHAT"):
            mode = "CHAT"
        elif mode in ("VOICE", "AUDIO"):
            mode = "VOICE"
        else:
            return jsonify({"success": False, "message": "answer_mode must be chat or voice."}), 400
        session, error_response, error_status = _get_owned_session(session_id)
        if error_response is not None:
            return error_response, error_status
        session["answer_mode"] = mode
        session["state"] = "QUESTION"
        session["question"] = _first_question(session["analysis"], session["role"], session.get("preferred_language", "ENGLISH"), session.get("interview_type", "mixed"))
        message = _language_text(
            session.get("preferred_language"),
            f"Perfect. We'll use {'voice' if mode == 'VOICE' else 'chat'} mode. Let's begin.",
            f"ठीक है। हम {'वॉइस' if mode == 'VOICE' else 'चैट'} मोड में आगे बढ़ेंगे। शुरू करते हैं।",
        )
        return _respond({"success": True, "type": "question", "answer_mode": mode, "message": message, "speech_text": message, "question": session["question"], "question_number": 1, "question_count": session["question_count"], "state": "QUESTION", "finished": False})

    @app.route("/api/interview/evaluate", methods=["POST"])
    @require_auth
    def interview_evaluate():
        try:
            data = request.get_json(silent=True) or {}
            session_id = _text(data.get("session_id"))
            answer = _text(data.get("answer"))
            if not session_id:
                return jsonify({"success": False, "message": "Session ID is required."}), 400
            if not answer:
                return jsonify({"success": False, "message": "Please provide an answer."}), 400
            session, error_response, error_status = _get_owned_session(session_id)
            if error_response is not None:
                return error_response, error_status

            intent_result = _classify_intent(answer, session)
            intent = _text(intent_result.get("intent"), "ANSWER")
            language = _text(session.get("preferred_language"), "ENGLISH").upper()
            if language not in ("ENGLISH", "HINDI", "HINGLISH"):
                language = "ENGLISH"
            session["conversation_turns"].append({"speaker": "candidate", "text": answer, "intent": intent, "time": _now()})

            # Opening readiness check.
            if session["state"] == "READY_CHECK":
                if intent == "READY":
                    session["state"] = "MODE_SELECT"
                    message = _interview_message(language, "ready")
                    session["conversation_turns"].append({"speaker": "interviewer", "text": message, "time": _now()})
                    return _respond({"success": True, "type": "mode_select", "intent": "READY", "message": message, "speech_text": message, "state": "MODE_SELECT", "finished": False})
                if intent == "NOT_READY":
                    message = _interview_message(language, "not_ready")
                    return _respond({"success": True, "type": "conversation", "intent": "NOT_READY", "message": message, "speech_text": message, "state": "READY_CHECK", "finished": False})
                message = _interview_message(language, "ready_check")
                return _respond({"success": True, "type": "conversation", "intent": "READY_CHECK", "message": message, "speech_text": message, "state": "READY_CHECK", "finished": False})

            # Mode selection can be handled through the same conversational endpoint.
            if session["state"] == "MODE_SELECT":
                if intent == "VOICE_MODE":
                    mode = "VOICE"
                elif intent == "CHAT_MODE":
                    mode = "CHAT"
                else:
                    message = _interview_message(language, "mode_prompt")
                    return _respond({"success": True, "type": "mode_select", "intent": intent, "message": message, "speech_text": message, "state": "MODE_SELECT", "finished": False})
                session["answer_mode"] = mode
                session["state"] = "QUESTION"
                session["question"] = _first_question(session["analysis"], session["role"], language, session.get("interview_type", "mixed"))
                message = _interview_message(
                    language,
                    "mode_set",
                    mode=("voice" if mode == "VOICE" else "chat") if language == "ENGLISH" else ("वॉइस" if mode == "VOICE" else "चैट"),
                )
                session["conversation_turns"].append({"speaker": "interviewer", "text": message, "time": _now()})
                return _respond({"success": True, "type": "question", "intent": intent, "answer_mode": mode, "message": message, "speech_text": message, "question": session["question"], "question_number": 1, "question_count": session["question_count"], "state": "QUESTION", "finished": False})

            question = session.get("question") or {}

            # Conversational requests never accidentally advance the interview.
            if intent in ("YES", "GREETING", "CLARIFICATION", "ASK_EXPLANATION", "QUESTION_TO_INTERVIEWER", "OFF_TOPIC"):
                if intent == "CLARIFICATION":
                    message = _interview_message(
                        language,
                        "clarification",
                        question=question.get("question", ""),
                    )
                elif intent == "ASK_EXPLANATION":
                    explanation = _explain_question(session, question, language, answer)
                    message = _interview_message(language, "explanation", explanation=explanation)
                    session["state"] = "EXPLANATION_CHECK"
                elif intent == "QUESTION_TO_INTERVIEWER":
                    message = _interview_message(language, "question_back", question=_text(question.get("question")))
                elif intent == "OFF_TOPIC":
                    message = _interview_message(language, "off_topic", question=_text(question.get("question")))
                elif intent == "YES":
                    message = _interview_message(language, "yes_continue")
                else:
                    message = _interview_message(
                        language,
                        "continue",
                        name=session["candidate_name"],
                        question=question.get("question", ""),
                    )
                session["conversation_turns"].append({"speaker": "interviewer", "text": message, "time": _now()})
                return _respond({"success": True, "type": "conversation", "intent": intent, "message": message, "speech_text": message, "question": question, "state": session["state"], "finished": False})

            # If we just explained something, YES means retry; NO means offer another explanation.
            if session["state"] == "EXPLANATION_CHECK":
                if intent == "YES":
                    session["state"] = "QUESTION"
                    rephrased = dict(question)
                    rephrased["question"] = _rephrase_question(session, question, language)
                    rephrased["is_rephrase"] = True
                    session["question"] = rephrased
                    message = _interview_message(language, "retry")
                    return _respond({"success": True, "type": "question", "intent": "YES", "message": message, "speech_text": message, "next_question": rephrased, "question_number": session["question_index"] + 1, "next_question_number": session["question_index"] + 1, "question_count": session["question_count"], "state": "QUESTION", "finished": False})
                if intent == "NO":
                    explanation = _explain_question(session, question, language, "The candidate says the explanation is not clear.")
                    message = _interview_message(language, "explain_again", explanation=explanation)
                    return _respond({"success": True, "type": "conversation", "intent": "NO", "message": message, "speech_text": message, "state": "EXPLANATION_CHECK", "finished": False})
                explanation = _explain_question(session, question, language, answer)
                message = _interview_message(language, "explain_clearer", explanation=explanation)
                return _respond({"success": True, "type": "conversation", "message": message, "speech_text": message, "state": "EXPLANATION_CHECK", "finished": False})

            # Explicitly unknown: ask permission before teaching.
            if intent == "DONT_KNOW":
                session["state"] = "GUIDANCE_OFFER"
                message = _interview_message(language, "dont_know")
                if language == "HINDI":
                    ev = {"score": 20, "label": "मार्गदर्शन आवश्यक", "passed": False, "feedback": "उम्मीदवार ने अपनी जानकारी की सीमा के बारे में ईमानदारी दिखाई।", "explanation": "", "strengths": ["अपनी जानकारी की सीमा के बारे में ईमानदार।"], "improvements": ["इस अवधारणा को दोहराएँ और फिर से प्रयास करें।"], "missing_points": ["सीधा उत्तर"], "next_action": "EXPLAIN"}
                else:
                    ev = {"score": 20, "label": "NEEDS GUIDANCE", "passed": False, "feedback": "The candidate was honest about not knowing.", "explanation": "", "strengths": ["Honest about knowledge limits."], "improvements": ["Review this concept and try it again."], "missing_points": ["A direct answer"], "next_action": "EXPLAIN"}
                session["history"].append({"question_number": session["question_index"] + 1, "main_question_number": session["question_index"] + 1, "question": question, "answer": answer, "intent": intent, "evaluation": ev, "attempt": session.get("retry_count", 0) + 1, "count_for_score": False, "timestamp": _now()})
                return _respond({"success": True, "type": "guidance_offer", "intent": "DONT_KNOW", "evaluation": ev, "message": message, "speech_text": message, "state": "GUIDANCE_OFFER", "finished": False, "question": question, "question_number": session["question_index"] + 1, "question_count": session["question_count"], "average_score": _average_score(session)})

            # Guidance permission.
            if session["state"] == "GUIDANCE_OFFER":
                if intent == "YES":
                    explanation = _explain_question(session, question, language, "Candidate requested an explanation.")
                    session["state"] = "EXPLANATION_CHECK"
                    message = _interview_message(language, "guidance_yes", explanation=explanation)
                    return _respond({"success": True, "type": "guidance", "intent": "YES", "message": message, "speech_text": message, "explanation": explanation, "state": "EXPLANATION_CHECK", "finished": False})
                if intent == "NO":
                    session["question_index"] += 1
                    session["retry_count"] = 0
                    if session["question_index"] >= session["question_count"]:
                        session["state"] = "COMPLETED"
                        session["finished_at"] = _now()
                        session["report"] = _generate_report(session)
                        return _respond({"success": True, "type": "complete", "intent": "NO", "finished": True, "average_score": _average_score(session), "valid_answer_count": _valid_answer_count(session), "report": session["report"], "state": "COMPLETED"})
                    session["state"] = "QUESTION"
                    session["question"] = _next_question(session, "Candidate chose to move on.", {"score": 0, "label": "SKIPPED"})
                    message = _interview_message(language, "move_on")
                    return _respond({"success": True, "type": "question", "intent": "NO", "message": message, "speech_text": message, "next_question": session["question"], "next_question_number": session["question_index"] + 1, "question_count": session["question_count"], "average_score": _average_score(session), "state": "QUESTION", "finished": False})
                message = _interview_message(language, "guidance_prompt")
                return _respond({"success": True, "type": "guidance_offer", "message": message, "speech_text": message, "state": "GUIDANCE_OFFER", "finished": False})

            # Normal answer evaluation.
            evaluation = _evaluate_answer(session, answer)
            session["retry_count"] = session.get("retry_count", 0) + 1
            session["history"].append({"question_number": session["question_index"] + 1, "main_question_number": session["question_index"] + 1, "question": question, "answer": answer, "intent": intent, "evaluation": evaluation, "attempt": session["retry_count"], "count_for_score": True, "timestamp": _now()})

            if evaluation.get("should_follow_up") and session["retry_count"] < 3 and _text(evaluation.get("follow_up_question")):
                follow_up = dict(question)
                follow_up["question"] = _text(evaluation["follow_up_question"])
                follow_up["is_follow_up"] = True
                session["question"] = follow_up
                message = _text(evaluation.get("feedback"), _interview_message(language, "feedback_followup"))
                return _respond({"success": True, "type": "evaluation", "evaluation": evaluation, "passed": False, "finished": False, "message": message, "speech_text": message, "next_question": follow_up, "next_question_number": session["question_index"] + 1, "question_count": session["question_count"], "average_score": _average_score(session), "valid_answer_count": _valid_answer_count(session), "state": "QUESTION"})

            # Good enough: advance to a genuinely new question.
            session["question_index"] += 1
            session["retry_count"] = 0
            if session["question_index"] >= session["question_count"]:
                session["state"] = "COMPLETED"
                session["finished_at"] = _now()
                session["report"] = _generate_report(session)
                message = _text(evaluation.get("feedback"), _interview_message(language, "thanks"))
                return _respond({"success": True, "type": "evaluation", "evaluation": evaluation, "passed": True, "finished": True, "message": message, "speech_text": message, "next_question": None, "average_score": _average_score(session), "state": "COMPLETED", "report": session["report"]})

            session["state"] = "QUESTION"
            session["question"] = _next_question(session, answer, evaluation)
            message = _text(evaluation.get("feedback"), _interview_message(language, "continue_next"))
            return _respond({"success": True, "type": "evaluation", "evaluation": evaluation, "passed": True, "finished": False, "message": message, "speech_text": message, "next_question": session["question"], "next_question_number": session["question_index"] + 1, "question_count": session["question_count"], "average_score": _average_score(session), "valid_answer_count": _valid_answer_count(session), "state": "QUESTION"})

        except Exception as error:
            print(f"[INTERVIEW] Evaluation error: {error}")
            return jsonify({"success": False, "message": "Unable to process this interview turn."}), 500

    @app.route("/api/interview/guidance", methods=["POST"])
    @require_auth
    def interview_guidance():
        # Backwards-compatible endpoint. The main conversation now lives in /evaluate.
        data = request.get_json(silent=True) or {}
        data["answer"] = _text(data.get("answer"), "yes")
        with app.test_request_context(
            json=data,
            headers={
                "Authorization": request.headers.get("Authorization", "")
            }
        ):
            return interview_evaluate()

    @app.route("/api/interview/transcribe", methods=["POST"])
    @require_auth
    def interview_transcribe():
        try:
            if not _elevenlabs_stt_available():
                return jsonify({"success": False, "enabled": False, "message": "ElevenLabs Scribe is temporarily unavailable. Use browser voice input or type your answer."}), 503
            if "audio" not in request.files:
                return jsonify({"success": False, "message": "Audio recording is required."}), 400
            audio_file = request.files["audio"]
            audio_bytes = audio_file.read()
            if not audio_bytes:
                return jsonify({"success": False, "message": "The audio recording is empty."}), 400
            if len(audio_bytes) > 12 * 1024 * 1024:
                return jsonify({"success": False, "message": "Audio recording is too large."}), 413
            result = _elevenlabs_transcribe(audio_bytes, filename=audio_file.filename or "answer.webm", mime_type=audio_file.mimetype or "audio/webm")
            if not result:
                return jsonify({"success": False, "enabled": True, "message": "Unable to transcribe the voice answer."}), 502
            return _respond({"success": True, "provider": "elevenlabs", **result})
        except Exception as error:
            print(f"[INTERVIEW] Transcription error: {error}")
            return jsonify({"success": False, "message": "Unable to process the voice answer."}), 500

    @app.route("/api/interview/speak", methods=["POST"])
    @require_auth
    def interview_speak():
        try:
            data = request.get_json(silent=True) or {}
            text = _text(data.get("text"))
            if not text:
                return jsonify({"success": False, "message": "Text is required."}), 400
            if not _elevenlabs_available():
                return jsonify({"success": False, "enabled": False, "message": "ElevenLabs is not configured."}), 503
            audio = _elevenlabs_audio(text)
            if not audio:
                return jsonify({"success": False, "enabled": True, "message": "ElevenLabs voice generation failed."}), 502
            response = app.response_class(audio, mimetype="audio/mpeg")
            response.headers["Cache-Control"] = "no-store"
            response.headers["X-Voice-Provider"] = "ElevenLabs"
            return response
        except Exception as error:
            print(f"[INTERVIEW] TTS error: {error}")
            return jsonify({"success": False, "message": "Unable to generate interviewer voice."}), 500

    @app.route("/api/interview/session/<session_id>", methods=["GET"])
    @require_auth
    def interview_session(session_id):
        session, error_response, error_status = _get_owned_session(session_id)
        if error_response is not None:
            return error_response, error_status
        return jsonify({
            "success": True,
            "session_id": session_id,
            "username": session["username"],
            "candidate_name": session["candidate_name"],
            "target_role": session["role"],
            "interview_type": session.get("interview_type", "mixed"),
            "interview_type_label": _interview_type_label(session.get("interview_type"), session.get("preferred_language", "ENGLISH")),
            "preferred_language": session.get("preferred_language", "ENGLISH"),
            "question_number": min(session["question_index"] + 1, session["question_count"]),
            "question_count": session["question_count"],
            "valid_answer_count": _valid_answer_count(session),
            "question": session.get("question"),
            "state": session["state"],
            "answer_mode": session.get("answer_mode"),
            "history": session.get("history", []),
            "finished": session["state"] == "COMPLETED",
            "report": session.get("report"),
            "gemini_enabled": _gemini_available(),
            "elevenlabs_enabled": _elevenlabs_available(),
            "elevenlabs_stt_enabled": bool(ELEVENLABS_API_KEY),
            "voice_provider": "elevenlabs" if _elevenlabs_available() else "browser_fallback",
        }), 200

    @app.route("/api/interview/report/<session_id>", methods=["GET"])
    @require_auth
    def interview_report(session_id):
        session, error_response, error_status = _get_owned_session(session_id)
        if error_response is not None:
            return error_response, error_status
        report = session.get("report") or _generate_report(session)
        return _respond({"success": True, "session_id": session_id, "username": session["username"], "candidate_name": session["candidate_name"], "target_role": session["role"], "interview_type": session.get("interview_type", "mixed"), "interview_type_label": _interview_type_label(session.get("interview_type"), session.get("preferred_language", "ENGLISH")), "preferred_language": session.get("preferred_language", "ENGLISH"), "completed": session["state"] == "COMPLETED", "report": report})


    @app.route("/api/interview/latest/<username>", methods=["GET"])
    @require_auth
    def interview_latest(username):
        """Return the latest completed interview report for a dashboard user."""
        username = _text(username)
        if not username:
            return jsonify({"success": False, "message": "Username is required."}), 400

        persisted_sessions = load_records(
            "interview_session",
            "username",
            username,
        )
        with SESSION_LOCK:
            for session in persisted_sessions:
                session_id = _text(session.get("session_id"))
                if session_id:
                    INTERVIEW_SESSIONS.setdefault(session_id, session)

            sessions = [
                session for session in INTERVIEW_SESSIONS.values()
                if _text(session.get("username")).lower() == username.lower()
            ]

        completed = [s for s in sessions if s.get("state") == "COMPLETED"]
        if not completed:
            return jsonify({
                "success": True,
                "username": username,
                "has_interview": False,
                "report": None,
                "message": "No completed interview found yet."
            }), 200

        latest = max(
            completed,
            key=lambda s: s.get("finished_at") or s.get("started_at") or ""
        )
        report = latest.get("report") or _generate_report(latest)
        return _respond({
            "success": True,
            "username": username,
            "has_interview": True,
            "session_id": latest.get("session_id"),
            "candidate_name": latest.get("candidate_name"),
            "target_role": latest.get("role"),
            "interview_type": latest.get("interview_type", "mixed"),
            "interview_type_label": _interview_type_label(latest.get("interview_type"), latest.get("preferred_language", "ENGLISH")),
            "preferred_language": latest.get("preferred_language", "ENGLISH"),
            "completed_at": latest.get("finished_at"),
            "valid_answer_count": _valid_answer_count(latest),
            "report": report,
        })


print("=" * 60)
print("        INTERVIEW INTELLIGENCE ENGINE v2")
print("=" * 60)
print("Gemini:" + (" ENABLED" if _gemini_available() else " DISABLED / FALLBACK MODE"))
print(f"Model: {GEMINI_MODEL}")
print(f"Questions per interview: {QUESTION_COUNT}")
print("Resume-aware adaptive interviewing: ENABLED")
print("Conversation-state memory: ENABLED")
print("Contextual follow-ups: ENABLED")
print("Explain-on-request flow: ENABLED")
print("English / Hindi / Hinglish: ENABLED")
print("ElevenLabs voice:" + (" ENABLED" if _elevenlabs_available() else " OPTIONAL / BROWSER FALLBACK"))
print("ElevenLabs STT:" + (" ENABLED" if ELEVENLABS_API_KEY else " DISABLED"))
print("=" * 60)