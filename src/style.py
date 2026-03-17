import streamlit as st


TOPBAR_H = 92  # 헤더 높이(px) - 취향대로 84~110 사이 조절

def apply_style():
    CSS = f"""
    <style>
    :root {{
      --topbar-h: {TOPBAR_H}px;
    }}

    /* 기본 상단바(Deploy 있는 Streamlit header) 제거 */
    header[data-testid="stHeader"] {{
      visibility: hidden !important;
    }}
    header[data-testid="stHeader"] [data-testid*="Sidebar"],
    header[data-testid="stHeader"] button[aria-label*="sidebar"],
    header[data-testid="stHeader"] button[title*="sidebar"],
    header[data-testid="stHeader"] button[kind="headerNoPadding"]{{
      visibility: visible !important;
      opacity: 1 !important;
      pointer-events: auto !important;
    }}
    footer {{
      visibility: hidden;
    }}

    /* 앱 배경 */
    div[data-testid="stAppViewContainer"] {{
      background: #F5F7FB;
      overflow-x: hidden;
    }}

  /* ✅ 고정 헤더 때문에, 전체 컨텐츠를 헤더 높이만큼 아래로 + 중앙정렬 */
  div[data-testid="stAppViewContainer"] .main .block-container{{
    padding-top: calc(var(--topbar-h) + 24px) !important;
    padding-bottom: 48px !important;

    max-width: 1320px !important;
    margin-left: auto !important;
    margin-right: auto !important;

    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
  }}


/* =========================
   ✅ Sidebar: 헤더를 절대 안 덮게 (배경까지 내려감)
   - position: fixed 쓰지 말기(토글 깨짐 원인)
   ========================= */

    /* 사이드바 "컨테이너" 자체를 헤더 아래로 */
    section[data-testid="stSidebar"]{{
      top: var(--topbar-h) !important;
      height: calc(100vh - var(--topbar-h)) !important;
      background: #F3F4F6 !important;
    }}

    /* 사이드바 안쪽 padding은 과하게 주면 이중으로 내려가서 최소만 */
    section[data-testid="stSidebar"] > div{{
      padding-top: 10px !important;
      height: 100% !important;
      overflow: auto !important;
    }}
    
    /* =========================
       Top Hero (고정 헤더)
    ========================== */
    #top-hero {{
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      height: var(--topbar-h);
      z-index: 9999;
      display: flex;
      align-items: center;
      pointer-events: none;
      background: linear-gradient(135deg, #4F46E5, #4338CA);
      box-shadow: 0 10px 30px rgba(79,70,229,0.25);
    }}

    #top-hero .inner {{
      width: 100%;
      max-width: 1320px;
      margin: 0 auto;
      padding: 0 1.5rem;
      color: white;
      display: flex;
      flex-direction: column;
      justify-content: center;
      pointer-events: auto;
    }}
    #top-hero .title {{
      font-size: 28px;
      font-weight: 900;
      line-height: 1.05;
      margin: 0;
      color: #fff;
    }}
    #top-hero .sub {{
      font-size: 14px;
      font-weight: 600;
      margin-top: 6px;
      color: rgba(255,255,255,0.88);
    }}

    /* 기존 카드 클래스(너 프로젝트에서 쓰는 것들) */
    .card {{
      background: #ffffff;
      border-radius: 18px;
      padding: 24px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.06);
      border: 1px solid rgba(0,0,0,0.06);
    }}
    .card-muted {{
      background: rgba(59,130,246,0.08);
      border: 1px solid rgba(59,130,246,0.20);
      border-radius: 14px;
      padding: 14px 16px;
    }}

    /* empty 화면 */
    .empty {{
      width: 100%;
      min-height: 460px;
      display:flex;
      align-items:center;
      justify-content:center;
      flex-direction: column;
      gap: 10px;
    }}
    .empty .icon{{ font-size: 46px; opacity: 0.5; }}
    .empty .title{{ font-size: 28px; font-weight: 900; letter-spacing: -0.02em; }}
    .empty .desc{{ font-size: 15px; color: rgba(0,0,0,0.58); text-align:center; }}
    .empty .info{{
      margin-top: 10px;
      width: 520px;
      max-width: 92%;
      border-radius: 14px;
      padding: 14px 16px;
      background: rgba(59,130,246,0.08);
      border: 1px solid rgba(59,130,246,0.20);
      color: rgba(0,0,0,0.75);
      font-size: 14px;
    }}
    .empty .info b{{ display:block; margin-bottom: 6px; }}
    .empty ul{{ margin: 0; padding-left: 18px; }}
    
        /* ===== Report UI styles ===== */

    .h1{{
      font-size:42px;
      font-weight:900;
      letter-spacing:-0.03em;
      margin:6px 0;
    }}

    .sub{{
      font-size:14px;
      color:rgba(0,0,0,0.65);
      margin-bottom:18px;
    }}

    .kpi-grid{{
      display:grid;
      grid-template-columns:repeat(3,1fr);
      gap:14px;
    }}

    .kpi{{
      border-radius:18px;
      padding:18px;
      background:#fff;
      border:1px solid rgba(0,0,0,0.06);
      box-shadow:0 10px 22px rgba(0,0,0,0.05);
    }}

    .rfm-box{{
      background:rgba(99,102,241,0.07);
      border:1px solid rgba(99,102,241,0.18);
      border-radius:18px;
      padding:16px;
    }}

    .alert{{
      border-radius:18px;
      padding:16px;
      background:rgba(239,68,68,0.08);
      border:1px solid rgba(239,68,68,0.18);
    }}

    .bar-wrap{{
      display:flex;
      flex-direction:column;
      gap:10px;
    }}

    .row{{
      display:grid;
      grid-template-columns:220px 1fr 80px;
      gap:12px;
      align-items:center;
    }}

    .row .track{{
      height:10px;
      background:rgba(0,0,0,0.08);
      border-radius:999px;
    }}

    .row .fill{{
      height:100%;
    }}

    /* ✅ 사이드바 접힌 상태에서 나타나는 '열기(>)' 버튼 위치/우선순위 강제 */
    [data-testid="stSidebarCollapsedControl"],
    button[aria-label="Open sidebar"],
    button[title="Open sidebar"],
    button[aria-label*="Open sidebar"],
    button[title*="Open sidebar"]{{
      position: fixed !important;
      top: calc(var(--topbar-h) + 14px) !important;
      left: 14px !important;
      z-index: 10001 !important;
      visibility: visible !important;
      opacity: 1 !important;
      pointer-events: auto !important;
    }}

    </style>
    """
    st.markdown(CSS, unsafe_allow_html=True)


def render_top_hero(title: str, subtitle: str):
    st.markdown(
        f"""
        <div id="top-hero">
          <div class="inner">
            <div class="title">{title}</div>
            <div class="sub">{subtitle}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )