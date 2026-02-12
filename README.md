# SolarAIAssistant  
### AI-Powered Rooftop Solar Feasibility & Savings Engine for Indian Households (PM Surya Ghar Ready)

SolarAIAssistant is a physics-based rooftop solar decision-support system designed specifically for Indian homeowners evaluating rooftop solar under the **PM Surya Ghar Muft Bijli Yojana**.

It answers a simple but critical question:

> “Should I install rooftop solar under PM Surya Ghar?  
> How much will I actually save?”

---

## What This Project Does

SolarAIAssistant combines:

- AI-based rooftop detection (Segment Anything Model)
- Physics-based solar simulation using pvlib
- Climate-aware modeling with real temperature data
- Real CEC solar module & inverter database integration
- Loss modeling & performance ratio calculation
- ROI & payback estimation
- Clear-sky vs real-world performance comparison

Instead of using rough estimates, this system performs **hourly photovoltaic simulation for a full year**, producing realistic energy generation results.

---

## 🇮🇳 Why This Matters for India

India is rapidly expanding rooftop solar through PM Surya Ghar. However:

- Homeowners lack clear feasibility understanding
- Online solar calculators rely on rough assumptions
- Subsidy benefits are often misunderstood
- Financial returns are not clearly projected

This project aims to provide a **trustworthy, physics-based solar decision engine tailored for Indian conditions.**

---

## Who This Is For

- Indian homeowners evaluating rooftop solar
- Solar installers pre-screening potential customers
- Climate-tech enthusiasts
- Policy & energy researchers
- Financial institutions analyzing rooftop solar ROI

---

## System Architecture

```
Choose Your Input Method:

- **Rooftop Image (Optional)** → AI Segmentation → Usable Area Calculation  
- **Monthly Electricity Bill** → Consumption Estimation  

↓

Location & State Selection  
↓
System Capacity Estimation  
↓
pvlib Time-Series Solar Simulation (Annual Generation)  
↓
Loss Modeling & Performance Ratio  
↓
PM Surya Ghar Subsidy Calculation  
↓
Net Metering & Bill Offset Modeling  
↓
10-Year Financial Projection (Savings, Degradation & Inflation)  
↓
Final Recommendation: Install or Not?
```

---

## Technical Stack

- Python
- Streamlit
- pvlib (solar performance modeling)
- Meteostat (climate data)
- Segment Anything Model (Meta AI)
- CEC Module & Inverter Databases
- Matplotlib (visualization)

---

## Current Features

- AI-based rooftop detection  
- Automated rooftop area estimation  
- System capacity sizing  
- Physics-based annual solar generation simulation  
- Clear-sky vs real-world performance comparison  
- Performance ratio calculation  
- System loss modeling  
- ROI and payback period estimation  
- Monthly energy output visualization   

---

## Installation Guide

### Clone the Repository

```
git clone https://github.com/aman-coder03/SolarAIAssistant.git
cd SolarAIAssistant
```

### Create a Virtual Environment
```
python -m venv venv
venv\Scripts\activate
```

### Install Dependencies

Install PyTorch first (if not installed):
`pip install torch torchvision`

Then install all requirements:
`pip install -r requirements.txt`

### Run the Application
`streamlit run app.py`

Open in your browser:
http://localhost:8501


## Upcoming India-Focused Enhancements

- State-wise electricity tariff modeling  
- PM Surya Ghar subsidy calculator  
- Bill-based optimal system sizing  
- Net metering logic integration  
- 10-year financial projection  
- Panel degradation modeling (0.5% per year)  
- Inflation-adjusted electricity savings  
- Intelligent decision recommendation engine