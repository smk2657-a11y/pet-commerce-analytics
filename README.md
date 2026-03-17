# 🐶 Pet Commerce Customer Analytics Platform

반려동물 커머스 데이터를 기반으로  
**고객 행동 분석 · 이탈 위험 예측 · CRM 전략 추천**을 수행하는  
**데이터 분석 + Streamlit 기반 SaaS형 분석 플랫폼**입니다.

이 프로젝트는 단순한 대시보드가 아니라

✔ 고객 세분화  
✔ 이탈 위험 분석  
✔ 매출 손실 예측  
✔ 운영 전략 추천  

까지 자동으로 수행하는 **데이터 분석 시스템**입니다.

---

# 🎯 Project Goal

소규모 온라인 쇼핑몰 운영자도 사용할 수 있는  
**데이터 기반 고객 관리 자동화 분석 플랫폼**을 구축하는 것이 목표입니다.

### 문제

많은 소상공인 쇼핑몰은

- 고객 데이터를 분석하지 못함
- 이탈 고객을 미리 파악하지 못함
- 어떤 고객에게 마케팅해야 할지 모름

### 해결

이 플랫폼은

1️⃣ 거래 데이터를 업로드하면  
2️⃣ 자동으로 고객 행동을 분석하고  
3️⃣ 이탈 위험 고객을 찾아내며  
4️⃣ 마케팅 전략까지 추천합니다.

---

# 🧠 Core Analytics

이 프로젝트는 단순 대시보드가 아니라  
**실제 데이터 분석 로직이 포함된 분석 시스템입니다.**

---

## 1️⃣ RFM 기반 고객 세분화

고객을 다음 기준으로 분석합니다.

- Recency (최근 구매)
- Frequency (구매 빈도)
- Monetary (구매 금액)

세그먼트 예시

- VVIP
- VIP
- 활성 고객
- 관심 필요 고객
- 휴면 고객

---

## 2️⃣ 고객 이탈 위험 분석

고객 행동 데이터를 기반으로  
**이탈 위험 점수 (Risk Score)** 를 계산합니다.

분석 기준

- 구매 빈도 감소
- 최근 구매 경과일 증가
- 구매 금액 변화
- 환불 여부

출력 결과

- High Risk 고객 식별
- 예상 매출 손실 계산
- 고객별 대응 전략 추천

---

## 3️⃣ 카테고리 위험 분석

어떤 상품 카테고리에서  
고객 이탈이 많이 발생하는지 분석합니다.

예시

사료 → 안정적  
간식 → 중간 위험  
장난감 → 높은 이탈 위험  

이를 통해

- 상품 전략
- 마케팅 우선순위

를 결정할 수 있습니다.

---

## 4️⃣ 환불 분석

환불 데이터를 분석하여

- 고객 경험 문제
- 상품 문제
- 배송 문제

가능성을 분석합니다.

---

## 5️⃣ 매출 손실 예측

이탈 위험 고객을 기반으로

Expected Revenue Loss

예상 매출 손실을 계산합니다.

---

# 📊 Visualization

Streamlit + Plotly 기반 인터랙티브 분석

지원 차트

- RFM Scatter Plot
- Risk Heatmap
- Category Risk Chart
- Segment Distribution
- Customer Risk Table

---

# 🧾 PDF Report Export

분석 결과를 **PDF 리포트로 자동 생성**할 수 있습니다.

포함 내용

- KPI 요약
- 세그먼트 분석
- 카테고리 위험도
- 고객 리스트
- 이탈 예측 결과

PDF는 **ReportLab 기반으로 생성됩니다.**

---

# 🗂 Project Structure

```
project
│
├── app.py
│
├── src
│   ├── analytics.py
│   ├── churn_model.py
│   ├── data_io.py
│   ├── mapping_ui.py
│   ├── free_ui.py
│   ├── report_ui.py
│   ├── pdf_export.py
│   ├── auth.py
│   ├── storage.py
│   └── style.py
│
├── models
│   ├── pet_churn_lgbm.pkl
│   └── pet_churn_feature_cols.pkl
│
├── users.yaml
├── requirements.txt
└── README.md
```

---

# ⚙️ Tech Stack

### Data Analysis
- Python
- Pandas
- Numpy

### Machine Learning
- LightGBM
- Scikit-learn

### Visualization
- Plotly
- Streamlit

### Backend
- SQLite
- YAML Authentication

### Report Generation
- ReportLab

---

# 🚀 How to Run

### 1️⃣ Install dependencies

```
pip install -r requirements.txt
```

### 2️⃣ Run Streamlit

```
streamlit run app.py
```

### 3️⃣ Open browser

```
http://localhost:8501
```

---

# 🧩 Key Features

✔ CSV 업로드 기반 자동 분석  
✔ 컬럼 자동 매핑 기능  
✔ 고객 세분화 (RFM)  
✔ 고객 이탈 위험 분석  
✔ 예상 매출 손실 계산  
✔ PDF 리포트 자동 생성  
✔ 분석 결과 저장 및 관리  

---

# 📈 Example Workflow

```
CSV 업로드
      ↓
컬럼 자동 매핑
      ↓
고객 데이터 분석
      ↓
이탈 위험 계산
      ↓
카테고리 위험 분석
      ↓
CRM 전략 추천
      ↓
PDF 리포트 생성
```

---

# 💡 Portfolio Highlights

이 프로젝트는 다음 역량을 보여줍니다.

✔ 데이터 분석 파이프라인 구축  
✔ 고객 행동 분석 (Customer Analytics)  
✔ 이탈 예측 모델 적용  
✔ 데이터 기반 비즈니스 인사이트 도출  
✔ Streamlit 기반 데이터 제품 개발  

---

# 👨‍💻 Author

Data Analyst Portfolio Project

Customer Analytics  
Churn Prediction  
CRM Strategy