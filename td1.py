import streamlit as st
import pdfplumber
import pandas as pd
from google import genai
import json
import re
import plotly.express as px
import io
import pymupdf
from PIL import Image
import pytesseract
import platform

# ==========================================
# ⚙️ إعدادات محرك الـ OCR (خاص بنظام الويندوز)
# ==========================================
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# ==========================================
# ⚙️ إعداد الصفحة
# ==========================================
st.set_page_config(page_title="المحلل المالي الذكي | AI Financial Analyzer", layout="wide")

# ==========================================
# 🎛️ القائمة الجانبية واختيار اللغة
# ==========================================
with st.sidebar:
    lang_choice = st.selectbox("🌐 اختر اللغة / Choose Language / Choisir la langue:",
                               ["العربية", "Français", "English"])

# --- قاموس اللغات (Translations Dictionary) ---
langs = {
    "العربية": {
        "title": "🤖 المحلل المالي الذكي للتقارير (TD)",
        "subtitle": "ارفع التقرير المالي (PDF) ليقوم الذكاء الاصطناعي بقراءته، استخراج بيانات الشركة وحساب النسب المالية، ثم تقديم تقرير وصفي شامل.",
        "api_h": "⚙ إعدادات الذكاء الاصطناعي",
        "api_l": "أدخل مفتاح Google Gemini API:",
        "api_i": "🔑 المفتاح ضروري لعملية التحليل واستخراج البيانات.",
        "up": "📂 ارفع التقرير المالي بصيغة PDF",
        "btn": "🚀 ابدأ التحليل المالي",
        "spin1": "⏳ جاري قراءة الملف واستخراج الجداول...",
        "sub1": "📑 الجداول المنظمة المستخرجة من التقرير",
        "exp1": "📑 عرض الجداول الخام المستخرجة (انقر للتوسيع)",
        "tbl_p": "📊 جدول مستخرج من الصفحة",
        "no_tbl": "لا توجد جداول مهيكلة واضحة للعرض.",
        "ocr_w": "⚠️ الملف مصور (Scan). جاري تفعيل محرك الـ OCR لقراءته...",
        "ocr_s": "✅ تمت قراءة الصورة بنجاح عبر محرك الذكاء البصري.",
        "ocr_e1": "❌ تنبيه: محرك القراءة البصرية (Tesseract) غير مثبت.",
        "ocr_e2": "⚠️ تعذرت قراءة الصورة:",
        "txt_info": "سيتم الاعتماد على قراءة النصوص الذكية لغياب الجداول المهيكلة.",
        "spin2": "🤖 الذكاء الاصطناعي يستخرج بيانات الشركة ويحلل النسب...",
        "comp_info_title": "🏢 بطاقة تعريف الشركة (مستخرجة من التقرير)",
        "comp_name": "اسم الشركة:", "comp_sec": "قطاع النشاط:", "comp_cap": "رأس المال:", "comp_yr": "السنة المالية:",
        "sub2": "💡 المؤشرات والنسب المالية مع التحليل المباشر",
        "exp2": "📚 القواعد الأكاديمية للنسب المالية (دليل المراجعة للطلبة)",
        "no_val": "لم يتمكن الذكاء الاصطناعي من استخراج أرقام مالية دقيقة.",
        "sub3": "📈 التصور المرئي للبيانات (Charts)",
        "ch_t1": "النسب والمؤشرات المالية",
        "ch_t2": "التوزيع الهيكلي للأرقام",
        "no_ch1": "لا توجد قيم رقمية صالحة للرسم البياني.",
        "no_ch2": "البيانات المستخرجة لا تسمح برسم المخطط الدائري.",
        "no_ch3": "⚠️ تعذر رسم المخططات: لم يعثر الذكاء الاصطناعي على أرقام كافية.",
        "sub4": "📝 التقرير المالي الوصفي (تحليل الخبير الاصطناعي)",
        "err": "حدث خطأ غير متوقع أثناء التحليل:",
        "prompt_lang": "العربية (Arabic)",
        "col_cat": "الفئة", "col_ind": "المؤشر", "col_form": "قاعدة الحساب", "col_val": "القيمة", "col_unit": "الوحدة",
        "col_an": "التحليل المقابل",
        "acad_text": """
**💧 نسب السيولة** (تقيس قدرة الشركة على سداد ديونها قصيرة الأجل):
* **نسبة التداول:** الأصول المتداولة ÷ الالتزامات المتداولة.
* **نسبة السيولة السريعة:** (الأصول المتداولة - المخزون) ÷ الالتزامات المتداولة.
* **السيولة النقدية:** النقد وما يعادله ÷ الالتزامات المتداولة.

**📈 نسب الربحية** (تقيس كفاءة الشركة في تحقيق الأرباح):
* **هامش صافي الربح:** صافي الربح ÷ إجمالي المبيعات.
* **العائد على الأصول (ROA):** صافي الربح ÷ إجمالي الأصول.
* **العائد على حقوق الملكية (ROE):** صافي الربح ÷ حقوق الملكية.

**📉 نسب النشاط (الكفاءة)** (تقيس سرعة استغلال الأصول):
* **معدل دوران المخزون:** تكلفة البضاعة المباعة ÷ متوسط المخزون.
* **معدل دوران الذمم المدينة:** المبيعات الآجلة ÷ متوسط الذمم المدينة.
* **معدل دوران الأصول الإجمالية:** إجمالي المبيعات ÷ إجمالي الأصول.

**⚠️ نسب المديونية** (تقيس الاعتماد على التمويل الخارجي):
* **نسبة الدين إلى الإجمالي:** إجمالي الديون ÷ إجمالي الأصول.
* **نسبة الدين إلى حقوق الملكية:** إجمالي الديون ÷ حقوق الملكية.
* **تغطية الفوائد:** الأرباح قبل الفوائد والضرائب ÷ مصروف الفوائد.

**💡 نسب السوق** (تقيم الأداء بالنسبة للمستثمرين):
* **ربحية السهم (EPS):** صافي الربح ÷ عدد الأسهم المصدرة.
* **مضاعف الربحية (P/E):** سعر السهم ÷ ربحية السهم.
* **عائد التوزيعات:** توزيعات الأرباح للسهم ÷ سعر السهم.
"""
    },
    "Français": {
        "title": "🤖 Analyseur Financier Intelligent (TD)",
        "subtitle": "Téléchargez le rapport financier (PDF) pour extraire le profil de l'entreprise, calculer les ratios et générer un rapport descriptif.",
        "api_h": "⚙️ Paramètres IA",
        "api_l": "Entrez la clé Google Gemini API :",
        "api_i": "🔑 La clé est nécessaire pour l'analyse des données.",
        "up": "📂 Téléchargez le rapport financier (PDF)",
        "btn": "🚀 Lancer l'analyse financière",
        "spin1": "⏳ Lecture du fichier et extraction des tableaux...",
        "sub1": "📑 Tableaux extraits du rapport",
        "exp1": "📑 Afficher les tableaux bruts (Cliquez pour développer)",
        "tbl_p": "📊 Tableau extrait de la page",
        "no_tbl": "Aucun tableau structuré clair à afficher.",
        "ocr_w": "⚠️ Fichier scanné. Activation de l'OCR...",
        "ocr_s": "✅ Image lue avec succès via l'IA visuelle.",
        "ocr_e1": "❌ Attention : Tesseract OCR n'est pas installé.",
        "ocr_e2": "⚠️ Impossible de lire l'image :",
        "txt_info": "L'analyse se basera sur le texte brut faute de tableaux structurés.",
        "spin2": "🤖 L'IA extrait les infos et analyse les ratios...",
        "comp_info_title": "🏢 Fiche d'Identité de l'Entreprise (Extraite)",
        "comp_name": "Nom :", "comp_sec": "Secteur :", "comp_cap": "Capital :", "comp_yr": "Exercice :",
        "sub2": "💡 Indicateurs et Ratios Financiers avec Analyse",
        "exp2": "📚 Règles Académiques des Ratios Financiers (Guide)",
        "no_val": "L'IA n'a pu extraire aucun chiffre financier précis.",
        "sub3": "📈 Visualisation des Données (Graphiques)",
        "ch_t1": "Ratios et Indicateurs (Calculés)",
        "ch_t2": "Répartition Structurelle des Valeurs",
        "no_ch1": "Aucune valeur numérique valide pour le graphique.",
        "no_ch2": "Les données ne permettent pas de générer un graphique circulaire.",
        "no_ch3": "⚠️ Impossible de tracer les graphiques : manque de données.",
        "sub4": "📝 Rapport Financier Descriptif (Analyse IA)",
        "err": "Une erreur inattendue est survenue :",
        "prompt_lang": "Français (French)",
        "col_cat": "Catégorie", "col_ind": "Indicateur", "col_form": "Formule de Calcul", "col_val": "Valeur",
        "col_unit": "Unité", "col_an": "Analyse Correspondante",
        "acad_text": """
**💧 Ratios de Liquidité** (Capacité à payer les dettes à court terme) :
* **Liquidité Générale :** Actifs Circulants ÷ Passifs Circulants.
* **Liquidité Réduite :** (Actifs Circulants - Stocks) ÷ Passifs Circulants.
* **Liquidité Immédiate :** Trésorerie ÷ Passifs Circulants.

**📈 Ratios de Rentabilité** (Efficacité à générer des profits) :
* **Marge Nette :** Bénéfice Net ÷ Chiffre d'Affaires.
* **Rendement des Actifs (ROA) :** Bénéfice Net ÷ Total des Actifs.
* **Rendement des Capitaux Propres (ROE) :** Bénéfice Net ÷ Capitaux Propres.

**📉 Ratios d'Activité** (Efficacité de l'utilisation des actifs) :
* **Rotation des Stocks :** Coût des Ventes ÷ Stock Moyen.
* **Rotation des Créances :** Ventes à Crédit ÷ Créances Moyennes.
* **Rotation des Actifs :** Chiffre d'Affaires ÷ Total des Actifs.

**⚠️ Ratios d'Endettement** (Dépendance aux financements) :
* **Taux d'Endettement :** Total des Dettes ÷ Total des Actifs.
* **Dettes sur Capitaux Propres :** Total des Dettes ÷ Capitaux Propres.
* **Couverture des Intérêts :** EBIT ÷ Charges d'Intérêts.

**💡 Ratios de Marché** (Performance boursière) :
* **Bénéfice par Action (BPA) :** Bénéfice Net ÷ Nombre d'Actions.
* **Ratio Cours/Bénéfice (PER) :** Prix de l'Action ÷ BPA.
* **Rendement du Dividende :** Dividende par Action ÷ Prix de l'Action.
"""
    },
    "English": {
        "title": "🤖 Smart Financial Analyzer (TD)",
        "subtitle": "Upload the financial report (PDF) to extract the company profile, calculate ratios, and generate a descriptive report.",
        "api_h": "⚙️ AI Settings",
        "api_l": "Enter Google Gemini API Key:",
        "api_i": "🔑 The key is required for data analysis.",
        "up": "📂 Upload Financial Report (PDF)",
        "btn": "🚀 Start Financial Analysis",
        "spin1": "⏳ Reading file and extracting tables...",
        "sub1": "📑 Extracted Structured Tables",
        "exp1": "📑 View Raw Extracted Tables (Click to Expand)",
        "tbl_p": "📊 Table extracted from page",
        "no_tbl": "No clear structured tables to display.",
        "ocr_w": "⚠️ Scanned file detected. Activating OCR...",
        "ocr_s": "✅ Image successfully read via visual AI.",
        "ocr_e1": "❌ Warning: Tesseract OCR is not installed.",
        "ocr_e2": "⚠️ Failed to read image:",
        "txt_info": "Analysis will rely on raw text due to missing structured tables.",
        "spin2": "🤖 AI is extracting info and analyzing ratios...",
        "comp_info_title": "🏢 Company Profile (Extracted from Report)",
        "comp_name": "Name:", "comp_sec": "Sector:", "comp_cap": "Capital:", "comp_yr": "Fiscal Year:",
        "sub2": "💡 Financial Indicators & Ratios with Analysis",
        "exp2": "📚 Academic Rules for Financial Ratios (Guide)",
        "no_val": "The AI could not extract precise financial figures.",
        "sub3": "📈 Data Visualization (Charts)",
        "ch_t1": "Calculated Ratios & Indicators",
        "ch_t2": "Structural Distribution of Values",
        "no_ch1": "No valid numerical values for the chart.",
        "no_ch2": "Extracted data does not support a pie chart.",
        "no_ch3": "⚠️ Cannot plot charts: Insufficient data.",
        "sub4": "📝 Descriptive Financial Report (AI Analysis)",
        "err": "An unexpected error occurred:",
        "prompt_lang": "English",
        "col_cat": "Category", "col_ind": "Indicator", "col_form": "Calculation Formula", "col_val": "Value",
        "col_unit": "Unit", "col_an": "Analysis",
        "acad_text": """
**💧 Liquidity Ratios** (Ability to pay short-term debts):
* **Current Ratio:** Current Assets ÷ Current Liabilities.
* **Quick Ratio:** (Current Assets - Inventory) ÷ Current Liabilities.
* **Cash Ratio:** Cash & Equivalents ÷ Current Liabilities.

**📈 Profitability Ratios** (Efficiency in generating profit):
* **Net Profit Margin:** Net Profit ÷ Total Revenue.
* **Return on Assets (ROA):** Net Profit ÷ Total Assets.
* **Return on Equity (ROE):** Net Profit ÷ Shareholders' Equity.

**📉 Activity Ratios** (Efficiency of asset utilization):
* **Inventory Turnover:** COGS ÷ Average Inventory.
* **Receivables Turnover:** Credit Sales ÷ Average Receivables.
* **Asset Turnover:** Total Revenue ÷ Total Assets.

**⚠️ Leverage Ratios** (Reliance on external financing):
* **Debt Ratio:** Total Debt ÷ Total Assets.
* **Debt-to-Equity:** Total Debt ÷ Shareholders' Equity.
* **Interest Coverage:** EBIT ÷ Interest Expense.

**💡 Market Ratios** (Performance for investors):
* **Earnings Per Share (EPS):** Net Profit ÷ Number of Shares.
* **Price-to-Earnings (P/E):** Share Price ÷ EPS.
* **Dividend Yield:** Dividend Per Share ÷ Share Price.
"""
    }
}

