from io import BytesIO
from pathlib import Path
from datetime import datetime

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

BASE_DIR = Path(__file__).resolve().parent.parent


def _register_korean_font():
    """
    프로젝트 내부 한글 폰트 탐색
    우선순위:
    1) assets/fonts/NanumGothic.ttf
    2) fonts/NanumGothic.ttf
    """
    font_candidates = [
        BASE_DIR / "assets" / "fonts" / "NanumGothic.ttf",
        BASE_DIR / "fonts" / "NanumGothic.ttf",
    ]

    for font_path in font_candidates:
        if font_path.exists():
            pdfmetrics.registerFont(TTFont("KoreanFont", str(font_path)))
            return "KoreanFont", str(font_path)

    return None, None


def _safe_text(x):
    if x is None:
        return "-"
    return str(x)


def _fmt_num(x):
    try:
        return f"{float(x):,.0f}"
    except Exception:
        return _safe_text(x)


def _fmt_pct(x):
    try:
        return f"{float(x):.1f}%"
    except Exception:
        return _safe_text(x)


def _select_ml_pdf_columns(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame()

    preferred_cols = [
        "고객ID",
        "churn_prob",
        "rule_risk",
        "model_risk",
        "Final_Segment",
        "reason",
        "recommended_action",
    ]
    existing = [c for c in preferred_cols if c in df.columns]
    if existing:
        return df[existing].copy()

    fallback_cols = [
        "고객ID",
        "이탈확률",
        "규칙위험",
        "모델위험",
        "세그먼트",
        "사유",
        "추천액션",
    ]
    existing_fb = [c for c in fallback_cols if c in df.columns]
    if existing_fb:
        return df[existing_fb].copy()

    return df.head(20).copy()


def _df_to_table_data(df: pd.DataFrame, max_rows: int = 20):
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return [["데이터 없음"]]

    show = df.head(max_rows).copy()

    for col in show.columns:
        show[col] = show[col].apply(lambda v: _safe_text(v))

    return [list(show.columns)] + show.values.tolist()


def _build_col_widths(data, total_width_mm=245):
    """
    컬럼 수에 따라 대략적인 폭 자동 분배
    """
    if not data or not data[0]:
        return None

    n_cols = len(data[0])
    total_width = total_width_mm * mm
    each = total_width / max(n_cols, 1)
    return [each] * n_cols


def _make_table(data, font_name="KoreanFont", col_widths=None):
    if col_widths is None:
        col_widths = _build_col_widths(data)

    table = Table(data, colWidths=col_widths, repeatRows=1)

    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("LEADING", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("TOPPADDING", (0, 0), (-1, 0), 5),
        ("WORDWRAP", (0, 0), (-1, -1), "CJK"),
    ])
    table.setStyle(style)
    return table


def build_report_pdf(
    title: str,
    user_name: str,
    run_name: str,
    kpi: dict,
    category_df: pd.DataFrame | None = None,
    segment_df: pd.DataFrame | None = None,
    customer_df: pd.DataFrame | None = None,
    ml_df: pd.DataFrame | None = None,
    refund_df: pd.DataFrame | None = None,
    inventory_df: pd.DataFrame | None = None,
) -> bytes:
    font_name, font_path = _register_korean_font()

    if not font_name:
        raise FileNotFoundError(
            "한글 폰트 파일을 찾을 수 없습니다. "
            "'assets/fonts/NanumGothic.ttf' 또는 'fonts/NanumGothic.ttf' 경로에 폰트를 넣어주세요."
        )

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="TitleKo",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=18,
        leading=22,
        spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="HeadingKo",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=12,
        leading=15,
        spaceAfter=8,
        spaceBefore=8,
    ))
    styles.add(ParagraphStyle(
        name="BodyKo",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=9,
        leading=12,
    ))

    story = []

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    story.append(Paragraph(title, styles["TitleKo"]))
    story.append(Paragraph(f"사용자: {_safe_text(user_name)}", styles["BodyKo"]))
    story.append(Paragraph(f"저장 이름: {_safe_text(run_name)}", styles["BodyKo"]))
    story.append(Paragraph(f"생성 시각: {generated_at}", styles["BodyKo"]))
    story.append(Spacer(1, 8))

    # 1. KPI
    story.append(Paragraph("1. 핵심 요약", styles["HeadingKo"]))
    kpi_rows = [
        ["지표", "값"],
        ["총 고객 수", _fmt_num(kpi.get("total_customers", 0))],
        ["고위험 고객 비중", _fmt_pct(kpi.get("high_ratio", 0))],
        ["평균 위험 점수", _fmt_num(kpi.get("avg_risk", 0))],
        ["예상 매출 이탈", _fmt_num(kpi.get("expected_loss", 0))],
    ]
    story.append(_make_table(kpi_rows, font_name=font_name, col_widths=[60 * mm, 120 * mm]))
    story.append(Spacer(1, 10))

    # 2. 세그먼트 요약
    story.append(Paragraph("2. 세그먼트 요약", styles["HeadingKo"]))
    seg_data = _df_to_table_data(segment_df, 15)
    story.append(_make_table(seg_data, font_name=font_name))
    story.append(Spacer(1, 10))

    # 3. 카테고리 위험도
    story.append(Paragraph("3. 카테고리 위험도", styles["HeadingKo"]))
    cat_data = _df_to_table_data(category_df, 15)
    story.append(_make_table(cat_data, font_name=font_name))
    story.append(Spacer(1, 10))

    # 4. 고객 위험도 상위 목록
    story.append(Paragraph("4. 고객 위험도 상위 목록", styles["HeadingKo"]))
    cust_data = _df_to_table_data(customer_df, 20)
    story.append(_make_table(cust_data, font_name=font_name))
    story.append(PageBreak())

    # 5. ML 이탈예측 결과
    story.append(Paragraph("5. ML 이탈예측 결과", styles["HeadingKo"]))
    ml_pdf_df = _select_ml_pdf_columns(ml_df)
    ml_data = _df_to_table_data(ml_pdf_df, 20)
    story.append(_make_table(ml_data, font_name=font_name))
    story.append(Spacer(1, 10))

    # 6. 환불 분석
    story.append(Paragraph("6. 환불 분석", styles["HeadingKo"]))
    refund_data = _df_to_table_data(refund_df, 20)
    story.append(_make_table(refund_data, font_name=font_name))
    story.append(Spacer(1, 10))

    # 7. 재고 권장안
    story.append(Paragraph("7. 재고 권장안", styles["HeadingKo"]))
    inv_data = _df_to_table_data(inventory_df, 20)
    story.append(_make_table(inv_data, font_name=font_name))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf