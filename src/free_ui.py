# src/free_ui.py
import streamlit as st
import pandas as pd
from .analytics import compute_rfm_and_risk


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


def _fmt_percent(x) -> str:
    try:
        return f"{float(x):.1f}%"
    except Exception:
        return "-"


def _make_status_comment(high_ratio: float, refund_rate: float, expected_loss: int) -> str:
    if high_ratio >= 30:
        return f"현재 고객 이탈 위험이 높은 편입니다. 지금 대응하지 않으면 예상 매출 손실은 {_fmt_currency(expected_loss)} 수준으로 보입니다."
    if refund_rate >= 2:
        return f"이탈 위험은 보통 수준이지만 환불 비율이 높아 상품/배송/품질 이슈를 함께 점검하는 것이 좋습니다."
    return f"현재 전체 위험도는 비교적 안정적입니다. 다만 이탈 위험 고객 관리와 재구매 유도는 계속 필요합니다."


def _make_simple_action_list(high_ratio: float, refund_rate: float, top_cat: str, top_seg: str):
    actions = []

    if high_ratio >= 30:
        actions.append("이탈 위험 고객에게 재구매 알림이나 할인 쿠폰을 먼저 보내세요.")
    else:
        actions.append("최근 구매가 끊긴 고객부터 순서대로 다시 연락해보세요.")

    if refund_rate >= 1:
        actions.append("환불이 있는 카테고리는 상품 설명·배송·품질 문제를 먼저 점검하세요.")

    if top_seg == "휴면형":
        actions.append("휴면형 고객 비중이 커 복귀 캠페인을 우선 운영하는 것이 좋습니다.")
    elif top_seg == "VIP":
        actions.append("VIP 고객은 별도 혜택으로 이탈을 막는 것이 중요합니다.")
    elif top_cat and top_cat != "-":
        actions.append(f"{top_cat} 카테고리는 상대적으로 위험도가 높아 우선 관리가 필요합니다.")

    return actions[:3]


def _customer_action(row) -> str:
    seg = str(row.get("세그먼트", ""))
    risk = str(row.get("위험도", ""))
    recency = pd.to_numeric(row.get("Recency", 0), errors="coerce")

    if risk == "High" and seg == "VIP":
        return "VIP 혜택 안내"
    if risk == "High" and pd.notna(recency) and recency >= 120:
        return "복귀 쿠폰 발송"
    if risk == "High":
        return "재구매 알림"
    return "일반 관리"


