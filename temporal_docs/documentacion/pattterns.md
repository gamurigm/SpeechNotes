Implementation Plan - Design Patterns
This plan outlines the implementation of Singleton, Abstract Method, and Abstract Factory patterns to improve the architecture of the SpeechNotes application.

Goal Description
Refactor the existing codebase to strictly adhere to the following design patterns:

Singleton: For 
ConfigManager
 to ensure a single point of configuration.
Abstract Method (Interface/Template): For 
Transcriber
 to define a common interface for different transcription backends.
Abstract Factory: For creating families of related objects (Transcriber, Recorder, Formatter) to support different environments (e.g., Riva, Local, Cloud).
User Review Required
IMPORTANT

This refactoring will modify core instantiation logic. Existing scripts using 
ConfigManager
 or 
RivaTranscriber
 directly may need to be updated to use the new Factory or Singleton accessors.

Proposed Changes
Core Component (src/core)
[MODIFY] 
config.py
Implement Singleton pattern for ConfigManager.
Use __new__ to ensure only one instance exists.
Add a class method get_instance() for global access.
[MODIFY] 
riva_client.py
Make RivaTranscriber inherit from the new Transcriber abstract base class.
Ensure it implements all abstract methods.
[NEW] 
factory.py
Define Abstract Factory TranscriptionEnvironmentFactory.
create_transcriber()
create_recorder()
create_formatter()
Implement RivaEnvironmentFactory.
Transcription Component (src/transcription)
[NEW] 
transcriber.py
Define Abstract Method (Interface) Transcriber.
Abstract methods: transcribe(audio_data, language), stream_transcribe(audio_stream, language).
[MODIFY] 
service.py
Update type hints to use abstract Transcriber instead of concrete RivaTranscriber.
Verification Plan
Automated Tests
Create a new test script tests/test_patterns.py (or similar) to verify:
ConfigManager returns the same instance (Singleton).
RivaEnvironmentFactory creates the correct family of objects.
RivaTranscriber implements the Transcriber interface.
Manual Verification
Run the application using the new factory to ensure transcription still works.
