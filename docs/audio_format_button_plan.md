# 🎵 Audio Format Button - Functional Specification & Implementation Plan

## 📋 Executive Summary

This document outlines the complete functionality specification for the **Audio Format Button** feature that leverages **FFmpeg** to convert and optimize audio files for transcription and storage in the SpeechNotes application.

---

## 🎯 Feature Objectives

### Primary Goals
1. **Format Conversion**: Convert audio files between different formats (MP3, WAV, M4A, OGG, WebM, etc.)
2. **Optimization for Transcription**: Standardize audio to NVIDIA Riva's requirements (16kHz, mono, 16-bit PCM)
3. **File Size Reduction**: Compress audio files for efficient storage while maintaining quality
4. **Batch Processing**: Allow multiple files to be formatted simultaneously
5. **Quality Control**: Preserve audio quality while optimizing for speech recognition

### Secondary Goals
- Provide progress feedback during conversion
- Generate metadata about the conversion process
- Maintain original file backups
- Support custom format profiles

---

## 🏗️ Architecture Design

### Component Structure

```
backend/
├── services/
│   ├── audio_formatter.py          # Core formatting service (NEW)
│   └── audio_processor.py          # Existing audio processing
├── routers/
│   └── audio_format.py             # REST API endpoints (NEW)
└── tests/
    └── test_audio_formatter.py     # Unit & integration tests (NEW)
```

### Technology Stack
- **FFmpeg** (via pydub): Audio conversion engine
- **FastAPI**: REST API framework
- **WebSocket**: Real-time progress updates
- **Pydantic**: Data validation and models
- **pytest**: Testing framework

---

## ⚙️ Functional Requirements

### FR-1: Audio Format Detection
**Description**: Automatically detect the format of uploaded audio files

**Acceptance Criteria**:
- ✅ Support common formats: MP3, WAV, M4A, OGG, FLAC, WebM, AAC
- ✅ Extract metadata: sample rate, channels, bit depth, duration, codec
- ✅ Handle corrupted or invalid files gracefully
- ✅ Return detailed format information to the user

**API Endpoint**: `GET /api/audio-format/detect`

**Request**:
```json
{
  "file_path": "audio/mi_audio.wav"
}
```

**Response**:
```json
{
  "format": "wav",
  "codec": "pcm_s16le",
  "sample_rate": 44100,
  "channels": 2,
  "bit_depth": 16,
  "duration_seconds": 120.5,
  "file_size_mb": 20.5,
  "is_optimized": false
}
```

---

### FR-2: Single File Conversion
**Description**: Convert a single audio file to a target format

**Acceptance Criteria**:
- ✅ Support multiple output formats: WAV, MP3, OGG, M4A
- ✅ Apply preset profiles: "transcription", "storage", "high_quality"
- ✅ Allow custom parameters: sample_rate, channels, bitrate
- ✅ Create backup of original file
- ✅ Generate conversion report with before/after metrics

**API Endpoint**: `POST /api/audio-format/convert`

**Request**:
```json
{
  "input_path": "audio/mi_audio.wav",
  "output_format": "wav",
  "profile": "transcription",
  "custom_params": {
    "sample_rate": 16000,
    "channels": 1,
    "bit_depth": 16
  },
  "backup_original": true
}
```

**Response**:
```json
{
  "status": "success",
  "job_id": "fmt_20260202_213000",
  "output_path": "audio/mi_audio_formatted.wav",
  "backup_path": "audio/backups/mi_audio.original.wav",
  "metrics": {
    "original_size_mb": 20.5,
    "formatted_size_mb": 5.2,
    "compression_ratio": 3.94,
    "processing_time_seconds": 2.3
  }
}
```

---

### FR-3: Batch File Conversion
**Description**: Convert multiple audio files in a single operation

**Acceptance Criteria**:
- ✅ Accept list of file paths
- ✅ Process files in parallel (with configurable concurrency)
- ✅ Provide WebSocket progress updates
- ✅ Generate individual reports for each file
- ✅ Handle partial failures gracefully

**API Endpoint**: `POST /api/audio-format/batch`

**Request**:
```json
{
  "files": [
    "audio/Gran_RESET.mp3",
    "audio/Gran_RESET.wav",
    "audio/mi_audio.wav"
  ],
  "output_format": "wav",
  "profile": "transcription",
  "max_concurrent": 3
}
```

**Response**:
```json
{
  "job_id": "batch_20260202_213100",
  "total_files": 3,
  "status": "processing",
  "ws_url": "/api/audio-format/ws/batch_20260202_213100"
}
```

**WebSocket Progress Message**:
```json
{
  "type": "progress",
  "job_id": "batch_20260202_213100",
  "current_file": "audio/Gran_RESET.mp3",
  "file_index": 1,
  "total_files": 3,
  "status": "converting",
  "progress_percent": 33.3
}
```

---

