import streamlit as st
import pandas as pd
import folium
import streamlit.components.v1 as components

from math import radians, sin, cos, sqrt, atan2
from itertools import combinations


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="GRIDPOINT",
    page_icon="🏭",
    layout="wide"
)


# =========================================================
# TITLE
# =========================================================

st.title("🏭 GRIDPOINT")
st.subheader("Warehouse Location Optimization Platform")

st.write(
    "Optimize warehouse locations, assign neighborhoods, "
    "respect capacity and service-radius constraints, "
    "simulate demand changes, and compare costs."
)


# =========================================================
# SESSION STATE
# =========================================================

if "optimization_done" not in st.session_state:
    st.session_state.optimization_done = False

if "best_warehouses" not in st.session_state:
    st.session_state.best_warehouses = None

if "best_total_weighted_distance" not in st.session_state:
    st.session_state.best_total_weighted_distance = None

if "assignment_table" not in st.session_state:
    st.session_state.assignment_table = None

if "data_source" not in st.session_state:
    st.session_state.data_source = None

if "tradeoff_table" not in st.session_state:
    st.session_state.tradeoff_table = None

if "config_signature" not in st.session_state:
    st.session_state.config_signature = None


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("⚙️ GRIDPOINT Controls")


# =========================================================
# CSV UPLOAD
# =========================================================

st.sidebar.header("📂 Neighborhood Data")

uploaded_file = st.sidebar.file_uploader(
    "Upload Neighborhood CSV",
    type=["csv"]
)


# =========================================================
# LOAD ORIGINAL DATA
# =========================================================

if uploaded_file is not None:

    try:

        base_data = pd.read_csv(
            uploaded_file
        )

        current_data_source = uploaded_file.name

    except Exception as e:

        st.error(
            f"❌ Could not read the uploaded CSV: {e}"
        )

        st.stop()

else:

    try:

        base_data = pd.read_csv(
            "data/neighborhoods.csv"
        )

        current_data_source = "sample_bangalore_dataset"

    except FileNotFoundError:

        st.error(
            "❌ Could not find data/neighborhoods.csv"
        )

        st.stop()


# Clean column names
base_data.columns = (
    base_data.columns.str.strip()
)


# =========================================================
# RESET WHEN DATASET CHANGES
# =========================================================

if (
    st.session_state.data_source is not None
    and st.session_state.data_source
    != current_data_source
):

    st.session_state.optimization_done = False

    st.session_state.best_warehouses = None

    st.session_state.best_total_weighted_distance = None

    st.session_state.assignment_table = None

    st.session_state.tradeoff_table = None

    st.session_state.config_signature = None


st.session_state.data_source = (
    current_data_source
)


# =========================================================
# DATA VALIDATION
# =========================================================

required_columns = [
    "neighborhood",
    "address",
    "latitude",
    "longitude",
    "daily_orders"
]


missing_columns = [
    column
    for column in required_columns
    if column not in base_data.columns
]


if missing_columns:

    st.error(
        "❌ Your CSV is missing these columns: "
        + ", ".join(missing_columns)
    )

    st.stop()


# Convert numeric columns
try:

    base_data["latitude"] = pd.to_numeric(
        base_data["latitude"]
    )

    base_data["longitude"] = pd.to_numeric(
        base_data["longitude"]
    )

    base_data["daily_orders"] = pd.to_numeric(
        base_data["daily_orders"]
    )

except ValueError:

    st.error(
        "❌ Latitude, longitude and daily_orders "
        "must contain valid numbers."
    )

    st.stop()


# Empty dataset
if base_data.empty:

    st.error(
        "❌ The dataset contains no neighborhoods."
    )

    st.stop()


# Negative orders
if (
    base_data["daily_orders"] < 0
).any():

    st.error(
        "❌ Daily orders cannot be negative."
    )

    st.stop()


# Latitude validation
if (
    (base_data["latitude"] < -90)
    | (base_data["latitude"] > 90)
).any():

    st.error(
        "❌ Latitude must be between -90 and 90."
    )

    st.stop()


# Longitude validation
if (
    (base_data["longitude"] < -180)
    | (base_data["longitude"] > 180)
).any():

    st.error(
        "❌ Longitude must be between -180 and 180."
    )

    st.stop()


# =========================================================
# DEMAND SIMULATION
# =========================================================

st.sidebar.header("📈 Demand Scenario")

demand_change_percent = st.sidebar.slider(
    "Demand change (%)",
    min_value=-50,
    max_value=100,
    value=0,
    step=10
)


# Create working copy
data = base_data.copy()


# Keep the original demand
data["base_daily_orders"] = (
    data["daily_orders"]
)


# Apply demand scenario
demand_multiplier = (
    1 + demand_change_percent / 100
)


data["daily_orders"] = (
    data["base_daily_orders"]
    * demand_multiplier
).round().astype(int)


# =========================================================
# DISTANCE FUNCTION
# =========================================================

def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2
):
    """
    Calculate geographical distance between
    two latitude/longitude points.

    Returns distance in kilometers.
    """

    earth_radius = 6371

    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))

    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return earth_radius * c


# =========================================================
# OPTIMIZATION SETTINGS
# =========================================================

st.sidebar.header(
    "🎯 Optimization Settings"
)


max_warehouse_options = min(
    5,
    len(data)
)


number_of_warehouses = st.sidebar.number_input(
    "Number of warehouses",
    min_value=1,
    max_value=max_warehouse_options,
    value=min(2, max_warehouse_options),
    step=1
)


cost_per_km = st.sidebar.number_input(
    "Delivery cost per order-km (₹)",
    min_value=0.0,
    value=15.0,
    step=1.0
)


max_service_radius = st.sidebar.number_input(
    "Maximum service radius (km)",
    min_value=1.0,
    value=15.0,
    step=1.0
)


warehouse_capacity = st.sidebar.number_input(
    "Warehouse capacity (orders/day)",
    min_value=1,
    value=500,
    step=50
)


infrastructure_cost_per_warehouse = (
    st.sidebar.number_input(
        "Warehouse infrastructure cost/day (₹)",
        min_value=0.0,
        value=5000.0,
        step=500.0
    )
)


# =========================================================
# EXISTING WAREHOUSE
# =========================================================

st.sidebar.header(
    "🏭 Existing Warehouse"
)


default_latitude = float(
    data["latitude"].mean()
)


default_longitude = float(
    data["longitude"].mean()
)


current_warehouse_latitude = (
    st.sidebar.number_input(
        "Existing warehouse latitude",
        value=default_latitude,
        format="%.6f"
    )
)


current_warehouse_longitude = (
    st.sidebar.number_input(
        "Existing warehouse longitude",
        value=default_longitude,
        format="%.6f"
    )
)


# =========================================================
# CONFIGURATION SIGNATURE
# =========================================================

current_config_signature = (

    current_data_source,

    demand_change_percent,

    int(number_of_warehouses),

    float(cost_per_km),

    float(max_service_radius),

    int(warehouse_capacity),

    float(
        infrastructure_cost_per_warehouse
    ),

    round(
        float(current_warehouse_latitude),
        6
    ),

    round(
        float(current_warehouse_longitude),
        6
    )
)


# Clear old results when user changes settings
if (
    st.session_state.config_signature
    is not None
    and
    st.session_state.config_signature
    != current_config_signature
):

    st.session_state.optimization_done = False

    st.session_state.best_warehouses = None

    st.session_state.best_total_weighted_distance = None

    st.session_state.assignment_table = None

    st.session_state.tradeoff_table = None


st.session_state.config_signature = (
    current_config_signature
)


# =========================================================
# OPTIMIZE BUTTON
# =========================================================

optimize_button = st.sidebar.button(
    "🚀 Optimize Warehouses",
    use_container_width=True
)


# =========================================================
# CURRENT DEMAND SUMMARY
# =========================================================

base_total_orders = int(
    data["base_daily_orders"].sum()
)


scenario_total_orders = int(
    data["daily_orders"].sum()
)


# =========================================================
# SUMMARY METRICS
# =========================================================

col1, col2, col3, col4 = (
    st.columns(4)
)


with col1:

    st.metric(
        "Neighborhoods",
        len(data)
    )


with col2:

    st.metric(
        "Original Orders",
        f"{base_total_orders:,}"
    )


with col3:

    st.metric(
        "Scenario Orders",
        f"{scenario_total_orders:,}",
        f"{demand_change_percent}%"
    )


with col4:

    st.metric(
        "Warehouses Selected",
        number_of_warehouses
    )


# =========================================================
# DEMAND SCENARIO MESSAGE
# =========================================================

if demand_change_percent > 0:

    st.warning(
        f"📈 Demand increased by "
        f"{demand_change_percent}% "
        f"for this scenario."
    )

