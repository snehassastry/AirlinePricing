# ✈️ Airline Revenue Optimization using Dynamic Programming

## Overview

This project explores **dynamic pricing** and **overbooking optimization** for airline ticket sales, using **Dynamic Programming (DP)** to maximize the expected discounted profit over a 365-day booking window.

By modeling customer behavior, seat constraints, and overbooking penalties, the project simulates and evaluates multiple pricing policies and overbooking scenarios to identify the most profitable strategy.

📁 **Files Included**
- `Airlines(DP).ipynb`: Python notebook implementing the DP logic and simulations.
- `AirlinePricing.pdf`: Detailed report explaining the problem, model, assumptions, methodology, and results.

---

## 💡 Objective

Maximize total expected profit over a year by:
- Setting daily prices for coach and first-class tickets.
- Deciding the optimal number of seats to overbook.
- Incorporating customer no-show probabilities.
- Accounting for overbooking penalties and upgrades.

---

## 🔧 Model Components

- **State Variables**: Days until flight, coach seats sold, first-class seats sold.
- **Decision Variables**: Prices for coach and first-class tickets ($300/$350 and $425/$500).
- **Stochastic Dynamics**:
  - Sale probabilities based on price and availability.
  - Show-up probabilities (95% for coach, 97% for first-class).
- **Reward Structure**:
  - Immediate revenue from ticket sales.
  - Penalty costs at departure for overbooked passengers.

---

## 📊 Key Features

### 1. Dynamic Programming Framework
- Uses **backward induction** and the **Bellman Equation**.
- Computes optimal policy and value function over 365 days.
- Considers **all pricing combinations** and **probabilistic transitions**.

### 2. Overbooking Optimization
- Evaluates profits under 0 to 20 overbooked coach seats.
- Simulates bumping to first-class and customer offloading costs.
- Finds that overbooking 9–20 seats (with flexibility) yields the highest return.

### 3. No-Sale Option
- Allows skipping coach ticket sales on certain days.
- Helps manage overbooking risk.
- Slightly increases profits while reducing customer dissatisfaction.

### 4. Seasonality Modeling
- Adjusts sale probabilities based on proximity to flight date.
- Reflects real-world demand spikes.
- Slightly reduces profit due to discounting late revenue.

---

## 🧪 Simulation Metrics

- **Expected Profit & Std. Deviation**
- **Overbooking Rate**
- **Average Overbooking Cost**
- **Percentage of Kicked Passengers**
- **Blocked Upgrades**

---

## ✅ Results Summary

| Policy                                | Overbooking | Profit ($)   | % Gain from Baseline |
|--------------------------------------|-------------|--------------|----------------------|
| No Seasonality, No No-Sell           | 9 seats     | 42,134.62    | 3.64%                |
| No Seasonality, With No-Sell         | 20 seats    | 42,139.89    | 3.65%                |
| Seasonality, No No-Sell              | 9 seats     | 41,820.96    | 2.87%                |
| Seasonality, With No-Sell (best-fit) | 20 seats    | 41,826.45    | 2.89%                |

---

## 📝 Final Recommendation

Allow **up to 20 overbooked coach seats** and **enable the no-sell option** for coach class during low-demand days. Include **seasonality** in the model for realistic demand trends.

---

## 🚀 Future Scope

- Incorporate competitor pricing
- Support multi-leg/connecting flights
- Real-time pricing using ML/RL methods
- Analyze long-term customer satisfaction impact

---

## 👩‍💻 Authors

- Austin Yeh  
- Felipe Zapater  
- Sonali Hornick  
- Sneha Sastry Rayadurgam  

📍 Project for **Optimization II**, University of Texas at Austin, Spring 2025.


