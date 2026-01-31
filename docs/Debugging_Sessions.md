# Debugging Sessions Index

This document tracks all debugging investigations and their resolutions. Each entry links to a detailed debugging document.

## Active Issues

None

## Resolved Issues

### 2026-01-15: Riva Connection Timeout Error

**File**: [Debugging_Riva_Connection_Timeout.md](Debugging_Riva_Connection_Timeout.md)

**Summary**: Real-time transcription crashed with gRPC timeout errors during audio transcription. 

**Root Cause**: Missing gRPC channel configuration and no retry logic for network failures.

**Solution**: 
- Added gRPC channel options with keepalive and timeout settings
- Implemented automatic retry with exponential backoff
- Created diagnostic tool (`test_riva_connection.py`)

**Status**: ✅ Resolved

---

## How to Use This Document

1. **Before starting debugging**: Check if the issue has been investigated before
2. **During debugging**: Document findings in real-time
3. **After resolution**: Create detailed file named `Debugging_[description].md`
4. **Update this index**: Add entry with link to detailed document
