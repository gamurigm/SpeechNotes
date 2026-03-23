import asyncio
import os
from dotenv import load_dotenv
from pathlib import Path
from backend.services.agents.formatter_agent import FormatterAgent

load_dotenv()

async def test():
    agent = FormatterAgent(Path.cwd())
    job_id = agent.create_job(['notas/transcripcion_20260323_115240.md'])
    async for p in agent.run_job(job_id):
        print(p)

asyncio.run(test())
