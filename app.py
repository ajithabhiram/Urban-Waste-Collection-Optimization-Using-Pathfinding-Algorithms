import os
import re
from flask import Flask, render_template, request, redirect, url_for
import numpy as np
import pandas as pd
import random
from geopy.distance import geodesic
import folium
from branca.element import Element
import time

app = Flask(__name__)

# Sample data: List of locations with latitude, longitude, and garbage capacity
locations = {
    'Location': ['MG Road', 'Indiranagar', 'Koramangala', 'Whitefield', 'Electronic City',
                 'Jayanagar', 'Hebbal', 'Yelahanka', 'Marathahalli', 'Basavanagudi', 'Disposal Point'],
    'Latitude': [12.975787, 12.971891, 12.935228, 12.969800, 12.839969,
                 12.925007, 13.035542, 13.100000, 12.956345, 12.941230, 12.9716],
    'Longitude': [77.604977, 77.641151, 77.624485, 77.749947, 77.677034,
                  77.593803, 77.597100, 77.600000, 77.701136, 77.573290, 77.5946],
    #Garbage': [random.randint(0, 100) for _ in range(10)] + [0]  # Random garbage levels; disposal has 0
    # Assign specific garbage levels (in kg) for each location
    'Garbage': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 0]  # Disposal Point has 0 garbage
}

df = pd.DataFrame(locations)

# Calculate distance matrix
def calculate_distance_matrix(df):
    num_locations = len(df)
    distance_matrix = np.zeros((num_locations, num_locations))

    for i in range(num_locations):
        for j in range(num_locations):
            if i != j:
                distance_matrix[i][j] = geodesic(
                    (df.loc[i, 'Latitude'], df.loc[i, 'Longitude']),
                    (df.loc[j, 'Latitude'], df.loc[j, 'Longitude'])
                ).km
    return distance_matrix

distance_matrix = calculate_distance_matrix(df)
print("Distance Matrix:")
print(distance_matrix)

# Garbage level classification
def classify_garbage_level(garbage_level):
    if garbage_level >= 70:  # High Garbage
        return 'High', '#FFFF00'
    elif 40 <= garbage_level < 70:  # Medium Garbage
        return 'Medium', '#FFFF00'
    else:  # Low Garbage
        return 'Low', 'green'



def nearest_neighbor_with_capacity(distance_matrix, start, garbage_levels, truck_capacity, disposal_index):
    num_locations = len(distance_matrix)
    visited = [False] * num_locations
    visited[start] = True  # Mark starting location as visited
    current_location = start
    garbage_collected = 0
    path = [current_location]
    total_distance = 0
    trips_to_disposal = 0  # Counter for trips to the disposal point

    while not all(visited[:-1]):  # Exclude the Disposal Point from "all visited" check
        min_distance = float('inf')
        next_location = -1

        # Find the nearest unvisited location
        for i in range(num_locations):
            if not visited[i] and distance_matrix[current_location][i] < min_distance:
                min_distance = distance_matrix[current_location][i]
                next_location = i

        # If no valid next location is found, break
        if next_location == -1:
            break

        # Check if truck capacity is exceeded
        if garbage_collected + garbage_levels[next_location] > truck_capacity:
            # Go to Disposal Point
            total_distance += distance_matrix[current_location][disposal_index]
            path.append(disposal_index)
            garbage_collected = 0
            trips_to_disposal += 1  # Increment trip counter
            current_location = disposal_index

        # Visit the next location
        total_distance += distance_matrix[current_location][next_location]
        path.append(next_location)
        garbage_collected += garbage_levels[next_location]
        garbage_levels[next_location] = 0  # Empty the garbage bin at this location
        visited[next_location] = True
        current_location = next_location

    # Return to the Disposal Point at the end if not already there
    if current_location != disposal_index:
        total_distance += distance_matrix[current_location][disposal_index]
        path.append(disposal_index)
        trips_to_disposal += 1  # Increment trip counter

    return path, total_distance, "O(V^2)", "O(V)"


