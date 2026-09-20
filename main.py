import pandas as pd
import folium

# Read our neighborhood data
data = pd.read_csv("data/neighborhoods.csv")

# Create a map centered around Bangalore
m = folium.Map(location=[12.9716, 77.5946], zoom_start=11)

# Add every neighborhood to the map
for _, row in data.iterrows():
    folium.Marker(
        location=[row["latitude"], row["longitude"]],
        popup=f'{row["neighborhood"]} - {row["daily_orders"]} orders/day'
    ).add_to(m)

# Save the map
m.save("map.html")

print("Map created successfully!")
from math import radians, sin, cos, sqrt, atan2

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c
distance = calculate_distance(
    data.loc[0, "latitude"],
    data.loc[0, "longitude"],
    data.loc[1, "latitude"],
    data.loc[1, "longitude"]
)

print("Distance between", data.loc[0, "neighborhood"],
      "and", data.loc[1, "neighborhood"], "=", round(distance, 2), "km")
# For now, assume MG Road is our warehouse
warehouse_lat = data.loc[0, "latitude"]
warehouse_lon = data.loc[0, "longitude"]

total_weighted_distance = 0

for _, row in data.iterrows():
    distance = calculate_distance(
        warehouse_lat,
        warehouse_lon,
        row["latitude"],
        row["longitude"]
    )

    weighted_distance = distance * row["daily_orders"]

    total_weighted_distance += weighted_distance

    print(
        row["neighborhood"],
        "→",
        round(distance, 2),
        "km |",
        row["daily_orders"],
        "orders |",
        "weighted distance =",
        round(weighted_distance, 2)
    )

print("\nTotal weighted delivery distance:",
      round(total_weighted_distance, 2))
# Try every neighborhood as a possible warehouse

best_warehouse = None
lowest_cost = float("inf")

for warehouse_index, warehouse in data.iterrows():

    total_cost = 0

    for _, neighborhood in data.iterrows():

        distance = calculate_distance(
            warehouse["latitude"],
            warehouse["longitude"],
            neighborhood["latitude"],
            neighborhood["longitude"]
        )

        weighted_cost = distance * neighborhood["daily_orders"]

        total_cost += weighted_cost

    print(
        warehouse["neighborhood"],
        "-> total weighted cost:",
        round(total_cost, 2)
    )

    if total_cost < lowest_cost:
        lowest_cost = total_cost
        best_warehouse = warehouse["neighborhood"]


print("\nBEST WAREHOUSE LOCATION:")
print(best_warehouse)

print("LOWEST TOTAL WEIGHTED COST:")
print(round(lowest_cost, 2))
# Try every neighborhood as a possible warehouse

best_warehouse = None
lowest_cost = float("inf")

for warehouse_index, warehouse in data.iterrows():

    total_cost = 0

    for _, neighborhood in data.iterrows():

        distance = calculate_distance(
            warehouse["latitude"],
            warehouse["longitude"],
            neighborhood["latitude"],
            neighborhood["longitude"]
        )

        weighted_cost = distance * neighborhood["daily_orders"]

        total_cost += weighted_cost

    print(
        warehouse["neighborhood"],
        "-> total weighted cost:",
        round(total_cost, 2)
    )

    if total_cost < lowest_cost:
        lowest_cost = total_cost
        best_warehouse = warehouse["neighborhood"]


print("\nBEST WAREHOUSE LOCATION:")
print(best_warehouse)

print("LOWEST TOTAL WEIGHTED COST:")
print(round(lowest_cost, 2))
from itertools import combinations

# We want 2 warehouses
number_of_warehouses = 2

best_warehouses = None
lowest_total_cost = float("inf")

# Try every possible pair of warehouse locations
for warehouse_indices in combinations(data.index, number_of_warehouses):

    warehouses = data.loc[list(warehouse_indices)]

    total_cost = 0

    # Check every neighborhood
    for _, neighborhood in data.iterrows():

        nearest_distance = float("inf")

        # Find the nearest warehouse
        for _, warehouse in warehouses.iterrows():

            distance = calculate_distance(
                neighborhood["latitude"],
                neighborhood["longitude"],
                warehouse["latitude"],
                warehouse["longitude"]
            )

            if distance < nearest_distance:
                nearest_distance = distance

        # Weighted delivery cost
        weighted_cost = nearest_distance * neighborhood["daily_orders"]

        total_cost += weighted_cost

    # Check whether this pair is better
    if total_cost < lowest_total_cost:
        lowest_total_cost = total_cost
        best_warehouses = warehouse_indices


print("\nBEST 2 WAREHOUSES:")

