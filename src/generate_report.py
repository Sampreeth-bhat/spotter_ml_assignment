"""
Generate the submission report as a .docx file.
Run from project root:
    .\\venv\\Scripts\\python.exe src\\generate_report.py
"""

from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime

ROOT  = Path(__file__).parent.parent
OUT   = ROOT / "Freight_Rate_Prediction_Report.docx"
CHART      = ROOT / "scorer_results" / "candidate_december.png"
EDA_DIST   = ROOT / "scorer_results" / "eda" / "01_rate_distribution.png"
EDA_TIME   = ROOT / "scorer_results" / "eda" / "02_rate_over_time.png"
EDA_DIST_RATE = ROOT / "scorer_results" / "eda" / "04_distance_vs_rate.png"

BRAND  = RGBColor(0x06, 0x4A, 0x56)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
GREY   = RGBColor(0x44, 0x44, 0x44)
LGREY  = RGBColor(0x88, 0x88, 0x88)


# ── Spacing helpers ───────────────────────────────────────────────────────────
def set_para_spacing(para, before=0, after=4):
    """Set paragraph spacing in points."""
    pPr = para._p.get_or_add_pPr()
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:before"), str(int(before * 20)))
    spacing.set(qn("w:after"),  str(int(after  * 20)))
    pPr.append(spacing)

def tight_para(doc, text="", bold=False, italic=False, size=11, color=None, align=None):
    p = doc.add_paragraph()
    set_para_spacing(p, before=0, after=3)
    if text:
        run = p.add_run(text)
        run.bold   = bold
        run.italic = italic
        run.font.size = Pt(size)
        if color:
            run.font.color.rgb = color
    if align:
        p.alignment = align
    return p

def add_caption(doc, text):
    p = tight_para(doc, text, italic=True, size=9, color=LGREY,
                   align=WD_ALIGN_PARAGRAPH.CENTER)
    set_para_spacing(p, before=2, after=6)

def add_colored_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    set_para_spacing(h, before=10 if level == 1 else 6, after=4)
    for run in h.runs:
        run.font.color.rgb = BRAND
    return h

def add_bullet(doc, text, size=11):
    p = doc.add_paragraph(style="List Bullet")
    set_para_spacing(p, before=0, after=3)
    run = p.add_run(text)
    run.font.size = Pt(size)
    return p

def add_code_block(doc, text):
    p = doc.add_paragraph()
    set_para_spacing(p, before=4, after=4)
    run = p.add_run(text)
    run.font.name = "Courier New"
    run.font.size = Pt(9)
    run.font.color.rgb = BRAND
    # Light grey background shading on the paragraph
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), "F0F0F0")
    pPr.append(shd)

def add_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    # Header
    hdr_row = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr_row.cells[i]
        cell.text = h
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_para_spacing(p, before=2, after=2)
        run = p.runs[0]
        run.bold = True
        run.font.size = Pt(10)
        run.font.color.rgb = WHITE
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "064A56")
        shd.set(qn("w:val"), "clear")
        tcPr.append(shd)
    # Data rows — alternating light shade
    for r_idx, row_data in enumerate(rows):
        fill = "EAF2F3" if r_idx % 2 == 0 else "FFFFFF"
        for c_idx, val in enumerate(row_data):
            cell = table.rows[r_idx + 1].cells[c_idx]
            cell.text = str(val)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            set_para_spacing(p, before=2, after=2)
            if p.runs:
                p.runs[0].font.size = Pt(10)
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            shd = OxmlElement("w:shd")
            shd.set(qn("w:fill"), fill)
            shd.set(qn("w:val"), "clear")
            tcPr.append(shd)
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Inches(w)
    return table

def add_pic(doc, path, width=5.5):
    if Path(path).exists():
        doc.add_picture(str(path), width=Inches(width))
        last = doc.paragraphs[-1]
        last.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_para_spacing(last, before=4, after=0)


# ── Build Document ────────────────────────────────────────────────────────────
doc = Document()

