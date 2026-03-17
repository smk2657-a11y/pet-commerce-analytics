import streamlit as st
import pandas as pd

from .data_io import STD_REQUIRED, STD_OPTIONAL, get_sample_mapping_hint


def _guess_mapping(cols: list[str]) -> dict[str, str | None]:
    """아주 가벼운 휴리스틱(초기값)"""
    lower = {c: str(c).lower() for c in cols}

    def find_any(keys: list[str]) -> str | None:
        for c, lc in lower.items():
            for k in keys:
                if k in lc:
                    return c
        return None

    return {
        "고객ID": find_any(["고객", "customer", "cust", "user", "member", "client", "id", "uid", "no"]),
        "주문번호": find_any(["주문", "order", "invoice", "tx", "transaction", "orderno"]),
        "거래일시": find_any(["일시", "날짜", "date", "time", "datetime", "purchase", "orderdate", "created"]),
        "매출": find_any(["매출", "금액", "amount", "sales", "revenue", "price", "pay", "total"]),
        "카테고리": find_any(["카테고리", "category", "cate", "group", "producttype", "class"]),
        "구매채널": find_any(["채널", "channel", "store", "online", "offline", "source"]),
        "시도": find_any(["지역", "시도", "city", "province", "region", "state"]),
        "결제수단": find_any(["결제", "payment", "paymethod", "method", "card", "cash"]),
        "온라인채널": find_any(["온라인채널", "platform", "app", "web", "mall", "market"]),
    }


def _mapping_table_for_sample() -> pd.DataFrame:
    hint = get_sample_mapping_hint()
    explain = {
        "고객ID": "누가 샀는지(회원번호/고객번호)",
        "주문번호": "어떤 주문인지(주문 1건 ID)",
        "거래일시": "언제 샀는지(구매/주문 날짜·시간)",
        "매출": "얼마에 샀는지(주문 금액)",
        "카테고리": "무엇을 샀는지(상품 분류)",
        "구매채널": "어디서 샀는지(온라인/오프라인)",
        "온라인채널": "어느 플랫폼인지(쿠팡/스마트스토어/자사몰 등)",
        "결제수단": "어떻게 결제했는지(카드/현금 등)",
        "시도": "어느 지역인지(시/도)",
    }
    return pd.DataFrame(
        [{"표준 컬럼": k, "샘플 컬럼(추천)": v, "설명": explain.get(k, "")} for k, v in hint.items()]
    )