elif demand_change_percent < 0:

    st.info(
        f"📉 Demand decreased by "
        f"{abs(demand_change_percent)}% "
        f"for this scenario."
    )

else:

    st.info(
        "📊 Using the original demand data."
    )


# =========================================================
# DATA TABLE
# =========================================================

st.write(
    "## 📋 Neighborhood Data"
)


display_data = data[
    [
        "neighborhood",
        "address",
        "latitude",
        "longitude",
        "base_daily_orders",
        "daily_orders"
    ]
].copy()


display_data = display_data.rename(
    columns={
        "base_daily_orders":
            "Original Orders",

        "daily_orders":
            "Scenario Orders"
    }
)


st.dataframe(
    display_data,
    use_container_width=True
)


# =========================================================
# OPTIMIZATION FUNCTION
# =========================================================

def evaluate_warehouse_combination(
    warehouse_indices,
    data,
    max_service_radius,
    warehouse_capacity,
    cost_per_km
):
    """
    Evaluate one candidate warehouse combination.
    """

    warehouse_orders = {
        index: 0
        for index in warehouse_indices
    }

    total_weighted_distance = 0

    assignments = []


    # Process high-demand neighborhoods first
    sorted_neighborhoods = data.sort_values(
        by="daily_orders",
        ascending=False
    )


    for _, neighborhood in (
        sorted_neighborhoods.iterrows()
    ):

        possible_warehouses = []


        # -------------------------------------------------
        # Find warehouses inside radius
        # -------------------------------------------------

        for index in warehouse_indices:

            warehouse = data.loc[index]


            distance = calculate_distance(

                neighborhood["latitude"],
                neighborhood["longitude"],

                warehouse["latitude"],
                warehouse["longitude"]
            )


            if (
                distance
                <= max_service_radius
            ):

                possible_warehouses.append(
                    (distance, index)
                )


        # -------------------------------------------------
        # Sort nearest first
        # -------------------------------------------------

        possible_warehouses.sort(
            key=lambda item: item[0]
        )


        assigned_warehouse_index = None
        assigned_distance = None


        # -------------------------------------------------
        # Find nearest warehouse with capacity
        # -------------------------------------------------

        for distance, index in (
            possible_warehouses
        ):

            current_orders = (
                warehouse_orders[index]
            )

            neighborhood_orders = int(
                neighborhood["daily_orders"]
            )


            if (
                current_orders
                + neighborhood_orders
                <= warehouse_capacity
            ):

                assigned_warehouse_index = index
                assigned_distance = distance

                break


        # -------------------------------------------------
        # No feasible warehouse
        # -------------------------------------------------

        if (
            assigned_warehouse_index
            is None
        ):

            return (
                False,
                None,
                None
            )


        # -------------------------------------------------
        # Update capacity
        # -------------------------------------------------

        warehouse_orders[
            assigned_warehouse_index
        ] += int(
            neighborhood["daily_orders"]
        )


        # -------------------------------------------------
        # Weighted distance
        # -------------------------------------------------

        weighted_distance = (
            assigned_distance
            * neighborhood["daily_orders"]
        )


        total_weighted_distance += (
            weighted_distance
        )


        # -------------------------------------------------
        # Delivery cost
        # -------------------------------------------------

        delivery_cost = (
            weighted_distance
            * cost_per_km
        )


        warehouse_name = data.loc[
            assigned_warehouse_index,
            "neighborhood"
        ]


        assignments.append({

            "Neighborhood":
                neighborhood["neighborhood"],

            "Address":
                neighborhood["address"],

            "Warehouse":
                warehouse_name,

            "Distance (km)":
                round(
                    assigned_distance,
                    2
                ),

            "Scenario Orders":
                int(
                    neighborhood["daily_orders"]
                ),

            "Weighted Distance":
                round(
                    weighted_distance,
                    2
                ),

            "Delivery Cost (₹)":
                round(
                    delivery_cost,
                    2
                )
        })


    return (
        True,
        total_weighted_distance,
        assignments
    )


# =========================================================
# FIND BEST SOLUTION
# =========================================================