def dijkstra_with_capacity(distance_matrix, start, garbage_levels, truck_capacity, disposal_index):
    num_locations = len(distance_matrix)
    visited = [False] * num_locations
    dist = [float('inf')] * num_locations
    dist[start] = 0
    current_location = start
    garbage_collected = 0
    path = [current_location]  # Initial path starts with the starting location
    total_distance = 0
    trips_to_disposal = 0  # Counter for trips to the disposal point

    while not all(visited[:-1]):  # Exclude the Disposal Point from "all visited" check
        # Find the nearest unvisited location
        next_location = -1
        min_distance = float('inf')

        for i in range(num_locations):
            if not visited[i] and distance_matrix[current_location][i] < min_distance:
                next_location = i
                min_distance = distance_matrix[current_location][i]

        # If no valid next location remains, break
        if next_location == -1:
            break

        # Check if truck capacity is exceeded
        if garbage_collected + garbage_levels[next_location] > truck_capacity:
            # Travel to the Disposal Point
            total_distance += distance_matrix[current_location][disposal_index]
            path.append(disposal_index)
            garbage_collected = 0
            trips_to_disposal += 1  # Increment trip counter
            current_location = disposal_index

        # Travel to the next location
        total_distance += distance_matrix[current_location][next_location]
        path.append(next_location)
        garbage_collected += garbage_levels[next_location]
        garbage_levels[next_location] = 0  # Empty garbage at current location
        visited[next_location] = True
        current_location = next_location

    # Return to the Disposal Point at the end if garbage remains in the truck
    if garbage_collected > 0 and current_location != disposal_index:
        total_distance += distance_matrix[current_location][disposal_index]
        path.append(disposal_index)
        trips_to_disposal += 1  # Increment trip counter

    # Remove duplicate start location if it exists
    if len(path) > 1 and path[0] == path[1]:
        path.pop(0)

    return path, total_distance, "O(V^2)", "O(V)"



def bellman_ford_with_capacity(distance_matrix, start, garbage_levels, truck_capacity, disposal_index):
    num_locations = len(distance_matrix)
    
    # Initialize distances and visited status
    dist = [float('inf')] * num_locations
    dist[start] = 0
    garbage_collected = 0
    path = [start]
    total_distance = 0
    visited = [False] * num_locations
    current_location = start
    trips_to_disposal = 0  # Counter for trips to the disposal point

    while not all(visited[:-1]):  # Exclude the Disposal Point from "all visited" check
        # Check if the truck's capacity is exceeded
        if garbage_collected + garbage_levels[current_location] > truck_capacity:
            # Go to the Disposal Point to unload
            total_distance += distance_matrix[current_location][disposal_index]
            path.append(disposal_index)
            garbage_collected = 0  # Reset garbage collected
            trips_to_disposal += 1  # Increment trip counter
            current_location = disposal_index

        # Find the nearest unvisited location with the shortest distance
        next_location = -1
        min_distance = float('inf')

        for i in range(num_locations):
            if not visited[i] and dist[i] < min_distance:
                next_location = i
                min_distance = dist[i]

        # If no valid next location remains, break
        if next_location == -1:
            break

        # Visit the next location
        total_distance += distance_matrix[current_location][next_location]
        path.append(next_location)
        garbage_collected += garbage_levels[next_location]

        # Mark the current location as visited and empty its garbage
        garbage_levels[next_location] = 0
        visited[next_location] = True
        current_location = next_location

        # Update distances for neighbors of the current location
        for v in range(num_locations):
            if distance_matrix[current_location][v] > 0 and dist[current_location] + distance_matrix[current_location][v] < dist[v]:
                dist[v] = dist[current_location] + distance_matrix[current_location][v]

    # Ensure a final trip to the Disposal Point if garbage remains
    if garbage_collected > 0 and current_location != disposal_index:
        total_distance += distance_matrix[current_location][disposal_index]
        path.append(disposal_index)
        trips_to_disposal += 1  # Increment trip counter

    # Remove unnecessary duplicate entries
    clean_path = []
    for loc in path:
        if not clean_path or clean_path[-1] != loc:
            clean_path.append(loc)

    return clean_path, total_distance, "O(VE)", "O(V)"






