from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Ensure FastAPI can import from our src folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.predict import forecast_traffic
from src.route_optimizer import RouteOptimizer

app = FastAPI(title="Traffic Optimization API", version="1.0.0")

# Phase 20 (Deployment prep): Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow React to connect
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize our Graph
optimizer = RouteOptimizer()

class TrafficInput(BaseModel):
    road_id: str
    temperature: float = 25.0
    rainfall: float = 0.0
    hour: int
    is_weekend: int = 0
    is_peak_hour: int = 0
    density_lag_1: float = 50.0

@app.get("/health")
def health_check():
    return {"status": "Live", "engine": "XGBoost & Dijkstra Ready"}

@app.post("/predict-traffic")
def predict_traffic(data: TrafficInput):
    # Get ML Predictions
    predictions = forecast_traffic(data.dict())
    
    # Update our Route Graph with real-time predictions
    optimizer.update_traffic(data.road_id, predictions['current_density'])
    
    class_map = {0: "Low", 1: "Moderate", 2: "High", 3: "Very High"}
    
    return {
        "road_id": data.road_id,
        "predicted_density": predictions['current_density'],
        "traffic_level": class_map.get(predictions['congestion_class'], "Unknown")
    }

@app.post("/forecast-traffic")
def forecast_traffic_api(data: TrafficInput):
    predictions = forecast_traffic(data.dict())
    return predictions

@app.get("/optimize-route")
def optimize_route(source: str, destination: str):
    if source not in optimizer.graph.nodes or destination not in optimizer.graph.nodes:
        raise HTTPException(status_code=400, detail="Invalid source or destination nodes. Use A, B, C, or D.")
    
    route = optimizer.get_optimized_route(source.upper(), destination.upper())
    return route