# Page margins
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Inches(1.1)
sec.top_margin  = sec.bottom_margin = Inches(1.0)

# Default style
normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(11)

# ── Title Page ────────────────────────────────────────────────────────────────
for _ in range(3):
    tight_para(doc)

p = tight_para(doc, "Freight Rate Prediction", bold=True, size=28,
               color=BRAND, align=WD_ALIGN_PARAGRAPH.CENTER)
set_para_spacing(p, before=0, after=6)

tight_para(doc, "Machine Learning Engineer Assessment — Solution Report",
           size=13, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER)

tight_para(doc)

tight_para(doc, f"Candidate:  Sampreeth Bhat", size=11, color=GREY,
           align=WD_ALIGN_PARAGRAPH.CENTER)
tight_para(doc, f"Date:  {datetime.date.today().strftime('%B %d, %Y')}", size=11,
           color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER)

doc.add_page_break()

# ── 1. Executive Summary ──────────────────────────────────────────────────────
add_colored_heading(doc, "1. Executive Summary")
p = tight_para(doc,
    "This report documents the design, implementation, and results of a machine learning "
    "solution for predicting freight load rates (USD) across US trucking lanes. "
    "A LightGBM regression model was trained on 48,000 historical loads spanning "
    "January to October 2025, using a strict temporal train/validation split to prevent "
    "data leakage. The model achieves an R\u00b2 of 0.8086 on a held-out October 2025 "
    "validation set, with an RMSE of $668.69 and a MAPE of 8.72%. Final predictions were "
    "generated for 12,000 unseen loads (November 2025) and for all 31 days of December 2025 "
    "on a fixed lane (Lexington \u2192 Fort Wayne), validated and scored successfully."
)

# ── 2. Data Overview ──────────────────────────────────────────────────────────
add_colored_heading(doc, "2. Data Overview")
tight_para(doc, "Three datasets were provided for this assessment:")
add_table(doc,
    ["File", "Rows", "Purpose"],
    [
        ["train-test.csv",                      "48,000", "Labelled training data  (Jan\u2013Oct 2025)"],
        ["validation.csv",                      "12,000", "Unlabelled validation set (Nov 2025)"],
        ["december-chart-inputs.csv",           "31",     "Fixed lane, one row per day in Dec 2025"],
        ["validation-predictions-template.csv", "12,000", "Output template to fill and submit"],
    ],
    col_widths=[2.4, 0.8, 3.1]
)

add_colored_heading(doc, "2.1  Feature Schema", level=2)
add_table(doc,
    ["Column", "Type", "Description"],
    [
        ["load_id",            "string",  "Unique load identifier"],
        ["pickup / delivery",  "string",  "Origin and destination city (64 unique each)"],
        ["pickup/delivery lat/lon", "float", "GPS coordinates of origin and destination"],
        ["distance",           "float",   "Haul distance in miles"],
        ["equipment",          "string",  "Trailer type: Dry Van, Reefer, or Flatbed"],
        ["weight",             "float",   "Load weight in pounds"],
        ["date",               "date",    "Shipment pickup date"],
        ["market_index",       "float",   "Market conditions index (\u223c0.88\u20131.01)"],
        ["quote_signal",       "float",   "Demand / quote activity signal"],
        ["posted_rate",        "float",   "Target \u2014 load rate in USD"],
    ],
    col_widths=[1.8, 0.9, 3.5]
)

doc.add_page_break()

# ── 3. EDA ────────────────────────────────────────────────────────────────────
add_colored_heading(doc, "3. Exploratory Data Analysis")

add_colored_heading(doc, "3.1  Target Variable", level=2)
tight_para(doc,
    "The posted_rate ranges from $57.22 to $25,533.00 with a mean of $2,374 and a "
    "right-skewed distribution. A log-transform (log1p) was applied to the target during "
    "training to normalise the distribution and stabilise variance."
)
add_table(doc,
    ["Statistic", "Value"],
    [
        ["Min",           "$57.22"],
        ["25th percentile", "$1,251.55"],
        ["Median",        "$2,030.76"],
        ["Mean",          "$2,373.98"],
        ["75th percentile", "$3,330.75"],
        ["Max",           "$25,533.00"],
        ["Std Dev",       "$1,486.49"],
    ],
    col_widths=[2.2, 1.8]
)
add_pic(doc, EDA_DIST, width=5.5)
add_caption(doc, "Figure 1 \u2014 posted_rate distribution (raw and log-transformed)")

