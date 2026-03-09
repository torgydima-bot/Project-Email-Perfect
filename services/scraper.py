import httpx
from bs4 import BeautifulSoup


def _extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()
    main = (
        soup.find("main") or
        soup.find("article") or
        soup.find(class_=lambda c: c and "content" in c.lower()) or
        soup.find("body")
    )
    text = (main or soup).get_text(separator="\n", strip=True)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines[:200])[:8000]


def _fetch_with_browser(url: str, timeout: int) -> str:
    """Загружает страницу через Playwright (для JS-сайтов типа Тильда)."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)  # ждём JS-рендер
            text = page.inner_text("body")
            browser.close()
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        return "\n".join(lines[:300])[:8000]
    except Exception as e:
        return f"[Ошибка браузера: {e}]"


def fetch_product_og_image(url: str, timeout: int = 10) -> str:
    """Извлекает og:image URL из HTML страницы продукта (без JS, работает быстро)."""
    if not url or not url.startswith("http"):
        return ""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
        soup = BeautifulSoup(resp.text, "html.parser")
        tag = soup.find("meta", property="og:image")
        if tag and tag.get("content"):
            return tag["content"]
    except Exception:
        pass
    return ""


def fetch_product_text(url: str, timeout: int = 20) -> str:
    """
    Скачивает страницу продукта и возвращает текстовое содержимое.
    Сначала пробует httpx, если мало контента — использует Playwright.
    """
    if not url or not url.startswith("http"):
        return ""

    # Сначала пробуем быстрый httpx
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
        text = _extract_text(resp.text)
    except Exception:
        text = ""

    # Если получили мало текста (JS-сайт) — используем браузер
    if len(text) < 200:
        text = _fetch_with_browser(url, timeout)

    return text
