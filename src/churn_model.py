import pandas as pd
import numpy as np
import joblib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "pet_churn_lgbm.pkl"
FEATURE_PATH = MODEL_DIR / "pet_churn_feature_cols.pkl"


def preprocess_pet_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    df["거래일시"] = pd.to_datetime(df["거래일시"], errors="coerce")
    df["매출"] = (
        df["매출"].astype(str).str.replace(",", "", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )

    # 선택 컬럼 기본값
    for col, default in {
        "카테고리": "Unknown",
        "구매채널": "Unknown",
        "온라인채널": "offline",
        "결제수단": "Unknown",
        "시도": "Unknown",
    }.items():
        if col not in df.columns:
            df[col] = default
        else:
            df[col] = df[col].fillna(default)

    # 카테고리 정리
    df["카테고리"] = df["카테고리"].replace({
        "Pet Food": "Food",
        "Cleaning Supplies": "Cleanig Supplies",
        "Cleaning supplies": "Cleanig Supplies"
    }).fillna("Unknown")

    df = df.dropna(subset=["고객ID", "주문번호", "거래일시", "매출"]).copy()
    df = df[df["매출"] != 0].copy()

    return df


def assign_segment(row):
    if row["recency_ratio"] > 2.5:
        return "휴면형"
    if row["recency_ratio"] > 1.5:
        return "위험형"
    if row["monetary"] >= row["monetary_q80"] and row["frequency"] >= row["frequency_q80"]:
        return "VVIP"
    if row["monetary"] >= row["monetary_q60"] and row["frequency"] >= row["frequency_q60"]:
        return "VIP"
    if row["frequency"] >= row["frequency_q50"]:
        return "활발한 일반 고객"
    return "관심필요 고객"


def build_customer_features(df: pd.DataFrame, snapshot_date: pd.Timestamp) -> pd.DataFrame:
    hist = df[df["거래일시"] <= snapshot_date].copy()
    g = hist.groupby("고객ID")

    last_order = g["거래일시"].max()
    first_order = g["거래일시"].min()
    frequency = g["주문번호"].nunique()
    monetary = g["매출"].sum()

    recency = (snapshot_date - last_order).dt.days
    active_months = ((snapshot_date - first_order).dt.days / 30.0).clip(lower=1)

    customer = pd.DataFrame({
        "고객ID": frequency.index,
        "recency": recency.values,
        "frequency": frequency.values,
        "monetary": monetary.values,
        "active_months": active_months.values,
        "frequency_per_month": (frequency / active_months).values,
        "monetary_per_month": (monetary / active_months).values,
        "AOV": (monetary / frequency.replace(0, 1)).values,
        "last_order_date": last_order.values,
        "first_order_date": first_order.values,
    })

    order_dates = (
        hist[["고객ID", "거래일시"]]
        .drop_duplicates()
        .sort_values(["고객ID", "거래일시"])
    )
    order_dates["prev_date"] = order_dates.groupby("고객ID")["거래일시"].shift(1)
    order_dates["gap"] = (order_dates["거래일시"] - order_dates["prev_date"]).dt.days

    gap_stats = order_dates.groupby("고객ID")["gap"].agg(["mean", "std"]).reset_index()
    gap_stats.columns = ["고객ID", "avg_cycle", "cycle_std"]

    customer = customer.merge(gap_stats, on="고객ID", how="left")
    customer["avg_cycle"] = customer["avg_cycle"].fillna(120).clip(lower=1, upper=120)
    customer["cycle_std"] = customer["cycle_std"].fillna(0)

    customer["expected_next_purchase_date"] = (
        pd.to_datetime(customer["last_order_date"]) +
        pd.to_timedelta(customer["avg_cycle"], unit="D")
    )
    customer["days_over_expected"] = (
        snapshot_date - customer["expected_next_purchase_date"]
    ).dt.days.clip(lower=0)

    customer["recency_ratio"] = customer["recency"] / customer["avg_cycle"].replace(0, 1)

    # category ratio
    cat_sales = hist.groupby(["고객ID", "카테고리"])["매출"].sum().reset_index()
    total_sales = hist.groupby("고객ID")["매출"].sum().rename("total_sales").reset_index()
    cat_sales = cat_sales.merge(total_sales, on="고객ID", how="left")
    cat_sales["ratio"] = cat_sales["매출"] / cat_sales["total_sales"].replace(0, 1)

    pivot = cat_sales.pivot_table(
        index="고객ID", columns="카테고리", values="ratio",
        aggfunc="sum", fill_value=0
    ).reset_index()

    pivot = pivot.rename(columns={
        "Food": "food_ratio",
        "Disposables": "disposable_ratio",
        "Grooming": "grooming_ratio",
        "Supplements": "supplements_ratio",
        "Electronics": "electronics_ratio"
    })

    for c in ["food_ratio", "disposable_ratio", "grooming_ratio", "supplements_ratio", "electronics_ratio"]:
        if c not in pivot.columns:
            pivot[c] = 0.0

    customer = customer.merge(
        pivot[["고객ID", "food_ratio", "disposable_ratio", "grooming_ratio", "supplements_ratio", "electronics_ratio"]],
        on="고객ID", how="left"
    )

    # segment
    customer["frequency_q50"] = customer["frequency"].quantile(0.5)
    customer["frequency_q60"] = customer["frequency"].quantile(0.6)
    customer["frequency_q80"] = customer["frequency"].quantile(0.8)
    customer["monetary_q60"] = customer["monetary"].quantile(0.6)
    customer["monetary_q80"] = customer["monetary"].quantile(0.8)

    customer["Final_Segment"] = customer.apply(assign_segment, axis=1)
    customer = customer.drop(columns=["frequency_q50", "frequency_q60", "frequency_q80", "monetary_q60", "monetary_q80"])

    return customer

def score_customers(df_std: pd.DataFrame) -> pd.DataFrame:
    df = preprocess_pet_data(df_std)
    snapshot_date = df["거래일시"].max()

    feat = build_customer_features(df, snapshot_date)

    model = joblib.load(MODEL_PATH)
    feature_cols = joblib.load(FEATURE_PATH)

    # 원본 세그먼트 보관
    display_df = feat.copy()
    model_df = pd.get_dummies(feat.copy(), columns=["Final_Segment"], drop_first=False)

    for col in feature_cols:
        if col not in model_df.columns:
            model_df[col] = 0

    X = model_df[feature_cols].copy()
    display_df["churn_prob"] = model.predict_proba(X)[:, 1]
    score_df = feat.copy()
    original_segment = score_df["Final_Segment"].copy()


    
    # 원본 세그먼트 복원
    display_df["Final_Segment"] = original_segment.values

    display_df["rule_risk"] = np.select(
        [
            display_df["recency_ratio"] > 2.5,
            display_df["recency_ratio"] > 1.5
        ],
        ["휴면", "위험"],
        default="정상"
    )

    display_df["model_risk"] = pd.cut(
        display_df["churn_prob"],
        bins=[-0.01, 0.3, 0.6, 0.8, 1.0],
        labels=["안정", "주의", "위험", "휴면직전"]
    )

    def explain_row(row):
        reasons = []
        if row["recency_ratio"] > 2.5:
            reasons.append("평균 구매주기 대비 장기 미구매")
        elif row["recency_ratio"] > 1.5:
            reasons.append("구매주기 초과")
        if row["food_ratio"] >= 0.4:
            reasons.append("Food 중심 고객")
        if row["disposable_ratio"] >= 0.2:
            reasons.append("Disposables 중심 고객")
        if row["days_over_expected"] > 0:
            reasons.append("예상 재구매일 경과")
        return ", ".join(reasons) if reasons else "일반 패턴"

    def recommend_action(row):
        if row["rule_risk"] == "휴면":
            return "강한 재구매 쿠폰 + 리마인드 메시지"
        if row["rule_risk"] == "위험":
            return "재구매 유도 쿠폰 + 베스트상품 추천"
        if row["food_ratio"] > 0.4:
            return "사료 정기구매 유도 캠페인"
        if row["disposable_ratio"] > 0.2:
            return "소모품 번들 추천"
        return "일반 CRM 캠페인"

    display_df["reason"] = display_df.apply(explain_row, axis=1)
    display_df["recommended_action"] = display_df.apply(recommend_action, axis=1)

    return display_df[[
        "고객ID",
        "last_order_date",
        "recency",
        "frequency",
        "monetary",
        "avg_cycle",
        "cycle_std",
        "days_over_expected",
        "recency_ratio",
        "food_ratio",
        "disposable_ratio",
        "grooming_ratio",
        "supplements_ratio",
        "electronics_ratio",
        "Final_Segment",
        "churn_prob",
        "rule_risk",
        "model_risk",
        "reason",
        "recommended_action"
    ]].sort_values("churn_prob", ascending=False)
