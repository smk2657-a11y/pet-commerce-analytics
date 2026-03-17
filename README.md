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

# 📌 Project Background

## E-commerce Industry

이커머스 산업에서는 **신규 고객 확보보다 기존 고객 유지가 훨씬 높은 수익성을 가진다.**

- 신규 고객 확보 비용은 기존 고객 유지보다 **5~25배 높음**
- 고객 유지율이 **5% 증가하면 이익이 25~95% 증가**

한국 이커머스 시장은 **네이버, 쿠팡 등 대형 종합 쇼핑 플랫폼 중심으로 성장**하고 있으며  
판매자들은 다양한 플랫폼에서 판매 데이터를 얻고 있다.

하지만 플랫폼마다 **데이터 형식이 서로 달라 통합 분석이 어렵고**,  
데이터의 양은 늘어나지만 **활용 방법을 몰라 제대로 활용하지 못하는 경우가 많다.**

따라서 판매자가 데이터를 활용해 **고객 이탈을 관리하고 매출을 유지할 수 있는 분석 플랫폼**이 필요하다.

---

## Pet Industry

반려동물 시장은 지속적으로 성장하고 있다.

- 반려동물 보유 인구: **1,546만 명 (전체 인구의 29.9%)**
- 반려동물 가구 수 **6만 가구 증가**
- 월 평균 반려동물 관리 지출  
  **194,000원 (약 142달러)**

이는 2년 전 **154,000원 대비 약 6.8% 증가한 수치**이다.

이러한 시장 성장 속에서 반려동물 판매자가  
**고객 데이터를 활용해 효율적으로 운영할 수 있는 분석 플랫폼**을 구축하는 것이 본 프로젝트의 목적이다.

---

# 🧠 Problem Definition (SCQA)

## S — Situation

- 이커머스 산업의 성장으로 방대한 고객 데이터가 축적되고 있다.
- 고객 이탈 예측과 관리가 기업 수익성에 매우 중요한 요소가 되었다.
- 반려동물 판매자는 여러 플랫폼에서 판매하기 때문에 데이터 구조가 서로 다르다.

---

## C — Complication

- 고객군별 구매 패턴이 달라 이탈 예측이 어렵다.
- 고가치 고객이 이탈하면 매출 손실이 크게 발생한다.
- 다양한 플랫폼 데이터를 통합 분석하기 어렵다.

---

## Q — Question

본 프로젝트는 다음 질문에 답하고자 한다.

- RFM·CLV 기반 고객 세그먼트는 어떤 행동적 차이를 보이는가?
- 머신러닝을 통해 **고객 이탈을 사전에 예측할 수 있는가?**
- 고객 세그먼트별 **효과적인 CRM 전략은 무엇인가?**
- 서로 다른 플랫폼 데이터를 **통합 분석할 수 있는가?**

---

## A — Answer

이 프로젝트는 다음 방식으로 문제를 해결한다.

- RFM / CLV 기반 고객 세그먼트 생성
- 머신러닝 기반 고객 이탈 예측 모델 구축
- 데이터 업로드 시 자동 컬럼 매핑
- 분석 결과를 시각화 대시보드로 제공

이를 통해 판매자는

- 고객 세그먼트
- 고객 이탈 위험도
- 카테고리별 매출 위험
- CRM 전략

을 쉽게 파악할 수 있다.

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

### Install dependencies

```
pip install -r requirements.txt
```

### Run Streamlit

```
streamlit run app.py
```

### Open browser

```
http://localhost:8501
```

---

# 🧠 Machine Learning Model

이 프로젝트는 **LightGBM 기반 머신러닝 모델**을 활용하여  
고객 이탈 위험을 예측합니다.

---

## Model

```
LGBMClassifier
```

---

## Model Performance

```
ROC-AUC : 0.70
PR-AUC  : 0.86
```

---

# 🔬 Data Science Pipeline

```
Raw Data
   ↓
Data Preprocessing
   ↓
Feature Engineering
   ↓
RFM / CLV Analysis
   ↓
Machine Learning Model
   ↓
Customer Churn Prediction
   ↓
Risk Analysis
   ↓
Streamlit Dashboard
```

---

# 📈 Example Insights

- 어떤 고객이 이탈할 가능성이 높은가
- 어떤 상품 카테고리에서 고객 이탈이 많이 발생하는가
- VIP 고객 중 이탈 위험 고객은 누구인가
- 예상 매출 손실 규모는 얼마인가
- 어떤 고객에게 CRM 캠페인을 진행해야 하는가

---

# 🚀 Future Improvements

- 카테고리별 churn prediction 모델 확장
- 추천 시스템 추가
- 실시간 고객 분석 시스템 구축
- 마케팅 자동화 시스템 연동

---

# 📦 Version History

| Version | Description |
|------|------|
| v1.5.1 | 로그인 시 이전 분석 기록 자동 표시 |
| v1.5.0 | 머신러닝 churn 기준 개선 및 유료/무료 기능 분리 |
| v1.4.0 | LightGBM 기반 리스크 예측 및 환불 분석 탭 추가 |
| v1.3.0 | 분석 비교 UI 구조 개선 |
| v1.2.0 | SQLite 기반 분석 기록 저장 기능 추가 |
| v1.1.0 | 로그인 / 회원가입 기능 추가 |
| v1.0.0 | CSV 업로드 및 컬럼 매핑 기능 구현 |

---

# 👨‍💻 Author

Data Analytics Portfolio Project
Customer Analytics / Churn Prediction / CRM Strategy