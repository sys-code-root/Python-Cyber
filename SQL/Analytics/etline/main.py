import asyncio
from loguru import logger

import config  
from database import DatabaseManager
from orchestrator import PipelineOrchestrator

if __name__ == "__main__":
    dw_manager = DatabaseManager("sqlite+aiosqlite:///:memory:")
    orchestrator = PipelineOrchestrator(dw_manager)
    
    try:
        asyncio.run(orchestrator.run_pipeline())
    except KeyboardInterrupt:
        logger.info("Pipeline execution interrupted by the user.")