add_colored_heading(doc, "3.2  Key Correlations", level=2)
tight_para(doc,
    "Distance is the dominant predictor (Pearson r\u00a0=\u00a00.91, explaining ~83% of "
    "target variance). Market signals have weak direct correlations but contribute through "
    "interaction features."
)
add_table(doc,
    ["Feature", "Correlation with posted_rate"],
    [
        ["distance",      "0.9085  \u2605 dominant predictor"],
        ["weight",        "0.0348"],
        ["market_index",  "0.0342"],
        ["quote_signal",  "\u22120.0399"],
    ],
    col_widths=[2.2, 3.5]
)
add_pic(doc, EDA_DIST_RATE, width=5.5)
add_caption(doc, "Figure 2 \u2014 Distance vs posted_rate coloured by equipment type")

add_colored_heading(doc, "3.3  Equipment Analysis", level=2)
tight_para(doc,
    "Reefer trailers command the highest median rate per mile, followed by Flatbed "
    "and Dry Van."
)
add_table(doc,
    ["Equipment", "Count", "Mean Rate", "Median Rate", "Std Dev"],
    [
        ["Dry Van", "27,202 (57%)", "$2,271.55", "$1,953.04", "$1,423.03"],
        ["Reefer",  "12,045 (25%)", "$2,553.64", "$2,196.67", "$1,589.67"],
        ["Flatbed", " 8,753 (18%)", "$2,445.09", "$2,076.81", "$1,505.05"],
    ],
    col_widths=[1.0, 1.3, 1.1, 1.1, 1.0]
)
add_pic(doc, EDA_TIME, width=5.5)
add_caption(doc, "Figure 3 \u2014 Average freight rate over time (Jan\u2013Oct 2025)")

doc.add_page_break()

# ── 4. Data Quality ───────────────────────────────────────────────────────────
add_colored_heading(doc, "4. Data Quality Issues & Handling")
tight_para(doc, "Two columns contained missing values in the training data:")
add_table(doc,
    ["Column", "Missing", "Resolution"],
    [
        ["weight",       "300 rows (0.6%)", "Imputed with column median before feature computation"],
        ["market_index", "374 rows (0.8%)", "Imputed with 1.0 (neutral market baseline)"],
    ],
    col_widths=[1.4, 1.5, 3.3]
)
tight_para(doc,
    "No duplicate load IDs, impossible rates, or corrupt coordinates were found. "
    "Imputation was applied before log-transforms to prevent NaN propagation through "
    "derived features. A final safety fillna(median) was applied at the end of the "
    "feature pipeline to handle any edge-case NaN in unseen route pairs."
)

doc.add_page_break()

# ── 5. Data Split ─────────────────────────────────────────────────────────────
add_colored_heading(doc, "5. Data Split Strategy")
tight_para(doc,
    "A strict temporal split was used to preserve chronological ordering and prevent "
    "data leakage. Random K-Fold cross-validation was explicitly avoided \u2014 it would "
    "allow training on future data to predict past rates."
)
add_table(doc,
    ["Partition", "Date Range", "Rows", "Purpose"],
    [
        ["Training",         "Jan 1 \u2013 Sep 30, 2025", "43,147", "Model fitting"],
        ["Local Validation", "Oct 1 \u2013 Oct 31, 2025", " 4,853", "Model comparison & HP selection"],
        ["Final Model",      "Jan 1 \u2013 Oct 31, 2025", "48,000", "Retrain on all data before final prediction"],
    ],
    col_widths=[1.4, 2.0, 0.8, 2.0]
)

