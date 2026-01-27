"""
Dojo Router - Leadership Simulation Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from ..services.dojo_service import DojoService
import os

router = APIRouter()

# Pydantic Models
class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class StartScenarioRequest(BaseModel):
    scenario_id: str
    language: str = "es"

class RoleplayRequest(BaseModel):
    scenario_id: str
    message: str
    history: List[Message] = []
    language: str = "es"
    system_prompt: Optional[str] = None # For custom scenarios

class EvaluateRequest(BaseModel):
    scenario_id: str
    history: List[Message]
    language: str = "es"
    system_prompt: Optional[str] = None

class CreateScenarioRequest(BaseModel):
    description: str
    language: str = "es"

# Initialize Dojo service
def get_dojo_service():
    api_key = os.environ.get("GOOGLE_API_KEY")
    return DojoService(api_key=api_key)

@router.get("/scenarios")
async def get_scenarios(
    language: str = "es",
    dojo_service: DojoService = Depends(get_dojo_service)
):
    """
    Get list of available Dojo scenarios
    """
    scenarios = dojo_service.get_scenarios(language=language)
    return {"scenarios": scenarios}

@router.post("/create")
async def create_custom_scenario(
    request: CreateScenarioRequest,
    dojo_service: DojoService = Depends(get_dojo_service)
):
    """
    Generate a custom scenario from a description
    """
    result = dojo_service.create_scenario_from_description(
        description=request.description,
        language=request.language
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return result

@router.post("/start")
async def start_scenario(
    request: StartScenarioRequest,
    dojo_service: DojoService = Depends(get_dojo_service)
):
    """
    Start a Dojo scenario and get the opening line
    """
    result = dojo_service.start_scenario(
        scenario_id=request.scenario_id,
        language=request.language
    )
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

@router.post("/message")
async def send_roleplay_message(
    request: RoleplayRequest,
    dojo_service: DojoService = Depends(get_dojo_service)
):
    """
    Send a message in the roleplay and get character's response
    """
    try:
        # Convert Pydantic models to dicts
        history_dicts = [{"role": m.role, "content": m.content} for m in request.history]
        
        response_text = dojo_service.generate_roleplay_response(
            scenario_id=request.scenario_id,
            user_input=request.message,
            history=history_dicts,
            language=request.language,
            custom_system_prompt=request.system_prompt
        )
        
        return {"message": response_text}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@router.post("/evaluate")
async def evaluate_performance(
    request: EvaluateRequest,
    dojo_service: DojoService = Depends(get_dojo_service)
):
    """
    Evaluate the user's performance in the roleplay
    """
    try:
        # Convert Pydantic models to dicts
        history_dicts = [{"role": m.role, "content": m.content} for m in request.history]
        
        evaluation = dojo_service.evaluate_performance(
            scenario_id=request.scenario_id,
            history=history_dicts,
            language=request.language
        )
        
        return {"evaluation": evaluation}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating evaluation: {str(e)}")
