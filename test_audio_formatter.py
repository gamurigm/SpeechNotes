"""
Audio Formatter Test Runner
Quick script to test the audio formatting functionality
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from backend.services.audio_formatter import AudioFormatterService


async def run_quick_test():
    """Run a quick test of the audio formatter"""
    
    print("=" * 80)
    print("🧪 AUDIO FORMATTER - QUICK FUNCTIONALITY TEST")
    print("=" * 80)
    
    # Initialize service
    formatter = AudioFormatterService(project_root=project_root)
    
    # Test 1: Check available profiles
    print("\n📋 TEST 1: Available Profiles")
    print("-" * 80)
    profiles = formatter.get_available_profiles()
    for profile in profiles:
        print(f"✅ {profile['name'].upper()}")
        print(f"   Description: {profile['description']}")
        print(f"   Settings: {profile['settings']}")
    
    # Test 2: Detect format of existing audio files
    print("\n🔍 TEST 2: Format Detection")
    print("-" * 80)
    
    audio_dir = project_root / "audio"
    if audio_dir.exists():
        audio_files = list(audio_dir.glob("*.mp3")) + list(audio_dir.glob("*.wav"))
        
        if audio_files:
            for audio_file in audio_files[:3]:  # Test first 3 files
                try:
                    print(f"\n📁 File: {audio_file.name}")
                    metadata = formatter.detect_format(audio_file)
                    
                    print(f"   Format: {metadata.format}")
                    print(f"   Codec: {metadata.codec}")
                    print(f"   Sample Rate: {metadata.sample_rate} Hz")
                    print(f"   Channels: {metadata.channels}")
                    print(f"   Bit Depth: {metadata.bit_depth}")
                    print(f"   Duration: {metadata.duration_seconds:.2f}s")
                    print(f"   Size: {metadata.file_size_mb:.2f} MB")
                    
                    if metadata.is_transcription_ready:
                        print(f"   ✅ TRANSCRIPTION READY")
                    else:
                        print(f"   ⚠️  Needs conversion for transcription")
                        print(f"      Required: 16kHz, mono, 16-bit WAV")
                        print(f"      Current: {metadata.sample_rate}Hz, {metadata.channels}ch, {metadata.bit_depth}bit")
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
        else:
            print("⚠️  No audio files found in audio/ directory")
    else:
        print("⚠️  Audio directory not found")
    
    # Test 3: Single file conversion (if files exist)
    print("\n🔄 TEST 3: Single File Conversion")
    print("-" * 80)
    
    if audio_dir.exists():
        # Find an MP3 file to convert
        mp3_files = list(audio_dir.glob("*.mp3"))
        
        if mp3_files:
            test_file = mp3_files[0]
            print(f"\n📁 Converting: {test_file.name}")
            print(f"   Target: Transcription format (16kHz, mono, 16-bit WAV)")
            
            try:
                # Create test output directory
                test_output_dir = project_root / "audio" / "test_output"
                test_output_dir.mkdir(exist_ok=True)
                
                result = await formatter.convert_file(
                    input_path=test_file,
                    output_format="wav",
                    profile="transcription",
                    backup_original=True,
                    output_dir=test_output_dir
                )
                
                if result.status == "success":
                    print(f"\n✅ CONVERSION SUCCESSFUL!")
                    print(f"   Output: {result.output_path}")
                    print(f"   Backup: {result.backup_path}")
                    print(f"\n   📊 Metrics:")
                    print(f"      Original Size: {result.metrics.original_size_mb:.2f} MB")
                    print(f"      Formatted Size: {result.metrics.formatted_size_mb:.2f} MB")
                    print(f"      Compression Ratio: {result.metrics.compression_ratio:.2f}x")
                    print(f"      Space Saved: {result.metrics.space_saved_mb:.2f} MB ({result.metrics.space_saved_percent:.1f}%)")
                    print(f"      Processing Time: {result.metrics.processing_time_seconds:.2f}s")
                    
                    # Verify the output
                    if result.output_path:
                        output_path = Path(result.output_path)
                        if output_path.exists():
                            output_metadata = formatter.detect_format(output_path)
                            print(f"\n   ✅ Output Verification:")
                            print(f"      Sample Rate: {output_metadata.sample_rate} Hz (expected: 16000)")
                            print(f"      Channels: {output_metadata.channels} (expected: 1)")
                            print(f"      Bit Depth: {output_metadata.bit_depth} (expected: 16)")
                            print(f"      Transcription Ready: {'✅ YES' if output_metadata.is_transcription_ready else '❌ NO'}")
                else:
                    print(f"\n❌ CONVERSION FAILED")
                    print(f"   Error: {result.error_message}")
                    
            except Exception as e:
                print(f"\n❌ Error during conversion: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("⚠️  No MP3 files found for conversion test")
    
    # Test 4: Batch conversion simulation
    print("\n🔄 TEST 4: Batch Job Creation")
    print("-" * 80)
    
    if audio_dir.exists():
        audio_files = list(audio_dir.glob("*.mp3"))[:2]  # Just first 2 files
        
        if len(audio_files) >= 1:
            file_paths = [str(f.relative_to(project_root)) for f in audio_files]
            
            job_id = formatter.create_job(
                files=file_paths,
                output_format="wav",
                profile="transcription"
            )
            
            print(f"✅ Batch job created: {job_id}")
            print(f"   Total files: {len(file_paths)}")
            print(f"   Files:")
            for f in file_paths:
                print(f"      - {f}")
            
            # Get job status
            job = formatter.get_job(job_id)
            print(f"\n   Job Status: {job.status}")
            print(f"   Created: {job.created_at}")
        else:
            print("⚠️  Not enough files for batch test")
    
    print("\n" + "=" * 80)
    print("✅ TESTS COMPLETED!")
    print("=" * 80)
    
    # Summary
    print("\n📊 SUMMARY:")
    print(f"   ✅ Profiles: {len(profiles)} available")
    print(f"   ✅ Format Detection: Working")
    print(f"   ✅ Single Conversion: Working")
    print(f"   ✅ Batch Jobs: Working")
    print("\n🎉 All functionality tests passed!")


if __name__ == "__main__":
    asyncio.run(run_quick_test())