def mapping_step(df_raw: pd.DataFrame) -> pd.DataFrame | None:
    """
    - 샘플 데이터: 친절 UI(카드/추천표/안내 문구)
    - 업로드 CSV: 설명 최소(캡션 1줄 + 도움말 expander 기본 접힘)
    """
    is_sample = st.session_state.get("data_source") == "sample"
    cols = list(df_raw.columns)

    # -----------------------
    # 1) 데이터 확인
    # -----------------------
    st.markdown("## 1) 데이터 확인")
    if is_sample:
        st.caption("샘플 데이터를 먼저 확인하고, 다음 단계에서 표준 컬럼으로 맞춰볼게요.")
    else:
        st.caption("업로드한 데이터가 맞는지 확인하세요.")
    st.dataframe(df_raw.head(20), use_container_width=True)

    # -----------------------
    # 2) 컬럼 매핑
    # -----------------------
    st.markdown("## 2) 컬럼 매핑")
    if is_sample:
        st.caption("내 CSV 컬럼을 표준 컬럼에 연결해 주세요. 샘플은 기본값이 대부분 맞게 채워져 있어요.")
    else:
        st.caption("필수 4개(고객ID/주문번호/거래일시/매출)만 매핑하면 다음 단계로 이동합니다.")

    guesses = _guess_mapping(cols)

    # 샘플이면 "정답표"를 기본값으로 적용
    if is_sample:
        hint = get_sample_mapping_hint()
        guesses.update({k: v for k, v in hint.items() if v in cols})

    # -----------------------
    # 샘플용 친절 UI / 업로드용 미니 UI
    # -----------------------
    if is_sample:
        st.markdown(
            """
            <div class="card-muted" style="padding:14px; font-size:14px; color: rgba(0,0,0,0.75);">
              <b>샘플 데이터로 연습 중 👶</b><br/>
              이 단계는 컬럼 이름이 제각각인 CSV도 분석할 수 있게 <b>표준 컬럼</b>으로 맞춰주는 과정이에요.<br/>
              먼저 <b>필수 4개</b>만 맞추면 바로 다음 단계로 갈 수 있어요.
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("📌 샘플 데이터 추천 매핑표", expanded=True):
            st.dataframe(_mapping_table_for_sample(), use_container_width=True)
            st.caption("드롭다운 기본값이 이미 채워져 있으면 그대로 ‘확인’만 누르세요.")

        st.markdown(
            """
            <div style="margin-top:10px; font-size:13px; color: rgba(0,0,0,0.65);">
              ✅ <b>꼭 필요한 것</b>: 고객ID / 주문번호 / 거래일시 / 매출<br/>
              (선택 컬럼은 나중에 해도 돼요)
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # 업로드는 불필요한 설명 제거: 필요한 사람만 보게 접어둠
        with st.expander("도움말(필요할 때만 보기)", expanded=False):
            st.write("드롭다운에서 내 CSV 컬럼을 표준 컬럼에 매핑하세요.")
            st.write("필수 4개(고객ID/주문번호/거래일시/매출)는 반드시 지정해야 다음 단계로 넘어갑니다.")
            st.write("선택 컬럼은 없어도 진행 가능하며, 있으면 분석 품질이 좋아집니다.")

    # -----------------------
    # 폼으로 묶어서 UI 흔들림 줄이기
    # -----------------------
    with st.form("mapping_form", border=True):

        st.subheader("필수 컬럼")

        selected: dict[str, str | None] = {}

        def dropdown(label: str, default_col: str | None, key: str) -> str | None:
            options = ["(선택 안함)"] + cols
            idx = options.index(default_col) if default_col in cols else 0
            choice = st.selectbox(label, options, index=idx, key=key)
            return None if choice == "(선택 안함)" else choice

        # 1) 필수 컬럼 먼저
        for std_col in STD_REQUIRED:
            selected[std_col] = dropdown(std_col, guesses.get(std_col), key=f"req_{std_col}")

        # 2) 선택 컬럼 (샘플은 펼치고, 업로드는 접기)
        with st.expander("선택 컬럼", expanded=is_sample):
            for std_col in STD_OPTIONAL:
                selected[std_col] = dropdown(std_col, guesses.get(std_col), key=f"opt_{std_col}")

        # 상태/검증(폼 안)
        chosen = [v for v in selected.values() if v is not None]
        dup = {c for c in chosen if chosen.count(c) > 1}
        missing_required = [k for k in STD_REQUIRED if selected.get(k) is None]

        if dup:
            st.error(f"중복 매핑: {sorted(list(dup))}")

        if missing_required:
            # 업로드는 더 짧게, 샘플은 조금 친절하게
            if is_sample:
                st.warning(f"필수 컬럼이 아직 비어있어요: {missing_required}")
            else:
                st.warning(f"필수 컬럼 누락: {missing_required}")

        st.divider()
        col1, col2 = st.columns([1, 1], gap="small")
        back = col1.form_submit_button("⬅️ 업로드로 돌아가기", use_container_width=True)
        confirm = col2.form_submit_button("✅ 확인", type="primary", use_container_width=True)

    # -----------------------
    # 버튼 동작
    # -----------------------
    if back:
        st.session_state.step = 0
        st.rerun()

    if not confirm:
        return None

    if dup:
        st.error("중복 매핑을 먼저 해결해주세요.")
        return None

    if missing_required:
        st.error("필수 4개를 모두 매핑해야 다음 단계로 갈 수 있어요.")
        return None

    # -----------------------
    # 표준화 DF 생성
    # -----------------------
    rename_map = {selected[k]: k for k in selected if selected[k] is not None}

    # 안전장치: 혹시라도 키가 None이 섞였을 때 방어
    rename_map = {src: dst for src, dst in rename_map.items() if src is not None}

    df_std = df_raw[list(rename_map.keys())].copy()
    df_std.rename(columns=rename_map, inplace=True)

    st.success("매핑이 완료됐어요. 다음 단계로 넘어갑니다.")
    if is_sample:
        st.caption("샘플은 연습용이라 기본값이 잘 맞게 들어가 있어요. 이제 업로드한 CSV도 같은 방식으로 해보면 됩니다.")

    return df_std