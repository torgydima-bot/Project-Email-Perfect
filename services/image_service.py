"""
Генерация изображений через AI:
1. Stable Horde — бесплатно, без регистрации, сообщество GPU (stablehorde.net)
2. Kandinsky (FusionBrain) — если настроен API ключ
3. Picsum — красивые природные фото (fallback, без регистрации)
"""
import time
import uuid
import random
import json
import base64
from pathlib import Path
import httpx
import config


def generate_image(prompt_ru: str, prompt_en: str = "") -> str | None:
    """
    Генерирует изображение по промту. Возвращает filename в static/uploads/ или None.
    """
    # Используем английский промт для Stable Horde (лучше понимает)
    en_prompt = prompt_en or prompt_ru

    # 1. Stable Horde — бесплатно, без регистрации
    filename = _stable_horde(en_prompt)
    if filename:
        return filename

    # 2. Kandinsky — если настроен
    if config.FUSIONBRAIN_KEY and config.FUSIONBRAIN_SECRET:
        filename = _kandinsky(prompt_ru)
        if filename:
            return filename

    # 3. Picsum — красивые природные фото
    return _picsum_fallback()


def _stable_horde(prompt: str) -> str | None:
    """
    Генерирует изображение через Stable Horde.
    Бесплатно, без регистрации. Анонимный ключ: 0000000000
    """
    api_key = config.STABLE_HORDE_KEY if hasattr(config, "STABLE_HORDE_KEY") and config.STABLE_HORDE_KEY else "0000000000"

    try:
        with httpx.Client(timeout=120) as client:
            # Отправляем задание
            r = client.post(
                "https://stablehorde.net/api/v2/generate/async",
                headers={"apikey": api_key, "Content-Type": "application/json"},
                json={
                    "prompt": prompt + ", high quality, professional photography, 4k",
                    "params": {
                        "width": 512,
                        "height": 512,
                        "steps": 25,
                        "n": 1,
                        "sampler_name": "k_euler_a",
                        "cfg_scale": 7,
                    },
                    "models": ["Dreamshaper"],
                    "r2": True,
                },
            )
            if r.status_code != 202:
                return None

            job_id = r.json().get("id")
            if not job_id:
                return None

            # Ждём результат (до 3 минут)
            for _ in range(36):
                time.sleep(5)
                check = client.get(
                    f"https://stablehorde.net/api/v2/generate/check/{job_id}",
                    headers={"apikey": api_key},
                )
                check_data = check.json()
                if check_data.get("done"):
                    # Получаем результат
                    result = client.get(
                        f"https://stablehorde.net/api/v2/generate/status/{job_id}",
                        headers={"apikey": api_key},
                    )
                    generations = result.json().get("generations", [])
                    if generations:
                        img_url = generations[0].get("img", "")
                        if img_url:
                            img_r = client.get(img_url, follow_redirects=True)
                            if img_r.status_code == 200:
                                filename = f"horde_{uuid.uuid4().hex[:8]}.jpg"
                                (Path("static/uploads") / filename).write_bytes(img_r.content)
                                return filename
                        # Иногда возвращается base64
                        img_b64 = generations[0].get("img_b64", "")
                        if img_b64:
                            img_bytes = base64.b64decode(img_b64)
                            filename = f"horde_{uuid.uuid4().hex[:8]}.jpg"
                            (Path("static/uploads") / filename).write_bytes(img_bytes)
                            return filename
                    return None
                elif check_data.get("faulted"):
                    return None

    except Exception:
        pass
    return None


def _kandinsky(prompt: str) -> str | None:
    """Генерирует изображение через Kandinsky API (fusionbrain.ai)."""
    base_url = "https://api-key.fusionbrain.ai/key/api/v1"
    headers = {
        "X-Key": f"Key {config.FUSIONBRAIN_KEY}",
        "X-Secret": f"Secret {config.FUSIONBRAIN_SECRET}",
    }

    try:
        with httpx.Client(timeout=90) as client:
            r = client.get(f"{base_url}/models", headers=headers)
            if r.status_code != 200:
                return None
            models = r.json()
            if not models:
                return None
            model_id = models[0]["id"]

            params = {
                "type": "GENERATE",
                "numImages": 1,
                "width": 680,
                "height": 440,
                "generateParams": {"query": prompt},
            }
            gen_r = client.post(
                f"{base_url}/text2image/run",
                headers=headers,
                data={"model_id": str(model_id), "params": json.dumps(params)},
            )
            if gen_r.status_code != 201:
                return None
            task_uuid = gen_r.json()["uuid"]

            for _ in range(20):
                time.sleep(3)
                status_r = client.get(f"{base_url}/pipeline/status/{task_uuid}", headers=headers)
                data = status_r.json()
                if data.get("status") == "DONE":
                    images = data.get("images", [])
                    if images:
                        img_bytes = base64.b64decode(images[0])
                        filename = f"kandinsky_{uuid.uuid4().hex[:8]}.jpg"
                        (Path("static/uploads") / filename).write_bytes(img_bytes)
                        return filename
                elif data.get("status") == "FAIL":
                    return None
    except Exception:
        pass
    return None


def _picsum_fallback() -> str | None:
    """Возвращает публичный URL от Picsum (без скачивания — работает в письмах)."""
    seed = random.randint(1, 500)
    return f"https://picsum.photos/seed/{seed}/680/440"