t = langs[lang_choice]

with st.sidebar:
    st.header(t["api_h"])
    api_key = st.text_input(t["api_l"], type="password")
    st.info(t["api_i"])

# ==========================================
# 🎨 إعدادات التوجيه (RTL / LTR) الفائقة
# ==========================================
if lang_choice == "العربية":
    st.markdown(f"""
    <style>
        .stApp, .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, div, span, li, ul, ol, table, th, td {{
            direction: rtl !important;
            text-align: right !important;
        }}
        .js-plotly-plot .plotly, .js-plotly-plot .plotly * {{ direction: ltr !important; }}
        .ai-report-container {{
            background-color: #161b22; padding: 25px; border-radius: 10px; border-right: 6px solid #FFD700;
            color: #ffffff; font-size: 16px; line-height: 1.8; margin-top: 15px; direction: rtl !important; text-align: right !important;
        }}
        .ai-report-container * {{ color: #ffffff !important; }}
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <style>
        .stApp, .stMarkdown, .stText, p, h1, h2, h3, h4, h5, h6, div, span, li, ul, ol, table, th, td {{
            direction: ltr !important;
            text-align: left !important;
        }}
        .ai-report-container {{
            background-color: #161b22; padding: 25px; border-radius: 10px; border-left: 6px solid #FFD700;
            color: #ffffff; font-size: 16px; line-height: 1.8; margin-top: 15px; direction: ltr !important; text-align: left !important;
        }}
        .ai-report-container * {{ color: #ffffff !important; }}
    </style>
    """, unsafe_allow_html=True)