def free_report_step(df_std: pd.DataFrame):
    result = compute_rfm_and_risk(df_std)

    kpi = result["kpi"]
    rfm_df = result["rfm"]
    cust_list = result["customer_list"]
    cat = result["category_risk"]
    seg = result["segment_summary"]
    refund = result.get("refund", {})

    total_customers = int(kpi.get("total_customers", 0) or 0)
    high_ratio = float(kpi.get("high_ratio", 0) or 0)
    expected_loss = int(kpi.get("expected_loss", 0) or 0)
    refund_rate = float(refund.get("refund_rate", 0) or 0)

    top_cat = "-"
    if isinstance(cat, pd.DataFrame) and not cat.empty and "카테고리" in cat.columns:
        try:
            top_cat = str(cat.sort_values("위험", ascending=False).iloc[0]["카테고리"])
        except Exception:
            pass

    top_seg = "-"
    if isinstance(seg, pd.DataFrame) and not seg.empty and "세그먼트" in seg.columns and "인원" in seg.columns:
        try:
            top_seg = str(seg.sort_values("인원", ascending=False).iloc[0]["세그먼트"])
        except Exception:
            pass

    status_comment = _make_status_comment(high_ratio, refund_rate * 100, expected_loss)
    action_list = _make_simple_action_list(high_ratio, refund_rate * 100, top_cat, top_seg)

    st.markdown('<div class="h1">쉬운 분석 결과</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub">소상공인도 바로 이해할 수 있도록 핵심 내용만 쉽고 직관적으로 보여드립니다.</div>',
        unsafe_allow_html=True,
    )

    # ----------------------------
    # KPI 카드
    # ----------------------------
    c1, c2, c3, c4 = st.columns(4)

    card_data = [
        ("전체 고객 수", f"{_fmt_int(total_customers)}명", "현재 분석 대상 고객 규모"),
        ("이탈 위험 고객 비율", _fmt_percent(high_ratio), f"고객 10명 중 약 {round(high_ratio/10,1)}명 수준"),
        ("예상 매출 손실", _fmt_currency(expected_loss), "빠른 대응이 필요한 예상 손실"),
        ("환불률", _fmt_percent(refund_rate * 100), "전체 주문 대비 환불 비율"),
    ]

    for col, (title, value, desc) in zip([c1, c2, c3, c4], card_data):
        with col:
            st.markdown(
                f"""
                <div class="card" style="padding:22px; min-height:180px;">
                  <div style="font-size:13px; color:rgba(0,0,0,0.55); font-weight:800;">{title}</div>
                  <div style="font-size:42px; font-weight:900; margin-top:22px; line-height:1.15;">{value}</div>
                  <div style="margin-top:14px; font-size:13px; color:rgba(0,0,0,0.55); line-height:1.5;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # ----------------------------
    # 한눈에 보기
    # ----------------------------
    st.markdown(
        f"""
        <div class="card" style="padding:20px 22px;">
          <div style="font-size:22px; font-weight:900; margin-bottom:10px;">한눈에 보기</div>
          <div style="font-size:16px; line-height:1.85; color:rgba(0,0,0,0.75);">
            {status_comment}<br/>
            현재 가장 주의해서 볼 카테고리는 <b>{top_cat}</b>이며,
            고객 그룹 기준으로는 <b>{top_seg}</b> 관리가 중요합니다.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # ----------------------------
    # 운영자가 바로 알아야 할 내용
    # ----------------------------
    a1, a2 = st.columns([1.2, 1])

    with a1:
        st.markdown("## 지금 관리가 필요한 고객")
        st.markdown(
            "<div class='sub' style='margin-top:-6px;'>복잡한 분석보다, 바로 연락하거나 관리해야 할 고객만 추려서 보여드립니다.</div>",
            unsafe_allow_html=True,
        )

        show = cust_list.copy()
        if isinstance(show, pd.DataFrame) and not show.empty:
            if "위험도" in show.columns:
                show = show[show["위험도"].eq("High")].copy()

            if "주문금액" in show.columns:
                show["주문금액"] = show["주문금액"].apply(_fmt_currency)

            if "Recency" in show.columns:
                show["최근 구매 경과일"] = show["Recency"]

            show["추천조치"] = show.apply(_customer_action, axis=1)

            cols = [c for c in ["고객ID", "최근 구매 경과일", "주문금액", "세그먼트", "추천조치"] if c in show.columns]
            show = show[cols].head(10)

            st.dataframe(show, use_container_width=True, hide_index=True)
        else:
            st.info("관리 대상 고객 데이터가 없습니다.")

    with a2:
        st.markdown("## 지금 가장 위험한 카테고리")
        st.markdown(
            "<div class='sub' style='margin-top:-6px;'>카테고리 기준으로 어떤 영역을 먼저 챙겨야 하는지 보여줍니다.</div>",
            unsafe_allow_html=True,
        )

        if isinstance(cat, pd.DataFrame) and not cat.empty:
            cat_show = cat.sort_values("위험", ascending=False).head(5).copy()
            for i, (_, row) in enumerate(cat_show.iterrows(), start=1):
                name = row.get("카테고리", "-")
                risk = row.get("위험", "-")
                cnt = row.get("고객수", "-")

                st.markdown(
                    f"""
                    <div class="card" style="padding:14px 16px; margin-bottom:10px;">
                      <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div style="font-size:16px; font-weight:900;">{i}. {name}</div>
                        <div style="font-size:13px; color:rgba(0,0,0,0.58);">위험 {risk}점 · 고객 {cnt}명</div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("카테고리 위험도 데이터가 없습니다.")

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # ----------------------------
    # 고객 그룹 요약
    # ----------------------------
    st.markdown("## 고객 그룹 요약")
    st.markdown(
        "<div class='sub' style='margin-top:-6px;'>어떤 고객군이 많은지, 평균 주문과 금액이 어떤지 쉽게 볼 수 있습니다.</div>",
        unsafe_allow_html=True,
    )

    if isinstance(seg, pd.DataFrame) and not seg.empty:
        seg_show = seg.copy()
        if "평균주문" in seg_show.columns:
            seg_show["평균주문"] = seg_show["평균주문"].round(2)
        if "평균금액" in seg_show.columns:
            seg_show["평균금액"] = seg_show["평균금액"].round(0).astype(int).apply(_fmt_currency)
        if "평균위험" in seg_show.columns:
            seg_show["평균위험"] = seg_show["평균위험"].round(1)

        st.dataframe(seg_show, use_container_width=True, hide_index=True)
    else:
        st.info("고객 그룹 요약 데이터가 없습니다.")

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # ----------------------------
    # 추천 액션
    # ----------------------------
    st.markdown("## 추천 액션")
    st.markdown(
        "<div class='sub' style='margin-top:-6px;'>바로 실행할 수 있는 운영 액션을 정리했습니다.</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='card' style='padding:18px 20px; line-height:1.95;'>" +
        "<ul style='margin:0; padding-left:18px;'>" +
        "".join([f"<li><b>{x}</b></li>" for x in action_list]) +
        "</ul></div>",
        unsafe_allow_html=True,
    )