'''def a_star_algorithm(distance_matrix, start, garbage_levels, truck_capacity, disposal_index):
    import heapq

    num_locations = len(distance_matrix)
    visited = [False] * num_locations
    heap = []
    trips_to_disposal = 0  # Counter for trips to the disposal point

    # (estimated_cost, current_location, path, garbage_collected, actual_cost)
    heapq.heappush(heap, (0, start, [start], 0, 0))
    total_distance = 0

    while heap:
        estimated_cost, current_location, path, garbage_collected, actual_cost = heapq.heappop(heap)

        if not visited[current_location]:
            visited[current_location] = True

            # If truck capacity is exceeded, go to the disposal point
            if garbage_collected > truck_capacity:
                total_distance += distance_matrix[current_location][disposal_index]
                path.append(disposal_index)
                garbage_collected = 0
                trips_to_disposal += 1  # Increment trips counter
                current_location = disposal_index

            # If all locations (except disposal) are visited, return to disposal point
            if all(visited[:-1]):
                total_distance += distance_matrix[current_location][disposal_index]
                path.append(disposal_index)
                trips_to_disposal += 1  # Final trip to the disposal point
                return path, total_distance, trips_to_disposal, "O(E log V)", "O(V)"

            # Explore neighbors
            for neighbor in range(num_locations):
                if not visited[neighbor] and distance_matrix[current_location][neighbor] > 0:
                    # Heuristic: Distance to the disposal point from the neighbor
                    heuristic = distance_matrix[neighbor][disposal_index]
                    estimated_cost = actual_cost + distance_matrix[current_location][neighbor] + heuristic
                    heapq.heappush(heap, (
                        estimated_cost,
                        neighbor,
                        path + [neighbor],
                        garbage_collected + garbage_levels[neighbor],
                        actual_cost + distance_matrix[current_location][neighbor]
                    ))

    # If the loop ends without visiting all nodes
    return path, total_distance, "O(E log V)", "O(V)"
'''


def johnsons_algorithm(distance_matrix, start, garbage_levels, truck_capacity, disposal_index):
    from scipy.sparse.csgraph import johnson

    num_locations = len(distance_matrix)
    shortest_paths = johnson(distance_matrix)
    visited = [False] * num_locations
    path = [start]
    current_location = start
    garbage_collected = 0
    total_distance = 0
    trips_to_disposal = 0  # Counter for trips to the disposal point

    while not all(visited[:-1]):  # Exclude Disposal Point
        visited[current_location] = True

        # Check if truck capacity is exceeded
        if garbage_collected + garbage_levels[current_location] > truck_capacity:
            path.append(disposal_index)
            garbage_collected = 0
            total_distance += shortest_paths[current_location][disposal_index]
            current_location = disposal_index
            trips_to_disposal += 1  # Increment trips counter

        # Select next closest unvisited location
        next_location = -1
        min_distance = float('inf')

        for i in range(num_locations):
            if not visited[i] and shortest_paths[current_location][i] < min_distance:
                min_distance = shortest_paths[current_location][i]
                next_location = i

        if next_location == -1:  # No valid location remains
            break

        # Travel to the next location
        total_distance += shortest_paths[current_location][next_location]
        path.append(next_location)
        garbage_collected += garbage_levels[next_location]
        garbage_levels[next_location] = 0
        current_location = next_location

    # Final trip to the disposal point if garbage remains
    if garbage_collected > 0:
        total_distance += shortest_paths[current_location][disposal_index]
        path.append(disposal_index)
        trips_to_disposal += 1

    return path, total_distance, "O(VE + V log V)", "O(V^2)"




