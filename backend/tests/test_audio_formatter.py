"""
Test Suite for Audio Formatter Service
Tests format detection, conversion, batch processing, and profiles
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from backend.services.audio_formatter import (
    AudioFormatterService,
    AudioMetadata,
    ConversionResult,
    FormatProfile,
    FormatJob
)


# ==================== Fixtures ====================

@pytest.fixture
def project_root():
    """Get the project root directory"""
    # Adjust this path based on your actual project structure
    test_file_path = Path(__file__).resolve()
    return test_file_path.parent.parent


@pytest.fixture
def audio_formatter(project_root):
    """Create AudioFormatterService instance"""
    return AudioFormatterService(project_root=project_root)


@pytest.fixture
def sample_audio_files(project_root):
    """Get paths to sample audio files"""
    audio_dir = project_root / "audio"
    
    # Assuming these files exist from the earlier directory listing
    return {
        "mp3": audio_dir / "Gran_RESET.mp3",
        "wav": audio_dir / "Gran_RESET.wav",
        "large_wav": audio_dir / "mi_audio.wav"
    }


@pytest.fixture
def temp_output_dir():
    """Create temporary directory for test outputs"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup after tests
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


# ==================== Test Format Detection ====================

class TestFormatDetection:
    """Test audio format detection capabilities"""
    
    def test_detect_wav_format(self, audio_formatter, sample_audio_files):
        """Test detection of WAV file format"""
        if not sample_audio_files["wav"].exists():
            pytest.skip("Sample WAV file not found")
        
        metadata = audio_formatter.detect_format(sample_audio_files["wav"])
        
        assert isinstance(metadata, AudioMetadata)
        assert metadata.format is not None
        assert metadata.sample_rate > 0
        assert metadata.channels > 0
        assert metadata.bit_depth > 0
        assert metadata.duration_seconds > 0
        assert metadata.file_size_mb > 0
        
        print(f"\n✅ WAV Detection Test Passed:")
        print(f"   Format: {metadata.format}")
        print(f"   Sample Rate: {metadata.sample_rate} Hz")
        print(f"   Channels: {metadata.channels}")
        print(f"   Bit Depth: {metadata.bit_depth}")
        print(f"   Duration: {metadata.duration_seconds:.2f}s")
        print(f"   Size: {metadata.file_size_mb:.2f} MB")
    
    def test_detect_mp3_format(self, audio_formatter, sample_audio_files):
        """Test detection of MP3 file format"""
        if not sample_audio_files["mp3"].exists():
            pytest.skip("Sample MP3 file not found")
        
        metadata = audio_formatter.detect_format(sample_audio_files["mp3"])
        
        assert isinstance(metadata, AudioMetadata)
        assert metadata.format is not None
        assert metadata.sample_rate > 0
        
        print(f"\n✅ MP3 Detection Test Passed:")
        print(f"   Format: {metadata.format}")
        print(f"   Codec: {metadata.codec}")
        print(f"   Sample Rate: {metadata.sample_rate} Hz")
    
    def test_transcription_ready_check(self, audio_formatter, sample_audio_files):
        """Test if audio is optimized for transcription"""
        if not sample_audio_files["wav"].exists():
            pytest.skip("Sample WAV file not found")
        
        metadata = audio_formatter.detect_format(sample_audio_files["wav"])
        
        # Check if it meets transcription requirements
        is_ready = metadata.is_transcription_ready
        
        print(f"\n✅ Transcription Ready Check:")
        print(f"   Sample Rate: {metadata.sample_rate} Hz (required: 16000)")
        print(f"   Channels: {metadata.channels} (required: 1)")
        print(f"   Bit Depth: {metadata.bit_depth} (required: 16)")
        print(f"   Transcription Ready: {is_ready}")
        
        assert isinstance(is_ready, bool)


# ==================== Test Single File Conversion ====================

