# 🧠 Urban Waste Collection Optimization Using Pathfinding Algorithms

## 📌 Project Overview

Urban waste management is becoming increasingly complex with the growth of cities and population. This project aims to optimize waste collection routes by applying various pathfinding algorithms to reduce travel time, fuel consumption, and CO₂ emissions. Simulated waste data from ten key locations in Bengaluru was used to test and evaluate the efficiency of six routing algorithms under operational constraints such as vehicle capacity and waste priority levels.

---

## 🚀 Features

- 📍 Extraction of spatial data from OpenStreetMap  
- 📐 Distance matrix computation using the Haversine formula  
- 🗑️ Waste load simulation and classification into High, Medium, Low priorities  
- ⚙️ Implementation of routing algorithms:
  - Dijkstra’s Algorithm  
  - Bellman-Ford Algorithm  
  - Johnson’s Algorithm  
  - Floyd-Warshall Algorithm  
  - Nearest Neighbor  
  - Ant Colony Optimization (ACO)  
- 🚛 Vehicle capacity-aware routing  
- 📊 Performance evaluation using:
  - Execution Time  
  - Space Complexity  
  - Total Distance  
  - Fuel Consumption  
  - CO₂ Emissions  
  - Number of Trips  
- 🗺️ Visual route comparison for decision making

---

## 🛠️ Technologies Used

- **Python 3.10+**  
- **Pandas** – Data manipulation  
- **NumPy** – Numerical calculations  
- **Matplotlib / Folium** – Visualization and mapping  
- **OpenStreetMap** – Geospatial data extraction  
- **Jupyter Notebook / Streamlit (optional)** – UI and interactive analysis

---

## 📊 Evaluation Metrics

| Metric             | Description                                                    |
|--------------------|----------------------------------------------------------------|
| Execution Time     | Time taken by each algorithm to compute optimal routes         |
| Space Complexity   | Memory used by the algorithm during execution                  |
| Total Distance     | Sum of distances in the optimized route                        |
| Fuel Consumption   | Estimated using 10 km/l fuel efficiency                        |
| CO₂ Emissions      | Calculated as 2.31 kg CO₂ per litre of petrol consumed         |
| Number of Trips    | Based on garbage loads and vehicle capacity constraints        |

---

## 🧪 Sample Outputs

- Route maps per algorithm (color-coded for priorities)
- Performance tables comparing all six algorithms
- Combined route visualization for benchmarking
- Example locations: Indiranagar, MG Road, Whitefield, Electronic City, etc.

---

## 🔮 Future Scope

- 🔌 Integrate IoT-enabled smart bins for real-time data  
- 🚦 Use real-time traffic data from APIs (e.g., Google Maps)  
- 🧠 Train ML models to predict waste patterns by region  
- ☁️ Deploy to cloud with Docker & CI/CD pipeline  
- 🏙️ Partner with municipal bodies for city-scale implementation

---

## 👨‍💻 Authors

- **D. Abhiram**  
- **K. Dhanush Reddy**  
- **P.Koushik Reddy** – Contributed to model integration, evaluation and presentaion
- **Pooja Gowda**  

**Department of Computer Science and Engineering**  
Amrita School of Computing, Bengaluru  
Amrita Vishwa Vidyapeetham

---

## 📄 License

This project is intended for academic and research purposes only.
