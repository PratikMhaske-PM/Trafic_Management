import networkx as nx

class RouteOptimizer:
    def __init__(self):
        # Phase 9: Representing the road network as a Graph
        self.graph = nx.DiGraph()
        self._build_city_graph()
        
    def _build_city_graph(self):
        # Nodes are Intersections (A, B, C, D)
        # Edges are Roads connecting them with physical properties
        self.graph.add_edge('A', 'B', road_id='R101', distance=5.0, max_speed=100, current_density=20)
        self.graph.add_edge('B', 'D', road_id='R102', distance=4.0, max_speed=100, current_density=20)
        
        self.graph.add_edge('A', 'C', road_id='R201', distance=6.0, max_speed=60, current_density=20)
        self.graph.add_edge('C', 'D', road_id='R202', distance=3.0, max_speed=60, current_density=20)
        
    def update_traffic(self, road_id, density):
        # Update dynamic edge weights based on real-time ML predictions
        for u, v, data in self.graph.edges(data=True):
            if data['road_id'] == road_id:
                data['current_density'] = density
                
    def get_optimized_route(self, source, target):
        # Phase 10: Traffic-Aware Route Optimization (Dijkstra)
        
        # Calculate dynamic cost for every edge
        for u, v, data in self.graph.edges(data=True):
            # Speed drops as density increases
            speed_penalty = max(0.1, 1.0 - (data['current_density'] / 100))
            actual_speed = data['max_speed'] * speed_penalty
            
            travel_time = data['distance'] / actual_speed
            
            # Route Cost = Time heavily penalized by traffic density
            data['cost'] = travel_time * (1 + (data['current_density'] / 50))
            
        # Dijkstra's Algorithm using our custom 'cost' weight
        try:
            path = nx.shortest_path(self.graph, source=source, target=target, weight='cost')
            
            # Calculate total metrics for the chosen path
            total_distance = 0
            total_time = 0
            for i in range(len(path)-1):
                edge = self.graph[path[i]][path[i+1]]
                total_distance += edge['distance']
                # basic time formula (hours to mins)
                total_time += (edge['distance'] / (edge['max_speed'] * max(0.1, 1 - (edge['current_density'] / 100)))) * 60
                
            return {
                "route_path": path,
                "total_distance_km": round(total_distance, 2),
                "estimated_time_mins": round(total_time, 2),
                "algorithm_used": "Dijkstra (Traffic-Aware)"
            }
        except nx.NetworkXNoPath:
            return {"error": "No route exists"}

if __name__ == "__main__":
    optimizer = RouteOptimizer()
    optimizer.update_traffic('R101', 95) # Massive traffic jam on the highway
    print(optimizer.get_optimized_route('A', 'D'))