def find_best_solution(
    warehouse_count,
    data,
    max_service_radius,
    warehouse_capacity,
    cost_per_km
):
    """
    Exhaustively test warehouse combinations for the
    selected warehouse count.
    """

    total_demand = int(
        data["daily_orders"].sum()
    )


    total_capacity = (
        warehouse_count
        * warehouse_capacity
    )


    if total_capacity < total_demand:

        return (
            None,
            None,
            None
        )


    best_warehouses = None

    lowest_total_weighted_distance = (
        float("inf")
    )

    best_assignments = None


    for warehouse_indices in (
        combinations(
            data.index,
            warehouse_count
        )
    ):

        (
            valid_solution,
            total_cost,
            assignments
        ) = evaluate_warehouse_combination(

            warehouse_indices,

            data,

            max_service_radius,

            warehouse_capacity,

            cost_per_km
        )


        if valid_solution:

            if (
                total_cost
                < lowest_total_weighted_distance
            ):

                lowest_total_weighted_distance = (
                    total_cost
                )

                best_warehouses = (
                    warehouse_indices
                )

                best_assignments = (
                    assignments
                )


    return (
        best_warehouses,
        lowest_total_weighted_distance,
        best_assignments
    )


# =========================================================
# CURRENT ARRANGEMENT COST
# =========================================================

current_weighted_distance = 0


for _, neighborhood in data.iterrows():

    distance = calculate_distance(

        current_warehouse_latitude,
        current_warehouse_longitude,

        neighborhood["latitude"],
        neighborhood["longitude"]
    )


    current_weighted_distance += (
        distance
        * neighborhood["daily_orders"]
    )


current_daily_delivery_cost = (
    current_weighted_distance
    * cost_per_km
)


# =========================================================
# RUN OPTIMIZATION
# =========================================================

if optimize_button:

    # Clear previous results

    st.session_state.optimization_done = False

    st.session_state.best_warehouses = None

    st.session_state.best_total_weighted_distance = None

    st.session_state.assignment_table = None

    st.session_state.tradeoff_table = None


    # -----------------------------------------------------
    # Find solution for selected warehouse count
    # -----------------------------------------------------

    (
        best_warehouses,
        lowest_total_weighted_distance,
        best_assignments
    ) = find_best_solution(

        int(number_of_warehouses),

        data,

        max_service_radius,

        warehouse_capacity,

        cost_per_km
    )


    # -----------------------------------------------------
    # No feasible solution
    # -----------------------------------------------------

    if best_warehouses is None:

        st.error(
            "❌ No feasible warehouse arrangement "
            "was found with the current settings."
        )


        total_available_capacity = (
            int(number_of_warehouses)
            * warehouse_capacity
        )


        st.info(

            f"Scenario demand: "
            f"{scenario_total_orders:,} orders/day | "

            f"Available capacity: "
            f"{total_available_capacity:,} orders/day"
        )


    # -----------------------------------------------------
    # Success
    # -----------------------------------------------------

    else:

        st.session_state.best_warehouses = (
            best_warehouses
        )

        st.session_state.best_total_weighted_distance = (
            lowest_total_weighted_distance
        )

        st.session_state.assignment_table = (
            pd.DataFrame(
                best_assignments
            )
        )

        st.session_state.optimization_done = True


    # =====================================================
    # WAREHOUSE COUNT TRADE-OFF
    # =====================================================

    tradeoff_results = []


    with st.spinner(
        "Calculating warehouse-count trade-off..."
    ):


        for warehouse_count in range(
            1,
            max_warehouse_options + 1
        ):


            (
                test_warehouses,
                test_weighted_distance,
                test_assignments
            ) = find_best_solution(

                warehouse_count,

                data,

                max_service_radius,

                warehouse_capacity,

                cost_per_km
            )


            if test_warehouses is None:

                tradeoff_results.append({

                    "Warehouses":
                        warehouse_count,

                    "Delivery Cost (₹)":
                        None,

                    "Infrastructure Cost (₹)":
                        warehouse_count
                        * infrastructure_cost_per_warehouse,

                    "Total Cost (₹)":
                        None,

                    "Feasible":
                        "No"
                })


            else:

                test_delivery_cost = (
                    test_weighted_distance
                    * cost_per_km
                )


                test_infrastructure_cost = (
                    warehouse_count
                    * infrastructure_cost_per_warehouse
                )


                test_total_cost = (
                    test_delivery_cost
                    + test_infrastructure_cost
                )


                tradeoff_results.append({

                    "Warehouses":
                        warehouse_count,

                    "Delivery Cost (₹)":
                        round(
                            test_delivery_cost,
                            2
                        ),

                    "Infrastructure Cost (₹)":
                        round(
                            test_infrastructure_cost,
                            2
                        ),

                    "Total Cost (₹)":
                        round(
                            test_total_cost,
                            2
                        ),

                    "Feasible":
                        "Yes"
                })


    st.session_state.tradeoff_table = (
        pd.DataFrame(
            tradeoff_results
        )
    )