### FR-4: Format Presets/Profiles
**Description**: Pre-configured format settings for common use cases

**Profiles**:

#### 1. **Transcription Profile** (Default)
- **Purpose**: Optimize for NVIDIA Riva transcription
- **Settings**:
  - Format: WAV (PCM)
  - Sample Rate: 16000 Hz
  - Channels: 1 (mono)
  - Bit Depth: 16-bit
  - Codec: pcm_s16le

#### 2. **Storage Profile**
- **Purpose**: Minimize file size for archival
- **Settings**:
  - Format: MP3
  - Sample Rate: 22050 Hz
  - Channels: 1 (mono)
  - Bitrate: 64 kbps
  - Codec: libmp3lame

#### 3. **High Quality Profile**
- **Purpose**: Preserve maximum audio quality
- **Settings**:
  - Format: FLAC
  - Sample Rate: 48000 Hz
  - Channels: 2 (stereo)
  - Bit Depth: 24-bit
  - Codec: flac

#### 4. **Custom Profile**
- **Purpose**: User-defined parameters
- **Settings**: User-specified

---

### FR-5: Audio Optimization
**Description**: Apply audio enhancements for better transcription

**Features**:
- 🔊 **Normalization**: Adjust audio levels to optimal range
- 🔇 **Noise Reduction**: Remove background noise (basic)
- 📊 **Dynamic Range Compression**: Even out volume levels
- ⚡ **Silence Trimming**: Remove leading/trailing silence

**API Endpoint**: `POST /api/audio-format/optimize`

**Request**:
```json
{
  "input_path": "audio/mi_audio.wav",
  "optimizations": {
    "normalize": true,
    "remove_silence": true,
    "target_loudness_db": -16.0
  }
}
```

---

### FR-6: Job Status and History
**Description**: Track and query format job status

**API Endpoint**: `GET /api/audio-format/job/{job_id}`

**Response**:
```json
{
  "job_id": "fmt_20260202_213000",
  "status": "completed",
  "created_at": "2026-02-02T21:30:00Z",
  "completed_at": "2026-02-02T21:30:05Z",
  "total_files": 1,
  "successful": 1,
  "failed": 0,
  "results": [
    {
      "input_file": "audio/mi_audio.wav",
      "output_file": "audio/mi_audio_formatted.wav",
      "status": "success",
      "metrics": {...}
    }
  ]
}
```

---

## 🎨 Frontend Integration

### UI Components

#### 1. **Format Button**
- Location: Audio file list / toolbar
- Appearance: Icon button with speaker/wrench symbol
- States: Default, Processing, Success, Error

#### 2. **Format Dialog**
- **Profile Selection**: Dropdown with presets
- **Custom Settings**: Collapsible advanced options
- **File Selection**: Multi-select file list
- **Preview**: Before/after metadata comparison
- **Action Buttons**: "Format", "Cancel"

#### 3. **Progress Indicator**
- Real-time progress bar
- Current file being processed
- Estimated time remaining
- Success/failure count

#### 4. **Results Summary**
- Files processed count
- Total size saved
- Average compression ratio
- Link to formatted files

---

## 🧪 Testing Strategy

### Unit Tests
1. **Format Detection**
   - Test various audio formats
   - Test corrupted files
   - Test unsupported formats

2. **Conversion Logic**
   - Test each preset profile
   - Test custom parameters
   - Test file size reduction
   - Test quality preservation

3. **Error Handling**
   - Test missing files
   - Test insufficient disk space
   - Test invalid parameters

### Integration Tests
1. **End-to-End Conversion**
   - Upload → Detect → Convert → Verify
   - Test with real audio samples

2. **Batch Processing**
   - Test parallel processing
   - Test progress updates
   - Test partial failures

### Performance Tests
1. **Large File Handling**
   - Test files > 100MB
   - Measure processing time
   - Monitor memory usage

2. **Concurrent Jobs**
   - Test multiple simultaneous jobs
   - Verify no resource conflicts

---

## 📊 Success Metrics

### Performance KPIs
- ✅ Conversion time: < 0.5x audio duration
- ✅ File size reduction: 50-75% for transcription profile
- ✅ Quality preservation: > 95% speech recognition accuracy
- ✅ Batch throughput: 10+ files/minute

### Reliability KPIs
- ✅ Success rate: > 99%
- ✅ Error recovery: 100% (no data loss)
- ✅ Uptime: 99.9%

---

## 🚀 Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [ ] Create `AudioFormatterService` class
- [ ] Implement format detection
- [ ] Implement single file conversion
- [ ] Create REST API endpoints
- [ ] Write unit tests

### Phase 2: Batch Processing (Week 2)
- [ ] Implement batch conversion
- [ ] Add WebSocket progress streaming
- [ ] Implement job queue system
- [ ] Add concurrent processing
- [ ] Write integration tests