add_colored_heading(doc, "5.1  Walk-Forward Validation", level=2)
tight_para(doc,
    "Walk-forward validation across four consecutive monthly holdouts confirmed "
    "consistent generalisation (mean RMSE $655.96 \u00b1 $15.11), ruling out a "
    "lucky single-split result."
)
add_table(doc,
    ["Fold", "RMSE", "R\u00b2", "MAPE"],
    [
        ["Jan\u2013Jun \u2192 Jul 2025", "$671.95", "0.8006", "7.73%"],
        ["Jan\u2013Jul \u2192 Aug 2025", "$648.07", "0.8069", "7.48%"],
        ["Jan\u2013Aug \u2192 Sep 2025", "$635.13", "0.8262", "6.63%"],
        ["Jan\u2013Sep \u2192 Oct 2025", "$668.69", "0.8086", "8.72%"],
        ["Mean",                        "$655.96", "\u2014",  "7.64%"],
    ],
    col_widths=[2.4, 1.0, 0.8, 0.8]
)

doc.add_page_break()

# ── 6. Features ───────────────────────────────────────────────────────────────
add_colored_heading(doc, "6. Feature Engineering  (35 features)")
tight_para(doc,
    "All transformations were computed strictly from the training partition and "
    "applied to validation/test sets."
)
add_table(doc,
    ["Group", "Features", "Count"],
    [
        ["Distance & Weight",  "distance, log_distance, weight, log_weight, distance \u00d7 weight", "5"],
        ["Geographic",         "pickup/delivery lat/lon, lat_delta, lon_delta, haversine_dist, mid_lat/lon, abs deltas", "12"],
        ["Equipment",          "equipment_code (ordinal), one-hot: Dry Van / Reefer / Flatbed", "4"],
        ["Market Signals",     "market_index, quote_signal, market\u00d7quote, market\u00d7distance, quote\u00d7distance", "5"],
        ["Temporal",           "day_of_week, month, week_of_year, day_of_year, quarter, is_weekend, is_holiday, days_since_start", "8"],
        ["Route Encoding",     "route_mean_rate, route_count  (from training data only)", "2"],
    ],
    col_widths=[1.5, 4.0, 0.7]
)
tight_para(doc,
    "Top features by LightGBM split importance: route_mean_rate (1,361), quote_signal (961), "
    "day_of_year (896), weight (832), market_index (822), distance \u00d7 weight (818)."
)

doc.add_page_break()

# ── 7. Model Selection ────────────────────────────────────────────────────────
add_colored_heading(doc, "7. Model Selection & Training")

add_colored_heading(doc, "7.1  Models Compared", level=2)
tight_para(doc,
    "Four models were trained on the temporal training set and evaluated on the "
    "October 2025 holdout. Log1p target transformation was used for all models."
)
add_table(doc,
    ["Model", "RMSE", "MAE", "R\u00b2", "MAPE"],
    [
        ["LightGBM \u2705",   "$668.69", "$182.90", "0.8086", "8.72%"],
        ["Ridge",             "$668.75", "$141.65", "0.8086", "6.19%"],
        ["Random Forest",     "$681.14", "$172.49", "0.8014", "7.90%"],
        ["XGBoost",           "$683.15", "$206.14", "0.8003", "9.93%"],
    ],
    col_widths=[1.6, 1.0, 1.0, 0.8, 0.8]
)

add_colored_heading(doc, "7.2  Why LightGBM", level=2)
tight_para(doc, "LightGBM was selected as the final model by lowest RMSE. Key advantages:")
for item in [
    "Handles mixed numeric and encoded categorical features efficiently via GOSS and EFB",
    "Natively supports missing values (374 missing market_index rows in training)",
    "Fast training \u2014 500 trees trained in under 10 seconds on 43,000 rows",
    "Robust to wide rate range ($57\u2013$25,533) when combined with log-transform of target",
]:
    add_bullet(doc, item)

