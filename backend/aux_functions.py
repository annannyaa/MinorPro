import requests
import networkx as nx
from datetime import datetime, timedelta, time
from math import radians, sin, cos, sqrt, atan2
from queue import PriorityQueue
from flask import jsonify, request
import folium
import random
API_KEY = "TkJNeMv0lEO00urfRPxkgCbaZvHpHCYp"

class RoutingOptimizer:
    def __init__(self, tomtom_api_key):
        self.tomtom_api_key = tomtom_api_key
        self.base_url_traffic = "https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json?point="
        self.base_url_route = "https://api.tomtom.com/routing/1/calculateRoute/"
        self.extra_route = "/json?&vehicleHeading=90&sectionType=traffic&report=effectiveSettings&routeType=eco&traffic=true&travelMode=car&vehicleMaxSpeed=120&vehicleCommercial=false&vehicleEngineType=combustion&key="
        self.cache = {}

    def calculate_time_priority(self, current_time, deadline):
        time_to_deadline = (deadline - current_time).total_seconds() / 3600
        return max(0, min(1, 1 - (time_to_deadline / 24)))

    def get_route_details(self, start_coords, end_coords):
        cache_key = (start_coords, end_coords)
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            start_lat, start_long = start_coords
            end_lat, end_long = end_coords

            traffic_response = requests.get(
                f"{self.base_url_traffic}{start_lat}%2C{start_long}&unit=KMPH&openLr=false&key={self.tomtom_api_key}")
            route_response = requests.get(
                f"{self.base_url_route}{start_lat},{start_long}:{end_lat},{end_long}{self.extra_route}{self.tomtom_api_key}")

            if traffic_response.status_code == 200 and route_response.status_code == 200:
                traffic_data = traffic_response.json()
                route_data = route_response.json()

                route_info = {
                    'travel_time': route_data['routes'][0]['summary']['travelTimeInSeconds'],
                    'distance': route_data['routes'][0]['summary']['lengthInMeters'] / 1000,
                    'current_speed': traffic_data['flowSegmentData']['currentSpeed']
                }

                self.cache[cache_key] = route_info
                return route_info
            else:
                raise Exception("API error")
        except Exception as e:
            print(f"Exception in get_route_details: {e}")
            return {'travel_time': float('inf'), 'distance': float('inf'), 'current_speed': 0}

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def heuristic_cost(self, start_dest, end_dest):
        geo_distance = self.haversine(start_dest['latitude'], start_dest['longitude'], end_dest['latitude'], end_dest['longitude'])
        time_priority = max(0.01, self.calculate_time_priority(datetime.now(), start_dest['deadline']))
        route_info = self.get_route_details((start_dest['latitude'], start_dest['longitude']), (end_dest['latitude'], end_dest['longitude']))

        heuristic_value = (
            geo_distance * 0.3 +
            (1 / time_priority) * 0.4 +
            (route_info['travel_time'] / 3600) * 0.3
        )

        return heuristic_value

    def a_star(self, destinations):
        # Initialize nodes and graph
        G = nx.DiGraph()
        for i, dest in enumerate(destinations):
            G.add_node(i, **dest)

        for start_idx, start_dest in enumerate(destinations):
            for end_idx, end_dest in enumerate(destinations):
                if start_idx != end_idx:
                    heuristic_weight = self.heuristic_cost(start_dest, end_dest)
                    G.add_edge(start_idx, end_idx, weight=heuristic_weight)

        all_paths = []
        for start in range(len(destinations)):
            try:
                current_path = [start]
                unvisited = set(range(len(destinations))) - {start}

                while unvisited:
                    next_dest = min(
                        unvisited,
                        key=lambda x: self.heuristic_cost(destinations[current_path[-1]], destinations[x])
                    )
                    current_path.append(next_dest)
                    unvisited.remove(next_dest)

                path_cost = sum(
                    self.heuristic_cost(destinations[current_path[i]], destinations[current_path[i+1]])
                    for i in range(len(current_path) - 1)
                )

                all_paths.append((current_path, path_cost))

            except Exception as e:
                print(f"Error calculating path from {start}: {e}")

        if all_paths:
            optimal_path, path_cost = min(all_paths, key=lambda x: x[1])
            return optimal_path

        return None



def get_coordinates(source, destination):
    # TomTom API endpoint
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{source[0]},{source[1]}:{destination[0]},{destination[1]}/json"

    # Parameters for the API request
    params = {
        "key": API_KEY,
        "routeType": "fastest",
        "travelMode": "car"
    }

    # Make API request
    response = requests.get(url, params=params)

    # Check response status
    if response.status_code == 200:
        data = response.json()
        # Extract route geometry (polyline of the route)
        route_points = data["routes"][0]["legs"][0]["points"]
        coordinates = [(point["latitude"], point["longitude"]) for point in route_points]
    else:
        print("Error:", response.status_code, response.text)
        exit()

    return coordinates
def string_to_datetime(deadline_str):
    """Convert a time string in 'HH:MM' format to a datetime object with today's date."""
    today = datetime.today().date()
    hour, minute = map(int, deadline_str.split(':'))
    deadline_time = time(hour, minute)  # Create a time object
    return datetime.combine(today, deadline_time)  # Combine with today's date

def plan_optimized_route(dustbins):
    destinations = []
    for dustbin in dustbins:
        print(dustbin)
        latitude, longitude, deadline = dustbin  # Only latitude and longitude, ignoring capacity
        # deadline = datetime.combine(datetime.today(), time(17, 0))  # Assuming 5:00 PM deadline
        destinations.append({'latitude': float(latitude), 'longitude': float(longitude), 'deadline': string_to_datetime(deadline)})

    optimizer = RoutingOptimizer('mTrA9kG5mGHYEIBmGPkwvCIAQ0DlARhJ')
    optimized_route = optimizer.a_star(destinations)
    bins = []
    print(optimized_route)
    for bin in list(optimized_route):
        print(f"Bins : {bin}")
        print(f"{dustbins[bin][0]}, {dustbins[bin][1]}")
        bins.append((dustbins[bin][0], dustbins[bin][1]))
    generate_map_html(bins)

    return optimized_route

def generate_map_html(transit_points = []):
    # Plot the route using folium
    # Start with the source location
    if len(transit_points) == 0:
        return

    map_route = folium.Map(location=transit_points[0], zoom_start=6)
    colour_list = ["green", "blue", "yellow", "orange", "ping", "purple", "grey", "black", "brown"]

    # Add markers
    for idx, transit in enumerate(transit_points):
        if idx == 0:
            folium.Marker(location=transit, popup="Source", icon=folium.Icon(color="red")).add_to(map_route)
        elif idx == len(transit_points) - 1:
            folium.Marker(location=transit, popup="Destination", icon=folium.Icon(color="red")).add_to(map_route)
        else:
            folium.Marker(location=transit, popup="Transit", icon=folium.Icon(color=random.choice(colour_list))).add_to(map_route)

    colour_list = ["green", "yellow", "orange", "ping", "purple", "grey", "black", "brown"]

    # Add the route line
    for idx, transit in enumerate(transit_points):
        if idx == len(transit_points) - 1:
            break
        if idx == 0:
            folium.PolyLine(locations=get_coordinates(transit_points[idx], transit_points[idx+1]), color="blue", weight=5).add_to(map_route)
        else:
            folium.PolyLine(locations=get_coordinates(transit_points[idx], transit_points[idx+1]), color=random.choice(colour_list), weight=5).add_to(map_route)

    # Save map to HTML and display
    map_route.save("route_map.html")
    print("Map saved as route_map.html. Open it in your browser.")
