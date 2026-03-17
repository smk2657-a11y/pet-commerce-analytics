import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple


STD_REQUIRED = ["고객ID", "주문번호", "거래일시", "매출"]

# 환불 컬럼 후보
REFUND_CANDIDATES = [
    "환불금액",
    "refund",
    "refund_amount",
    "cancel_amount",
    "취소금액",
]


def _safe_to_datetime(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce")


def _safe_to_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")

def _safe_qcut_score(series, n_bins=5, labels=None, reverse=False):
    s = pd.to_numeric(series, errors="coerce")

    # 값이 거의 없으면 기본값 반환
    if s.dropna().empty:
        return pd.Series([3] * len(s), index=s.index)

    # 유니크 값이 1개뿐이면 전부 중간 점수
    if s.dropna().nunique() < 2:
        return pd.Series([3] * len(s), index=s.index)

    ranked = s.rank(method="average")

    try:
        # 먼저 labels 없이 잘라서 실제 bin 개수 파악
        cat, bins = pd.qcut(ranked, q=n_bins, retbins=True, duplicates="drop")

        actual_bins = len(bins) - 1

        # 실제 bin 수에 맞는 라벨 생성
        if labels is None:
            use_labels = list(range(1, actual_bins + 1))
        else:
            use_labels = list(labels)[:actual_bins]

        # reverse 옵션 처리
        if reverse:
            use_labels = use_labels[::-1]

        cat = pd.qcut(ranked, q=actual_bins, labels=use_labels, duplicates="drop")
        return cat.astype(int)

    except Exception:
        # fallback: cut 사용
        try:
            actual_bins = min(n_bins, int(s.dropna().nunique()))
            if actual_bins < 2:
                return pd.Series([3] * len(s), index=s.index)

            if labels is None:
                use_labels = list(range(1, actual_bins + 1))
            else:
                use_labels = list(labels)[:actual_bins]

            if reverse:
                use_labels = use_labels[::-1]

            cat = pd.cut(ranked, bins=actual_bins, labels=use_labels, include_lowest=True)
            return cat.astype(int)

        except Exception:
            return pd.Series([3] * len(s), index=s.index)
        
# def _safe_qcut_score(series: pd.Series, q: int, labels: List[int]) -> pd.Series:
#     """
#     qcut 중복 구간 에러 방지용 안전 함수
#     - duplicates='drop' 적용
#     - bins 수가 줄어들면 labels도 자동 축소
#     - 그래도 실패하면 rank 기반 fallback
#     """
#     s = pd.to_numeric(series, errors="coerce").fillna(0)

#     if s.nunique() < 2:
#         return pd.Series([labels[len(labels) // 2]] * len(s), index=s.index)

#     try:
#         cat = pd.qcut(s, q=q, duplicates="drop")
#     except Exception:
#         try:
#             ranked = s.rank(method="average")
#             cat = pd.qcut(ranked, q=min(q, ranked.nunique()), duplicates="drop")
#         except Exception:
#             return pd.Series([labels[len(labels) // 2]] * len(s), index=s.index)

#     n_bins = len(cat.cat.categories)
#     use_labels = labels[:n_bins]

#     try:
#         cat = pd.qcut(s, q=n_bins, labels=use_labels, duplicates="drop")
#     except Exception:
#         ranked = s.rank(method="average")
#         cat = pd.qcut(ranked, q=n_bins, labels=use_labels, duplicates="drop")

#     return cat.astype(int)


# ---------------------------------------------------------
# Multi Pet Detection
# ---------------------------------------------------------
def _detect_multi_pet(
    work: pd.DataFrame,
    customer_id_col: str = "고객ID",
    category_col: str = "카테고리",
    product_col: Optional[str] = None,
) -> pd.DataFrame:
    """
    Multi-Pet detection (추정 로직)
    - 1차: 상품명/카테고리에서 강아지/고양이 키워드로 종 추정
    - 2차: 카테고리 다양도 + 구매빈도 기반 다반려 추정
    """
    if customer_id_col not in work.columns:
        return pd.DataFrame(columns=[customer_id_col, "multi_pet", "근거", "카테고리다양도", "구매빈도"])

    tmp = work.copy()

    text_parts = []
    if category_col in tmp.columns:
        text_parts.append(tmp[category_col].astype(str))
    if product_col and product_col in tmp.columns:
        text_parts.append(tmp[product_col].astype(str))

    if text_parts:
        text = text_parts[0].fillna("").astype(str).str.lower()
        for s in text_parts[1:]:
            text = text.str.cat(s.fillna("").astype(str).str.lower(), sep=" ")
    else:
        text = pd.Series([""] * len(tmp), index=tmp.index)

    dog_kw = ["강아지", "강쥐", "dog", "도그", "puppy", "퍼피", "견"]
    cat_kw = ["고양이", "냥", "cat", "캣", "kitten", "키튼", "묘"]

    def has_kw(series: pd.Series, kws: List[str]) -> pd.Series:
        mask = pd.Series(False, index=series.index)
        for kw in kws:
            mask = mask | series.str.contains(kw, na=False)
        return mask

    tmp["_dog"] = has_kw(text, dog_kw).astype(int)
    tmp["_cat"] = has_kw(text, cat_kw).astype(int)

    g = tmp.groupby(customer_id_col)

    freq = g["주문번호"].nunique() if "주문번호" in tmp.columns else g.size()
    cat_div = g[category_col].nunique() if category_col in tmp.columns else g.size()

    dog_any = g["_dog"].max()
    cat_any = g["_cat"].max()

    out = pd.DataFrame({
        customer_id_col: freq.index,
        "구매빈도": freq.values,
        "카테고리다양도": cat_div.values,
        "dog_signal": dog_any.values,
        "cat_signal": cat_any.values,
    })

    out["multi_pet"] = (
        ((out["dog_signal"] > 0) & (out["cat_signal"] > 0)) |
        ((out["카테고리다양도"] >= 3) & (out["구매빈도"] >= 3))
    )

    def reason(r):
        if r["dog_signal"] and r["cat_signal"]:
            return "강아지+고양이 구매"
        if r["multi_pet"]:
            return "카테고리 다양도 기반"
        return "단일 반려 추정"

    out["근거"] = out.apply(reason, axis=1)

    return out[[customer_id_col, "multi_pet", "근거", "카테고리다양도", "구매빈도"]]


# ---------------------------------------------------------
# Refill Cycle 계산
# ---------------------------------------------------------
def _refill_cycle_by_category(
    work: pd.DataFrame,
    customer_id_col: str = "고객ID",
    date_col: str = "거래일시",
    category_col: str = "카테고리",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    카테고리별 재구매 주기 계산
    """
    if category_col not in work.columns:
        return pd.DataFrame(), pd.DataFrame()

    tmp = work[[customer_id_col, category_col, date_col]].copy()
    tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
    tmp = tmp.dropna(subset=[date_col])

    tmp = tmp.sort_values([customer_id_col, category_col, date_col])
    tmp["gap"] = tmp.groupby([customer_id_col, category_col])[date_col].diff().dt.days
    tmp = tmp[tmp["gap"] > 0]

    if tmp.empty:
        return pd.DataFrame(), pd.DataFrame()

    cust_cycle = (
        tmp.groupby([customer_id_col, category_col])["gap"]
        .median()
        .reset_index()
    )

    cat_cycle = (
        cust_cycle.groupby(category_col)["gap"]
        .median()
        .reset_index()
    )

    cat_cycle.columns = ["카테고리", "재구매주기"]
    cat_cycle["재구매주기"] = cat_cycle["재구매주기"].round(0).astype(int)

    q1 = cat_cycle["재구매주기"].quantile(0.33)
    q2 = cat_cycle["재구매주기"].quantile(0.66)

    def group(x):
        if x <= q1:
            return "소모품"
        elif x <= q2:
            return "중간주기"
        else:
            return "롱테일"

    cat_cycle["그룹"] = cat_cycle["재구매주기"].apply(group)

    cat_group = cat_cycle[["카테고리", "그룹", "재구매주기"]].copy()

    return cat_cycle, cat_group


# ---------------------------------------------------------
# ---------------------------------------------------------
# Optional ML scoring
# ---------------------------------------------------------
def _load_churn_scored(work: pd.DataFrame) -> pd.DataFrame:
    """
    churn_model.py가 있고 정상 작동하면 결과를 붙이고,
    없거나 에러나면 빈 DataFrame 반환.
    """
    try:
        from .churn_model import score_customers  # type: ignore

        scored = score_customers(work.copy())
        if isinstance(scored, pd.DataFrame):
            return scored
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


# Main: RFM + Risk + Pet Insights
# ---------------------------------------------------------
def compute_rfm_and_risk(df: pd.DataFrame) -> Dict[str, Any]:
    work = df.copy()

    # 필수 체크
    for col in STD_REQUIRED:
        if col not in work.columns:
            raise ValueError(f"필수 컬럼 누락: {col}")

    work["거래일시"] = pd.to_datetime(work["거래일시"], errors="coerce")
    work = work.dropna(subset=["거래일시"]).copy()

    work["매출"] = (
        work["매출"]
        .astype(str)
        .str.strip()
        .str.replace(",", "", regex=False)
        .str.replace("₩", "", regex=False)
        .str.replace("원", "", regex=False)
        .str.replace("−", "-", regex=False)   # 유니코드 마이너스 처리
        .str.replace(r"\((.*?)\)", r"-\1", regex=True)  # (10000) -> -10000
        .str.replace(r"[^0-9\.-]", "", regex=True)      # 숫자, 소수점, 마이너스만 남김
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
    )

    snapshot = work["거래일시"].max() + pd.Timedelta(days=1)
    # ---------------------------------------------------------
    # Refund Detection
    # - 우선순위 1: 환불 컬럼 존재 시 사용
    # - 우선순위 2: 없으면 매출 < 0 을 환불로 간주
    # ---------------------------------------------------------
    refund_col = None

    for c in REFUND_CANDIDATES:
        if c in work.columns:
            refund_col = c
            break

    refund_rate = 0.0
    refund_customers = pd.DataFrame()
    refund_category = pd.DataFrame()

    # -----------------------------
    # 환불 여부 / 환불금액 계산
    # -----------------------------
    if refund_col:
        work[refund_col] = pd.to_numeric(work[refund_col], errors="coerce").fillna(0)

        work["is_refund"] = work[refund_col] != 0
        work["refund_amount_calc"] = work[refund_col].abs()

    else:
        # 매출 음수 → 환불
        work["is_refund"] = work["매출"] < 0
        work["refund_amount_calc"] = work["매출"].where(work["매출"] < 0, 0).abs()

    # -----------------------------
    # 1) 전체 환불률
    # -----------------------------
    total_orders = work["주문번호"].nunique()

    refund_orders = (
        work.loc[work["is_refund"], "주문번호"]
        .drop_duplicates()
        .nunique()
    )

    if total_orders > 0:
        refund_rate = refund_orders / total_orders

    # -----------------------------
    # 2) 고객별 환불 분석
    # -----------------------------
    refund_customers = (
        work.groupby("고객ID")
        .agg(
            주문수=("주문번호", "nunique"),
            환불수=("is_refund", "sum"),
            환불금액=("refund_amount_calc", "sum"),
        )
        .reset_index()
    )

    refund_customers["환불비율"] = (
        refund_customers["환불수"] / refund_customers["주문수"].replace(0, 1)
    )

    refund_customers = refund_customers[
        refund_customers["환불수"] > 0
    ].sort_values(["환불비율", "환불금액"], ascending=False)

    # -----------------------------
    # 3) 카테고리별 환불 분석
    # -----------------------------
    if "카테고리" in work.columns:

        refund_category = (
            work.groupby("카테고리")
            .agg(
                주문수=("주문번호", "nunique"),
                환불수=("is_refund", "sum"),
                환불금액=("refund_amount_calc", "sum"),
            )
            .reset_index()
        )

        refund_category["환불률"] = (
            refund_category["환불수"] / refund_category["주문수"].replace(0, 1)
        )

        refund_category = refund_category[
            refund_category["환불수"] > 0
        ].sort_values("환불률", ascending=False)

    # 고객 단위 RFM
    rfm = (
        work.groupby("고객ID")
        .agg(
            Recency=("거래일시", lambda x: (snapshot - x.max()).days),
            Frequency=("주문번호", "nunique"),
            Monetary=("매출", "sum"),
        )
        .reset_index()
    )

    # 안전한 qcut
    rfm["R"] = _safe_qcut_score(rfm["Recency"], 5, [5, 4, 3, 2, 1])
    rfm["F"] = _safe_qcut_score(rfm["Frequency"], 5, [1, 2, 3, 4, 5])
    rfm["M"] = _safe_qcut_score(rfm["Monetary"], 5, [1, 2, 3, 4, 5])

    rfm["RFM"] = rfm["R"] + rfm["F"] + rfm["M"]

    # 세그먼트 기준값 계산
    segment_cut = {
        "monetary_q80": rfm["Monetary"].quantile(0.8),
        "monetary_q60": rfm["Monetary"].quantile(0.6),
        "frequency_q80": rfm["Frequency"].quantile(0.8),
        "frequency_q60": rfm["Frequency"].quantile(0.6),
        "frequency_q50": rfm["Frequency"].quantile(0.5),
        "recency_q20": rfm["Recency"].quantile(0.2),
        "recency_q60": rfm["Recency"].quantile(0.6),
        "recency_q80": rfm["Recency"].quantile(0.8),
    }

    def segment(row):
        r = row["Recency"]
        f = row["Frequency"]
        m = row["Monetary"]

        if m >= segment_cut["monetary_q80"] and f >= segment_cut["frequency_q80"] and r <= segment_cut["recency_q20"]:
            return "VVIP"
        elif m >= segment_cut["monetary_q60"] and f >= segment_cut["frequency_q60"]:
            return "VIP"
        elif m >= segment_cut["monetary_q60"] and r > segment_cut["recency_q60"]:
            return "고가치 감소형"
        elif r > segment_cut["recency_q80"]:
            return "휴면형"
        elif f >= segment_cut["frequency_q50"]:
            return "활발한 일반 고객"
        else:
            return "관심필요 고객"

    rfm["세그먼트"] = rfm.apply(segment, axis=1)

    # 위험도 점수
    rec_n = (rfm["Recency"] - rfm["Recency"].min()) / (rfm["Recency"].max() - rfm["Recency"].min() + 1e-9)
    fre_n = (rfm["Frequency"] - rfm["Frequency"].min()) / (rfm["Frequency"].max() - rfm["Frequency"].min() + 1e-9)
    mon_n = (rfm["Monetary"] - rfm["Monetary"].min()) / (rfm["Monetary"].max() - rfm["Monetary"].min() + 1e-9)

    risk = (0.45 * rec_n + 0.30 * (1 - fre_n) + 0.25 * (1 - mon_n)) * 100
    rfm["위험도점수"] = risk.round().astype(int)

    def risk_label(x):
        if x >= 70:
            return "High"
        if x >= 40:
            return "Medium"
        return "Low"

    rfm["위험도"] = rfm["위험도점수"].apply(risk_label)

    # 전체 KPI
    high_ratio = (rfm["위험도"] == "High").mean() * 100 if len(rfm) else 0
    avg_risk = rfm["위험도점수"].mean() if len(rfm) else 0
    total_customers = rfm["고객ID"].nunique()

    expected_loss = int(
        rfm["Monetary"].mean() * (rfm["위험도"] == "High").sum() * 0.4
    ) if len(rfm) else 0

    # 세그먼트 요약
    seg_summary = (
        rfm.groupby("세그먼트")
        .agg(
            인원=("고객ID", "count"),
            평균주문=("Frequency", "mean"),
            평균금액=("Monetary", "mean"),
            평균위험=("위험도점수", "mean"),
        )
        .reset_index()
    )

    # 고객 리스트
    cust_list = rfm.sort_values(["위험도점수", "Monetary"], ascending=False).head(15).copy()
    cust_list = cust_list.rename(columns={"Monetary": "주문금액"})

    # 카테고리 위험도
    if "카테고리" in work.columns:
        tmp_merge = work.groupby(["고객ID", "카테고리"])["매출"].sum().reset_index()
        tmp_merge = tmp_merge.merge(rfm[["고객ID", "위험도점수"]], on="고객ID", how="left")
        category_risk = (
            tmp_merge.groupby("카테고리")
            .agg(
                고객수=("고객ID", "nunique"),
                위험=("위험도점수", "mean"),
            )
            .reset_index()
        )
        category_risk["위험"] = category_risk["위험"].round().astype(int)
    else:
        category_risk = pd.DataFrame(columns=["카테고리", "고객수", "위험"])

    # 재고
    if "카테고리" in work.columns and "거래일시" in work.columns:
        inventory_src = work.copy()
        inventory_src["거래일시"] = pd.to_datetime(inventory_src["거래일시"], errors="coerce")
        inventory_src = inventory_src.dropna(subset=["거래일시"])

        rows = []

        if not inventory_src.empty:
            for cat, g in inventory_src.groupby("카테고리"):
                g = g.sort_values("거래일시").copy()

                latest_date = g["거래일시"].max()
                three_months_ago = latest_date - pd.DateOffset(months=3)

                # 최근 3개월 데이터만 사용
                recent_g = g[g["거래일시"] >= three_months_ago].copy()

                if recent_g.empty:
                    continue

                start_date = recent_g["거래일시"].min()
                end_date = recent_g["거래일시"].max()

                # 실제 존재 데이터 기간(일수)
                days = (end_date.normalize() - start_date.normalize()).days + 1
                days = max(days, 1)

                sales_count = len(recent_g)

                # 존재하는 기간 기준 월평균 판매량
                monthly_avg_sales = sales_count / days * 30

                # 안전재고량 = 월평균 + 7일치 여유분
                safety_stock = monthly_avg_sales * (1 + 7 / 30)

                rows.append({
                    "카테고리": cat,
                    "예상판매량": round(monthly_avg_sales, 1),
                    "안전재고량": int(round(safety_stock)),
                })

            inventory = pd.DataFrame(rows)

            if not inventory.empty:
                inventory = inventory.sort_values("안전재고량", ascending=False).reset_index(drop=True)
        else:
            inventory = pd.DataFrame(columns=["카테고리", "예상판매량", "안전재고량"])

    else:
        inventory = pd.DataFrame(columns=["카테고리", "예상판매량", "안전재고량"])
        
    # 매출 예측레
    forecast = {
        "label": "다음달 예상 매출",
        "value": int(work["매출"].sum() * 0.35),
    }

    # Pet Commerce 확장
    cat_cycle, cat_group = _refill_cycle_by_category(work)
    product_col = "상품명" if "상품명" in work.columns else None
    multi_pet = _detect_multi_pet(work, product_col=product_col)

    multi_pet_cnt = int(multi_pet["multi_pet"].sum()) if not multi_pet.empty else 0
    pet_insights = {
        "multi_pet_cnt": multi_pet_cnt,
        "multi_pet_ratio": float(multi_pet_cnt / total_customers * 100) if total_customers else 0,
    }
    churn_scored = _load_churn_scored(work)
    churn_summary = {
        "avg_churn_prob": float(churn_scored["churn_prob"].mean()) if len(churn_scored) and "churn_prob" in churn_scored.columns else 0.0,
        "high_risk_count": int((churn_scored["churn_prob"] >= 0.8).sum()) if len(churn_scored) and "churn_prob" in churn_scored.columns else 0,
        "rule_dormant_count": int((churn_scored["rule_risk"] == "휴면").sum()) if len(churn_scored) and "rule_risk" in churn_scored.columns else 0,
        "rule_risk_count": int((churn_scored["rule_risk"] == "위험").sum()) if len(churn_scored) and "rule_risk" in churn_scored.columns else 0,
    }
    return {
        "df_work": work,
        "rfm": rfm,
        "kpi": {
            "high_ratio": high_ratio,
            "avg_risk": avg_risk,
            "total_customers": total_customers,
            "expected_loss": expected_loss,
            "refund_rate": refund_rate,
        },
        "category_risk": category_risk,
        "customer_list": cust_list,
        "segment_summary": seg_summary,
        "forecast": forecast,
        "inventory": inventory,
        "refill_cycle_by_category": cat_cycle,
        "refill_category_group": cat_group,
        "multi_pet_customers": multi_pet,
        "pet_insights": pet_insights,
        "refund": {
            "refund_rate": refund_rate,
            "refund_customers": refund_customers.head(30),
            "refund_category": refund_category,
        },
        "churn_scored": churn_scored,
        "churn_summary": churn_summary,
    }