def floyd_warshall_with_capacity(distance_matrix, start, garbage_levels, truck_capacity, disposal_index):
    num_locations = len(distance_matrix)
    
    # Initialize distances and paths
    dist = [[float('inf')] * num_locations for _ in range(num_locations)]
    next_node = [[-1] * num_locations for _ in range(num_locations)]

    # Set initial distances and paths
    for i in range(num_locations):
        for j in range(num_locations):
            if i == j:
                dist[i][j] = 0
            elif distance_matrix[i][j] > 0:
                dist[i][j] = distance_matrix[i][j]
                next_node[i][j] = j

    # Floyd-Warshall core logic
    for k in range(num_locations):
        for i in range(num_locations):
            for j in range(num_locations):
                if dist[i][j] > dist[i][k] + dist[k][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    next_node[i][j] = next_node[i][k]

    # Path reconstruction helper
    def reconstruct_path(start, end):
        if next_node[start][end] == -1:
            return []
        path = [start]
        while start != end:
            start = next_node[start][end]
            path.append(start)
        return path

    # Garbage collection logic
    visited = [False] * num_locations
    visited[start] = True
    current_location = start
    path = [start]
    garbage_collected = 0
    total_distance = 0
    trips_to_disposal = 0  # Counter for trips to the disposal point

    while not all(visited[:-1]):  # Exclude the disposal point
        # Find the nearest unvisited node
        min_distance = float('inf')
        next_location = -1
        for i in range(num_locations):
            if not visited[i] and dist[current_location][i] < min_distance:
                min_distance = dist[current_location][i]
                next_location = i

        if next_location == -1:  # No unvisited nodes remain
            break

        # If the truck is full, go to the disposal point
        if garbage_collected + garbage_levels[next_location] > truck_capacity:
            sub_path = reconstruct_path(current_location, disposal_index)
            total_distance += sum(dist[sub_path[i]][sub_path[i + 1]] for i in range(len(sub_path) - 1))
            path.extend(sub_path[1:])  # Append without duplicating current_location
            garbage_collected = 0
            current_location = disposal_index
            trips_to_disposal += 1

        # Visit the next location
        sub_path = reconstruct_path(current_location, next_location)
        total_distance += sum(dist[sub_path[i]][sub_path[i + 1]] for i in range(len(sub_path) - 1))
        path.extend(sub_path[1:])  # Append without duplicating current_location
        garbage_collected += garbage_levels[next_location]
        garbage_levels[next_location] = 0
        visited[next_location] = True
        current_location = next_location

    # Return to the disposal point if not already there
    if current_location != disposal_index:
        sub_path = reconstruct_path(current_location, disposal_index)
        total_distance += sum(dist[sub_path[i]][sub_path[i + 1]] for i in range(len(sub_path) - 1))
        path.extend(sub_path[1:])
        trips_to_disposal += 1

    return path, total_distance, "O(V^3)", "O(V^2)"


def ant_colony_optimization(distance_matrix, start, garbage_levels, truck_capacity, disposal_index):
    """
    ACO for garbage vehicle routing with truck capacity constraint.

    Parameters:
        distance_matrix: 2D list or numpy array with distances between locations.
        start: Index of the starting location.
        garbage_levels: List of garbage levels at each location (kg).
        truck_capacity: Maximum garbage capacity of the truck.
        disposal_index: Index of the disposal point.

    Returns:
        best_path: List of location indices representing the best route.
        best_distance: Total distance of the best route.
        trips_to_disposal: Number of trips to the disposal point.
        time_complexity: Time complexity of the algorithm.
        space_complexity: Space complexity of the algorithm.
    """
    # Parameters
    num_locations = len(distance_matrix)
    num_ants = 10
    pheromone = np.ones((num_locations, num_locations))  # Pheromone matrix
    alpha = 1  # Pheromone importance
    beta = 2   # Distance importance
    evaporation_rate = 0.5
    iterations = 100

    best_path = None
    best_distance = float('inf')
    best_trips = float('inf')

    for _ in range(iterations):
        all_paths = []
        for ant in range(num_ants):
            visited = [False] * num_locations
            visited[start] = True
            current_path = [start]
            current_location = start
            current_garbage_levels = garbage_levels[:]  # Copy garbage levels for this ant
            garbage_collected = 0
            total_distance = 0
            trips_to_disposal = 0

            while not all(visited[:-1]):  # Exclude the disposal point
                probabilities = []
                for next_location in range(num_locations):
                    if not visited[next_location] and distance_matrix[current_location][next_location] > 0:
                        # Compute probability for unvisited nodes
                        probabilities.append(
                            (pheromone[current_location][next_location] ** alpha) *
                            ((1.0 / distance_matrix[current_location][next_location]) ** beta)
                        )
                    else:
                        probabilities.append(0)

                probabilities = np.array(probabilities)
                if probabilities.sum() == 0:  # No feasible moves left
                    break
                probabilities /= probabilities.sum()

                # Choose the next location
                next_location = np.random.choice(range(num_locations), p=probabilities)

                # Check truck capacity
                if garbage_collected + current_garbage_levels[next_location] > truck_capacity:
                    # Route to disposal point
                    current_path.append(disposal_index)
                    total_distance += distance_matrix[current_location][disposal_index]
                    current_location = disposal_index
                    garbage_collected = 0
                    trips_to_disposal += 1  # Increment trips counter

                # Move to the next location
                current_path.append(next_location)
                total_distance += distance_matrix[current_location][next_location]
                garbage_collected += current_garbage_levels[next_location]
                current_garbage_levels[next_location] = 0  # Mark garbage as collected
                visited[next_location] = True
                current_location = next_location

            # Return to the disposal point if not already there
            if current_location != disposal_index:
                current_path.append(disposal_index)
                total_distance += distance_matrix[current_location][disposal_index]
                trips_to_disposal += 1

            # Save the path and its total distance
            all_paths.append((current_path, total_distance, trips_to_disposal))

        # Update pheromones
        pheromone *= (1 - evaporation_rate)  # Evaporation
        for path, dist, trips in all_paths:
            # Update the best path
            if dist < best_distance:
                best_path, best_distance, best_trips = path, dist, trips
            # Deposit pheromones
            for i in range(len(path) - 1):
                pheromone[path[i]][path[i + 1]] += 1.0 / dist

    return best_path, best_distance, "O(iterations * ants * V^2)", "O(V^2)"


def get_best_algorithm(distance_matrix, start, garbage_levels, truck_capacity, disposal_index):
    algorithms = [
        ('Nearest Neighbor with Capacity', nearest_neighbor_with_capacity),
        ('Dijkstra with Capacity', dijkstra_with_capacity),
        ('Bellman-Ford with Capacity', bellman_ford_with_capacity),
        ('Johnson\'s Algorithm', johnsons_algorithm),
        ('Floyd-Warshall Algorithm', floyd_warshall_with_capacity),
        ('Ant Colony Optimization (ACO)', ant_colony_optimization),
    ]

    best_result = None
    best_algorithm = None

    for algo_name, algo_func in algorithms:
        try:
            # Call the algorithm function
            path, total_distance, time_complexity, space_complexity = algo_func(
                distance_matrix, start, garbage_levels[:], truck_capacity, disposal_index
            )

            # Define your optimization metric (e.g., minimize total distance)
            if best_result is None or total_distance < best_result['total_distance']:
                best_result = {
                    'algorithm': algo_name,
                    'path': path,
                    'total_distance': total_distance,
                    'time_complexity': time_complexity,
                    'space_complexity': space_complexity
                }
                best_algorithm = algo_name

        except Exception as e:
            print(f"Error with {algo_name}: {str(e)}")

    return best_result


def calculate_trips_from_path(path, disposal_index):
    """
    Calculate the number of trips based on the number of occurrences
    of the disposal point in the path.
    
    Args:
        path (list): The list of locations visited in the route.
        disposal_index (int): The index representing the disposal point.
        
    Returns:
        int: The number of trips to the disposal point.
    """
    return path.count(disposal_index)-1



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Inputs
        start_location = int(request.form['start_location'])
        disposal_index = len(df) - 1
        truck_capacity = 100
        garbage_levels = df['Garbage'].tolist()

        # Validate garbage levels
        if any(g < 0 for g in garbage_levels):
            return render_template('error.html', message="Garbage levels cannot be negative.")

        results = []
        individual_maps = []

        # Define colors for routes
        route_colors = {
            'Nearest Neighbor Algorithm': 'red',
            'Dijkstra Algorithm': 'blue',
            'Bellman-Ford Algorithm': 'green',
            'Johnson\'s Algorithm': 'orange',
            'floyd warshall Algorithm': 'brown',
            'Ant Colony Optimization (ACO)': 'pink'
        }

        # Garbage level classification
        def classify_garbage_level(garbage_level):
            if garbage_level >= 70:  # High Garbage
                return 'High', 'red'
            elif 40 <= garbage_level < 70:  # Medium Garbage
                return 'Medium', 'orange'
            else:  # Low Garbage
                return 'Low', 'green'

        # Create the combined map
        map_center = (df.loc[start_location, 'Latitude'], df.loc[start_location, 'Longitude'])
        combined_map = folium.Map(location=map_center, zoom_start=12)

        # Add markers for all locations to combined map
        for idx, row in df.iterrows():
            if idx == disposal_index:
                folium.Marker(
                    location=(row['Latitude'], row['Longitude']),
                    popup=f"<strong>Disposal Point</strong><br>Garbage Capacity: Unlimited",
                    icon=folium.Icon(color='black', icon='trash')
                ).add_to(combined_map)
            else:
                garbage_status, marker_color = classify_garbage_level(row['Garbage'])
                folium.Marker(
                    location=(row['Latitude'], row['Longitude']),
                    popup=f"{row['Location']}<br>Garbage Level: {garbage_status} ({row['Garbage']} kg)",
                    icon=folium.Icon(color=marker_color)
                ).add_to(combined_map)

        # Algorithms
        algorithms = [
            ('Nearest Neighbor Algorithm', nearest_neighbor_with_capacity),
            ('Dijkstra Algorithm', dijkstra_with_capacity),
            ('Bellman-Ford Algorithm', bellman_ford_with_capacity),
            ('Johnson\'s Algorithm', johnsons_algorithm),
            ('floyd warshall Algorithm', floyd_warshall_with_capacity),
            ('Ant Colony Optimization (ACO)', ant_colony_optimization),
        ]

        # Directory for saving maps
        maps_dir = os.path.join(os.getcwd(), 'static', 'maps')
        if not os.path.exists(maps_dir):
            os.makedirs(maps_dir)

        for algo_name, algo_func in algorithms:
            try:
                # Measure execution time
                start_time = time.time()
                path, total_distance, time_complexity, space_complexity = algo_func(
                    distance_matrix, start_location, garbage_levels[:], truck_capacity, disposal_index
                )
                execution_time = time.time() - start_time

                # Add the route to the combined map
                for i in range(len(path) - 1):
                    start_coords = (df.loc[path[i], 'Latitude'], df.loc[path[i], 'Longitude'])
                    end_coords = (df.loc[path[i + 1], 'Latitude'], df.loc[path[i + 1], 'Longitude'])
                    folium.PolyLine(
                        [start_coords, end_coords],
                        color=route_colors[algo_name],
                        weight=2.5,
                        tooltip=f"{algo_name} Route"
                    ).add_to(combined_map)

                # Create a specific algorithm map
                algo_map = folium.Map(location=map_center, zoom_start=12)

                # Add markers for individual maps
                for idx, row in df.iterrows():
                    if idx == disposal_index:
                        folium.Marker(
                            location=(row['Latitude'], row['Longitude']),
                            popup=f"<strong>Disposal Point</strong><br>Garbage Capacity: Unlimited",
                            icon=folium.Icon(color='black', icon='trash')
                        ).add_to(algo_map)
                    else:
                        garbage_status, marker_color = classify_garbage_level(row['Garbage'])
                        folium.Marker(
                            location=(row['Latitude'], row['Longitude']),
                            popup=f"{row['Location']}<br>Garbage Level: {garbage_status} ({row['Garbage']} kg)",
                            icon=folium.Icon(color=marker_color)
                        ).add_to(algo_map)

                # Add the route to the individual map
                for i in range(len(path) - 1):
                    start_coords = (df.loc[path[i], 'Latitude'], df.loc[path[i], 'Longitude'])
                    end_coords = (df.loc[path[i + 1], 'Latitude'], df.loc[path[i + 1], 'Longitude'])
                    folium.PolyLine(
                        [start_coords, end_coords],
                        color=route_colors[algo_name],
                        weight=2.5,
                        tooltip=f"{algo_name} Route"
                    ).add_to(algo_map)
                # Add a legend to the individual map
                legend_html = """
<div style="position: fixed; bottom: 50px; left: 50px; width: 300px; height: auto; 
background-color: white; z-index:9999; font-size:14px; 
border:2px solid grey; padding: 10px;">
<strong>Legend:</strong><br>
<i style="background:red; width: 10px; height: 10px; display:inline-block;"></i> High Garbage (70+ kg)<br>
<i style="background:orange; width: 10px; height: 10px; display:inline-block;"></i> Medium Garbage (40-69 kg)<br>
<i style="background:green; width: 10px; height: 10px; display:inline-block;"></i> Low Garbage (0-39 kg)<br>
<i style="background:black; width: 10px; height: 10px; display:inline-block;"></i> Disposal Point<br>
<hr>
<i style="background:red; width: 10px; height: 10px; display:inline-block;"></i> Nearest Neighbor Route<br>
<i style="background:blue; width: 10px; height: 10px; display:inline-block;"></i> Dijkstra Route<br>
<i style="background:green; width: 10px; height: 10px; display:inline-block;"></i> Bellman-Ford Route<br>

<i style="background:orange; width: 10px; height: 10px; display:inline-block;"></i> Johnson's Algorithm Route<br>
<i style="background:brown; width: 10px; height: 10px; display:inline-block;"></i> floyd warshall Algorithm Route<br>
<i style="background:pink; width: 10px; height: 10px; display:inline-block;"></i> Ant Colony Optimization Route<br>
</div>
"""

                algo_map.get_root().html.add_child(folium.Element(legend_html))


                # Save the individual map
                safe_algo_name = re.sub(r'[^a-zA-Z0-9]', '_', algo_name)  # Replace invalid characters
                map_file = os.path.join(maps_dir, f"{safe_algo_name}_map.html")
                algo_map.save(map_file)
                
                individual_maps.append((algo_name, f"/static/maps/{os.path.basename(map_file)}"))

                # Append results
                results.append({
                    'algorithm': algo_name,
                    'path_length': round(total_distance, 2),
                    'fuel_consumption': round(total_distance / 10.0, 2),
                    'co2_emissions': round((total_distance / 10.0) * 2.31, 2),
                    'execution_time': round(execution_time, 4),
                    'trips': calculate_trips_from_path(path, disposal_index),
                    'path': ' -> '.join([df.loc[i, 'Location'] for i in path]),
                    'time_complexity': time_complexity,
                    'space_complexity': space_complexity,
                    'error': None
                })

            except Exception as e:
                results.append({
                    'algorithm': algo_name,
                    'path_length': None,
                    'fuel_consumption': None,
                    'co2_emissions': None,
                    'execution_time': None,
                    'trips': None,
                    'path': None,
                    'time_complexity': None,
                    'space_complexity': None,
                    'error': str(e)
                })
        # Get the best algorithm result
        best_result = get_best_algorithm(
            distance_matrix, start_location, garbage_levels[:], truck_capacity, disposal_index
        )
        # Identify the best algorithm result (based on path length or any other metric)
        best_result = min(results, key=lambda x: x['path_length'] if x['path_length'] is not None else float('inf'))

        



        # Add legend to combined map
        legend_html_combined = """
<div style="position: fixed; bottom: 50px; left: 50px; width: 300px; height: auto; 
    background-color: white; z-index:9999; font-size:14px; 
    border:2px solid grey; padding: 10px;">
    <strong>Legend:</strong><br>
    <i style="background:red; width: 10px; height: 10px; display:inline-block;"></i> High Garbage (70+ kg)<br>
    <i style="background:orange; width: 10px; height: 10px; display:inline-block;"></i> Medium Garbage (40-69 kg)<br>
    <i style="background:green; width: 10px; height: 10px; display:inline-block;"></i> Low Garbage (0-39 kg)<br>
    <i style="background:black; width: 10px; height: 10px; display:inline-block;"></i> Disposal Point<br>
    <hr>
    <i style="background:red; width: 10px; height: 10px; display:inline-block;"></i> Nearest Neighbor Route<br>
    <i style="background:blue; width: 10px; height: 10px; display:inline-block;"></i> Dijkstra Route<br>
    <i style="background:green; width: 10px; height: 10px; display:inline-block;"></i> Bellman-Ford Route<br>
    
    <i style="background:orange; width: 10px; height: 10px; display:inline-block;"></i> Johnson's Algorithm Route<br>
    <i style="background:brown; width: 10px; height: 10px; display:inline-block;"></i> floyd warshall Algorithm Route<br>
    <i style="background:pink; width: 10px; height: 10px; display:inline-block;"></i> Ant Colony Optimization Route<br>
</div>
"""
        combined_map.get_root().html.add_child(folium.Element(legend_html_combined))

        # Save the combined map
        combined_map_file = os.path.join(maps_dir, "combined_map.html")
        combined_map.save(combined_map_file)

        return render_template(
            'result.html',
            results=results,
            map_file=f"/static/maps/combined_map.html",
            best_result=min(results, key=lambda x: x['path_length'] if x['path_length'] is not None else float('inf')),
            individual_maps=individual_maps
        )

    return render_template('index.html', locations=df['Location'].tolist())



if __name__ == "__main__":
    app.run(debug=True)
