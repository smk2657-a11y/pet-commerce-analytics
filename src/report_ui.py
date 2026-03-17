import streamlit as st
import pandas as pd
from pathlib import Path
from typing import Optional, List, Tuple
from .pdf_export import build_report_pdf

from .analytics import compute_rfm_and_risk
from .storage import save_run, list_runs, get_run, delete_run


# ----------------------------
# Formatting helpers
# ----------------------------
def _fmt_currency(x) -> str:
    try:
        return f"₩{int(round(float(x))):,}"
    except Exception:
        return "-"


def _fmt_int(x) -> str:
    try:
        return f"{int(x):,}"
    except Exception:
        return "-"


def _fmt_float2(x) -> str:
    try:
        return f"{float(x):.2f}"
    except Exception:
        return "-"


def _pick_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    if df is None or df.empty:
        return None
    cols = set(df.columns)
    for c in candidates:
        if c in cols:
            return c
    return None


        
def _safe_qcut(
    s: pd.Series,
    q: int = 5,
    prefix: str = "Q",
    low_label: str = "낮음",
    high_label: str = "높음",
) -> Tuple[pd.Series, int]:
    s = pd.to_numeric(s, errors="coerce")
    s_nonan = s.dropna()
    if s_nonan.nunique() < 2:
        return pd.Series(["-"] * len(s), index=s.index), 1

    try:
        binned = pd.qcut(s, q=q, duplicates="drop")
    except Exception:
        r = s.rank(method="average")
        binned = pd.qcut(r, q=min(q, r.nunique()), duplicates="drop")

    actual_bins = len(binned.cat.categories)

    labels = []
    for i in range(1, actual_bins + 1):
        if i == 1:
            labels.append(f"{prefix}1({low_label})")
        elif i == actual_bins:
            labels.append(f"{prefix}{actual_bins}({high_label})")
        else:
            labels.append(f"{prefix}{i}")

    binned = binned.cat.rename_categories(labels)
    return binned.astype(str), actual_bins


def _plotly_ok() -> bool:
    try:
        import plotly.express as px  # noqa
        return True
    except Exception:
        return False


# ----------------------------
# Storage helpers
# ----------------------------
def _df_to_records(df: pd.DataFrame | None, limit: int = 2000) -> list[dict]:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return []
    tmp = df.head(limit).copy()
    for col in tmp.select_dtypes(include=["datetimetz", "datetime64[ns]", "datetime"]).columns:
        tmp[col] = tmp[col].astype(str)
    return tmp.to_dict(orient="records")


def _pack_report_for_storage(result: dict) -> dict:
    return {
        "kpi": result.get("kpi", {}),
        "forecast": result.get("forecast", {}),
        "category_risk": _df_to_records(result.get("category_risk"), 300),
        "segment_summary": _df_to_records(result.get("segment_summary"), 300),
        "customer_list": _df_to_records(result.get("customer_list"), 500),
        "inventory": _df_to_records(result.get("inventory"), 300),
        "rfm": _df_to_records(result.get("rfm"), 3000),
        "churn_summary": result.get("churn_summary", {}),
        "churn_scored": _df_to_records(result.get("churn_scored"), 500),
        "refund": {
            "refund_rate": float((result.get("refund", {}) or {}).get("refund_rate", 0.0) or 0.0),
            "refund_customers": _df_to_records((result.get("refund", {}) or {}).get("refund_customers"), 300),
            "refund_category": _df_to_records((result.get("refund", {}) or {}).get("refund_category"), 300),
        },
        "refill_cycle_by_category": _df_to_records(result.get("refill_cycle_by_category"), 300),
        "refill_category_group": _df_to_records(result.get("refill_category_group"), 300),
        "multi_pet_customers": _df_to_records(result.get("multi_pet_customers"), 300),
        "pet_insights": result.get("pet_insights", {}),
    }


def _metrics_from_result(result: dict) -> dict:
    df_work = result.get("df_work")
    revenue = int(df_work["매출"].sum()) if isinstance(df_work, pd.DataFrame) and "매출" in df_work.columns else 0
    orders = int(len(df_work)) if isinstance(df_work, pd.DataFrame) else 0
    customers = int(result.get("kpi", {}).get("total_customers", 0) or 0)
    return {"revenue": revenue, "orders": orders, "customers": customers}


def _render_saved_report_summary(saved_report: dict):
    kpi = saved_report.get("kpi", {})
    st.markdown("##### 요약")
    c1, c2, c3 = st.columns(3)
    c1.metric("총 고객 수", f"{int(kpi.get('total_customers', 0)):,}")
    c2.metric("고위험 고객 비중", f"{float(kpi.get('high_ratio', 0.0)):.1f}%")
    c3.metric("평균 위험 점수", f"{float(kpi.get('avg_risk', 0.0)):.0f}")

    st.markdown("##### 카테고리별 위험")
    st.dataframe(pd.DataFrame(saved_report.get("category_risk", [])), use_container_width=True, hide_index=True)

    st.markdown("##### 세그먼트 요약")
    st.dataframe(pd.DataFrame(saved_report.get("segment_summary", [])), use_container_width=True, hide_index=True)

    st.markdown("##### 고객 리스트")
    st.dataframe(pd.DataFrame(saved_report.get("customer_list", [])), use_container_width=True, hide_index=True)


# ----------------------------
# Plotly figures
# ----------------------------
def _plotly_layout_base(fig, title: str):
    fig.update_layout(
        template="plotly_white",
        height=420,
        margin=dict(l=10, r=10, t=60, b=10),
        title=title,
        title_font=dict(size=18, family="Pretendard, Apple SD Gothic Neo, Malgun Gothic, sans-serif"),
        font=dict(family="Pretendard, Apple SD Gothic Neo, Malgun Gothic, sans-serif", size=12),
        legend=dict(title_font=dict(size=12), font=dict(size=12)),
    )
    return fig


def _fig_risk_heatmap(rfm_df: pd.DataFrame):
    import plotly.express as px

    r_col = _pick_col(rfm_df, ["R", "Recency", "최근구매경과", "최근구매경과일", "최근구매경과일수", "recency"])
    f_col = _pick_col(rfm_df, ["F", "Frequency", "구매빈도", "purchase_freq", "frequency"])
    score_col = _pick_col(rfm_df, ["위험도점수", "risk_score", "RiskScore", "score", "위험점수", "위험"])

    if not (r_col and f_col):
        return None

    tmp = rfm_df.copy()
    tmp[r_col] = pd.to_numeric(tmp[r_col], errors="coerce")
    tmp[f_col] = pd.to_numeric(tmp[f_col], errors="coerce")
    if score_col:
        tmp[score_col] = pd.to_numeric(tmp[score_col], errors="coerce")

    tmp = tmp.dropna(subset=[r_col, f_col])
    if len(tmp) < 10:
        return None

    tmp["R_bin"], _ = _safe_qcut(tmp[r_col], q=5, prefix="R", low_label="최근", high_label="오래됨")
    tmp["F_bin"], _ = _safe_qcut(tmp[f_col], q=5, prefix="F", low_label="낮음", high_label="높음")

    if score_col and score_col in tmp.columns:
        pivot = tmp.pivot_table(index="F_bin", columns="R_bin", values=score_col, aggfunc="mean")
        value_title = "평균 위험 점수"
    else:
        pivot = tmp.pivot_table(index="F_bin", columns="R_bin", values=r_col, aggfunc="count")
        value_title = "고객 수"

    pivot = pivot.sort_index()
    fig = px.imshow(pivot, text_auto=".0f", aspect="auto", color_continuous_scale="YlOrRd")
    fig = _plotly_layout_base(fig, "리스크 히트맵 (Recency × Frequency)")
    fig.update_xaxes(title="Recency (→ 오래될수록 위험)")
    fig.update_yaxes(title="Frequency (↑ 높을수록 유지)")
    fig.update_coloraxes(colorbar_title=value_title)
    return fig


