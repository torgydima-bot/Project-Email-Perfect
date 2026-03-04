import io
import pandas as pd
from db.models import db, Contact, Product


def _read_df(file):
    filename = file.filename.lower()
    content = file.read()
    if filename.endswith(".xlsx") or filename.endswith(".xls"):
        return pd.read_excel(io.BytesIO(content))
    else:
        for enc in ("utf-8", "utf-8-sig", "cp1251", "latin-1"):
            for sep in (",", ";", "\t"):
                try:
                    df = pd.read_csv(io.StringIO(content.decode(enc)), sep=sep)
                    if len(df.columns) >= 1:
                        return df
                except Exception:
                    continue
    return pd.DataFrame()


def _normalize_col(df, *variants):
    """Возвращает первое совпадающее название колонки (без учёта регистра)."""
    cols_lower = {c.lower(): c for c in df.columns}
    for v in variants:
        if v.lower() in cols_lower:
            return cols_lower[v.lower()]
    return None


def import_contacts_from_file(file):
    df = _read_df(file)
    if df.empty:
        return 0, 0, 1

    email_col = _normalize_col(df, "email", "e-mail", "почта", "mail")
    if not email_col:
        return 0, 0, 1

    first_col = _normalize_col(df, "first_name", "firstname", "имя", "name", "название")
    last_col = _normalize_col(df, "last_name", "lastname", "фамилия", "surname")
    phone_col = _normalize_col(df, "phone", "телефон", "тел", "mobile")

    added = skipped = errors = 0

    for _, row in df.iterrows():
        try:
            email = str(row[email_col]).strip().lower()
            if not email or email == "nan":
                continue

            if Contact.query.filter_by(email=email).first():
                skipped += 1
                continue

            contact = Contact(
                email=email,
                first_name=str(row[first_col]).strip() if first_col else "",
                last_name=str(row[last_col]).strip() if last_col else "",
                phone=str(row[phone_col]).strip() if phone_col else "",
                source="manual",
            )
            # Убираем "nan"
            for field in ("first_name", "last_name", "phone"):
                if getattr(contact, field) == "nan":
                    setattr(contact, field, "")

            db.session.add(contact)
            added += 1
        except Exception:
            errors += 1

    db.session.commit()
    return added, skipped, errors


def _slug_to_name(slug):
    return slug.replace("-", " ").replace("_", " ").title()


def import_products_from_file(file):
    filename = file.filename.lower()
    content = file.read()

    df = pd.DataFrame()

    # Excel
    if filename.endswith(".xlsx") or filename.endswith(".xls"):
        df = pd.read_excel(io.BytesIO(content))
    else:
        # Попробуем с заголовками и без, разные разделители
        for enc in ("utf-8", "utf-8-sig", "cp1251", "latin-1"):
            for sep in (";", ",", "\t"):
                try:
                    raw = pd.read_csv(io.StringIO(content.decode(enc)), sep=sep, header=None)
                    if len(raw.columns) >= 1 and len(raw) > 0:
                        df = raw
                        break
                except Exception:
                    continue
            if not df.empty:
                break

    if df.empty:
        return 0, 0

    added = skipped = 0

    for _, row in df.iterrows():
        try:
            raw_name = str(row.iloc[0]).strip()
            if not raw_name or raw_name == "nan":
                continue

            # Если выглядит как slug (нет пробелов, есть дефисы) — конвертируем
            if " " not in raw_name and ("-" in raw_name or raw_name.islower()):
                name = _slug_to_name(raw_name)
            else:
                name = raw_name

            # URL — вторая колонка если есть
            url = ""
            if len(row) > 1:
                url = str(row.iloc[1]).strip()
                if url == "nan" or not url.startswith("http"):
                    url = ""

            if Product.query.filter_by(name=name).first():
                skipped += 1
                continue

            db.session.add(Product(name=name, url=url))
            added += 1
        except Exception:
            skipped += 1

    db.session.commit()
    return added, skipped
