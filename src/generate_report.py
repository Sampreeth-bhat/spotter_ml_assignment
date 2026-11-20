"""
Generate the submission report as a .docx file.
Run from project root:
    .\\venv\\Scripts\\python.exe src\\generate_report.py
"""

from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime

ROOT = Path(__file__).parent.parent
OUT  = ROOT / "Freight_Rate_Prediction_Report.docx"
CHART = ROOT / "scorer_results" / "candidate_december.png"
EDA_DIST  = ROOT / "scorer_results" / "eda" / "01_rate_distribution.png"
EDA_TIME  = ROOT / "scorer_results" / "eda" / "02_rate_over_time.png"
EDA_EQUIP = ROOT / "scorer_results" / "eda" / "03_rate_by_equipment.png"
EDA_DIST_RATE = ROOT / "scorer_results" / "eda" / "04_distance_vs_rate.png"


# ── Helpers ───────────────────────────────────────────────────────────────────
BRAND = RGBColor(0x06, 0x4A, 0x56)   # Spotter teal

def set_heading_color(paragraph, color=BRAND):
    for run in paragraph.runs:
        run.font.color.rgb = color

def add_colored_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    set_heading_color(h)
    return h

def add_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    # Header row
    hdr = table.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.text = h
        cell.paragraphs[0].runs[0].bold = True
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "064A56")
        shd.set(qn("w:color"), "FFFFFF")
        shd.set(qn("w:val"), "clear")
        tcPr.append(shd)
        cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    # Data rows
    for r_idx, row in enumerate(rows):
        tr = table.rows[r_idx + 1]
        for c_idx, val in enumerate(row):
            cell = tr.cells[c_idx]
            cell.text = str(val)
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Inches(w)
    return table

def add_caption(doc, text):
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].italic = True
    p.runs[0].font.size = Pt(9)
    p.runs[0].font.color.rgb = RGBColor(0x55, 0x55, 0x55)


# ── Build Document ────────────────────────────────────────────────────────────
doc = Document()

# Page margins
section = doc.sections[0]
section.left_margin   = Inches(1.1)
section.right_margin  = Inches(1.1)
section.top_margin    = Inches(1.0)
section.bottom_margin = Inches(1.0)

# Default font
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)

# ── Title Page ────────────────────────────────────────────────────────────────
doc.add_paragraph()
title = doc.add_paragraph("Freight Rate Prediction")
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.runs[0]
run.bold = True
run.font.size = Pt(26)
run.font.color.rgb = BRAND

sub = doc.add_paragraph("Machine Learning Engineer Assessment — Solution Report")
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub.runs[0].font.size = Pt(13)
sub.runs[0].font.color.rgb = RGBColor(0x44, 0x44, 0x44)

doc.add_paragraph()
meta = doc.add_paragraph(f"Candidate: Sampreeth Bhat\nDate: {datetime.date.today().strftime('%B %d, %Y')}")
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
meta.runs[0].font.color.rgb = RGBColor(0x55, 0x55, 0x55)

doc.add_page_break()

# ── 1. Executive Summary ──────────────────────────────────────────────────────
add_colored_heading(doc, "1. Executive Summary")
doc.add_paragraph(
    "This report documents the design, implementation, and results of a machine learning "
    "solution for predicting freight load rates (USD) across US trucking lanes. "
    "A LightGBM regression model was trained on 48,000 historical loads spanning "
    "January to October 2025, using a strict temporal train/validation split to prevent "
    "data leakage. The model achieves an R\u00b2 of 0.81 on a held-out October 2025 validation "
    "set, with an RMSE of $668.69 and a MAPE of 8.72%. Final predictions were generated "
    "for 12,000 unseen loads (November 2025) and for all 31 days of December 2025 on a "
    "fixed lane (Lexington \u2192 Fort Wayne)."
)