### Phase 3: Advanced Features (Week 3)
- [ ] Add audio optimization features
- [ ] Implement custom profiles
- [ ] Add metadata extraction
- [ ] Create job history/status API

### Phase 4: Frontend Integration (Week 4)
- [ ] Create format button component
- [ ] Build format dialog UI
- [ ] Implement progress tracking
- [ ] Add results visualization
- [ ] End-to-end testing

---

## 🔒 Security Considerations

1. **File Validation**
   - Validate file types before processing
   - Check file size limits (max 500MB)
   - Scan for malicious content

2. **Path Security**
   - Prevent directory traversal attacks
   - Sanitize file names
   - Use secure temporary directories

3. **Resource Limits**
   - Limit concurrent jobs per user
   - Set processing timeouts
   - Monitor disk space usage

---

## 📝 API Reference Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/audio-format/detect` | POST | Detect audio format and metadata |
| `/api/audio-format/convert` | POST | Convert single audio file |
| `/api/audio-format/batch` | POST | Batch convert multiple files |
| `/api/audio-format/optimize` | POST | Apply audio optimizations |
| `/api/audio-format/job/{job_id}` | GET | Get job status |
| `/api/audio-format/profiles` | GET | List available profiles |
| `/api/audio-format/ws/{job_id}` | WebSocket | Real-time progress updates |

---

## 🎓 Example Use Cases

### Use Case 1: Student Recording Lecture
**Scenario**: Student records 90-minute lecture in M4A on phone

**Flow**:
1. Upload M4A file (200MB)
2. Click "Format for Transcription"
3. System converts to 16kHz mono WAV (45MB)
4. Automatic transcription begins
5. Student receives formatted notes

**Benefit**: 77% size reduction, optimized for transcription accuracy

---

### Use Case 2: Batch Processing Old Recordings
**Scenario**: User has 50 old MP3 recordings to transcribe

**Flow**:
1. Select all 50 files
2. Choose "Batch Format"
3. Select "Transcription" profile
4. Monitor progress via WebSocket
5. Review results summary
6. Batch transcribe all files

**Benefit**: Automated processing, saves hours of manual work

---

### Use Case 3: Archive Storage
**Scenario**: User wants to archive old transcriptions

**Flow**:
1. Select completed sessions
2. Choose "Storage" profile (MP3 64kbps)
3. Convert for long-term storage
4. Free up disk space

**Benefit**: 90% size reduction while preserving intelligibility

---

## 🛠️ Technical Implementation Details

### Core Service Class Structure

```python
class AudioFormatterService:
    """
    Core service for audio format conversion and optimization
    """
    
    def __init__(self, temp_dir: Path = None):
        self.temp_dir = temp_dir or Path(tempfile.gettempdir()) / "audio_formatting"
        self.jobs: Dict[str, FormatJob] = {}
        
    async def detect_format(self, file_path: Path) -> AudioMetadata:
        """Detect audio format and extract metadata"""
        
    async def convert_file(
        self, 
        input_path: Path,
        output_format: str,
        profile: str = "transcription",
        custom_params: Dict = None
    ) -> ConversionResult:
        """Convert single audio file"""
        
    async def batch_convert(
        self,
        files: List[Path],
        output_format: str,
        profile: str = "transcription",
        max_concurrent: int = 3
    ) -> AsyncIterator[BatchProgress]:
        """Convert multiple files with progress updates"""
        
    async def optimize_audio(
        self,
        input_path: Path,
        optimizations: OptimizationSettings
    ) -> ConversionResult:
        """Apply audio optimizations"""
```

### Data Models

```python
class AudioMetadata(BaseModel):
    format: str
    codec: str
    sample_rate: int
    channels: int
    bit_depth: int
    duration_seconds: float
    file_size_mb: float
    is_optimized: bool

class ConversionResult(BaseModel):
    status: str
    input_path: str
    output_path: str
    backup_path: Optional[str]
    metrics: ConversionMetrics

class ConversionMetrics(BaseModel):
    original_size_mb: float
    formatted_size_mb: float
    compression_ratio: float
    processing_time_seconds: float
```

---

## 📚 References

- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [pydub Documentation](https://github.com/jiaaro/pydub)
- [NVIDIA Riva Audio Requirements](https://docs.nvidia.com/deeplearning/riva/user-guide/docs/asr/asr-overview.html)
- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)

---

## ✅ Acceptance Criteria for MVP

The Audio Format Button feature is considered complete when:

1. ✅ Users can convert audio files through the UI
2. ✅ At least 3 format profiles are available
3. ✅ Batch processing works for up to 50 files
4. ✅ Real-time progress updates are visible
5. ✅ Conversion preserves audio quality for transcription
6. ✅ All unit and integration tests pass
7. ✅ API documentation is complete
8. ✅ Frontend integration is seamless

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-02  
**Author**: SpeechNotes Development Team  
**Status**: ✅ Ready for Implementation
