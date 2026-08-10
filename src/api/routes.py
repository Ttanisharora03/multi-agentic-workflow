from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from typing import Dict, Any, cast, Literal
import uuid
import time
# pyright: ignore [reportMissingImports]
from src.schemas import PlanAPIRequest, PlanResponse
# pyrefly: ignore [missing-import]
from src.api.dependencies import get_graph_dependency
# pyrefly: ignore [missing-import]
from src.db.session import get_db, AsyncSession
# pyrefly: ignore [missing-import]
from src.db.models import Plan
from sqlalchemy.future import select
import structlog
import os
import tempfile
# pyrefly: ignore [missing-import]
from src.tools.audio import transcribe_audio

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1")

plans_db = {}

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/plan", response_model=PlanResponse)
async def plan_trip(request: PlanAPIRequest, fresh: bool = False, graph=Depends(get_graph_dependency), db: AsyncSession = Depends(get_db)):
    plan_id = str(uuid.uuid4())
    log = logger.bind(plan_id=plan_id)
    log.info("plan_trip_started", query=request.query)
    
    try:
        initial_state = {
            "raw_input": request.query,
            "errors": [],
            "retry_count": 0,
            "plan_id": plan_id,
            "fresh": fresh
        }
        start_time = time.time()
        
        result = graph.invoke(initial_state)
        
        if "errors" in result and result["errors"]:
            log.error("plan_trip_failed", errors=result["errors"])
            raise HTTPException(status_code=400, detail=result["errors"])
            
        if "final_itinerary" not in result:
            log.error("final_itinerary_missing")
            raise HTTPException(status_code=500, detail="Failed to generate final itinerary")
            
        processing_time = time.time() - start_time
        log.info("plan_trip_completed", processing_time=processing_time)
        
        response_data = PlanResponse(
            plan_id=plan_id,
            status="completed",
            itinerary=result.get("final_itinerary"),
            budget_summary=result.get("budget_output"),
            review=result.get("review_result"),
            errors=result.get("errors", []),
            processing_time_seconds=processing_time
        )
        
        # Try to persist to database, fallback to in-memory if DB is not available
        try:
            db_plan = Plan(
                id=plan_id,
                query=request.query,
                status="completed",
                itinerary=response_data.model_dump(),
                processing_time_seconds=processing_time
            )
            db.add(db_plan)
            await db.commit()
        except Exception as e:
            await db.rollback()
            log.warning("database_save_failed", error=str(e))
            plans_db[plan_id] = response_data
            

        return response_data
    except TimeoutError:
        log.error("plan_trip_timeout")
        raise HTTPException(status_code=504, detail="Request timed out")
    except Exception as e:
        log.error("plan_trip_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/plan/audio", response_model=PlanResponse)
async def plan_trip_audio(
    file: UploadFile = File(...),
    fresh: bool = False,
    graph=Depends(get_graph_dependency),
    db: AsyncSession = Depends(get_db)
):
    plan_id = str(uuid.uuid4())
    log = logger.bind(plan_id=plan_id)
    log.info("plan_trip_audio_started", filename=file.filename)
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".mp3", ".wav", ".m4a", ".ogg", ".webm"]:
        raise HTTPException(status_code=400, detail="Unsupported audio format")
        
    temp_path = ""
    try:
        # Save uploaded file to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
            
        log.info("audio_saved", path=temp_path)
        
        # Transcribe audio
        transcribed_text = await transcribe_audio(temp_path)
        if not transcribed_text:
            raise HTTPException(status_code=400, detail="Audio transcription failed or was empty")
            
        log.info("audio_transcribed", text=transcribed_text)
        
        # Now create a PlanAPIRequest and call the main plan_trip function logic
        request = PlanAPIRequest(query=transcribed_text, traveler_count=1)
        
        # We can just reuse the plan_trip logic by calling it directly, but since it generates its own plan_id
        # we'll just run the graph here directly to keep the plan_id tied to this audio request log context.
        initial_state = {
            "raw_input": request.query,
            "errors": [],
            "retry_count": 0,
            "plan_id": plan_id,
            "fresh": fresh
        }
        start_time = time.time()
        
        result = graph.invoke(initial_state)
        
        if "errors" in result and result["errors"]:
            log.error("plan_trip_audio_failed", errors=result["errors"])
            raise HTTPException(status_code=400, detail=result["errors"])
            
        if "final_itinerary" not in result:
            log.error("final_itinerary_missing")
            raise HTTPException(status_code=500, detail="Failed to generate final itinerary")
            
        processing_time = time.time() - start_time
        log.info("plan_trip_audio_completed", processing_time=processing_time)
        
        response_data = PlanResponse(
            plan_id=plan_id,
            status="completed",
            itinerary=result.get("final_itinerary"),
            budget_summary=result.get("budget_output"),
            review=result.get("review_result"),
            errors=result.get("errors", []),
            processing_time_seconds=processing_time
        )
        
        try:
            db_plan = Plan(
                id=plan_id,
                query=request.query,
                status="completed",
                itinerary=response_data.model_dump(),
                processing_time_seconds=processing_time
            )
            db.add(db_plan)
            await db.commit()
        except Exception as e:
            await db.rollback()
            log.warning("database_save_failed", error=str(e))
            plans_db[plan_id] = response_data
            
        return response_data
        
    except HTTPException:
        raise
    except TimeoutError:
        log.error("plan_trip_audio_timeout")
        raise HTTPException(status_code=504, detail="Request timed out")
    except Exception as e:
        log.error("plan_trip_audio_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@router.get("/plan/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Plan).where(Plan.id == plan_id))
        db_plan = result.scalars().first()
        if db_plan and db_plan.itinerary:
            return db_plan.itinerary
    except Exception as e:
        logger.warning("database_read_failed", plan_id=plan_id, error=str(e))
        
    if plan_id not in plans_db:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plans_db[plan_id]