def _fig_rfm_scatter(rfm_df: pd.DataFrame):
    import plotly.express as px

    r_col = _pick_col(rfm_df, ["R", "Recency", "최근구매경과", "최근구매경과일", "최근구매경과일수", "recency"])
    m_col = _pick_col(rfm_df, ["M", "Monetary", "누적구매금액", "누적금액", "총매출", "monetary", "주문금액"])
    risk_col = _pick_col(rfm_df, ["위험도", "Risk", "risk", "risk_level"])

    if not (r_col and m_col):
        return None

    tmp = rfm_df.copy()
    tmp[r_col] = pd.to_numeric(tmp[r_col], errors="coerce")
    tmp[m_col] = pd.to_numeric(tmp[m_col], errors="coerce")

    tmp = tmp.dropna(subset=[r_col, m_col])
    if len(tmp) < 10:
        return None

    hover_cols = []
    for c in [r_col, m_col, risk_col]:
        if c and c in tmp.columns and c not in hover_cols:
            hover_cols.append(c)

    df_plot = tmp.sample(min(len(tmp), 2000), random_state=42) if len(tmp) > 2000 else tmp

    fig = px.scatter(
        df_plot,
        x=r_col,
        y=m_col,
        color=risk_col if risk_col else None,
        hover_data=hover_cols,
        opacity=0.75,
    )
    fig = _plotly_layout_base(fig, "RFM 분포 (Recency vs Monetary)")
    fig.update_xaxes(title="최근 구매 경과일 (↑ 오래될수록 위험)")
    fig.update_yaxes(title="누적 구매금액 (↑ 가치)")
    if risk_col:
        fig.update_layout(legend_title_text="위험도")
    fig.update_traces(marker=dict(size=8))
    return fig


def _fig_category_bubble(rfm_df: pd.DataFrame):
    import plotly.express as px

    cat_col = _pick_col(rfm_df, ["카테고리", "category", "Category"])
    m_col = _pick_col(rfm_df, ["M", "Monetary", "누적구매금액", "누적금액", "총매출", "monetary", "주문금액"])
    score_col = _pick_col(rfm_df, ["위험도점수", "risk_score", "RiskScore", "score", "위험점수", "위험"])

    if not (cat_col and m_col):
        return None

    tmp = rfm_df.copy()
    tmp[m_col] = pd.to_numeric(tmp[m_col], errors="coerce")
    if score_col:
        tmp[score_col] = pd.to_numeric(tmp[score_col], errors="coerce")

    tmp = tmp.dropna(subset=[cat_col, m_col])
    if len(tmp) < 10:
        return None

    if score_col and score_col in tmp.columns:
        agg = (
            tmp.groupby(cat_col)
            .agg(매출=(m_col, "sum"), 평균위험=(score_col, "mean"), 고객수=(cat_col, "count"))
            .reset_index()
        )
        y_col = "평균위험"
        y_title = "평균 위험 점수 (↑ 위험)"
    else:
        agg = tmp.groupby(cat_col).agg(매출=(m_col, "sum"), 고객수=(cat_col, "count")).reset_index()
        agg["평균위험"] = agg["고객수"]
        y_col = "평균위험"
        y_title = "고객 수(대체 지표)"

    agg = agg.sort_values("매출", ascending=False).head(12)

    fig = px.scatter(
        agg,
        x="매출",
        y=y_col,
        size="고객수",
        text=cat_col,
        hover_data=[cat_col, "매출", y_col, "고객수"],
    )
    fig = _plotly_layout_base(fig, "카테고리 매출 vs 리스크 (우선순위)")
    fig.update_xaxes(title="카테고리 총매출 (↑ 매출)")
    fig.update_yaxes(title=y_title)
    fig.update_traces(textposition="top center")
    return fig


def _exec_summary_lines(high_ratio, expected_loss, refund_rate, top_seg, top_cat):
    lines = []
    lines.append(f"고위험 고객 비율은 {high_ratio:.1f}%로, 단기 리텐션 개입이 필요한 수준입니다.")
    lines.append(f"예상 매출 이탈 규모는 {_fmt_currency(expected_loss)} 수준으로 추정됩니다.")
    if refund_rate > 0:
        lines.append(f"환불률은 {refund_rate*100:.1f}%로, 이탈 분석과 함께 고객 경험 이슈를 병행 점검할 필요가 있습니다.")
    if top_seg and top_seg != "-":
        lines.append(f"고객군 기준으로는 {top_seg} 세그먼트에 대한 관리 우선순위가 높습니다.")
    if top_cat and top_cat != "-":
        lines.append(f"카테고리 관점에서는 {top_cat} 영역을 먼저 점검하는 것이 좋습니다.")
    return lines[:4]