# =========================================================
# DISPLAY RESULTS
# =========================================================

if (
    st.session_state.optimization_done
):

    st.write(
        "## ✅ Optimization Results"
    )


    st.success(
        "Optimization completed successfully!"
    )


    # =====================================================
    # SELECTED WAREHOUSES
    # =====================================================

    st.write(
        "### 🏭 Selected Warehouses"
    )


    warehouse_columns = st.columns(
        len(
            st.session_state.best_warehouses
        )
    )


    for position, index in enumerate(
        st.session_state.best_warehouses
    ):

        warehouse_name = data.loc[
            index,
            "neighborhood"
        ]


        with warehouse_columns[position]:

            st.metric(
                "Warehouse",
                warehouse_name
            )


    # =====================================================
    # OPTIMIZED COST
    # =====================================================

    optimized_weighted_distance = (
        st.session_state.best_total_weighted_distance
    )


    optimized_daily_delivery_cost = (
        optimized_weighted_distance
        * cost_per_km
    )


    # =====================================================
    # BEFORE VS AFTER
    # =====================================================

    savings = (
        current_daily_delivery_cost
        - optimized_daily_delivery_cost
    )


    if current_daily_delivery_cost > 0:

        savings_percentage = (
            savings
            / current_daily_delivery_cost
        ) * 100

    else:

        savings_percentage = 0


    st.write(
        "## 📊 Before vs After Optimization"
    )


    compare_col1, compare_col2, compare_col3 = (
        st.columns(3)
    )


    with compare_col1:

        st.metric(
            "Current Daily Cost",
            f"₹{current_daily_delivery_cost:,.2f}"
        )


    with compare_col2:

        st.metric(
            "Optimized Daily Cost",
            f"₹{optimized_daily_delivery_cost:,.2f}"
        )


    with compare_col3:

        st.metric(
            "Estimated Savings",
            f"₹{savings:,.2f}",
            f"{savings_percentage:.2f}%"
        )


    # =====================================================
    # COST CHART
    # =====================================================

    st.write(
        "### 💰 Delivery Cost Comparison"
    )


    cost_comparison = pd.DataFrame({

        "Arrangement": [
            "Current",
            "Optimized"
        ],

        "Daily Cost (₹)": [
            current_daily_delivery_cost,
            optimized_daily_delivery_cost
        ]
    })


    st.bar_chart(
        cost_comparison.set_index(
            "Arrangement"
        )
    )


    # =====================================================
    # INFRASTRUCTURE COST
    # =====================================================

    optimized_infrastructure_cost = (
        number_of_warehouses
        * infrastructure_cost_per_warehouse
    )


    optimized_total_business_cost = (
        optimized_daily_delivery_cost
        + optimized_infrastructure_cost
    )


    st.write(
        "### 🏗️ Infrastructure Trade-off"
    )


    infra_col1, infra_col2 = st.columns(2)


    with infra_col1:

        st.metric(
            "Infrastructure Cost / Day",
            f"₹{optimized_infrastructure_cost:,.2f}"
        )


    with infra_col2:

        st.metric(
            "Total Business Cost / Day",
            f"₹{optimized_total_business_cost:,.2f}"
        )


    # =====================================================
    # ASSIGNMENT TABLE
    # =====================================================

    st.write(
        "### 📦 Neighborhood Assignments"
    )


    st.dataframe(
        st.session_state.assignment_table,
        use_container_width=True
    )


    # =====================================================
    # CAPACITY USAGE
    # =====================================================

    st.write(
        "### 📊 Warehouse Capacity Usage"
    )


    capacity_data = []


    for index in (
        st.session_state.best_warehouses
    ):

        warehouse_name = data.loc[
            index,
            "neighborhood"
        ]


        assigned_orders = (
            st.session_state.assignment_table[
                st.session_state.assignment_table[
                    "Warehouse"
                ]
                == warehouse_name
            ]["Scenario Orders"].sum()
        )


        capacity_percentage = (
            assigned_orders
            / warehouse_capacity
        ) * 100


        capacity_data.append({

            "Warehouse":
                warehouse_name,

            "Assigned Orders":
                int(
                    assigned_orders
                ),

            "Capacity":
                int(
                    warehouse_capacity
                ),

            "Capacity Used (%)":
                round(
                    capacity_percentage,
                    2
                )
        })


    capacity_table = pd.DataFrame(
        capacity_data
    )


    st.dataframe(
        capacity_table,
        use_container_width=True
    )


    # =====================================================
    # WAREHOUSE COUNT TRADE-OFF
    # =====================================================

    if (
        st.session_state.tradeoff_table
        is not None
    ):

        st.write(
            "## 📈 Warehouse Count Trade-off"
        )


        st.dataframe(
            st.session_state.tradeoff_table,
            use_container_width=True
        )


        tradeoff_chart = (
            st.session_state.tradeoff_table
            .dropna(
                subset=["Total Cost (₹)"]
            )
            .set_index("Warehouses")[
                [
                    "Delivery Cost (₹)",
                    "Infrastructure Cost (₹)",
                    "Total Cost (₹)"
                ]
            ]
        )


        st.bar_chart(
            tradeoff_chart
        )


