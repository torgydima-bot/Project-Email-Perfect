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
    fn = "{{first_name}}"
    prompt = f"""Ты копирайтер для email-рассылки компании по продаже витаминов, минералов и БАД для здоровья.

Продукт: {product_name}

Информация со страницы продукта:
{product_page_text[:4000]}

Напиши контент для email-рассылки на русском языке. Верни ТОЛЬКО валидный JSON без markdown:
{{
  "subject": "тема письма — ОБЯЗАТЕЛЬНО начни с '{fn}, ' затем цепляющий текст (например: '{fn}, а вы знали...' или '{fn}, скоро весна —'). До 70 символов.",
  "greeting_text": "вводный абзац HTML — начни с вопроса или факта БЕЗ обращения по имени. Например: 'А вы знали, что...' или 'Задумывались ли вы...'. 2-3 предложения. Выдели 2-4 ключевых слова жирным: <b>слово</b>. Только теги <b>, без <p>.",
  "product_desc": "описание продукта (3-4 предложения: польза, состав, кому помогает)",
  "useful_fact": "ОБРАЗОВАТЕЛЬНАЯ статья о здоровье — НЕ о самом продукте (о нём уже написано выше в product_desc). Выбери более широкую тему здоровья, связанную с продуктом: например, если продукт с витаминами — о роли витаминов в энергии; если с магнием — о стрессе и нервной системе; если иммунный — о том как работает иммунитет. ОБЯЗАТЕЛЬНО начни с личного обращения '{fn}'. 2-3 абзаца HTML (<p>, <b>). Практичная польза. НЕ упоминай название продукта."
}}

Стиль: дружелюбный, личный, заботливый, экспертный. Без спама и кричащих заглавных букв.
ВАЖНО: используй {fn} как плейсхолдер имени — он будет заменён реальным именем получателя."""

    raw = _ask(prompt, max_tokens=2000)
    try:
        # Убираем возможные markdown-обёртки
        clean = raw.strip()
        if "```" in clean:
            parts = clean.split("```")
            for p in parts:
                p = p.strip()
                if p.startswith("json"):
                    p = p[4:].strip()
                if p.startswith("{"):
                    clean = p
                    break
        # Находим первый { и последний }
        start = clean.find("{")
        end = clean.rfind("}") + 1
        if start != -1 and end > start:
            clean = clean[start:end]
        return json.loads(clean)
    except Exception:
        return {
            "subject": f"{fn}, расскажем о {product_name}",
            "greeting_text": "",
            "product_desc": "",
            "useful_fact": "",
        }


def generate_article(topic: str) -> dict:
    """Генерирует образовательную статью о здоровье."""
    fn = "{{first_name}}"
    prompt = f"""Ты эксперт-нутрициолог, пишешь статью для email-рассылки о здоровье.

Тема: {topic}

Напиши статью на русском языке. Верни ТОЛЬКО валидный JSON:
{{
  "subject": "тема письма — ОБЯЗАТЕЛЬНО начни с '{fn}, ' затем цепляющий текст. До 70 символов.",
  "article_title": "заголовок статьи",
  "article_html": "текст статьи в HTML. ОБЯЗАТЕЛЬНО начни первый абзац с личного обращения '{fn}' — например '<p>{fn}, сегодня мы разберём...' или '<p>{fn}, вы когда-нибудь замечали...'. Используй <p>, <b>, <ul><li>. 300-400 слов. Практичная польза, живой стиль."
}}

ВАЖНО: {fn} — плейсхолдер имени читателя, он будет заменён реальным именем."""

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
