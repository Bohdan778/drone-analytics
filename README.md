<<<<<<< HEAD
# 🚁 Drone Analytics System

## 📌 Про проєкт

Цей проєкт створюється в рамках хакатону та призначений для аналізу телеметрії польотів БПЛА (Ardupilot).

Система:

* парсить лог-файли польоту
* обробляє GPS та IMU дані
* обчислює ключові метрики (швидкість, висота, дистанція)
* будує 3D траєкторію польоту
* (опціонально) генерує AI-висновки

---

## ⚙️ Як запустити проєкт

### 1. Клонувати репозиторій

```
git clone https://github.com/Bohdan778/drone-analytics.git
cd drone-analytics
```

### 2. Створити віртуальне середовище

```
python -m venv venv
venv\Scripts\activate
```

### 3. Встановити залежності

```
pip install -r requirements.txt
```

### 4. Запустити застосунок

```
streamlit run app/streamlit_app.py
```

---

## 👥 Розподіл ролей

* **Богдан** – Data Processing, Analytics
* **Артур** – Алгоритми, координатні системи, математика
* **Влад** – UI (Streamlit), інтерактивний інтерфейс
* **Даня** – 3D візуалізація (Plotly)

---
=======
# 🚁 Drone Flight Analytics Platform

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red)
![Plotly](https://img.shields.io/badge/Plotly-3D%20Viz-success)
![AI](https://img.shields.io/badge/AI-Hybrid%20Engine-purple)

A robust, full-stack telemetry analysis tool for ArduPilot drone logs (`.bin` / `.log`). This application parses low-level IMU and GPS data, calculates precise flight metrics, visualizes 3D trajectories, and provides a **Hybrid AI Diagnostic System** (Rule-based heuristics + optional Gemini LLM insights).

---

## 🌟 Key Features

* **⚡ Direct Binary Parsing:** Ingests ArduPilot MAVLink logs (`.bin`/`.log`) directly via `pymavlink`—no external conversion tools needed.
* **🧮 Advanced Physics Engine:** 
  * Converts WGS84 GPS coordinates to local ENU (East-North-Up) Cartesian space.
  * Computes dynamic velocity via **Trapezoidal IMU Integration** (using raw X/Y/Z accelerations + gravity compensation).
* **🎮 Interactive 3D Trajectory:** High-performance WebGL Plotly visualization. Color-map the flight path by time or 3D speed.
* **🧠 Hybrid AI Auto-Diagnostics (Production Ready):** 
  * **Local AI Engine (Offline):** Instant rule-based heuristics (Crash detection, regulatory altitude limits, extreme maneuver alerts).
  * **LLM Deep Insights (Cloud):** Connects to Google's `gemini-2.0-flash` for expert aviation summaries.
  * **🛡️ Graceful Fallback:** If the LLM API is unavailable (rate limits/network issues), the system smoothly degrades to the Local AI Engine without crashing.

---

## 🚀 Getting Started

Follow these simple steps to run the platform locally. 

### Prerequisites
* Python 3.9 or higher
* Git

### 💻 Option 1: Standard Local Installation

**1. Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/drone-analytics.git
cd drone-analytics
```

**2. Create and activate a Virtual Environment**
* **Mac/Linux:**
  ```bash
  python -m venv venv
  source venv/bin/activate
  ```
* **Windows:**
  ```cmd
  python -m venv venv
  venv\Scripts\activate
  ```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure AI (Optional but recommended)**
To enable the Deep LLM Analysis, create a file named `.env` in the root folder and add your Google Gemini API key:
```env
GEMINI_API_KEY=your_actual_api_key_here
```
*(Note: The app works perfectly fine without this key using its Local AI fallback!)*

**5. Launch the Application**
```bash
streamlit run app/streamlit_app.py
```
The app will automatically open in your browser at `http://localhost:8501`.

---

### 🐳 Option 2: Run via Docker (Isolated)

If you have Docker installed, you can run the app without setting up Python environments:

**Build the image:**
```bash
docker build -t drone-analytics .
```

**Run the container:**
```bash
docker run -p 8501:8501 -e GEMINI_API_KEY="your_api_key_here" drone-analytics
```
Open your browser at: `http://localhost:8501`

---

## 🧠 Mathematical Models Used

### 1. Velocity via IMU Integration
Velocity is derived strictly from accelerometer data rather than GPS derivation to ensure high-frequency accuracy:
$$V_x(t) = \int a_x dt \approx \sum \frac{1}{2}(a_{x, i} + a_{x, i-1}) \Delta t$$
*(A static initialization window is used to estimate and strip the $1G$ gravity bias from the Z-axis).*

### 2. Haversine Distance
Used to calculate horizontal travel distance between GPS coordinate pairs accurately over the Earth's sphere.

### 3. WGS84 to ENU (East-North-Up)
Approximates the Earth as flat over the short local flight distance to convert Lat/Lon/Alt into X/Y/Z meters relative to the home launch coordinate.

---
*Developed for the Drone Analytics challenge.*
>>>>>>> dev
