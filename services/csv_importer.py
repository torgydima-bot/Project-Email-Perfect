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
            try:
                return pd.read_csv(io.StringIO(content.decode(enc)))
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


def import_products_from_file(file):
    df = _read_df(file)
    if df.empty:
        return 0, 0

    name_col = _normalize_col(df, "name", "название", "product", "продукт", "наименование")
    url_col = _normalize_col(df, "url", "link", "ссылка", "href")

    if not name_col:
        return 0, 0

    added = skipped = 0

    for _, row in df.iterrows():
        try:
            name = str(row[name_col]).strip()
            if not name or name == "nan":
                continue

            if Product.query.filter_by(name=name).first():
                skipped += 1
                continue

            url = str(row[url_col]).strip() if url_col else ""
            if url == "nan":
                url = ""

            product = Product(name=name, url=url)
            db.session.add(product)
            added += 1
        except Exception:
            skipped += 1

    db.session.commit()
    return added, skipped