# =========================================================
# MAP
# =========================================================

st.write(
    "## 🗺️ Location Map"
)


map_latitudes = list(
    data["latitude"]
)

map_longitudes = list(
    data["longitude"]
)


map_latitudes.append(
    current_warehouse_latitude
)

map_longitudes.append(
    current_warehouse_longitude
)


map_center = [

    sum(map_latitudes)
    / len(map_latitudes),

    sum(map_longitudes)
    / len(map_longitudes)
]


m = folium.Map(

    location=map_center,

    zoom_start=11
)


# =========================================================
# NEIGHBORHOODS
# =========================================================

for _, row in data.iterrows():

    folium.Marker(

        location=[

            row["latitude"],
            row["longitude"]

        ],

        popup=(

            f"<b>📍 {row['neighborhood']}</b><br>"

            f"Address: "
            f"{row['address']}<br>"

            f"Original Orders: "
            f"{row['base_daily_orders']}<br>"

            f"Scenario Orders: "
            f"{row['daily_orders']}"

        ),

        icon=folium.Icon(

            color="blue",

            icon="map-marker"

        )

    ).add_to(m)


# =========================================================
# EXISTING WAREHOUSE
# =========================================================

folium.Marker(

    location=[

        current_warehouse_latitude,

        current_warehouse_longitude

    ],

    popup=(
        "<b>🟢 Existing Warehouse</b>"
    ),

    icon=folium.Icon(

        color="green",

        icon="home"

    )

).add_to(m)


# =========================================================
# FIT MAP
# =========================================================

map_bounds = [

    [

        min(map_latitudes),

        min(map_longitudes)

    ],

    [

        max(map_latitudes),

        max(map_longitudes)

    ]

]


m.fit_bounds(
    map_bounds
)


# =========================================================
# OPTIMIZED WAREHOUSES
# =========================================================

if st.session_state.optimization_done:

    for index in (
        st.session_state.best_warehouses
    ):

        warehouse = data.loc[index]


        folium.Marker(

            location=[

                warehouse["latitude"],

                warehouse["longitude"]

            ],

            popup=(

                "<b>🔴 Optimized Warehouse</b><br>"

                f"{warehouse['neighborhood']}"

            ),

            icon=folium.Icon(

                color="red",

                icon="home"

            )

        ).add_to(m)


    # =====================================================
    # ASSIGNMENT LINES
    # =====================================================

    for _, assignment in (
        st.session_state.assignment_table.iterrows()
    ):

        neighborhood_name = (
            assignment["Neighborhood"]
        )

        warehouse_name = (
            assignment["Warehouse"]
        )


        neighborhood = data[
            data["neighborhood"]
            == neighborhood_name
        ].iloc[0]


        warehouse = data[
            data["neighborhood"]
            == warehouse_name
        ].iloc[0]


        folium.PolyLine(

            locations=[

                [

                    neighborhood["latitude"],

                    neighborhood["longitude"]

                ],

                [

                    warehouse["latitude"],

                    warehouse["longitude"]

                ]

            ],

            tooltip=(

                f"{neighborhood_name}"

                f" → "

                f"{warehouse_name}"

            )

        ).add_to(m)


# =========================================================
# DISPLAY MAP
# =========================================================

components.html(

    m._repr_html_(),

    height=650

)    