class TestSingleFileConversion:
    """Test single file conversion with different profiles"""
    
    @pytest.mark.asyncio
    async def test_convert_to_transcription_format(
        self, 
        audio_formatter, 
        sample_audio_files, 
        temp_output_dir
    ):
        """Test conversion to transcription-optimized format"""
        if not sample_audio_files["mp3"].exists():
            pytest.skip("Sample MP3 file not found")
        
        result = await audio_formatter.convert_file(
            input_path=sample_audio_files["mp3"],
            output_format="wav",
            profile="transcription",
            backup_original=True,
            output_dir=temp_output_dir
        )
        
        assert result.status == "success"
        assert result.output_path is not None
        assert Path(result.output_path).exists()
        assert result.metrics is not None
        assert result.metrics.compression_ratio > 0
        
        # Verify the output is transcription-ready
        output_path = Path(result.output_path)
        output_metadata = audio_formatter.detect_format(output_path)
        
        assert output_metadata.sample_rate == 16000
        assert output_metadata.channels == 1
        assert output_metadata.bit_depth == 16
        assert output_metadata.is_transcription_ready
        
        print(f"\n✅ Transcription Conversion Test Passed:")
        print(f"   Input: {result.input_path}")
        print(f"   Output: {result.output_path}")
        print(f"   Original Size: {result.metrics.original_size_mb:.2f} MB")
        print(f"   Formatted Size: {result.metrics.formatted_size_mb:.2f} MB")
        print(f"   Compression Ratio: {result.metrics.compression_ratio:.2f}x")
        print(f"   Space Saved: {result.metrics.space_saved_mb:.2f} MB ({result.metrics.space_saved_percent:.1f}%)")
        print(f"   Processing Time: {result.metrics.processing_time_seconds:.2f}s")
        print(f"   Transcription Ready: ✅")
    
    @pytest.mark.asyncio
    async def test_convert_to_storage_format(
        self, 
        audio_formatter, 
        sample_audio_files, 
        temp_output_dir
    ):
        """Test conversion to storage-optimized format (compressed MP3)"""
        if not sample_audio_files["wav"].exists():
            pytest.skip("Sample WAV file not found")
        
        result = await audio_formatter.convert_file(
            input_path=sample_audio_files["wav"],
            output_format="mp3",
            profile="storage",
            backup_original=False,
            output_dir=temp_output_dir
        )
        
        assert result.status == "success"
        assert result.output_path is not None
        assert Path(result.output_path).exists()
        assert result.metrics.formatted_size_mb < result.metrics.original_size_mb
        
        print(f"\n✅ Storage Conversion Test Passed:")
        print(f"   Space Saved: {result.metrics.space_saved_mb:.2f} MB ({result.metrics.space_saved_percent:.1f}%)")
    
    @pytest.mark.asyncio
    async def test_backup_creation(
        self, 
        audio_formatter, 
        sample_audio_files, 
        temp_output_dir
    ):
        """Test that backup files are created correctly"""
        if not sample_audio_files["mp3"].exists():
            pytest.skip("Sample MP3 file not found")
        
        result = await audio_formatter.convert_file(
            input_path=sample_audio_files["mp3"],
            output_format="wav",
            profile="transcription",
            backup_original=True,
            output_dir=temp_output_dir
        )
        
        assert result.status == "success"
        assert result.backup_path is not None
        assert Path(result.backup_path).exists()
        
        print(f"\n✅ Backup Creation Test Passed:")
        print(f"   Backup Path: {result.backup_path}")


# ==================== Test Batch Conversion ====================

class TestBatchConversion:
    """Test batch file conversion with progress tracking"""
    
    @pytest.mark.asyncio
    async def test_batch_convert_multiple_files(
        self, 
        audio_formatter, 
        sample_audio_files
    ):
        """Test batch conversion of multiple files"""
        # Filter only existing files
        files_to_convert = [
            str(path.relative_to(audio_formatter.project_root))
            for path in sample_audio_files.values()
            if path.exists()
        ]
        
        if len(files_to_convert) < 2:
            pytest.skip("Not enough sample files for batch test")
        
        # Create batch job
        job_id = audio_formatter.create_job(
            files=files_to_convert,
            output_format="wav",
            profile="transcription"
        )
        
        assert job_id is not None
        
        # Track progress
        progress_updates = []
        
        async for progress in audio_formatter.batch_convert(job_id, max_concurrent=2):
            progress_updates.append(progress)
            print(f"\n   📊 Progress: {progress.progress_percent:.1f}% - {progress.current_file}")
            
            if progress.current_result:
                print(f"      Status: {progress.current_result.status}")
                if progress.current_result.metrics:
                    print(f"      Saved: {progress.current_result.metrics.space_saved_mb:.2f} MB")
        
        # Verify job completion
        job = audio_formatter.get_job(job_id)
        
        assert job is not None
        assert job.status == "completed"
        assert job.total_files == len(files_to_convert)
        assert job.successful + job.failed == job.total_files
        assert len(progress_updates) >= job.total_files
        
        print(f"\n✅ Batch Conversion Test Passed:")
        print(f"   Total Files: {job.total_files}")
        print(f"   Successful: {job.successful}")
        print(f"   Failed: {job.failed}")
        print(f"   Progress Updates: {len(progress_updates)}")
    
    @pytest.mark.asyncio
    async def test_job_status_tracking(self, audio_formatter, sample_audio_files):
        """Test job status tracking and retrieval"""
        files_to_convert = [
            str(path.relative_to(audio_formatter.project_root))
            for path in sample_audio_files.values()
            if path.exists()
        ][:1]  # Just use one file for quick test
        
        if not files_to_convert:
            pytest.skip("No sample files available")
        
        # Create job
        job_id = audio_formatter.create_job(
            files=files_to_convert,
            output_format="wav",
            profile="transcription"
        )
        
        # Check initial status
        job = audio_formatter.get_job(job_id)
        assert job.status == "pending"
        
        # Run job
        async for _ in audio_formatter.batch_convert(job_id):
            pass
        
        # Check final status
        job = audio_formatter.get_job(job_id)
        assert job.status == "completed"
        assert job.completed_at is not None
        
        print(f"\n✅ Job Status Tracking Test Passed:")
        print(f"   Job ID: {job_id}")
        print(f"   Final Status: {job.status}")


# ==================== Test Profiles ====================

