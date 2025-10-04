# 🌌 Space Weather Game API (NASA Challenge Project)

> A Django REST Framework-based backend for an interactive educational game simulating the effects of solar flares on Earth's systems.  
> This project integrates NASA data, mission-based gameplay, and AI-driven visual analytics.

---

## 📘 Table of Contents

1. [Overview](#-overview)
2. [Motivation](#-motivation)
3. [Objectives](#-objectives)
4. [Main Features](#-main-features)
5. [Tech Stack](#-tech-stack)
6. [API Structure](#-api-structure)
7. [Installation Guide](#-installation-guide)
8. [Unified Endpoint](#-unified-endpoint)
9. [Project Screenshots](#-project-screenshots)
10. [Future Improvements](#-future-improvements)
11. [Contributors](#-contributors)

---

## 🌍 Overview

**Space Weather Game API** is a backend system designed to simulate real solar weather phenomena (solar flares)  
and their impact on Earth's technological systems — such as satellites, power grids, and communications.

The system connects with **NASA’s APIs** to fetch real solar flare data,  
stores it in a Django database, and generates detailed **visual analytics** using Matplotlib.

It serves as the backend for a **Flutter-based game interface**, where users can:
- Create players.
- Start game sessions.
- Complete missions by choosing defense strategies.
- View charts, reports, and leaderboards.

---

## 💡 Motivation

Space weather has a real impact on technology and communication.  
The goal of this project is to make scientific data interactive, educational, and visually engaging —  
helping players understand how space storms affect Earth’s systems.

---

## 🎯 Objectives

- Simulate the effects of solar flares in a game environment.  
- Visualize NASA space data in real-time.  
- Provide a REST API that can be integrated easily with Flutter or web clients.  
- Create educational insight through gamification.

---

## 🧩 Main Features

✅ Player registration and management  
✅ Game session tracking and ranking  
✅ Mission system with success/failure simulation  
✅ NASA solar flare data fetching & simulation  
✅ Real-time visual analytics (Base64 encoded charts)  
✅ Global statistics and leaderboard  
✅ Unified API endpoint for Flutter integration  
✅ PDF/ZIP report generation (future-ready)

---

## 🛠️ Tech Stack

| Layer | Tools & Technologies |
|-------|----------------------|
| **Backend Framework** | Django, Django REST Framework |
| **Database** | SQLite / PostgreSQL |
| **Visualization** | Matplotlib, Base64 |
| **External APIs** | NASA Space Weather API |
| **Auth & Security** | Django Auth, DRF Permissions |
| **Serialization** | DRF Serializers |
| **Frontend (planned)** | Flutter |
| **Version Control** | Git & GitHub |

---

## 🌐 API Structure

| Endpoint | Description |
|-----------|-------------|
| `/players/` | Manage players |
| `/sessions/` | Create & update game sessions |
| `/missions/` | Track player missions |
| `/flares/` | Fetch NASA solar flare data |
| `/leaderboard/` | Top players |
| `/stats/global_stats/` | Global game statistics |
| `/charts/session/<id>/` | Generate visual charts |
| `/unified/` | Return all data in one response (for Flutter) |

---

## ⚙️ Installation Guide

```bash
# 1️⃣ Clone the repository
git clone https://github.com/Mohamed-omara-alt/space-weather-game.git
cd space-weather-game

# 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3️⃣ Install dependencies
pip install -r requirements.txt

# 4️⃣ Run migrations
python manage.py migrate

# 5️⃣ Start the development server
python manage.py runserver
