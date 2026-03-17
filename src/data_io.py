import io
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime


# 표준 컬럼 (프로젝트에서 "고정"으로 쓰는 이름)
STD_REQUIRED = ["고객ID", "주문번호", "거래일시", "매출"]
STD_OPTIONAL = ["카테고리", "구매채널", "온라인채널", "결제수단", "시도"]


def make_sample_data(n_tx: int = 300, seed: int = 7) -> pd.DataFrame:
    """
    초보자 연습용 샘플 데이터
    - 일부러 컬럼명을 표준 컬럼과 다르게 구성(매핑 연습)
    - 날짜/금액 문자열(콤마 포함)로도 들어오게 구성
    """
    rng = np.random.default_rng(seed)

    customers = rng.integers(10000, 20000, size=120)
    cust_ids = rng.choice(customers, size=n_tx, replace=True)

    start = datetime(2024, 1, 1)
    end = datetime(2024, 2, 29)
    dates = pd.to_datetime(
        rng.integers(int(start.timestamp()), int(end.timestamp()), size=n_tx),
        unit="s",
    )
    # 일부러 문자열 포맷 섞기(파싱 연습)
    date_str = np.where(
        rng.random(n_tx) < 0.5,
        dates.strftime("%Y/%m/%d %H:%M"),
        dates.strftime("%Y-%m-%d"),
    )

    order_ids = np.arange(1, n_tx + 1)

    categories = np.array(["사료", "간식", "장난감", "위생용품", "미용"])
    cat = rng.choice(categories, size=n_tx, p=[0.30, 0.30, 0.15, 0.15, 0.10])

    channel = rng.choice(["온라인", "오프라인"], size=n_tx, p=[0.78, 0.22])
    sido = rng.choice(["서울", "부산", "대구", "인천", "광주", "대전", "울산", "경기", "제주"], size=n_tx)

    pay = rng.choice(["카드", "현금", "계좌이체", "간편결제"], size=n_tx, p=[0.55, 0.15, 0.10, 0.20])
    platform = rng.choice(["스마트스토어", "쿠팡", "자사몰", "매장"], size=n_tx, p=[0.35, 0.35, 0.20, 0.10])

    base = {"사료": 32000, "간식": 15000, "장난감": 22000, "위생용품": 18000, "미용": 26000}
    amount = np.array([max(1000, int(rng.normal(base[c], base[c] * 0.45))) for c in cat])

    # ✅ 핵심: 표준 컬럼명과 다르게 구성(매핑 연습용)
    return pd.DataFrame(
        {
            "customer_no": cust_ids.astype(int),           # 고객ID
            "order_id": order_ids.astype(int),             # 주문번호
            "purchase_date": date_str,                     # 거래일시
            "total_price": [f"{x:,}" for x in amount],     # 매출(콤마 포함)
            "product_group": cat,                          # 카테고리
            "sales_channel": channel,                      # 구매채널
            "platform_name": platform,                     # 온라인채널
            "pay_type": pay,                               # 결제수단
            "region_name": sido,                           # 시도
            "상품명": rng.choice(["사료A", "간식B", "장난감C", "샴푸D", "패드E"], size=n_tx),  # 이해용
        }
    )


def get_sample_mapping_hint() -> dict:
    """샘플 데이터가 어떤 표준 컬럼으로 매핑되는지 '정답표'"""
    return {
        "고객ID": "customer_no",
        "주문번호": "order_id",
        "거래일시": "purchase_date",
        "매출": "total_price",
        "카테고리": "product_group",
        "구매채널": "sales_channel",
        "온라인채널": "platform_name",
        "결제수단": "pay_type",
        "시도": "region_name",
    }


def read_csv_safely(uploaded_file) -> pd.DataFrame:
    """UTF-8 / CP949 + 구분자 자동감지(가능하면) 방어."""
    def _try_read(enc):
        uploaded_file.seek(0)
        # sep=None + engine=python이면 , / ; / \t 등을 어느 정도 자동 감지
        df = pd.read_csv(uploaded_file, encoding=enc, sep=None, engine="python")
        df.columns = [str(c).strip() for c in df.columns]
        return df

    for enc in ["utf-8", "cp949", None]:
        try:
            return _try_read(enc)
        except Exception:
            continue

    uploaded_file.seek(0)
    df = pd.read_csv(uploaded_file, encoding="cp949")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def load_csv_or_sample_sidebar() -> pd.DataFrame | None:
    """
    STEP 0: 사이드바에서 업로드/샘플 선택 UI를 그린 뒤
    선택되면 df를 반환. 없으면 None.

    ✅ UI 순서(요구사항 반영)
    1) 설명 카드
    2) 파일 업로드
    3) OR 구분선
    4) 샘플 사용 버튼
    5) 샘플 CSV 다운로드 버튼
    """
    with st.sidebar:


        # 1) 설명 카드
        st.markdown(
            """
            <div class="card-muted" style="font-size:13px; color: rgba(0,0,0,0.70);">
              <b>사용 방법</b><br/>
              • CSV를 업로드하거나<br/>
              • 샘플 데이터로 먼저 연습할 수 있어요.<br/><br/>
              다음 단계에서 <b>컬럼명이 달라도 표준 컬럼으로 매핑</b>하면 됩니다.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

        # 2) 파일 업로드
        st.markdown('<div class="label">📁 CSV 업로드</div>', unsafe_allow_html=True)
        up = st.file_uploader(
            "CSV 파일 선택",
            type=["csv"],
            label_visibility="collapsed",
            help="업로드 후 다음 단계에서 컬럼을 매핑합니다.",
        )
        if up is not None:
            st.session_state.data_source = "upload"
            return read_csv_safely(up)

        # 3) OR 구분선
        st.markdown(
            """
            <div style="display:flex; align-items:center; gap:10px; margin:14px 0;">
              <div style="flex:1; height:1px; background: rgba(0,0,0,0.15);"></div>
              <div style="font-size:12px; color: rgba(0,0,0,0.55); font-weight:600;">OR</div>
              <div style="flex:1; height:1px; background: rgba(0,0,0,0.15);"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 샘플 준비(버튼/다운로드 공용)
        sample_df = make_sample_data()
        buf = io.StringIO()
        sample_df.to_csv(buf, index=False)

        # 4) 샘플 사용 버튼
        use_sample = st.button("✨ 샘플 데이터 사용", type="primary", use_container_width=True)
        if use_sample:
            st.session_state.data_source = "sample"
            st.success("샘플 데이터를 불러왔습니다! 다음 화면에서 컬럼 매핑을 진행해보세요.")
            return sample_df

        # 5) 샘플 CSV 다운로드 버튼
        st.download_button(
            "📥 샘플 CSV 다운로드",
            data=buf.getvalue(),
            file_name="sample_data.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # (선택) 표준 컬럼 안내
        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        st.markdown('<div class="label">📌 표준 컬럼(매핑 대상)</div>', unsafe_allow_html=True)
        st.caption("필수: 고객ID, 주문번호, 거래일시, 매출")
        st.caption("선택: 카테고리, 구매채널, 온라인채널, 결제수단, 시도")

    return None