for index in best_warehouses:
    print(data.loc[index, "neighborhood"])

print(
    "LOWEST TOTAL WEIGHTED COST:",
    round(lowest_total_cost, 2)
)
# Assign every neighborhood to its nearest warehouse

print("\nNEIGHBORHOOD ASSIGNMENTS:")

for _, neighborhood in data.iterrows():

    nearest_warehouse = None
    nearest_distance = float("inf")

    for index in best_warehouses:

        warehouse = data.loc[index]

        distance = calculate_distance(
            neighborhood["latitude"],
            neighborhood["longitude"],
            warehouse["latitude"],
            warehouse["longitude"]
        )

        if distance < nearest_distance:
            nearest_distance = distance
            nearest_warehouse = warehouse["neighborhood"]

    print(
        neighborhood["neighborhood"],
        "→",
        nearest_warehouse,
        "|",
        round(nearest_distance, 2),
        "km"
    )
    # Add optimized warehouses to the map

for warehouse_index in best_warehouses:

    warehouse = data.loc[warehouse_index]

    folium.Marker(
        location=[warehouse["latitude"], warehouse["longitude"]],
        popup=f'Warehouse: {warehouse["neighborhood"]}',
        icon=folium.Icon(color="red", icon="home")
    ).add_to(m)


# Draw a line from every neighborhood to its assigned warehouse

for _, neighborhood in data.iterrows():

    nearest_warehouse = None
    nearest_distance = float("inf")

    for index in best_warehouses:

        warehouse = data.loc[index]

        distance = calculate_distance(
            neighborhood["latitude"],
            neighborhood["longitude"],
            warehouse["latitude"],
            warehouse["longitude"]
        )

        if distance < nearest_distance:
            nearest_distance = distance
            nearest_warehouse = warehouse


    folium.PolyLine(
        locations=[
            [neighborhood["latitude"], neighborhood["longitude"]],
            [nearest_warehouse["latitude"], nearest_warehouse["longitude"]]
        ],
        tooltip=f'{neighborhood["neighborhood"]} → {nearest_warehouse["neighborhood"]}'
    ).add_to(m)


# Save the updated map
m.save("map.html")

print("\nUpdated map created!")
# Calculate total delivery cost for the optimized warehouses

total_delivery_cost = 0

cost_per_km = 15  # ₹15 per km

print("\nDELIVERY COST DETAILS:")

for _, neighborhood in data.iterrows():

    nearest_distance = float("inf")
    nearest_warehouse = None

    for index in best_warehouses:

        warehouse = data.loc[index]

        distance = calculate_distance(
            neighborhood["latitude"],
            neighborhood["longitude"],
            warehouse["latitude"],
            warehouse["longitude"]
        )

        if distance < nearest_distance:
            nearest_distance = distance
            nearest_warehouse = warehouse["neighborhood"]

    delivery_cost = (
        nearest_distance
        * neighborhood["daily_orders"]
        * cost_per_km
    )

    total_delivery_cost += delivery_cost

    print(
        neighborhood["neighborhood"],
        "→",
        nearest_warehouse,
        "| Distance:",
        round(nearest_distance, 2),
        "km",
        "| Cost: ₹",
        round(delivery_cost, 2)
    )

print("\nTOTAL DAILY DELIVERY COST: ₹", round(total_delivery_cost, 2))
# ---------------- BEFORE vs AFTER COMPARISON ----------------

# Assume the current warehouse is MG Road
current_warehouse = data.iloc[0]

current_total_cost = 0

for _, neighborhood in data.iterrows():

    distance = calculate_distance(
        current_warehouse["latitude"],
        current_warehouse["longitude"],
        neighborhood["latitude"],
        neighborhood["longitude"]
    )

    delivery_cost = (
        distance
        * neighborhood["daily_orders"]
        * cost_per_km
    )

    current_total_cost += delivery_cost


# Calculate savings
savings = current_total_cost - total_delivery_cost

if current_total_cost > 0:
    savings_percentage = (savings / current_total_cost) * 100
else:
    savings_percentage = 0


print("\n========== FINAL COMPARISON ==========")

print("Current warehouse:", current_warehouse["neighborhood"])
print("Current daily delivery cost: ₹", round(current_total_cost, 2))

print("\nOptimized warehouses:")

for index in best_warehouses:
    print("-", data.loc[index, "neighborhood"])

print("Optimized daily delivery cost: ₹", round(total_delivery_cost, 2))

print("\nEstimated daily savings: ₹", round(savings, 2))

print(
    "Estimated cost reduction:",
    round(savings_percentage, 2),
    "%"
)