import json
import anthropic
import config

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def _ask(prompt: str, max_tokens: int = 1500) -> str:
    try:
        msg = _get_client().messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        return f"[Ошибка AI: {e}]"


def generate_product_email(product_name: str, product_page_text: str) -> dict:
    """
    По названию и тексту страницы продукта генерирует все блоки письма.
    Возвращает: {subject, greeting_text, product_desc, useful_fact}
    """
    prompt = f"""Ты копирайтер для email-рассылки компании по продаже витаминов, минералов и БАД для здоровья.

Продукт: {product_name}

Информация со страницы продукта:
{product_page_text[:4000]}

Напиши контент для email-рассылки на русском языке. Верни ТОЛЬКО валидный JSON без markdown:
{{
  "subject": "тема письма (цепляющая, с крючком, до 60 символов)",
  "greeting_text": "вводный абзац после приветствия (2-3 предложения, почему этот продукт важен)",
  "product_desc": "описание продукта (3-4 предложения: польза, состав, кому помогает)",
  "useful_fact": "полезный факт или мини-статья (2-3 абзаца о теме здоровья связанной с продуктом)"
}}

Стиль: дружелюбный, заботливый, экспертный. Без спама и кричащих заглавных букв."""

    raw = _ask(prompt, max_tokens=1000)
    try:
        # Убираем возможные markdown-обёртки
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception:
        return {
            "subject": f"{product_name} — для вашего здоровья",
            "greeting_text": "",
            "product_desc": raw[:500],
            "useful_fact": "",
        }


def generate_article(topic: str) -> dict:
    """Генерирует образовательную статью о здоровье."""
    prompt = f"""Ты эксперт-нутрициолог, пишешь статью для email-рассылки о здоровье.

Тема: {topic}

Напиши статью на русском языке. Верни ТОЛЬКО валидный JSON:
{{
  "subject": "тема письма (до 60 символов, цепляющая)",
  "article_title": "заголовок статьи",
  "article_html": "текст статьи в HTML (используй <p>, <b>, <ul><li>). 300-400 слов. Практичная польза."
}}"""

    raw = _ask(prompt, max_tokens=1200)
    try:
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception:
        return {
            "subject": topic,
            "article_title": topic,
            "article_html": f"<p>{raw[:800]}</p>",
        }


def generate_subject_variants(topic: str) -> list:
    """Возвращает 3 варианта темы письма."""
    prompt = f"""Придумай 3 варианта темы email-письма для рассылки о здоровье и витаминах.
Тема письма: {topic}
Верни ТОЛЬКО JSON-массив из 3 строк: ["вариант 1", "вариант 2", "вариант 3"]
Каждый вариант до 60 символов. Цепляющие, разные по стилю."""

    raw = _ask(prompt, max_tokens=300)
    try:
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)
        return result if isinstance(result, list) else [topic]
    except Exception:
        return [topic, f"Важно о {topic}", f"Читайте: {topic}"]