class TestConversionProfiles:
    """Test different conversion profiles"""
    
    def test_get_available_profiles(self, audio_formatter):
        """Test retrieving available conversion profiles"""
        profiles = audio_formatter.get_available_profiles()
        
        assert len(profiles) >= 3  # At least transcription, storage, high_quality
        assert any(p["name"] == "transcription" for p in profiles)
        assert any(p["name"] == "storage" for p in profiles)
        assert any(p["name"] == "high_quality" for p in profiles)
        
        print(f"\n✅ Available Profiles Test Passed:")
        for profile in profiles:
            print(f"\n   Profile: {profile['name']}")
            print(f"   Description: {profile['description']}")
            print(f"   Settings: {profile['settings']}")
    
    @pytest.mark.asyncio
    async def test_transcription_profile_settings(
        self, 
        audio_formatter, 
        sample_audio_files, 
        temp_output_dir
    ):
        """Test that transcription profile produces correct settings"""
        if not sample_audio_files["mp3"].exists():
            pytest.skip("Sample MP3 file not found")
        
        result = await audio_formatter.convert_file(
            input_path=sample_audio_files["mp3"],
            output_format="wav",
            profile="transcription",
            output_dir=temp_output_dir
        )
        
        # Verify output meets transcription requirements
        output_metadata = audio_formatter.detect_format(Path(result.output_path))
        
        assert output_metadata.sample_rate == 16000
        assert output_metadata.channels == 1
        assert output_metadata.bit_depth == 16
        
        print(f"\n✅ Transcription Profile Settings Test Passed")


# ==================== Integration Tests ====================

class TestIntegration:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_conversion_pipeline(
        self, 
        audio_formatter, 
        sample_audio_files, 
        temp_output_dir
    ):
        """Test complete conversion pipeline: detect → convert → verify"""
        if not sample_audio_files["mp3"].exists():
            pytest.skip("Sample MP3 file not found")
        
        input_file = sample_audio_files["mp3"]
        
        # Step 1: Detect format
        print(f"\n🔍 Step 1: Detecting format...")
        initial_metadata = audio_formatter.detect_format(input_file)
        print(f"   Initial format: {initial_metadata.format}")
        print(f"   Transcription ready: {initial_metadata.is_transcription_ready}")
        
        # Step 2: Convert to transcription format
        print(f"\n🔄 Step 2: Converting to transcription format...")
        conversion_result = await audio_formatter.convert_file(
            input_path=input_file,
            output_format="wav",
            profile="transcription",
            backup_original=True,
            output_dir=temp_output_dir
        )
        
        assert conversion_result.status == "success"
        print(f"   Conversion: ✅")
        
        # Step 3: Verify output format
        print(f"\n✅ Step 3: Verifying output...")
        output_metadata = audio_formatter.detect_format(Path(conversion_result.output_path))
        
        assert output_metadata.is_transcription_ready
        print(f"   Output transcription ready: ✅")
        
        # Step 4: Verify backup
        assert conversion_result.backup_path is not None
        assert Path(conversion_result.backup_path).exists()
        print(f"   Backup created: ✅")
        
        print(f"\n✅ Full Pipeline Test Passed:")
        print(f"   Original: {initial_metadata.file_size_mb:.2f} MB")
        print(f"   Formatted: {output_metadata.file_size_mb:.2f} MB")
        print(f"   Saved: {conversion_result.metrics.space_saved_mb:.2f} MB")
        print(f"   Compression: {conversion_result.metrics.compression_ratio:.2f}x")


# ==================== Performance Tests ====================

class TestPerformance:
    """Test performance and resource usage"""
    
    @pytest.mark.asyncio
    async def test_large_file_conversion(
        self, 
        audio_formatter, 
        sample_audio_files, 
        temp_output_dir
    ):
        """Test conversion of large audio file"""
        if not sample_audio_files["large_wav"].exists():
            pytest.skip("Large sample file not found")
        
        start_time = datetime.now()
        
        result = await audio_formatter.convert_file(
            input_path=sample_audio_files["large_wav"],
            output_format="wav",
            profile="transcription",
            output_dir=temp_output_dir
        )
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        assert result.status == "success"
        
        # Get audio duration
        metadata = audio_formatter.detect_format(sample_audio_files["large_wav"])
        processing_speed = metadata.duration_seconds / total_time
        
        print(f"\n✅ Large File Performance Test:")
        print(f"   File Size: {metadata.file_size_mb:.2f} MB")
        print(f"   Audio Duration: {metadata.duration_seconds:.2f}s")
        print(f"   Processing Time: {total_time:.2f}s")
        print(f"   Speed: {processing_speed:.2f}x realtime")
        
        # Assert processing is faster than realtime (ideally)
        # This might fail on slow systems, so just log it
        if processing_speed > 1.0:
            print(f"   ⚡ Faster than realtime!")


# ==================== Main Test Runner ====================

if __name__ == "__main__":
    """Run tests with detailed output"""
    pytest.main([
        __file__,
        "-v",           # Verbose output
        "-s",           # Show print statements
        "--tb=short",   # Short traceback format
        "--color=yes"   # Colored output
    ])
