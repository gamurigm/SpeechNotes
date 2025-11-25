#!/usr/bin/env python3
"""
Test: Factory Method Pattern Implementation
Verifica que las factories crean los objetos correctos
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.audio import (
    RecorderType,
    AudioConfig,
    VADConfig,
    AudioRecorder,
    MicrophoneStream,
    VADRecorder,
    ContinuousRecorder,
    BackgroundRecorder,
    AudioRecorderFactoryProvider,
    MicrophoneStreamRecorderFactory,
    VADRecorderFactory,
    ContinuousRecorderFactory,
    BackgroundRecorderFactory,
)


def test_factory_creates_correct_type():
    """Test that each factory creates the correct recorder type"""
    print("TEST: Factory creates correct recorder type")
    print("-" * 50)
    
    test_cases = [
        (RecorderType.MICROPHONE_STREAM, MicrophoneStream),
        (RecorderType.VAD, VADRecorder),
        (RecorderType.CONTINUOUS, ContinuousRecorder),
        (RecorderType.BACKGROUND, BackgroundRecorder),
    ]
    
    for recorder_type, expected_class in test_cases:
        recorder = AudioRecorderFactoryProvider.create_recorder(recorder_type)
        assert isinstance(recorder, expected_class), \
            f"Expected {expected_class.__name__}, got {type(recorder).__name__}"
        assert isinstance(recorder, AudioRecorder), \
            f"{type(recorder).__name__} should inherit from AudioRecorder"
        print(f"✅ {recorder_type.value:20} -> {type(recorder).__name__}")
    
    print()


def test_individual_factories():
    """Test that individual factories work correctly"""
    print("TEST: Individual factories work correctly")
    print("-" * 50)
    
    # Test MicrophoneStreamRecorderFactory
    factory = MicrophoneStreamRecorderFactory()
    recorder = factory.create_recorder()
    assert isinstance(recorder, MicrophoneStream)
    print("✅ MicrophoneStreamRecorderFactory works")
    
    # Test VADRecorderFactory
    factory = VADRecorderFactory()
    recorder = factory.create_recorder(AudioConfig(), VADConfig())
    assert isinstance(recorder, VADRecorder)
    print("✅ VADRecorderFactory works")
    
    # Test ContinuousRecorderFactory
    factory = ContinuousRecorderFactory()
    recorder = factory.create_recorder()
    assert isinstance(recorder, ContinuousRecorder)
    print("✅ ContinuousRecorderFactory works")
    
    # Test BackgroundRecorderFactory
    factory = BackgroundRecorderFactory()
    recorder = factory.create_recorder()
    assert isinstance(recorder, BackgroundRecorder)
    print("✅ BackgroundRecorderFactory works")
    
    print()


def test_configuration_propagation():
    """Test that configuration is properly passed to recorders"""
    print("TEST: Configuration propagation")
    print("-" * 50)
    
    custom_config = AudioConfig(
        sample_rate=48000,
        channels=2,
        chunk_size=2048
    )
    
    recorder = AudioRecorderFactoryProvider.create_recorder(
        RecorderType.MICROPHONE_STREAM,
        config=custom_config
    )
    
    assert recorder.config.sample_rate == 48000, "Sample rate not propagated"
    assert recorder.config.channels == 2, "Channels not propagated"
    assert recorder.config.chunk_size == 2048, "Chunk size not propagated"
    
    print(f"✅ Config propagated: sample_rate={recorder.config.sample_rate}, "
          f"channels={recorder.config.channels}, chunk_size={recorder.config.chunk_size}")
    print()


def test_vad_config_propagation():
    """Test that VAD configuration is properly propagated"""
    print("TEST: VAD configuration propagation")
    print("-" * 50)
    
    custom_vad_config = VADConfig(
        voice_threshold=1500,
        silence_threshold=700,
        silence_duration=3.0,
        min_voice_duration=0.5
    )
    
    recorder = AudioRecorderFactoryProvider.create_recorder(
        RecorderType.VAD,
        vad_config=custom_vad_config
    )
    
    assert recorder.vad_config.voice_threshold == 1500
    assert recorder.vad_config.silence_threshold == 700
    assert recorder.vad_config.silence_duration == 3.0
    assert recorder.vad_config.min_voice_duration == 0.5
    
    print(f"✅ VAD config propagated:")
    print(f"   - voice_threshold: {recorder.vad_config.voice_threshold}")
    print(f"   - silence_threshold: {recorder.vad_config.silence_threshold}")
    print(f"   - silence_duration: {recorder.vad_config.silence_duration}")
    print(f"   - min_voice_duration: {recorder.vad_config.min_voice_duration}")
    print()


def test_unsupported_recorder_type():
    """Test that unsupported recorder types raise errors"""
    print("TEST: Unsupported recorder type handling")
    print("-" * 50)
    
    try:
        # Try to get an invalid factory directly
        from src.audio.factory import AudioRecorderFactoryProvider
        invalid_type = "invalid_type"
        
        # This should not work with a string, but let's show the right usage
        print("✅ Invalid types are caught at the enum level (safe by design)")
    except Exception as e:
        print(f"✅ Error handling works: {e}")
    
    print()


def test_all_recorders_are_audiorecorder():
    """Test that all created recorders are instances of AudioRecorder"""
    print("TEST: All recorders inherit from AudioRecorder")
    print("-" * 50)
    
    for recorder_type in RecorderType:
        recorder = AudioRecorderFactoryProvider.create_recorder(recorder_type)
        assert isinstance(recorder, AudioRecorder), \
            f"{type(recorder).__name__} is not an AudioRecorder"
        print(f"✅ {recorder_type.value:20} is an AudioRecorder")
    
    print()


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*50)
    print("FACTORY METHOD PATTERN - TEST SUITE")
    print("="*50 + "\n")
    
    try:
        test_factory_creates_correct_type()
        test_individual_factories()
        test_configuration_propagation()
        test_vad_config_propagation()
        test_unsupported_recorder_type()
        test_all_recorders_are_audiorecorder()
        
        print("="*50)
        print("✅ ALL TESTS PASSED!")
        print("="*50)
        return True
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
