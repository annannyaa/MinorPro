import networkx as nx
from geopy.distance import geodesic
import itertools
import random
import folium
import requests

API_KEY = "TkJNeMv0lEO00urfRPxkgCbaZvHpHCYp"

def plan_optimized_route(dustbins):
    """
    Plan optimized route for waste collection based on dustbin coordinates and capacities.
    Returns the sequence of dustbin IDs in the optimized order.
    """
    # Simple greedy algorithm for TSP
    # Start from the first dustbin and find the closest dustbin iteratively
    print(dustbins)
    dict={}
    for i in range(len(dustbins)):
        dict[i]={}
        dict[i]['latitude']=dustbins[i][0]
        dict[i]['longitude']=dustbins[i][1]
        dict[i]['capacity']=dustbins[i][2]
    print(dict)
        
    # Create a weighted graph
    G = nx.Graph()

    # Add nodes to the graph
    for bin_id, attrs in dict.items():
        G.add_node(bin_id, **attrs)

    # Calculate and add weighted edges to the graph considering effective capacity
    for start, start_attrs in dict.items():
        for end, end_attrs in dict.items():
            if start != end:
                dist = geodesic((start_attrs['latitude'], start_attrs['longitude']), (end_attrs['latitude'], end_attrs['longitude'])).kilometers
                start_remaining = start_attrs['capacity']
                end_remaining = end_attrs['capacity']
                weight = dist / min(start_remaining, end_remaining)
                G.add_edge(start, end, weight=weight)

    # Find the optimal path visiting all bins in the network
    all_bins = list(dict.keys())
    all_paths = []
    starting_bin = max(dict, key=lambda x: dict[x]['capacity'])  # Start from the most filled bin
    for perm in itertools.permutations(all_bins, len(all_bins)):
        if perm[0] == starting_bin:
            try:
                path_length = sum(nx.astar_path_length(G, perm[i], perm[i + 1], weight='weight') for i in range(len(perm) - 1))
                all_paths.append((perm, path_length))
            except nx.NetworkXNoPath:
                pass

    if all_paths:
        optimal_path = min(all_paths, key=lambda x: x[1])
        print("Optimal Path Routing Order considering all bins and their capacities:", list(optimal_path[0]))
        print("Path Length:", optimal_path[1])
    else:
        print("No feasible path found.")

    bins = []
    for bin in list(optimal_path[0]):
        bins.append((dustbins[bin][0], dustbins[bin][1]))
    generate_map_html(bins)

    #print(optimized_route)
    return list(optimal_path[0])

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
