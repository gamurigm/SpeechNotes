import asyncio
from pathlib import Path
from backend.services.agents.formatter_agent import FormatterAgent

async def main():
    agent = FormatterAgent(Path.cwd())
    job_id = agent.create_job(["notas/transcripcion_20260323_115410.md.original"])
    async for p in agent.run_job(job_id):
        print(p)

asyncio.run(main())
