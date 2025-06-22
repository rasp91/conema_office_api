import re
import io

from weasyprint import HTML
from jinja2 import Template

from src.v1.guest_book.schemas import RegisterModel


def generate_form(data: RegisterModel, form_data: str) -> io.BytesIO:
    # Build the HTML template with Jinja2
    html_template = """
    <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {
                    margin-top: 8mm;
                    margin-bottom: 8mm;
                    margin-left: 15mm;
                    margin-right: 15mm;
                }
                body {
                    font-family: sans-serif;
                    font-size: 12px;
                }
                h1, h2, h3, h4, h5, h6 {
                    color: #01579b !important;
                }
                h1 {
                    font-size: 24px;
                }
                hr {
                    border: 1px solid #ccc;
                }
                .ql-align-left {
                    text-align: left;
                }
                .ql-align-center {
                    text-align: center;
                }
                .ql-align-right {
                    text-align: right;
                }
                img {
                    max-width: 70px;
                    height: auto;
                }
                .signature {
                    margin-top: 10px;
                    max-width: 240px;
                    max-height: 120px;
                    border: 1px solid #ccc;
                    display: block;
                }
                .form-group {
                    margin-bottom: 10px;
                }
                .label {
                    font-weight: bold;
                    display: inline-block;
                    min-width: 150px;
                    color: #555;
                }
                .value {
                    display: inline-block;
                    color: #000;
                }
                .section {
                    margin-top: 20px;
                }
                .checkmark {
                    color: green;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <h1>{{ header }}</h1>
            <hr />
            {{ form_details | safe }}
            <hr />
            <div class="section">
                <div class="form-group">
                    <span class="label">{{ first_name_label }}:</span>
                    <span class="value">{{ first_name }}</span>
                </div>
                <div class="form-group">
                    <span class="label">{{ last_name_label }}:</span>
                    <span class="value">{{ last_name }}</span>
                </div>
                <div class="form-group">
                    <span class="label">{{ company_label }}:</span>
                    <span class="value">{{ company }}</span>
                </div>
                <div class="form-group">
                    <span class="label">{{ phone_label }}:</span>
                    <span class="value">{{ phone }}</span>
                </div>
                <div class="form-group">
                    <span class="label">{{ email_label }}:</span>
                    <span class="value">{{ email }}</span>
                </div>
                <div class="form-group">
                    <span class="label">{{ safety_instructions_label }}:</span>
                    <span class="value checkmark">✓ {{ safety_instructions }}</span>
                </div>
                <div class="form-group">
                    <span class="label">{{ gdpr_consent_label }}:</span>
                    <span class="value checkmark">✓ {{ gdpr_consent }}</span>
                </div>
                <div class="form-group">
                    <span class="label">{{ signature_label }}:</span>
                    <br />
                    <img class="signature" src="{{ signature_data }}" alt="Signature"/>
                </div>
            </div>
        </body>
    </html>
    """
    # Render the HTML template with the provided data
    template = Template(html_template)
    rendered_html = template.render(
        header=data.header,
        form_details=re.sub(r"&nbsp;", " ", form_data).strip(),
        first_name_label=get_field_label("first_name", data.locate),
        first_name=data.name,
        last_name_label=get_field_label("last_name", data.locate),
        last_name=data.surname,
        company_label=get_field_label("company", data.locate),
        company=data.company.name,
        phone_label=get_field_label("phone", data.locate),
        phone=data.phone,
        email_label=get_field_label("email", data.locate),
        email=data.email,
        safety_instructions_label=get_field_label("safety_instructions", data.locate),
        safety_instructions=get_field_label("yes" if data.acknowledged else "no", data.locate),
        gdpr_consent_label=get_field_label("gdpr_consent", data.locate),
        gdpr_consent=get_field_label("yes" if data.gdpr else "no", data.locate),
        signature_label=get_field_label("signature", data.locate),
        signature_data=data.signature,
    )
    # Convert the rendered HTML to PDF
    pdf_bytes = HTML(string=rendered_html).write_pdf()
    # Return the PDF as a BytesIO object
    return io.BytesIO(pdf_bytes)


def get_field_label(field_key: str, locale: str = "cs") -> str:
    labels = {
        "first_name": {
            "cs": "Jméno",
            "en": "First Name",
            "de": "Vorname",
        },
        "last_name": {
            "cs": "Příjmení",
            "en": "Last Name",
            "de": "Nachname",
        },
        "company": {
            "cs": "Společnost",
            "en": "Company",
            "de": "Firma",
        },
        "phone": {
            "cs": "Telefonní číslo",
            "en": "Phone Number",
            "de": "Telefonnummer",
        },
        "email": {
            "cs": "E-mail",
            "en": "Email",
            "de": "E-Mail",
        },
        "safety_instructions": {
            "cs": "Bezpečnostní pokyny",
            "en": "Safety Instructions",
            "de": "Sicherheitsanweisungen",
        },
        "gdpr_consent": {
            "cs": "Souhlas GDPR",
            "en": "GDPR Consent",
            "de": "DSGVO-Zustimmung",
        },
        "signature": {
            "cs": "Podpis",
            "en": "Signature",
            "de": "Unterschrift",
        },
        "yes": {
            "cs": "Ano",
            "en": "Yes",
            "de": "Ja",
        },
        "no": {
            "cs": "Ne",
            "en": "No",
            "de": "Nein",
        },
    }

    return labels.get(field_key, {}).get(locale, field_key)
