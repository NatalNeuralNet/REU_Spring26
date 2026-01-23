# Streamlit Thin-Films (Reflectivity / Transmission) App

An interactive Streamlit app for exploring optical thin films using real materials (n,k) from a **local refractiveindex.info database**. Select materials, wavelength(s), angle(s), and polarization to compute and visualize reflectivity/transmission behavior.

> Built for fast iteration: browse materials → pick parameters → immediately see optical results.

---

## Features

- **Material picker from local refractiveindex.info database** (YAML `n,k` data)
- Interface calculations (Fresnel coefficients) with **complex refractive indices**
- Supports **angle of incidence** sweeps and **wavelength** sweeps (depending on your UI)
- Polarization controls: **s / p / unpolarized**
- Tables + plots for quick inspection (R, T, phase if enabled)
- Streamlit caching for faster repeated runs

---

## Requirements

- Python **3.10+** recommended
- A **local copy** of the refractiveindex.info YAML database
---

## Installation

### 1) Clone the repo
```bash
git clone https://github.com/NatalNeuralNet/REU_Spring26
cd REU_Spring26
```
---
### 1a)Install the refractiveindex.info database
```bash
git clone https://github.com/polyanskiy/refractiveindex.info-database.git refractiveindex.info-database
```
### 2) Create and activate a virtual environment

  - ### Windows (PowerShell)
```bash
cd C:\Users\YOUR_USERNAME\REU_Spring26
python -m venv .venv
.venv\Scripts\activate.bat
```
  - ### macOS/Linux
```bash
python -m venv .venv
source .venv/bin/activate
```
### 3) Install dependencies
```bash
pip install -r requirements.txt
```

If you don’t have a requirements.txt yet, generate one after installing what you use:

pip freeze > requirements.txt

### 4) Run the App
```bash
streamlit run st.py
```
### Project File structure 

```plaintext
REU_Spring26/
│── refractiveindex.info-database/
|  │── database
|
│── background.ipynb
│── display_functions.py
│── physics_functions.py
│── st.py
│── requirements.txt
│── README.md
│── .gitignore
```
