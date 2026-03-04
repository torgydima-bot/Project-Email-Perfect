import httpx
from bs4 import BeautifulSoup


def fetch_product_text(url: str, timeout: int = 15) -> str:
    """
    Скачивает страницу продукта и возвращает текстовое содержимое
    (заголовок + основной текст, без навигации и футера).
    """
    if not url or not url.startswith("http"):
        return ""

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        return f"[Ошибка загрузки страницы: {e}]"

    soup = BeautifulSoup(resp.text, "html.parser")

    # Удаляем ненужные теги
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()

    # Пробуем найти основной контент
    main = (
        soup.find("main") or
        soup.find("article") or
        soup.find(class_=lambda c: c and "content" in c.lower()) or
        soup.find("body")
    )

    if main:
        text = main.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    # Чистим пустые строки
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    result = "\n".join(lines[:200])  # Берём первые 200 строк
    return result[:8000]  # Не больше 8000 символов для AI
