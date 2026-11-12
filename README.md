# Why Britain voted Leave, and where the explanation breaks

Final project of the Ironhack Data Analytics bootcamp, by Lena Chouchan.

On 23 June 2016, Great Britain voted 52.1% Leave. This project looks at the 380 counting areas of
Great Britain and asks two questions:

1. **Statistics:** what explains the Leave vote across areas?
2. **Machine learning:** where does a model built on population data fail, and why?

## Links

- **Tableau dashboard:** [Brexit Leave vote on Tableau Public](https://public.tableau.com/app/profile/lena.chouchan/viz/BrexitLeavevote/WhatexplainsLeavevote)
- **Streamlit app:** *add the link here after deploying*

## Key findings

**Education is the strongest link with the Leave vote.**
- Leave share vs share of graduates: r = -0.77.
- The 20% of areas with the most graduates voted 39.2% Leave; the 20% with the fewest voted 63.3%
  (a gap of -24.1 points).
- Other gaps between the highest and lowest 20% of areas: social grade AB -18.5 points, median pay -15.1,
  aged 65+ +12.3, claimant rate only +1.2.
- Most of the age effect is education in disguise: once graduates are in the model, age 65+ adds almost nothing.

**A model built on population data works well, except in Scotland.**
- A weighted regression with 4 population measures explains 72% of the differences between areas.
- Machine learning (Random Forest, one region held out at a time): 75% of areas outside Scotland are
  predicted within 5 points, but only 3% of Scottish councils.
- Scotland voted about 15 points less Leave than its population predicts. Adding the UKIP vote of 2014
  shrinks that gap a lot: Scotland's difference is mostly political, not demographic.

Results describe areas, not individual voters. Correlation does not show cause.

## Repository

```
├── app/                    Streamlit app "What explains the Leave vote"
│   ├── app.py
│   ├── brexit_data.py      loads the data and computes the numbers
│   └── requirements.txt
├── data/                   clean data used by the notebooks and the app
├── notebooks/
│   ├── 00_data_cleaning.ipynb
│   ├── 01_data_exploration.ipynb
│   ├── 02_statistical_tests.ipynb
│   ├── 02b_kpi_tests_and_model.ipynb
│   ├── 03_scotland_exploration.ipynb        further analysis
│   ├── 04_scotland_whatif_scenario.ipynb    further analysis (a scenario, not a forecast)
│   └── 05_machine_learning.ipynb
├── tableau/                Tableau workbook
└── requirements.txt
```

## Run it

```bash
pip install -r requirements.txt

# the app
streamlit run app/app.py

# the notebooks: open them from the notebooks folder
jupyter notebook notebooks/
```

## Data sources

- Electoral Commission: EU referendum results 2016, by counting area.
- 2011 Census and ONS: education, social grade, age, pay, claimant rate, child poverty.
- European Parliament elections 2014: UKIP vote share.
- Scottish independence referendum 2014: House of Commons Library RP14/50, cross-checked with Edinburgh DataShare.
- Boundaries: Ordnance Survey and ONS data © Crown copyright 2014, via UK-GeoJSON by Martin Chorley (CC BY 4.0).
- Brexit stance tweets: CEU annotated dataset (CC BY-SA 4.0), daily counts only.

## Tools

Python (pandas, NumPy, SciPy, scikit-learn, matplotlib, seaborn, Plotly), Streamlit, Tableau.
