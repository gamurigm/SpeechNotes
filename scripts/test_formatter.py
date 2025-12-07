#!/usr/bin/env python3
"""
Quick test script for the Formatter Agent
Tests backend functionality without needing the UI
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from backend.services.formatter_agent import FormatterAgent


async def test_formatter():
    """Test the formatter agent"""
    
    print("🧪 Testing Formatter Agent")
    print("=" * 60)
    
    # Initialize agent
    agent = FormatterAgent(project_root)
    
    # Check if Minimax is configured
    if not agent.client:
        print("❌ MINIMAX_API_KEY not configured")
        print("   Set it in .env file")
        return
    
    print("✅ Minimax client configured")
    print(f"   Model: {agent.model}")
    
    # List available files
    notas_dir = project_root / "notas"
    files = [
        f for f in notas_dir.glob("*.md")
        if not f.name.endswith("_formatted.md") and not f.name.endswith(".original.md")
    ]
    
    if not files:
        print("\n❌ No files found in notas/")
        return
    
    print(f"\n📁 Found {len(files)} files:")
    for f in files[:5]:  # Show first 5
        print(f"   - {f.name}")
    
    # Create a test job with just 1 file
    test_file = str(files[0].relative_to(project_root))
    print(f"\n🎯 Creating test job for: {test_file}")
    
    job_id = agent.create_job([test_file], "notas")
    print(f"   Job ID: {job_id}")
    
    # Run the job and print progress
    print("\n🚀 Starting formatting job...\n")
    
    async for progress in agent.run_job(job_id):
        status_icon = {
            'reading': '📖',
            'formatting': '🤖',
            'saving': '💾',
            'completed': '✅',
            'error': '❌'
        }.get(progress.status, '⏳')
        
        print(f"{status_icon} [{progress.current}/{progress.total}] {progress.file_name}: {progress.status}")
        
        if progress.error:
            print(f"   Error: {progress.error}")
        
        if progress.output_path:
            print(f"   Output: {progress.output_path}")
    
    # Print summary
    job = agent.get_job(job_id)
    print("\n" + "=" * 60)
    print("📊 Job Summary:")
    print(f"   Status: {job.status}")
    print(f"   ✅ Successful: {job.successful}")
    print(f"   ❌ Failed: {job.failed}")
    
    if job.successful > 0:
        print("\n🎉 Test completed successfully!")
        print("\nNext steps:")
        print("1. Check notas/ for the *_formatted.md file")
        print("2. Start the web UI: cd web && npm run dev")
        print("3. Visit http://localhost:3006/formatter")
    else:
        print("\n⚠️ Test completed with errors - check output above")


if __name__ == '__main__':
    asyncio.run(test_formatter())
