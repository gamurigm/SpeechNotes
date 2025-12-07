"""Script to run the FormatterAgent on a set of files.

Usage:
  python format_files.py

This will create a job for the listed files and run it synchronously using
the agent's run_job generator. If MINIMAX_API_KEY is not set, the agent will
use a local fallback formatter and write results to the `notas/` directory
as `<original>_formatted.md`.
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Load environment variables from repo `web/.env` if present so MINIMAX_API_KEY
# and related settings are available to the backend agent when launched from
# the backend folder.
web_env = ROOT.parent / 'web' / '.env'
if web_env.exists():
    load_dotenv(web_env)

from services.formatter_agent import FormatterAgent


async def main():
    agent = FormatterAgent(ROOT)

    files = [
        'notas/transcription_transcripcion_20251117_101413.md',
        'notas/transcription_transcripcion_20251117_120922.md',
        'notas/transcription_transcripcion_20251206_202701.md',
    ]

    job_id = agent.create_job(files, output_dir='notas')
    print(f'Created job {job_id} for {len(files)} files')

    async for progress in agent.run_job(job_id):
        print(f"[{progress.current}/{progress.total}] {progress.file_name} - {progress.status}")
        if progress.error:
            print('  Error:', progress.error)
        if progress.output_path:
            print('  Output:', progress.output_path)

    job = agent.get_job(job_id)
    print('Job completed:', job_id)
    print('Successful:', job.successful, 'Failed:', job.failed)


if __name__ == '__main__':
    asyncio.run(main())
