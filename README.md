# 🏭 GRIDPOINT

## Warehouse Location Optimization Platform

[🚀 Live Demo](https://gridpoint-beh5vykdslpo3jjxuxkpau.streamlit.app/)  
[💻 GitHub Repository](YOUR_GITHUB_REPOSITORY_URL)

GRIDPOINT is a warehouse location optimization platform designed for
e-commerce logistics.

It helps determine where warehouses should be located, which
neighborhoods should be assigned to each warehouse, and how delivery
cost changes under different logistics scenarios.

---

## 🎯 Problem Statement

An e-commerce company serves multiple neighborhoods.

Each neighborhood has:

- A geographical location
- A different number of daily orders
- Different distances from possible warehouse locations

The company wants to establish one or more warehouses while minimizing
overall delivery effort and cost.

Neighborhoods with higher order volumes contribute more heavily to the
delivery-cost objective.

GRIDPOINT addresses this problem by analyzing neighborhood demand and
geographical locations to identify suitable warehouse locations and
assign neighborhoods to them.

---

## 💡 Our Solution

GRIDPOINT takes neighborhood data as input and performs warehouse
location optimization.

The system:

1. Accepts neighborhood data through a CSV upload.
2. Visualizes neighborhood locations on an interactive map.
3. Allows the user to choose the number of warehouses.
4. Calculates geographical distances between locations.
5. Finds suitable warehouse locations.
6. Assigns neighborhoods to warehouses.
7. Considers warehouse capacity.
8. Considers maximum service radius.
9. Calculates demand-weighted delivery cost.
10. Compares the existing arrangement with the optimized arrangement.
11. Shows estimated delivery-cost savings.
12. Models infrastructure cost.
13. Allows demand-change simulations.

---

## ✨ Features

### 📂 Data Upload

Users can upload neighborhood data in CSV format.

### 🗺️ Interactive Map

Neighborhoods, existing warehouses, optimized warehouses, and
assignments are visualized on an interactive map.

### 🏭 Multiple Warehouses

Users can select the number of warehouses to evaluate.

### 📦 Demand-Weighted Optimization

Neighborhoods with higher daily order volumes have greater influence
on the delivery-cost objective.

### 🚚 Neighborhood Assignment

Each neighborhood is assigned to a feasible warehouse based on distance,
service radius, and available capacity.

### 📏 Maximum Service Radius

The system can prevent assignments that exceed the configured maximum
delivery radius.

### 🏢 Warehouse Capacity

Each warehouse has a configurable daily order capacity.

### 💰 Delivery Cost Analysis

GRIDPOINT calculates modeled delivery costs based on distance,
demand, and cost per order-kilometer.

### 📊 Before vs After Comparison

The existing warehouse arrangement can be compared with the optimized
arrangement.

### 🏗️ Infrastructure Cost

The system models an assumed daily infrastructure cost for each
warehouse and explores the trade-off between delivery cost and
infrastructure cost.

### 📈 Demand Simulation

Users can simulate changes in customer demand and observe how the
warehouse solution responds.

### ✅ Input Validation

The application checks uploaded CSV files for missing columns,
invalid coordinates, negative demand, and other invalid inputs.

---

## 🧠 Optimization Approach

GRIDPOINT models the problem as a demand-weighted warehouse location
optimization problem.

The main delivery objective is based on:

```text
Demand × Distance
| Team Member | Role |
|---|---|
| Rida | Optimization / Python |
| Ananya | Streamlit / UI |
| bavitha| Data / Algorithms |
| shreya| Presentation / Demo | 