add_colored_heading(doc, "7.3  Overfitting Assessment", level=2)
tight_para(doc,
    "The train-vs-validation RMSE gap (Train: $540.88, Val: $668.69, Gap: $127.81) "
    "is consistent with healthy generalisation for tree-based models. The 83% variance "
    "explained by distance creates a natural performance ceiling; the remaining 17% is "
    "driven by noisy market signals that cannot be reliably extracted without overfitting."
)

doc.add_page_break()

# ── 8. December Predictions ───────────────────────────────────────────────────
add_colored_heading(doc, "8. December 2025 Predictions")
tight_para(doc,
    "The final model predicted daily freight rates for the fixed lane "
    "Lexington \u2192 Fort Wayne (360 miles, Dry Van, 32,000 lb) for every day in "
    "December 2025. Since market_index and quote_signal are not provided for December, "
    "they were estimated from October 2025 means \u2014 the most recent training month."
)
add_table(doc,
    ["Signal", "Estimated Value", "Source"],
    [
        ["market_index", "0.9575", "Mean of October 2025 training data"],
        ["quote_signal",  "1.9428", "Mean of October 2025 training data"],
    ],
    col_widths=[1.5, 1.5, 3.2]
)
add_table(doc,
    ["Metric", "Value"],
    [
        ["Predicted rate range", "$826.61 \u2013 $848.00"],
        ["Predicted rate mean",  "$843.58"],
        ["Std deviation",        "$5.40"],
    ],
    col_widths=[2.2, 1.8]
)
tight_para(doc,
    "The narrow $21 spread across 31 days reflects the fixed lane \u2014 distance, "
    "equipment, and weight are identical for every row. Only date-driven temporal features "
    "(day of week, week of year) vary, producing small day-to-day fluctuations."
)
add_pic(doc, CHART, width=5.8)
add_caption(doc, "Figure 4 \u2014 December 2025 Predicted Load Rate  (Lexington \u2192 Fort Wayne)")

doc.add_page_break()

# ── 9. Results ────────────────────────────────────────────────────────────────
add_colored_heading(doc, "9. Results Summary")
tight_para(doc, "The scorer validated both output files successfully:")
for item in [
    "validation_predictions.csv \u2014 12,000 rows (TE-000001 \u2192 TE-012000), all rates positive",
    "december-chart-inputs.csv \u2014 31 rows covering Dec 1\u201331 2025, all constraints satisfied",
    "scorer_results/candidate_december.png \u2014 chart generated successfully",
]:
    add_bullet(doc, item)
tight_para(doc, "Scorer output:")
add_code_block(doc,
    "Validated 12,000 final predictions.\n"
    "Validated 31 fixed December predictions.\n"
    "Created chart: scorer_results/candidate_december.png\n"
    "Final validation metrics are calculated by Spotter after submission."
)

# ── 10. Conclusion ────────────────────────────────────────────────────────────
add_colored_heading(doc, "10. Conclusion")
tight_para(doc,
    "A production-ready LightGBM freight rate prediction pipeline was designed and implemented "
    "end-to-end. Key design decisions:"
)
for item in [
    "Temporal split (not random K-Fold) to prevent leakage and reflect real deployment",
    "Log-transform of target to handle right-skewed rate distribution",
    "35 engineered features across five domains: distance/weight, geography, equipment, market signals, temporal",
    "Route-level mean rate encoding computed strictly from training data to avoid leakage",
    "Walk-forward validation across four monthly holdouts to confirm consistent generalisation",
    "Retrain on all 48,000 rows before final prediction to maximise training signal",
]:
    add_bullet(doc, item)
tight_para(doc,
    "The model explains 80.86% of freight rate variance on unseen data. The primary "
    "performance ceiling is the noisiness of the residual 17% of variance driven by "
    "market signals with low direct correlation to the target. External data sources such "
    "as diesel fuel indices, carrier capacity rejection rates, or weather disruption flags "
    "could improve predictive power further."
)

# ── Save ──────────────────────────────────────────────────────────────────────
doc.save(str(OUT))
print(f"Report saved -> {OUT}")
print(f"File size: {OUT.stat().st_size / 1024:.1f} KB")