# ── 2. Data Overview ──────────────────────────────────────────────────────────
add_colored_heading(doc, "2. Data Overview")
doc.add_paragraph("Three datasets were provided for this assessment:")
add_table(doc,
    ["File", "Rows", "Purpose"],
    [
        ["train-test.csv",                      "48,000", "Labelled training data (Jan\u2013Oct 2025)"],
        ["validation.csv",                      "12,000", "Unlabelled validation set (Nov 2025)"],
        ["december-chart-inputs.csv",           "31",     "Fixed lane, one row per day (Dec 2025)"],
        ["validation-predictions-template.csv", "12,000", "Output template to fill"],
    ],
    col_widths=[2.4, 0.8, 3.0]
)
doc.add_paragraph()

add_colored_heading(doc, "2.1 Feature Schema", level=2)
doc.add_paragraph("Each row in the training data contains the following features:")
add_table(doc,
    ["Column", "Type", "Description"],
    [
        ["load_id",       "string",  "Unique load identifier"],
        ["pickup",        "string",  "Origin city (64 unique cities)"],
        ["delivery",      "string",  "Destination city (64 unique cities)"],
        ["pickup_lat/lon","float",   "Origin GPS coordinates"],
        ["delivery_lat/lon","float", "Destination GPS coordinates"],
        ["distance",      "float",   "Haul distance in miles"],
        ["equipment",     "string",  "Trailer type: Dry Van, Reefer, Flatbed"],
        ["weight",        "float",   "Load weight in pounds"],
        ["date",          "date",    "Shipment pickup date"],
        ["market_index",  "float",   "Market conditions index (\u223c0.88\u20131.01)"],
        ["quote_signal",  "float",   "Demand / quote activity signal"],
        ["posted_rate",   "float",   "Target \u2014 load rate in USD"],
    ],
    col_widths=[1.6, 0.8, 3.8]
)

doc.add_page_break()

# ── 3. Exploratory Data Analysis ─────────────────────────────────────────────
add_colored_heading(doc, "3. Exploratory Data Analysis")

add_colored_heading(doc, "3.1 Target Variable", level=2)
doc.add_paragraph(
    "The posted_rate (target) ranges from $57.22 to $25,533.00 with a mean of $2,374 and "
    "a right-skewed distribution. A log-transform (log1p) was applied to the target during "
    "training to normalise the distribution and improve model fit."
)
add_table(doc,
    ["Statistic", "Value"],
    [
        ["Min",    "$57.22"],
        ["25th %ile", "$1,251.55"],
        ["Median", "$2,030.76"],
        ["Mean",   "$2,373.98"],
        ["75th %ile", "$3,330.75"],
        ["Max",    "$25,533.00"],
        ["Std Dev","$1,486.49"],
    ],
    col_widths=[2.0, 2.0]
)
doc.add_paragraph()
if EDA_DIST.exists():
    doc.add_picture(str(EDA_DIST), width=Inches(5.5))
    add_caption(doc, "Figure 1 \u2014 posted_rate distribution (raw and log-transformed)")

doc.add_paragraph()
add_colored_heading(doc, "3.2 Key Correlations", level=2)
doc.add_paragraph(
    "Distance is by far the strongest predictor of freight rate, with a Pearson correlation "
    "of r\u00a0=\u00a00.91 (explaining ~83% of target variance). The market signals have weak direct "
    "correlations but are captured through interaction terms in the feature set."
)
add_table(doc,
    ["Feature", "Correlation with posted_rate"],
    [
        ["distance",      "0.9085 \u2605 dominant predictor"],
        ["weight",        "0.0348"],
        ["market_index",  "0.0342"],
        ["quote_signal",  "\u22120.0399"],
    ],
    col_widths=[2.2, 3.5]
)
doc.add_paragraph()
if EDA_DIST_RATE.exists():
    doc.add_picture(str(EDA_DIST_RATE), width=Inches(5.5))
    add_caption(doc, "Figure 2 \u2014 Distance vs posted_rate (coloured by equipment type)")

