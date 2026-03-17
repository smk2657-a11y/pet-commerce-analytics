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

---

# 🤖 Machine Learning Model

이 프로젝트는 고객 이탈 위험을 예측하기 위해  
**LightGBM 기반 머신러닝 모델**을 사용합니다.

고객의 구매 행동 데이터를 기반으로  
각 고객의 **이탈 확률 (Churn Probability)** 을 계산합니다.

---

## Model

LightGBM Classifier

```
LGBMClassifier
```

LightGBM은 Gradient Boosting 기반 모델로  
대규모 데이터에서도 높은 성능을 보이는 트리 기반 모델입니다.

---

## Feature Engineering

고객 행동 데이터를 기반으로 다음 Feature를 생성합니다.

- Recency (최근 구매 경과일)
- Frequency (구매 빈도)
- Monetary (구매 금액)
- 구매 카테고리 다양성
- 구매 채널
- 환불 여부
- 고객 세그먼트

이 Feature들은 고객의 구매 패턴과 이탈 가능성을 설명하는 핵심 변수입니다.

---

## Model Performance

모델 성능은 다음 지표로 평가했습니다.

Evaluation Metrics

```
ROC-AUC : 0.70
PR-AUC  : 0.86
```

ROC-AUC는 모델의 분류 성능을 평가하는 대표적인 지표이며  
PR-AUC는 이탈 고객과 같은 **불균형 데이터 문제에서 중요한 성능 지표**입니다.

---

## Model Output

모델은 고객별로 다음 값을 예측합니다.

```
churn probability
```

이를 기반으로 시스템은

- High Risk 고객 식별
- 고객 세그먼트 분석
- CRM 전략 추천
- 예상 매출 손실 계산

을 수행합니다.

---

## Model Files

머신러닝 모델은 학습 후 `.pkl` 파일로 저장되어  
Streamlit 분석 시스템에서 사용됩니다.

```
models
 ├── pet_churn_lgbm.pkl
 └── pet_churn_feature_cols.pkl
```

Streamlit 애플리케이션에서 해당 모델을 로드하여  
실시간으로 고객 이탈 위험을 예측합니다.

---

# 🔬 Data Science Pipeline

이 프로젝트는 다음과 같은 **End-to-End 데이터 분석 파이프라인**으로 구성되어 있습니다.

```
Raw Transaction Data
        ↓
Data Cleaning & Preprocessing
        ↓
Feature Engineering
        ↓
Customer Segmentation (RFM)
        ↓
Machine Learning Model Training
        ↓
Churn Prediction
        ↓
Customer Risk Analysis
        ↓
CRM Strategy Recommendation
        ↓
Streamlit Analytics Dashboard
```

이 구조는 단순한 시각화 대시보드가 아니라  
**실제 데이터 분석 및 머신러닝 기반 고객 분석 시스템**입니다.

---

# 📊 Example Insights

이 시스템을 통해 다음과 같은 비즈니스 인사이트를 얻을 수 있습니다.

- 어떤 고객이 이탈할 가능성이 높은가
- 어떤 상품 카테고리에서 고객 이탈이 많이 발생하는가
- VIP 고객 중 이탈 위험 고객은 누구인가
- 예상되는 매출 손실 규모는 얼마인가
- 어떤 고객에게 CRM 캠페인을 진행해야 하는가

---

# 🚀 Future Improvements

향후 개선 가능 영역

- 더 다양한 고객 행동 Feature 추가
- 딥러닝 기반 모델 실험
- 실시간 고객 분석 시스템 구축
- 마케팅 자동화 시스템 연동
- 추천 시스템 추가

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

Customer Analytics  
Churn Prediction  
CRM Strategy