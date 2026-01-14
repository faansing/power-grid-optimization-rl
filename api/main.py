"""
FastAPI REST API for Power Grid Optimization
Provides endpoints for model inference, training monitoring, and system health
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSON Response
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import numpy as np
import yaml
import logging
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from starlette.responses import Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Power Grid Optimization API",
    description="AI-powered grid dispatch optimization using Deep RL",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = Histogram(
    'api_request_duration_seconds',
    'API request latency',
    ['method', 'endpoint']
)
PREDICTION_COUNT = Counter(
    'predictions_total',
    'Total predictions made'
)
MODEL_LOAD_TIME = Gauge(
    'model_load_seconds',
    'Time to load model'
)

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Global model holder
class ModelHolder:
    def __init__(self):
        self.model = None
        self.env = None
        self.loaded = False
    
    def load_model(self, model_path: str = './models/best_model.zip'):
        """Load trained model"""
        from environment.power_env import PowerGridEnvironment
        from agent.ppo_agent import ppo_agent
        import time
        
        start_time = time.time()
        
        # Create dummy environment for model loading
        dummy_data = np.random.rand(1000) * 500 + 300
        self.env = PowerGridEnvironment(dummy_data, config, mode='inference')
        
        # Load model
        self.model = ppo_agent(self.env, config)
        self.model.load(model_path)
        
        load_time = time.time() - start_time
        MODEL_LOAD_TIME.set(load_time)
        
        self.loaded = True
        logger.info(f"Model loaded in {load_time:.2f}s")

model_holder = ModelHolder()

# Pydantic models
class GridState(BaseModel):
    """Current grid state for prediction"""
    current_demand: float = Field(..., description="Current demand in MW")
    demand_forecast: List[float] = Field(..., description="4-hour demand forecast")
    generator_outputs: List[float] = Field(..., description="Current generator outputs")
    hour_of_day: int = Field(..., ge=0, le=23, description="Hour of day (0-23)")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday)")

class DispatchRecommendation(BaseModel):
    """Dispatch recommendation from AI"""
    generator_adjustments: List[float]
    predicted_cost: float
    predicted_supply: float
    confidence: float
    timestamp: str

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    model_loaded: bool
    timestamp: str
    version: str

class TrainingStatus(BaseModel):
    """Training job status"""
    job_id: str
    status: str
    progress: Optional[float] = None
    metrics: Optional[Dict] = None

# API Endpoints

@app.get("/", tags=["General"])
async def root():
    """Root endpoint"""
    return {
        "message": "Power Grid Optimization API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if model_holder.loaded else "starting",
        model_loaded=model_holder.loaded,
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0"
    )

@app.post("/predict", response_model=DispatchRecommendation, tags=["Inference"])
async def predict_dispatch(state: GridState):
    """
    Get dispatch recommendation for current grid state
    
    Returns optimal generator adjustments to minimize cost while meeting demand
    """
    if not model_holder.loaded:
        raise HTTPException(status_code=503, detail="Model not loaded yet")
    
    try:
        PREDICTION_COUNT.inc()
        
        # Construct observation vector
        # This is a simplified version - adjust based on actual observation space
        obs = np.array([
            state.current_demand / 1000.0,  # Normalized demand
            state.hour_of_day / 24.0,
            state.day_of_week / 7.0,
        ] + state.demand_forecast + state.generator_outputs, dtype=np.float32)
        
        # Get prediction
        action, _ = model_holder.model.predict(obs, deterministic=True)
        
        # Calculate predicted metrics (simplified)
        predicted_supply = sum(state.generator_outputs) + sum(action) * 10
        predicted_cost = predicted_supply * 42.0  # Simplified cost estimate
        
        return DispatchRecommendation(
            generator_adjustments=action.tolist(),
            predicted_cost=predicted_cost,
            predicted_supply=predicted_supply,
            confidence=0.95,  # Placeholder
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/model/load", tags=["Model Management"])
async def load_model(model_path: Optional[str] = None):
    """Load or reload the model"""
    try:
        if model_path is None:
            model_path = './models/best_model.zip'
        
        model_holder.load_model(model_path)
        
        return {"status": "success", "message": "Model loaded successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

@app.get("/model/info", tags=["Model Management"])
async def model_info():
    """Get information about loaded model"""
    if not model_holder.loaded:
        raise HTTPException(status_code=404, detail="No model loaded")
    
    return {
        "loaded": model_holder.loaded,
        "observation_space": str(model_holder.env.observation_space),
        "action_space": str(model_holder.env.action_space),
        "num_generators": model_holder.env.num_generators
    }

@app.get("/training/status/{job_id}", response_model=TrainingStatus, tags=["Training"])
async def get_training_status(job_id: str):
    """Get status of training job"""
    # Placeholder - implement actual training job tracking
    return TrainingStatus(
        job_id=job_id,
        status="running",
        progress=0.65,
        metrics={"current_step": 325000, "total_steps": 500000}
    )

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.get("/stats", tags=["Monitoring"])
async def get_stats():
    """Get API usage statistics"""
    return {
        "total_predictions": PREDICTION_COUNT._value._value,
        "model_loaded": model_holder.loaded,
        "uptime_seconds": 0,  # Implement actual uptime tracking
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Starting Power Grid Optimization API")
    
    # Try to load model on startup
    try:
        model_holder.load_model()
        logger.info("Model pre-loaded successfully")
    except Exception as e:
        logger.warning(f"Could not pre-load model: {e}")
        logger.warning("Model will need to be loaded via /model/load endpoint")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Power Grid Optimization API")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