st.title(t["title"])
st.markdown(t["subtitle"])


# ==========================================
# 🛡️ نظام الطوارئ الذكي للنماذج
# ==========================================
def call_gemini_robust(client, prompt_text):
    last_error = ""
    best_models = ['gemini-1.5-flash', 'gemini-2.5-flash', 'gemini-pro']

    for model_name in best_models:
        try:
            response = client.chats.create(model=model_name).send_message(prompt_text)
            if response and response.text:
                return response.text
        except Exception as e:
            last_error = str(e)
            continue

    try:
        for m in client.models.list():
            safe_name = m.name.replace("models/", "")
            if "vision" in safe_name or "embedding" in safe_name or "aqa" in safe_name:
                continue
            try:
                response = client.chats.create(model=safe_name).send_message(prompt_text)
                if response and response.text:
                    return response.text
            except Exception as e:
                last_error = str(e)
                continue
    except Exception as e:
        last_error += f" | {str(e)}"

    raise Exception(f"{t['err']} {last_error}")


# ==========================================
# 📥 رفع الملف وبدء التحليل
# ==========================================
uploaded_file = st.file_uploader(t["up"], type="pdf")

if uploaded_file and api_key:
    if st.button(t["btn"]):

        with st.spinner(t["spin1"]):
            extracted_text = ""
            pdf_bytes = uploaded_file.read()
            tables_found = False

            with st.expander(t["exp1"], expanded=False):
                with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                    for i, page in enumerate(pdf.pages):
                        text = page.extract_text()
                        if text:
                            extracted_text += text + "\n"

                        tables = page.extract_tables()
                        for table in tables:
                            if len(table) > 1:
                                tables_found = True
                                raw_cols = table[0]
                                clean_cols = []
                                for j, col in enumerate(raw_cols):
                                    base_name = str(col).strip() if col and str(col).strip() not in ["None",
                                                                                                     ""] else f"col_{j + 1}"
                                    new_name = base_name
                                    counter = 1
                                    while new_name in clean_cols:
                                        new_name = f"{base_name}_{counter}"
                                        counter += 1
                                    clean_cols.append(new_name)

                                df_table = pd.DataFrame(table[1:], columns=clean_cols)
                                st.markdown(f"**{t['tbl_p']} {i + 1}:**")
                                st.dataframe(df_table, use_container_width=True)

                if not tables_found:
                    st.info(t["no_tbl"])

            if not tables_found and not extracted_text.strip():
                st.warning(t["ocr_w"])
                try:
                    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
                    first_page = doc.load_page(0)
                    pix = first_page.get_pixmap(dpi=200)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    extracted_text = pytesseract.image_to_string(img, lang='fra+eng+ara')
                    st.success(t["ocr_s"])
                except pytesseract.TesseractNotFoundError:
                    st.error(t["ocr_e1"])
                except Exception as e:
                    st.error(f"{t['ocr_e2']} {e}")

            if not tables_found and extracted_text.strip():
                st.info(t["txt_info"])

        # --- الخطوة 2: استخراج معلومات الشركة وتحليل النسب ---
        if extracted_text.strip():
            with st.spinner(t["spin2"]):
                try:
                    client = genai.Client(api_key=api_key)

                    prompt_json = f"""
                    Act as a financial expert. You need to extract general company info AND calculate 15 financial ratios.
                    ALL textual outputs (Name, Sector, Category, Indicator, Formula, Analysis) MUST be translated to: {t['prompt_lang']}.

                    CRITICAL: Return a SINGLE JSON object containing EXACTLY TWO KEYS: "Company_Info" and "Financial_Ratios".

                    1. "Company_Info": A JSON object with English keys: "Name", "Sector", "Capital", "Year". 
                       Extract these from the text. Translate the *values* to {t['prompt_lang']}. (If not found, write "N/A").

                    2. "Financial_Ratios": A JSON list of exactly 15 objects. The JSON keys MUST be exactly: "Category", "Indicator", "Formula", "Value", "Unit", "Analysis". 
                       Only the *values* should be translated to {t['prompt_lang']}. If a value cannot be calculated, set "Value" to 0 and state "Data Unavailable" in "Analysis".

                    Required 15 Ratios (Organize into these categories):
                    1. Liquidity (Current, Quick, Cash)
                    2. Profitability (Net Margin, ROA, ROE)
                    3. Activity (Inventory Turnover, Receivables Turnover, Asset Turnover)
                    4. Leverage (Debt to Total, Debt to Equity, Interest Coverage)
                    5. Market (EPS, P/E, Dividend Yield)

                    Expected JSON format:
                    {{
                      "Company_Info": {{
                        "Name": "...", "Sector": "...", "Capital": "...", "Year": "..."
                      }},
                      "Financial_Ratios": [
                        {{
                          "Category": "...", "Indicator": "...", "Formula": "...", "Value": 1.5, "Unit": "...", "Analysis": "..."
                        }}
                      ]
                    }}
                    Do not add Markdown formatting outside the JSON object. Output JSON only.

                    Text: {extracted_text[:7000]}
                    """

                    json_text_raw = call_gemini_robust(client, prompt_json)

                    match = re.search(r'```json(.*?)```', json_text_raw, re.DOTALL)
                    if match:
                        json_text_raw = match.group(1)

                    parsed_data = json.loads(json_text_raw.strip())

                    # استخراج وتجهيز بيانات الشركة
                    company_info = parsed_data.get("Company_Info", {})
                    financial_data = parsed_data.get("Financial_Ratios", [])
                    df_financials = pd.DataFrame(financial_data)

                    # 1. عرض بطاقة تعريف الشركة (Company Info Card)
                    st.divider()
                    st.subheader(t["comp_info_title"])

                    card_border = "border-right" if lang_choice == "العربية" else "border-left"
                    st.markdown(f"""
                    <div style="background-color: #1f242d; padding: 20px; border-radius: 10px; {card_border}: 5px solid #00d2ff; margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 15px;">
                            <div style="flex: 1; min-width: 150px;">
                                <span style="color: #00d2ff; font-size: 14px;">{t['comp_name']}</span><br>
                                <strong style="font-size: 18px; color: #ffffff;">{company_info.get('Name', 'N/A')}</strong>
                            </div>
                            <div style="flex: 1; min-width: 150px;">
                                <span style="color: #00d2ff; font-size: 14px;">{t['comp_sec']}</span><br>
                                <strong style="font-size: 18px; color: #ffffff;">{company_info.get('Sector', 'N/A')}</strong>
                            </div>
                            <div style="flex: 1; min-width: 150px;">
                                <span style="color: #00d2ff; font-size: 14px;">{t['comp_cap']}</span><br>
                                <strong style="font-size: 18px; color: #ffffff;">{company_info.get('Capital', 'N/A')}</strong>
                            </div>
                            <div style="flex: 1; min-width: 150px;">
                                <span style="color: #00d2ff; font-size: 14px;">{t['comp_yr']}</span><br>
                                <strong style="font-size: 18px; color: #ffffff;">{company_info.get('Year', 'N/A')}</strong>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 2. عرض جدول النسب والتحليل
                    st.subheader(t["sub2"])

                    with st.expander(t["exp2"]):
                        st.markdown(t["acad_text"])

                    if not df_financials.empty:
                        rename_map = {
                            "Category": t["col_cat"],
                            "Indicator": t["col_ind"],
                            "Formula": t["col_form"],
                            "Value": t["col_val"],
                            "Unit": t["col_unit"],
                            "Analysis": t["col_an"]
                        }
                        df_display = df_financials.rename(columns=rename_map)
                        st.dataframe(df_display, use_container_width=True)
                    else:
                        st.info(t["no_val"])

                    # --- الخطوة 3: الرسوم البيانية ---
                    st.subheader(t["sub3"])

                    if not df_financials.empty and 'Value' in df_financials.columns and 'Indicator' in df_financials.columns:
                        col1, col2 = st.columns(2)

                        df_financials['Value'] = pd.to_numeric(df_financials['Value'], errors='coerce').fillna(0)
                        df_plot = df_financials[df_financials['Value'] != 0]

                        with col1:
                            if not df_plot.empty:
                                fig_bar = px.bar(df_plot, x='Indicator', y='Value',
                                                 color='Category' if 'Category' in df_plot.columns else 'Indicator',
                                                 title=t["ch_t1"], text_auto='.2s')
                                st.plotly_chart(fig_bar, use_container_width=True)
                            else:
                                st.warning(t["no_ch1"])

                        with col2:
                            if not df_plot.empty:
                                df_pie = df_plot.copy()
                                df_pie['Absolute_Value'] = df_pie['Value'].abs()
                                df_pie_filtered = df_pie[df_pie['Absolute_Value'] > 0]
                                if not df_pie_filtered.empty:
                                    fig_pie = px.pie(df_pie_filtered, names='Indicator', values='Absolute_Value',
                                                     title=t["ch_t2"], hole=0.3)
                                    st.plotly_chart(fig_pie, use_container_width=True)
                                else:
                                    st.info(t["no_ch2"])
                    else:
                        st.warning(t["no_ch3"])

                    # --- الخطوة 4: التقرير الوصفي ---
                    st.divider()
                    st.subheader(t["sub4"])

                    prompt_report = f"""
                    Based on the extracted data: {json.dumps(financial_data, ensure_ascii=False)}
                    Write an academic descriptive report summarizing the company's financial status.
                    - The report MUST be entirely written in {t['prompt_lang']}.
                    - Provide a general conclusion and a final investment recommendation.
                    - Do NOT write headers like "Prepared by Academic Financial Analysis Department". Jump straight into the report.
                    - Do NOT use ANY HTML tags (like <div>, <p>, etc.) in your response. Output pure Markdown.
                    """

                    report_text = call_gemini_robust(client, prompt_report)

                    clean_report = report_text.replace('<div', '').replace('</div>', '').replace(
                        'class="custom-ai-report"', '').strip()

                    st.markdown(f"""
                    <div class="ai-report-container">

                    {clean_report}

                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"{t['err']} {e}")