# ----------------------------
# Main report step
# ----------------------------
def report_step(df_std: pd.DataFrame, user_key: str = "guest"):
    session_user = st.session_state.get("user_key", "guest")
    effective_user_key = session_user if (session_user != "guest" and user_key == "guest") else user_key
    is_member = effective_user_key != "guest"

    if "view_run_id" not in st.session_state:
        st.session_state["view_run_id"] = None
    if "sidebar_run_pick" not in st.session_state:
        st.session_state["sidebar_run_pick"] = "현재 분석"

    # -----------------------
    # Sidebar 먼저 처리
    # -----------------------
    with st.sidebar:
        st.markdown("### 📌 내 분석 기록")

        if not is_member:
            st.caption("로그인하면 분석 기록을 저장하고, 선택하면 본문에서 바로 확인할 수 있어요.")
        else:
            runs = list_runs(effective_user_key)

            if not runs:
                st.caption("저장된 기록이 없습니다. 먼저 분석을 저장해보세요.")
                st.session_state["view_run_id"] = None
                st.session_state["sidebar_run_pick"] = "현재 분석"
            else:
                rid_list = []
                label_map = {}

                for r in runs:
                    rid = r.get("run_id")
                    created = r.get("created_at", "")
                    run_name = (r.get("run_name") or "").strip()
                    m = r.get("metrics", {}) or {}

                    label_title = run_name if run_name else created
                    label = f"{label_title} · 매출 {int(m.get('revenue', 0)):,} · 고객 {int(m.get('customers', 0)):,}"

                    if rid is not None:
                        rid_list.append(rid)
                        label_map[rid] = label

                options = ["현재 분석"] + rid_list
                previous_pick = st.session_state.get("sidebar_run_pick", "현재 분석")
                if previous_pick not in options:
                    previous_pick = "현재 분석"
                    st.session_state["sidebar_run_pick"] = "현재 분석"

                picked = st.selectbox(
                    "저장된 분석 보기",
                    options,
                    index=options.index(previous_pick),
                    format_func=lambda x: "현재 분석" if x == "현재 분석" else label_map.get(x, str(x)),
                    key="sidebar_run_pick_widget",
                )

                if picked != previous_pick:
                    st.session_state["sidebar_run_pick"] = picked
                    st.session_state["view_run_id"] = None if picked == "현재 분석" else picked
                    st.rerun()

                if picked != "현재 분석":
                    c1, c2 = st.columns(2, gap="small")

                    if c1.button("현재 분석 보기", use_container_width=True):
                        st.session_state["view_run_id"] = None
                        st.session_state["sidebar_run_pick"] = "현재 분석"
                        st.rerun()

                    if c2.button("선택 기록 삭제", use_container_width=True):
                        ok = delete_run(effective_user_key, picked)
                        if ok:
                            st.session_state["view_run_id"] = None
                            st.session_state["sidebar_run_pick"] = "현재 분석"
                            st.success("선택한 분석 기록을 삭제했어요.")
                            st.rerun()
                        else:
                            st.error("삭제하지 못했어요.")

        st.divider()

        if st.button("⬅️ 매핑으로 돌아가기", use_container_width=True):
            st.session_state.step = 1
            st.rerun()

        with st.expander("🛠 저장 디버그(문제 있을 때만)", expanded=False):
            st.write("effective_user_key:", effective_user_key)
            db_file = Path("app.db").resolve()
            st.write("db file:", str(db_file))
            st.write("db exists:", db_file.exists())
            st.write("view_run_id:", st.session_state.get("view_run_id"))
            st.write("sidebar_run_pick:", st.session_state.get("sidebar_run_pick"))

    # -----------------------
    # 현재/저장본 결정
    # -----------------------
    selected_run_id = st.session_state.get("view_run_id")
    saved_run = None
    saved_report = None
    saved_metrics = None

    if is_member and selected_run_id is not None:
        try:
            saved_run = get_run(int(selected_run_id))
            if saved_run:
                saved_report = saved_run.get("report", {})
                saved_metrics = saved_run.get("metrics", {})
        except Exception:
            saved_run = None
            saved_report = None
            saved_metrics = None

    showing_saved = saved_report is not None

    st.markdown('<div class="h1">고객 이탈 리스크 분석 리포트</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub">반려동물용품 거래 데이터 기반 고객 행동 및 이탈 위험 분석</div>',
        unsafe_allow_html=True,
    )

    if not showing_saved:
        result = compute_rfm_and_risk(df_std)

        # 기본 빈값
        churn_summary = {}
        churn_scored = pd.DataFrame()
        refund_rate = 0.0
        refund_customers = pd.DataFrame()
        refund_category = pd.DataFrame()
        refill_cycle = pd.DataFrame()
        refill_group = pd.DataFrame()
        multi_pet_df = pd.DataFrame()
        pet_insights = {}

        kpi = result.get("kpi", {})
        cat = result.get("category_risk", pd.DataFrame())
        cust_list = result.get("customer_list", pd.DataFrame())
        seg = result.get("segment_summary", pd.DataFrame())
        forecast = result.get("forecast", {})
        inv = result.get("inventory", pd.DataFrame())
        rfm_df = result.get("rfm", pd.DataFrame())
        metrics = _metrics_from_result(result)
        df_work = result.get("df_work")

        churn_summary = result.get("churn_summary", {}) or {}

        churn_scored = result.get("churn_scored", pd.DataFrame())
        if not isinstance(churn_scored, pd.DataFrame):
            churn_scored = pd.DataFrame()

        refund = result.get("refund", {}) or {}
        refund_rate = float(refund.get("refund_rate", 0.0) or 0.0)

        refund_customers = refund.get("refund_customers", pd.DataFrame())
        if not isinstance(refund_customers, pd.DataFrame):
            refund_customers = pd.DataFrame()

        refund_category = refund.get("refund_category", pd.DataFrame())
        if not isinstance(refund_category, pd.DataFrame):
            refund_category = pd.DataFrame()

        refill_cycle = result.get("refill_cycle_by_category", pd.DataFrame())
        if not isinstance(refill_cycle, pd.DataFrame):
            refill_cycle = pd.DataFrame()

        refill_group = result.get("refill_category_group", pd.DataFrame())
        if not isinstance(refill_group, pd.DataFrame):
            refill_group = pd.DataFrame()

        multi_pet_df = result.get("multi_pet_customers", pd.DataFrame())
        if not isinstance(multi_pet_df, pd.DataFrame):
            multi_pet_df = pd.DataFrame()

        pet_insights = result.get("pet_insights", {}) or {}

    else:
        kpi = saved_report.get("kpi", {}) or {}
        forecast = saved_report.get("forecast", {}) or {}
        cat = pd.DataFrame(saved_report.get("category_risk", []) or [])
        seg = pd.DataFrame(saved_report.get("segment_summary", []) or [])
        cust_list = pd.DataFrame(saved_report.get("customer_list", []) or [])
        inv = pd.DataFrame(saved_report.get("inventory", []) or [])
        churn_summary = saved_report.get("churn_summary", {}) or {}
        churn_scored = pd.DataFrame(saved_report.get("churn_scored", []) or [])
        refund_saved = saved_report.get("refund", {}) or {}
        refund_rate = float(refund_saved.get("refund_rate", 0.0) or 0.0)
        refund_customers = pd.DataFrame(refund_saved.get("refund_customers", []) or [])
        refund_category = pd.DataFrame(refund_saved.get("refund_category", []) or [])
        refill_cycle = pd.DataFrame(saved_report.get("refill_cycle_by_category", []) or [])
        refill_group = pd.DataFrame(saved_report.get("refill_category_group", []) or [])
        multi_pet_df = pd.DataFrame(saved_report.get("multi_pet_customers", []) or [])
        pet_insights = saved_report.get("pet_insights", {}) or {}
        rfm_df = pd.DataFrame(saved_report.get("rfm", []) or [])
        metrics = saved_metrics or {}
        df_work = None

        name = (saved_run.get("run_name") if saved_run else None) or ""
        created = (saved_run.get("created_at") if saved_run else None) or ""
        title = name.strip() if str(name).strip() else created
        st.info(f"📌 저장된 분석을 보고 있어요: **{title}** (사이드바에서 '현재 분석 보기'로 돌아갈 수 있어요)")


    if not showing_saved:
        st.markdown("### 분석 저장")

        if not is_member:
            st.info("로그인하면 분석 기록을 이름 지정해서 저장하고, 나중에 비교할 수 있어요.")
        else:
            default_name = st.session_state.get("draft_run_name", "새 분석")
            with st.form("save_run_form", border=True):
                run_name = st.text_input(
                    "저장 이름",
                    value=default_name,
                    placeholder="예: 6월 캠페인 이후 고객이탈 분석",
                )
                c1, c2 = st.columns([1, 1], gap="small")
                do_save = c1.form_submit_button("저장", type="primary", use_container_width=True)
                clear_name = c2.form_submit_button("이름 지우기", use_container_width=True)

            if clear_name:
                st.session_state["draft_run_name"] = ""
                st.rerun()

            if do_save:
                name = (run_name or "").strip()
                if not name:
                    st.warning("저장 이름을 입력해주세요.")
                else:
                    try:
                        packed = _pack_report_for_storage(result)
                        run_id = save_run(effective_user_key, name, metrics, packed)
                        st.session_state["draft_run_name"] = name
                        st.session_state["view_run_id"] = None
                        st.session_state["sidebar_run_pick"] = "현재 분석"
                        st.success(f"저장 완료! (run_id={run_id})")
                        st.rerun()
                    except Exception as e:
                        st.error("저장 중 오류가 발생했습니다.")
                        st.exception(e)

        st.divider()

    total_customers = int(kpi.get("total_customers", 0) or 0)

    if isinstance(rfm_df, pd.DataFrame) and not rfm_df.empty and ("위험도" in rfm_df.columns):
        high_cnt = int(rfm_df["위험도"].eq("High").sum())
        vvip_high_cnt = int(((rfm_df.get("세그먼트") == "VVIP") & (rfm_df.get("위험도") == "High")).sum()) if (
            ("세그먼트" in rfm_df.columns) and ("위험도" in rfm_df.columns)
        ) else 0
    else:
        risk_col = _pick_col(cust_list, ["위험도", "risk", "Risk", "risk_level"])
        seg_col = _pick_col(cust_list, ["세그먼트", "segment", "Segment"])
        high_cnt = int(cust_list[risk_col].astype(str).eq("High").sum()) if (risk_col and not cust_list.empty) else 0
        vvip_high_cnt = int(
            ((cust_list[seg_col].astype(str) == "VVIP") & (cust_list[risk_col].astype(str) == "High")).sum()
        ) if (risk_col and seg_col and not cust_list.empty) else 0

    top_cat_name, top_cat_score = None, None
    if isinstance(cat, pd.DataFrame) and (len(cat) > 0) and ("카테고리" in cat.columns):
        risk_score_col = _pick_col(cat, ["위험", "risk", "Risk", "risk_score", "평균위험"])
        if risk_score_col:
            top_row = cat.sort_values(risk_score_col, ascending=False).head(1).iloc[0]
            top_cat_name = str(top_row["카테고리"])
            try:
                top_cat_score = int(float(top_row[risk_score_col]))
            except Exception:
                top_cat_score = None

    top_seg_name = "-"
    if isinstance(seg, pd.DataFrame) and not seg.empty and "세그먼트" in seg.columns and "인원" in seg.columns:
        try:
            top_seg_name = str(seg.sort_values("인원", ascending=False).iloc[0]["세그먼트"])
        except Exception:
            pass

    summary_lines = _exec_summary_lines(
        float(kpi.get("high_ratio", 0) or 0),
        int(kpi.get("expected_loss", 0) or 0),
        refund_rate,
        top_seg_name,
        top_cat_name or "-",
    )

    with st.sidebar:
        if not showing_saved:
            tx_count = len(df_work) if isinstance(df_work, pd.DataFrame) else 0
            cust_count = total_customers
            st.markdown(
                f"""
                <div class="card" style="border-color: rgba(34,197,94,0.22); background: rgba(34,197,94,0.06);">
                  <div style="font-weight:900; margin-bottom:6px;">집계 요약</div>
                  <div style="line-height:1.55;">
                    거래 <b>{_fmt_int(tx_count)}건</b> · 고객 <b>{_fmt_int(cust_count)}명</b>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    high_ratio = float(kpi.get("high_ratio", 0) or 0)
    avg_risk = float(kpi.get("avg_risk", 0) or 0)
    expected_loss = int(kpi.get("expected_loss", 0) or 0)

    # -----------------------
    # PDF 다운로드
    # -----------------------
    pdf_title = "고객 이탈 리스크 분석 리포트"
    pdf_user_name = st.session_state.get("user_key", "guest")

    if showing_saved:
        pdf_run_name = (saved_run.get("run_name") if saved_run else None) or "저장된 분석"
    else:
        pdf_run_name = st.session_state.get("draft_run_name", "현재 분석")

    pdf_col1, pdf_col2 = st.columns([1, 3])

    with pdf_col1:
        if st.button("PDF 준비", use_container_width=True):
            try:
                pdf_bytes = build_report_pdf(
                    title=pdf_title,
                    user_name=pdf_user_name,
                    run_name=pdf_run_name,
                    kpi=kpi,
                    category_df=cat if isinstance(cat, pd.DataFrame) else pd.DataFrame(cat or []),
                    segment_df=seg if isinstance(seg, pd.DataFrame) else pd.DataFrame(seg or []),
                    customer_df=cust_list if isinstance(cust_list, pd.DataFrame) else pd.DataFrame(cust_list or []),
                    ml_df=churn_scored if isinstance(churn_scored, pd.DataFrame) else pd.DataFrame(),
                    refund_df=refund_category if isinstance(refund_category, pd.DataFrame) else pd.DataFrame(),
                    inventory_df=inv if isinstance(inv, pd.DataFrame) else pd.DataFrame(inv or []),
                )
                st.session_state["report_pdf_bytes"] = pdf_bytes
                st.success("PDF가 준비되었습니다.")
            except Exception as e:
                st.error("PDF 생성 중 오류가 발생했습니다.")
                st.exception(e)

    with pdf_col2:
        pdf_bytes = st.session_state.get("report_pdf_bytes")
        if pdf_bytes:
            st.download_button(
                label="PDF 다운로드",
                data=pdf_bytes,
                file_name=f"{pdf_run_name}_report.pdf",
                mime="application/pdf",
                use_container_width=False,
            )
    # -----------------------
    # Tabs
    # -----------------------
    tab_overview, tab_segment, tab_category, tab_risk, tab_ml, tab_refund, tab_forecast, tab_inventory, tab_compare = st.tabs(
        ["개요", "세그먼트", "카테고리", "이탈리스크", "ML 이탈예측", "환불 분석", "매출전망", "재고전략", "분석 비교"]
    )

    with tab_overview:
        st.markdown("### Executive Overview")
        st.markdown(
            "<div class='sub' style='margin-top:-6px;'>현재(또는 저장된) 분석 기준 핵심 KPI 및 우선 대응 영역을 요약합니다.</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="kpi-grid">
              <div class="kpi red">
                <h4>고위험 고객 비율</h4>
                <div class="v">{high_ratio:.1f}%</div>
                <div style="margin-top:6px; font-size:12px; color: rgba(0,0,0,0.55); font-weight:700;">
                  고위험 고객: {_fmt_int(high_cnt)}명
                </div>
              </div>
              <div class="kpi yellow">
                <h4>평균 리스크 스코어</h4>
                <div class="v">{avg_risk:.0f}</div>
                <div style="margin-top:6px; font-size:12px; color: rgba(0,0,0,0.55); font-weight:700;">
                  기준 예시: High ≥ 70
                </div>
              </div>
              <div class="kpi blue">
                <h4>예상 매출 이탈</h4>
                <div class="v">{_fmt_currency(expected_loss)}</div>
                <div style="margin-top:6px; font-size:12px; color: rgba(0,0,0,0.55); font-weight:700;">
                  단기 리텐션 우선순위 필요
                </div>
              </div>
              <div class="kpi purple">
                <h4>환불률</h4>
                <div class="v">{refund_rate * 100:.1f}%</div>
                <div style="margin-top:6px; font-size:12px; color: rgba(0,0,0,0.55); font-weight:700;">
                  전체 주문 대비 환불 비율
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="rfm-box">
              <div class="rfm-title">세그먼트 정의 (RFM)</div>
              <div class="rfm-grid">
                <div><b>R (Recency)</b>: 최근 구매 경과일<br/>최근 120일 이상 → 휴면형</div>
                <div><b>F (Frequency)</b>: 구매 빈도 변화<br/>빈도 하락 시 → 이탈 가능성 증가</div>
                <div><b>M (Monetary)</b>: 누적 구매금액 수준<br/>상위 고객군(VIP/VVIP) 선제 케어 권장</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div class='card' style='padding:16px 18px; line-height:1.85; margin-top:14px;'>" +
            "<div style='font-size:18px; font-weight:900; margin-bottom:8px;'>Executive Summary</div>" +
            "<ul style='margin:0; padding-left:18px;'>" +
            "".join([f"<li>{line}</li>" for line in summary_lines]) +
            "</ul></div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="alert">
              <div class="t">⚠️ 우선 대응 필요</div>
              <div class="d" style="line-height:1.65;">
                고위험 고객 <b>{_fmt_int(high_cnt)}명</b>이 확인되었으며,
                VIP(특히 VVIP) 고위험 고객은 <b>{_fmt_int(vvip_high_cnt)}명</b>입니다.<br/>
                추정 매출 이탈 규모는 <b>{_fmt_currency(expected_loss)}</b> 수준으로 추정됩니다.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### 카테고리별 위험도 비교")
        if top_cat_name is not None and top_cat_score is not None:
            st.markdown(
                f"""
                <div class="card" style="margin-bottom:10px;">
                  <div style="font-weight:900; margin-bottom:4px;">관찰 요약</div>
                  <div style="color: rgba(0,0,0,0.72); line-height:1.6;">
                    현재 기준으로 <b>{top_cat_name}</b> 카테고리의 위험도가 가장 높게 나타났습니다
                    (평균 {top_cat_score}점).
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if isinstance(cat, pd.DataFrame) and len(cat) > 0 and ("카테고리" in cat.columns):
            risk_score_col = _pick_col(cat, ["위험", "risk", "Risk", "risk_score", "평균위험"])
            cnt_col = _pick_col(cat, ["고객수", "count", "고객 수", "customers"])

            if risk_score_col:
                max_score = max(int(pd.to_numeric(cat[risk_score_col], errors="coerce").max() or 1), 1)
                st.markdown('<div class="bar-wrap">', unsafe_allow_html=True)
                for _, r in cat.head(7).iterrows():
                    name = r.get("카테고리", "-")
                    cnt = int(r.get(cnt_col, 0)) if cnt_col else 0
                    try:
                        score = int(float(r.get(risk_score_col, 0)))
                    except Exception:
                        score = 0
                    w = int((score / max_score) * 100) if max_score else 0

                    if score >= 50:
                        fill = "background: rgba(245,158,11,0.92);"
                        pill_bg = "background: rgba(245,158,11,0.12);"
                    elif score >= 35:
                        fill = "background: rgba(245,158,11,0.78);"
                        pill_bg = "background: rgba(245,158,11,0.10);"
                    else:
                        fill = "background: rgba(34,197,94,0.72);"
                        pill_bg = "background: rgba(34,197,94,0.12);"

                    st.markdown(
                        f"""
                        <div class="row">
                          <div class="name">{name} ({cnt:,}명)</div>
                          <div class="track"><div class="fill" style="width:{w}%; {fill}"></div></div>
                          <div class="score" style="{pill_bg}">{score}점</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.dataframe(cat, use_container_width=True, hide_index=True)
    with tab_segment:
        st.markdown("### 고객 세그먼트 분석")
    
        if seg is None or not isinstance(seg, pd.DataFrame) or seg.empty:
            st.info("세그먼트 요약 데이터가 없습니다.")
        else:
            # 숫자형 변환
            seg_plot = seg.copy()
            if "인원" in seg_plot.columns:
                seg_plot["인원"] = pd.to_numeric(seg_plot["인원"], errors="coerce")
            if "평균금액" in seg_plot.columns:
                seg_plot["평균금액"] = pd.to_numeric(seg_plot["평균금액"], errors="coerce")
            if "평균위험" in seg_plot.columns:
                seg_plot["평균위험"] = pd.to_numeric(seg_plot["평균위험"], errors="coerce")

            import plotly.express as px

            st.markdown("### 세그먼트 시각화")
            segment_colors = {
                "VVIP": "#6366F1",
                "VIP": "#A78BFA",
                "고가치 감소형": "#F59E0B",
                "휴면형": "#FB7185",
                "활발한 일반 고객": "#10B981",
                "관심필요 고객": "#06B6D4",
            }
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 1) 세그먼트 구성 비율")
                if "세그먼트" in seg_plot.columns and "인원" in seg_plot.columns:
                    fig_pie = px.pie(
                        seg_plot,
                        names="세그먼트",
                        values="인원",
                        # hole=0.55,
                        color="세그먼트",
                        color_discrete_map=segment_colors
                    )
                    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                    fig_pie.update_layout(
                        height=420,
                        margin=dict(l=10, r=10, t=40, b=10),
                        legend_title_text="세그먼트",
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("도넛그래프를 그릴 데이터가 없습니다.")

            with col2:
                st.markdown("#### 2) 세그먼트별 평균 매출")
                if "세그먼트" in seg_plot.columns and "평균금액" in seg_plot.columns:
                    fig_bar_sales = px.bar(
                    seg_plot,
                    x="세그먼트",
                    y="평균금액",
                    text="평균금액",
                    color="세그먼트",
                    color_discrete_map=segment_colors
)
                    fig_bar_sales.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
                    fig_bar_sales.update_layout(
                        height=420,
                        margin=dict(l=10, r=10, t=40, b=10),
                        xaxis_title="세그먼트",
                        yaxis_title="평균 매출",
                    )
                    st.plotly_chart(fig_bar_sales, use_container_width=True)
                else:
                    st.info("평균 매출 그래프를 그릴 데이터가 없습니다.")

            st.markdown("#### 3) 세그먼트별 평균 이탈 위험점수")
            if "세그먼트" in seg_plot.columns and "평균위험" in seg_plot.columns:
                fig_bar_risk = px.bar(
                    seg_plot,
                    x="세그먼트",
                    y="평균위험",
                    text="평균위험",
                    color="세그먼트",
                    color_discrete_map=segment_colors
                )
                fig_bar_risk.update_traces(texttemplate="%{text:.1f}", textposition="outside")
                fig_bar_risk.update_layout(
                    height=420,
                    margin=dict(l=10, r=10, t=40, b=10),
                    xaxis_title="세그먼트",
                    yaxis_title="평균 이탈 위험점수",
                )
                st.plotly_chart(fig_bar_risk, use_container_width=True)
            else:
                st.info("평균 위험점수 그래프를 그릴 데이터가 없습니다.")
                
        st.markdown("### 고객 세그먼트 분석")
        if seg is None or not isinstance(seg, pd.DataFrame) or seg.empty:
            st.info("세그먼트 요약 데이터가 없습니다.")
        else:
            def seg_reco(seg_name: str) -> str:
                if seg_name == "휴면형":
                    return "복귀 캠페인 / 쿠폰 / 리마인드 메시지 우선"
                if "VIP" in seg_name:
                    return "전용 혜택 / 개인화 추천 / 재구매 주기 단축"
                if seg_name == "관심필요 고객":
                    return "정기 구매 유지 전략 / 리워드 / 추천 노출"
                return "일반 유지 전략 권장"

            for _, r in seg.iterrows():
                seg_name = r.get("세그먼트", "-")
                people = int(r.get("인원", 0) or 0)
                ratio = (people / total_customers * 100) if total_customers else 0
                avg_f = _fmt_float2(r.get("평균주문", 0))
                avg_m = _fmt_currency(r.get("평균금액", 0))
                avg_risk_seg = f"{float(r.get('평균위험', 0) or 0):.0f}점"

                st.markdown(
                    f"""
                    <div class="card" style="margin-bottom:12px;">
                      <div style="display:flex; justify-content:space-between; align-items:flex-end;">
                        <div style="font-size:20px; font-weight:900;">{seg_name}</div>
                        <div style="color: rgba(0,0,0,0.55); font-weight:800;">{people:,}명 ({ratio:.1f}%)</div>
                      </div>
                      <div style="display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 10px; margin-top:10px;">
                        <div>
                          <div style="font-size:12px; color:rgba(0,0,0,0.55); font-weight:800;">평균 주문</div>
                          <div style="font-size:18px; font-weight:900;">{avg_f}회</div>
                        </div>
                        <div>
                          <div style="font-size:12px; color:rgba(0,0,0,0.55); font-weight:800;">평균 금액</div>
                          <div style="font-size:18px; font-weight:900;">{avg_m}</div>
                        </div>
                        <div>
                          <div style="font-size:12px; color:rgba(0,0,0,0.55); font-weight:800;">평균 리스크</div>
                          <div style="font-size:18px; font-weight:900;">{avg_risk_seg}</div>
                        </div>
                      </div>
                      <div style="margin-top:12px; border: 1px solid rgba(59,130,246,0.22); background: rgba(59,130,246,0.05); border-radius: 10px; padding: 10px 12px;">
                        <b style="color: rgba(37,99,235,1);">권장 전략</b>:
                        <span style="color: rgba(0,0,0,0.72);">{seg_reco(seg_name)}</span>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with tab_category:
        st.markdown("### 카테고리")

        st.markdown("#### 1) 카테고리별 재구매(리필) 주기")
        if isinstance(refill_cycle, pd.DataFrame) and not refill_cycle.empty:
            st.markdown(
                "<div class='card' style='padding:14px 16px; margin-bottom:10px;'>"
                "<b>해석 가이드</b><br/>"
                "재구매 주기는 고객-카테고리 기준 구매 간격의 중앙값을 이용해 추정했습니다. "
                "카테고리별로 ‘정기구매 / 일반 / 일회성’으로 분류합니다"
                "</div>",
                unsafe_allow_html=True,
            )
            st.dataframe(refill_cycle, use_container_width=True, hide_index=True)
        else:
            st.info("카테고리/거래일시 데이터가 부족하여 재구매 주기를 계산할 수 없습니다.")

        st.markdown("#### 2) 다반려(멀티펫) 고객 추정")
        mp_cnt = int((pet_insights or {}).get("multi_pet_cnt", 0) or 0)
        mp_ratio = float((pet_insights or {}).get("multi_pet_ratio", 0) or 0)

        st.markdown(
            f"""
            <div class="card" style="padding:14px 16px;">
              <div style="font-weight:900; margin-bottom:6px;">요약</div>
              <div style="color: rgba(0,0,0,0.72); line-height:1.6;">
                다반려(멀티펫)로 추정되는 고객은 <b>{_fmt_int(mp_cnt)}명</b>이며, 전체의 <b>{mp_ratio:.1f}%</b> 입니다.<br/>
                (키워드 기반 + 카테고리 다양도/구매빈도 기반 추정)
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        if isinstance(multi_pet_df, pd.DataFrame) and not multi_pet_df.empty:
            st.markdown("**멀티펫 추정 고객 Top 20**")
            mp_show = multi_pet_df.copy()
            if "multi_pet" in mp_show.columns:
                mp_show = mp_show[mp_show["multi_pet"].eq(True)].copy()
            sort_cols = [c for c in ["구매빈도", "카테고리다양도"] if c in mp_show.columns]
            if sort_cols:
                mp_show = mp_show.sort_values(sort_cols, ascending=False)
            st.dataframe(mp_show.head(20), use_container_width=True, hide_index=True)
        else:
            st.info("멀티펫 추정을 위한 데이터가 부족합니다.")

        st.markdown("#### 3) 실행 체크리스트 ")
        st.markdown(
            """
            <div class="card" style="padding:14px 16px; line-height:1.75;">
              <ul style="margin:0; padding-left:18px;">
                <li><b>정기구매 고객</b>은 재구매 주기 기준 <b>리마인드 알림</b>과 <b>정기구독/묶음</b>이 효과적입니다.</li>
                <li><b>일회성 구매고객 / 일반고객</b>은 구매 사이클이 길어 <b>추천/콘텐츠</b>로 관심을 유지하는 전략이 적합합니다.</li>
                <li><b>멀티펫 고객</b>은 장바구니 규모가 커질 확률이 높아 <b>교차판매(크로스셀)</b> 캠페인 우선 타겟입니다.</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )


    with tab_risk:
        st.markdown("### 이탈 리스크 분석")
        st.markdown(
            "<div class='sub' style='margin-top:-6px;'>데이터 분석에 익숙하지 않은 사용자도 이해할 수 있도록 그래프 해석 가이드를 함께 제공합니다.</div>",
            unsafe_allow_html=True,
        )

        with st.expander("그래프 읽는 법"):
            st.markdown(
                """
                - **리스크 히트맵**: 최근 구매가 오래됐고 구매 빈도가 낮은 고객군일수록 이탈 위험이 높습니다.
                - **RFM 분포**: 오른쪽일수록 최근 구매가 오래된 고객, 위쪽일수록 누적 구매금액이 큰 고객입니다.
                - **카테고리 우선순위**: 매출이 크고 위험도가 높은 카테고리부터 우선 대응하는 것이 좋습니다.
                """
            )

        if isinstance(rfm_df, pd.DataFrame) and not rfm_df.empty:
            if showing_saved:
                st.caption("저장된 분석 결과입니다. (저장 시 함께 보관한 RFM 데이터로 차트를 다시 표시합니다.)")
            if not _plotly_ok():
                st.warning("Plotly가 설치되어 있지 않아 그래프를 표시할 수 없습니다. `pip install plotly` 후 다시 실행해주세요.")
            else:
                st.markdown("#### 분포 차트")
                col1, col2 = st.columns([1, 1])
                with col1:
                    fig1 = _fig_risk_heatmap(rfm_df)
                    if fig1 is None:
                        st.info("히트맵을 그리기 위한 데이터가 부족합니다.")
                    else:
                        st.plotly_chart(fig1, use_container_width=True)
                        st.markdown(
                            """
                            <div class="card" style="padding:10px 12px; margin-top:6px; font-size:13px; line-height:1.6;">
                              <b>해석</b><br/>
                              최근 구매가 오래됐고 구매 빈도가 낮은 고객일수록 서비스 이탈 가능성이 높습니다.
                              색이 진할수록 해당 고객군의 평균 위험 점수가 높다는 의미입니다.
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                with col2:
                    fig2 = _fig_rfm_scatter(rfm_df)
                    if fig2 is None:
                        st.info("산점도를 그리기 위한 데이터가 부족합니다.")
                    else:
                        st.plotly_chart(fig2, use_container_width=True)
                        st.markdown(
                            """
                            <div class="card" style="padding:10px 12px; margin-top:6px; font-size:13px; line-height:1.6;">
                              <b>해석</b><br/>
                              오른쪽으로 갈수록 최근 구매가 오래된 고객이고, 위로 갈수록 누적 구매금액이 큰 고객입니다.
                              오른쪽 위에 있는 고객은 이탈 시 매출 영향이 커 우선 관리 대상입니다.
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                st.markdown("#### 카테고리 매출 vs 리스크 (우선순위)")
                fig3 = _fig_category_bubble(rfm_df)
                if fig3 is None:
                    st.info("카테고리 버블 차트를 그리기 위한 데이터가 부족합니다.")
                else:
                    st.plotly_chart(fig3, use_container_width=True)
                    st.markdown(
                        """
                        <div class="card" style="padding:10px 12px; margin-top:6px; font-size:13px; line-height:1.6;">
                          <b>해석</b><br/>
                          매출이 크고 위험도가 높은 카테고리일수록 우선 대응이 필요합니다.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        else:
            if showing_saved:
                st.caption("저장된 분석 결과입니다. (이 저장본에는 rfm 데이터가 없어 표 중심으로 표시됩니다.)")

        st.markdown("#### 고객 위험도 분석 결과")
        if cust_list is None or cust_list.empty:
            st.info("고객 위험도 데이터가 없습니다.")
        else:
            colA, colB = st.columns([1, 1])
            with colA:
                only_high = st.checkbox("고위험(High) 고객만 보기", value=True)
            with colB:
                sort_by_sales = st.checkbox("주문금액 기준 정렬(내림차순)", value=True)

            show = cust_list.copy()
            if only_high and "위험도" in show.columns:
                show = show[show["위험도"].eq("High")].copy()
            if sort_by_sales and "주문금액" in show.columns:
                try:
                    show = show.sort_values("주문금액", ascending=False)
                except Exception:
                    pass
            if "주문금액" in show.columns:
                show["주문금액"] = show["주문금액"].apply(lambda x: _fmt_currency(x))
            st.dataframe(show, use_container_width=True, hide_index=True)


    with tab_ml:
        st.markdown("### ML 기반 이탈 예측")
        st.markdown(
            "<div class='sub' style='margin-top:-6px;'>고객별 재구매 주기와 카테고리 특성을 반영한 이탈 예측 결과입니다.</div>",
            unsafe_allow_html=True,
        )

        avg_churn_prob = float((churn_summary or {}).get("avg_churn_prob", 0.0) or 0.0)
        high_risk_count = int((churn_summary or {}).get("high_risk_count", 0) or 0)
        rule_dormant_count = int((churn_summary or {}).get("rule_dormant_count", 0) or 0)
        rule_risk_count = int((churn_summary or {}).get("rule_risk_count", 0) or 0)

        st.markdown(
            f"""
            <div class="kpi-grid">
              <div class="kpi red">
                <h4>평균 이탈확률</h4>
                <div class="v">{avg_churn_prob:.2%}</div>
              </div>
              <div class="kpi yellow">
                <h4>모델 고위험 고객</h4>
                <div class="v">{high_risk_count:,}</div>
              </div>
              <div class="kpi purple">
                <h4>규칙기반 위험 고객</h4>
                <div class="v">{rule_risk_count:,}</div>
              </div>
              <div class="kpi blue">
                <h4>규칙기반 휴면 고객</h4>
                <div class="v">{rule_dormant_count:,}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if churn_scored is None or churn_scored.empty:
            st.info("이탈예측 결과가 없습니다.")
        else:
            preferred_cols = [
                "고객ID", "last_order_date", "recency", "avg_cycle", "recency_ratio",
                "Final_Segment", "churn_prob", "rule_risk", "model_risk",
                "reason", "recommended_action"
            ]
            show_cols = [c for c in preferred_cols if c in churn_scored.columns]
            show_df = churn_scored[show_cols].copy() if show_cols else churn_scored.copy()

            if "churn_prob" in show_df.columns:
                try:
                    show_df["churn_prob"] = pd.to_numeric(show_df["churn_prob"], errors="coerce").mul(100).round(1).astype(str) + "%"
                except Exception:
                    pass

            st.dataframe(show_df, use_container_width=True, hide_index=True)

            try:
                csv_bytes = churn_scored.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "ML 이탈예측 결과 다운로드",
                    data=csv_bytes,
                    file_name="pet_churn_scored_result.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            except Exception:
                pass

    with tab_refund:
        st.markdown("### 환불 분석")
        st.markdown(
            "<div class='sub' style='margin-top:-6px;'>환불 데이터가 포함된 경우 환불률, 환불 위험 고객, 카테고리별 환불 현황을 확인할 수 있습니다.</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="kpi-grid">
              <div class="kpi purple">
                <h4>환불률</h4>
                <div class="v">{refund_rate:.1%}</div>
                <div class="sub">전체 주문 대비 환불 비율</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if (refund_customers is None or refund_customers.empty) and (refund_category is None or refund_category.empty):
            st.info(
                "일부 데이터셋에는 환불 정보가 포함되지 않을 수 있습니다. "
                "환불 데이터가 있는 경우 환불률 및 환불 고객 분석이 자동으로 표시됩니다."
            )
        else:
            col1, col2 = st.columns([1, 1])

            with col1:
                st.markdown("#### 환불 위험 고객")
                show_refund_customers = refund_customers.copy()
                if "환불금액" in show_refund_customers.columns:
                    show_refund_customers["환불금액"] = show_refund_customers["환불금액"].apply(_fmt_currency)
                if "환불비율" in show_refund_customers.columns:
                    try:
                        show_refund_customers["환불비율"] = (
                            pd.to_numeric(show_refund_customers["환불비율"], errors="coerce") * 100
                        ).round(1).astype(str) + "%"
                    except Exception:
                        pass
                st.dataframe(show_refund_customers, use_container_width=True, hide_index=True)

            with col2:
                st.markdown("#### 카테고리 환불 분석")
                show_refund_category = refund_category.copy()
                if "환불금액" in show_refund_category.columns:
                    show_refund_category["환불금액"] = show_refund_category["환불금액"].apply(_fmt_currency)
                if "환불률" in show_refund_category.columns:
                    try:
                        show_refund_category["환불률"] = (
                            pd.to_numeric(show_refund_category["환불률"], errors="coerce") * 100
                        ).round(1).astype(str) + "%"
                    except Exception:
                        pass
                st.dataframe(show_refund_category, use_container_width=True, hide_index=True)


    with tab_forecast:
        st.markdown("### 매출 전망")
        label = forecast.get("label", "전망")
        value = forecast.get("value", 0)
        try:
            value = int(value)
        except Exception:
            value = 0

        st.markdown(
            f"""
            <div class="card" style="background: rgba(59,130,246,0.06); border-color: rgba(59,130,246,0.16); padding: 18px 18px;">
              <div style="color: rgba(37,99,235,1); font-weight:900; margin-bottom:6px;">{label}</div>
              <div style="font-size:44px; font-weight:900; letter-spacing:-0.02em;">₩{value:,}</div>
              <div style="margin-top:6px; color: rgba(0,0,0,0.58); font-size: 13px;">
                현재(또는 저장된) 분석을 기준으로 단순 추정한 전망치입니다.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="card" style="padding:14px 16px; margin-top:12px;">
              <b>운영 해석</b><br/>
              매출 전망은 고객 유지율에 크게 영향을 받습니다. 고위험 고객과 고가치 고객을 우선적으로 관리할수록 실제 결과가 개선될 가능성이 높습니다.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with tab_inventory:
        st.markdown("### 재고 권장안")
        inv_show = inv.copy() if isinstance(inv, pd.DataFrame) else pd.DataFrame(inv or [])
        if isinstance(inv_show, pd.DataFrame) and "권장재고" in inv_show.columns:
            inv_show["권장재고"] = inv_show["권장재고"].apply(lambda x: f"약 {int(x):,}개" if pd.notna(x) else "-")

        if inv_show is None or inv_show.empty:
            st.info("재고 권장안 데이터가 없습니다.")
        else:
            st.dataframe(inv_show, use_container_width=True, hide_index=True)

        st.markdown(
            """
            <div class="card" style="padding:14px 16px; margin-top:12px;">
              <b>운영 해석</b><br/>
              재구매 주기가 짧은 카테고리는 재고 부족 리스크가 높고, 비정기 구매 카테고리는 과잉재고보다 회전율 관리가 중요합니다.
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not showing_saved:
            with st.expander("데이터 상세(선택)"):
                st.write("표준화 데이터(상위 20행)")
                st.dataframe(df_std.head(20), use_container_width=True)
                if isinstance(rfm_df, pd.DataFrame) and not rfm_df.empty:
                    st.write("고객단 RFM/위험도(상위 20행)")
                    st.dataframe(rfm_df.head(20), use_container_width=True)




    with tab_compare:
        st.markdown("### 저장된 분석 비교")

        if not is_member:
            st.info("로그인 후 이용할 수 있어요.")
        else:
            runs = list_runs(effective_user_key)
            if not runs or len(runs) < 2:
                st.warning("비교하려면 저장된 분석이 최소 2개 필요합니다.")
            else:
                rid_list = []
                label_map = {}
                for r in runs:
                    rid = r.get("run_id")
                    created = r.get("created_at", "")
                    run_name = (r.get("run_name") or "").strip()
                    m = r.get("metrics", {}) or {}
                    label_title = run_name if run_name else created
                    label = f"{label_title} · 매출 {int(m.get('revenue',0)):,} · 주문 {int(m.get('orders',0)):,} · 고객 {int(m.get('customers',0)):,}"
                    if rid is not None:
                        rid_list.append(rid)
                        label_map[rid] = label

                col_a, col_b = st.columns(2)
                with col_a:
                    a_id = st.selectbox("기준(이전) 분석", rid_list, format_func=lambda x: label_map.get(x, str(x)), key="cmp_a_main")
                with col_b:
                    b_id = st.selectbox("비교(현재/다른) 분석", rid_list, format_func=lambda x: label_map.get(x, str(x)), key="cmp_b_main")

                if a_id == b_id:
                    st.info("서로 다른 분석을 선택해주세요.")
                else:
                    a = get_run(a_id)
                    b = get_run(b_id)

                    if not a or not b:
                        st.error("선택한 분석을 불러오지 못했습니다.")
                    else:
                        rev_a = int(a["metrics"].get("revenue", 0))
                        rev_b = int(b["metrics"].get("revenue", 0))
                        ord_a = int(a["metrics"].get("orders", 0))
                        ord_b = int(b["metrics"].get("orders", 0))
                        cus_a = int(a["metrics"].get("customers", 0))
                        cus_b = int(b["metrics"].get("customers", 0))

                        k1, k2, k3 = st.columns(3)
                        k1.metric("매출 변화", f"{rev_b:,}", f"{rev_b - rev_a:+,}")
                        k2.metric("주문 변화", f"{ord_b:,}", f"{ord_b - ord_a:+,}")
                        k3.metric("고객 변화", f"{cus_b:,}", f"{cus_b - cus_a:+,}")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("#### 기준(이전)")
                            _render_saved_report_summary(a.get("report", {}))
                        with col2:
                            st.markdown("#### 비교(현재/다른)")
                            _render_saved_report_summary(b.get("report", {}))