doc.add_paragraph()
add_colored_heading(doc, "3.3 Equipment Analysis", level=2)
doc.add_paragraph(
    "Three equipment types are present. Reefer trailers command the highest median rate "
    "per mile, followed by Flatbed and Dry Van."
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
doc.add_paragraph()
if EDA_TIME.exists():
    doc.add_picture(str(EDA_TIME), width=Inches(5.5))
    add_caption(doc, "Figure 3 \u2014 Average freight rate over time (Jan\u2013Oct 2025)")

doc.add_page_break()

# ── 4. Data Quality Issues ────────────────────────────────────────────────────
add_colored_heading(doc, "4. Data Quality Issues & Handling")
doc.add_paragraph("Two columns contained missing values in the training data:")
add_table(doc,
    ["Column", "Missing Count", "Resolution"],
    [
        ["weight",       "300 rows (0.6%)", "Imputed with column median before feature computation"],
        ["market_index", "374 rows (0.8%)", "Imputed with 1.0 (neutral market baseline)"],
    ],
    col_widths=[1.4, 1.6, 3.2]
)
doc.add_paragraph()
doc.add_paragraph(
    "No duplicate load IDs, no impossible rate values, and no corrupted coordinates were found. "
    "Imputation was applied before log-transforms to prevent NaN propagation through "
    "derived features. A final safety fillna(median) was applied at the end of the "
    "feature pipeline to catch any edge-case NaN values in unseen route pairs."
)

doc.add_page_break()

# ── 5. Data Split Strategy ────────────────────────────────────────────────────
add_colored_heading(doc, "5. Data Split Strategy")
doc.add_paragraph(
    "A strict temporal split was used to preserve the chronological ordering of shipments "
    "and prevent data leakage:"
)
add_table(doc,
    ["Partition", "Date Range", "Rows", "Purpose"],
    [
        ["Training",         "Jan 1 \u2013 Sep 30, 2025", "43,147", "Model fitting"],
        ["Local Validation", "Oct 1 \u2013 Oct 31, 2025", " 4,853", "Hyperparameter selection & model comparison"],
        ["Final Model",      "Jan 1 \u2013 Oct 31, 2025", "48,000", "Retrain best model on all data before final prediction"],
    ],
    col_widths=[1.4, 2.0, 0.8, 2.0]
)
doc.add_paragraph()
doc.add_paragraph(
    "Random K-Fold cross-validation was explicitly avoided \u2014 it would cause data leakage "
    "by training on future data to predict past rates. Walk-forward validation across "
    "four consecutive monthly holdouts confirmed consistent generalisation "
    "(mean RMSE $655.96 \u00b1 $15.11), ruling out a lucky/unlucky single split."
)
doc.add_paragraph()
add_table(doc,
    ["Walk-Forward Fold", "RMSE", "R\u00b2", "MAPE"],
    [
        ["Jan\u2013Jun \u2192 Jul 2025", "$671.95", "0.8006", "7.73%"],
        ["Jan\u2013Jul \u2192 Aug 2025", "$648.07", "0.8069", "7.48%"],
        ["Jan\u2013Aug \u2192 Sep 2025", "$635.13", "0.8262", "6.63%"],
        ["Jan\u2013Sep \u2192 Oct 2025", "$668.69", "0.8086", "8.72%"],
        ["Mean",               "$655.96", "\u2014",      "7.64%"],
    ],
    col_widths=[2.2, 1.0, 0.8, 0.8]
)

doc.add_page_break()

# ── 6. Feature Engineering ────────────────────────────────────────────────────
add_colored_heading(doc, "6. Feature Engineering")
doc.add_paragraph(
    "35 features were engineered from the raw columns. All transformations were computed "
    "strictly from the training partition and applied to the validation/test sets to avoid "
    "leakage."
)
add_table(doc,
    ["Feature Group", "Features", "Count"],
    [
        ["Distance & Weight",  "distance, log_distance, weight, log_weight, distance \u00d7 weight", "5"],
        ["Geographic",         "pickup/delivery lat/lon, lat_delta, lon_delta, haversine_dist, mid_lat/lon, abs deltas", "12"],
        ["Equipment",          "equipment_code (ordinal), one-hot: equip_dry_van, equip_reefer, equip_flatbed", "4"],
        ["Market Signals",     "market_index, quote_signal, market\u00d7quote, market\u00d7distance, quote\u00d7distance", "5"],
        ["Temporal",           "day_of_week, month, week_of_year, day_of_year, quarter, is_weekend, is_holiday, days_since_start", "8"],
        ["Route Encoding",     "route_mean_rate, route_count (computed from training data only)", "2"],
    ],
    col_widths=[1.6, 4.0, 0.6]
)
doc.add_paragraph()
doc.add_paragraph(
    "Top features by LightGBM split importance: route_mean_rate (1,361), quote_signal (961), "
    "day_of_year (896), weight (832), market_index (822), distance \u00d7 weight (818). "
    "Despite distance having the highest raw correlation (r\u00a0=\u00a00.91), it is captured primarily "
    "through six derived interaction features, ranking 15th in raw split count."
)

doc.add_page_break()

# ── 7. Model Selection ────────────────────────────────────────────────────────
add_colored_heading(doc, "7. Model Selection & Training")

add_colored_heading(doc, "7.1 Models Compared", level=2)
doc.add_paragraph(
    "Four regression models were trained and evaluated on the October 2025 holdout. "
    "The log-transformed target (log1p) was used for all gradient boosting models."
)
add_table(doc,
    ["Model", "RMSE", "MAE", "R\u00b2", "MAPE"],
    [
        ["LightGBM \u2705",   "$668.69", "$182.90", "0.8086", "8.72%"],
        ["Ridge",         "$668.75", "$141.65", "0.8086", "6.19%"],
        ["Random Forest", "$681.14", "$172.49", "0.8014", "7.90%"],
        ["XGBoost",       "$683.15", "$206.14", "0.8003", "9.93%"],
    ],
    col_widths=[1.6, 1.0, 1.0, 0.8, 0.8]
)
doc.add_paragraph()

add_colored_heading(doc, "7.2 Why LightGBM", level=2)
doc.add_paragraph(
    "LightGBM was selected as the final model based on the lowest RMSE ($668.69). "
    "It offers several practical advantages for this dataset:"
)
items = [
    "Handles the mix of numeric and categorical-encoded features efficiently via GOSS and EFB",
    "Native support for missing values (useful for the 374 missing market_index rows)",
    "Fast training \u2014 500 trees trained in under 10 seconds on 43,000 rows",
    "Robust to the wide rate range ($57\u2013$25,533) when combined with log-transform",
]
for item in items:
    doc.add_paragraph(item, style="List Bullet")

doc.add_paragraph()
add_colored_heading(doc, "7.3 Overfitting Assessment", level=2)
doc.add_paragraph(
    "The train-vs-validation RMSE gap (Train: $540.88, Val: $668.69, Gap: $127.81) is "
    "consistent with healthy generalisation for tree-based models \u2014 not a sign of "
    "dangerous overfitting. The 83% variance explained by distance creates a natural "
    "performance ceiling; the remaining 17% is driven by noisy market signals that "
    "cannot be reliably extracted further without introducing overfit."
)

doc.add_page_break()

# ── 8. December 2025 Predictions ─────────────────────────────────────────────
add_colored_heading(doc, "8. December 2025 Predictions")
doc.add_paragraph(
    "The final model was used to predict daily freight rates for the fixed lane "
    "Lexington \u2192 Fort Wayne (360 miles, Dry Van, 32,000 lb) for every day in December 2025. "
    "Since market_index and quote_signal are not provided for December, they were estimated "
    "using the mean values from October 2025 (the most recent training month):"
)
add_table(doc,
    ["Signal", "Estimated Value", "Source"],
    [
        ["market_index", "0.9575", "Mean of October 2025 training data"],
        ["quote_signal",  "1.9428", "Mean of October 2025 training data"],
    ],
    col_widths=[1.5, 1.5, 3.2]
)
doc.add_paragraph()
add_table(doc,
    ["Metric", "Value"],
    [
        ["Predicted rate range", "$826.61 \u2013 $848.00"],
        ["Predicted rate mean",  "$843.58"],
        ["Std deviation",        "$5.40"],
    ],
    col_widths=[2.0, 2.0]
)
doc.add_paragraph()
doc.add_paragraph(
    "The narrow band of predictions ($21.39 spread) reflects the fixed nature of the lane \u2014 "
    "distance, equipment, and weight are identical for all 31 rows. Only date-driven temporal "
    "features (day of week, week of year) vary, producing small but meaningful day-to-day "
    "fluctuations in predicted rate."
)
doc.add_paragraph()
if CHART.exists():
    doc.add_picture(str(CHART), width=Inches(5.8))
    add_caption(doc, "Figure 4 \u2014 December 2025 Predicted Load Rate (Lexington \u2192 Fort Wayne)")

doc.add_page_break()

# ── 9. Results Summary ────────────────────────────────────────────────────────
add_colored_heading(doc, "9. Results Summary")
doc.add_paragraph("The scorer validated both output files successfully:")
items2 = [
    "validation_predictions.csv \u2014 12,000 rows (TE-000001 \u2192 TE-012000), all rates positive",
    "december-chart-inputs.csv \u2014 31 rows covering Dec 1\u201331 2025, all constraints satisfied",
    "scorer_results/candidate_december.png \u2014 chart generated successfully",
]
for item in items2:
    doc.add_paragraph(item, style="List Bullet")
doc.add_paragraph()
doc.add_paragraph("Scorer output:")
code = doc.add_paragraph(
    "Validated 12,000 final predictions.\n"
    "Validated 31 fixed December predictions.\n"
    "Created chart: scorer_results/candidate_december.png\n"
    "Final validation metrics are calculated by Spotter after submission."
)
code.style = "No Spacing"
code.runs[0].font.name = "Courier New"
code.runs[0].font.size = Pt(9.5)
code.runs[0].font.color.rgb = RGBColor(0x06, 0x4A, 0x56)

doc.add_page_break()

# ── 10. Conclusion ────────────────────────────────────────────────────────────
add_colored_heading(doc, "10. Conclusion")
doc.add_paragraph(
    "A production-ready LightGBM freight rate prediction pipeline was designed and implemented "
    "end-to-end. Key design decisions:"
)
decisions = [
    "Temporal split (not random K-Fold) to prevent leakage and reflect real deployment conditions",
    "Log-transform of the target to handle the right-skewed rate distribution",
    "35 engineered features across five domains: distance/weight, geography, equipment, market signals, and temporal",
    "Route-level mean rate encoding computed strictly from training data to avoid leakage",
    "Walk-forward validation across four monthly holdouts to confirm consistent generalisation",
    "Retrain on all 48,000 rows before final prediction to maximise training signal",
]
for d in decisions:
    doc.add_paragraph(d, style="List Bullet")
doc.add_paragraph()
doc.add_paragraph(
    "The model explains 80.86% of freight rate variance on unseen data. The primary performance "
    "ceiling is the inherent noisiness of the residual 17% of variance, which is driven by "
    "market signals with low direct correlation to the target. External data sources such as "
    "diesel fuel indices, carrier capacity rejection rates, or weather disruption flags could "
    "improve predictive power further."
)

# ── Save ──────────────────────────────────────────────────────────────────────
doc.save(str(OUT))
print(f"Report saved -> {OUT}")
print(f"File size: {OUT.stat().st_size / 1024:.1f} KB")
