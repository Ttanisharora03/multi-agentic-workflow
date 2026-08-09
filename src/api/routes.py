from fastapi import APIRouter, HTTPException, Depends
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

router = APIRouter(prefix="/api/v1")

plans_db = {}

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.post("/plan", response_model=PlanResponse)
async def plan_trip(request: PlanAPIRequest, graph=Depends(get_graph_dependency), db: AsyncSession = Depends(get_db)):
    try:
        initial_state = {
            "raw_input": request.query,
            "errors": [],
            "retry_count": 0
        }
        start_time = time.time()
        
        result = graph.invoke(initial_state)
        
        if "errors" in result and result["errors"]:
            raise HTTPException(status_code=400, detail=result["errors"])
            
        if "final_itinerary" not in result:
            raise HTTPException(status_code=500, detail="Failed to generate final itinerary")
            
        plan_id = str(uuid.uuid4())
        processing_time = time.time() - start_time
        
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
            print(f"Warning: Database save failed, falling back to memory. Error: {e}")
            plans_db[plan_id] = response_data
            

        return response_data
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Request timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plan/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Plan).where(Plan.id == plan_id))
        db_plan = result.scalars().first()
        if db_plan and db_plan.itinerary:
            return db_plan.itinerary
    except Exception as e:
        print(f"Warning: Database read failed. Error: {e}")
        
    if plan_id not in plans_db:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plans_db[plan_id]
