# Architecture & Design Patterns

This document details the software architecture and design patterns implemented in **SpeechNotes**. The system follows a modular, layered architecture emphasizing **SOLID principles** and clear separation of concerns.

## 1. High-Level Architecture

The application is split into two main parts:
- **Frontend (Next.js)**: Handles UI, Audio Capture (Web Audio API), and visualization.
- **Backend (FastAPI)**: Handles Transcription, VAD, Persistence (MongoDB), and AI processing (NVIDIA Riva).

Communication happens via:
- **REST API**: For CRUD operations on transcriptions.
- **Socket.IO**: For real-time audio streaming and transcription updates.

---

## 2. Design Patterns Implemented

### Backend Patterns

#### **1. Service Layer Pattern (Architecture)**
- **Purpose**: Encapsulate business logic and separate it from HTTP/Socket transport layers.
- **Implementation**:
  - `TranscriptionService` (`backend/services/transcription_service.py`) handles all transcription business rules.
  - `AudioService` handles audio conversions.
  - `VADService` handles voice activity detection.
- **Benefit**: Routers become thin controllers (SRP). Services can be tested independently.

#### **2. Dependency Injection (DIP)**
- **Purpose**: Decouple components from their dependencies.
- **Implementation**:
  - `FastAPI.Depends` injects `TranscriptionService` into routers.
  - `TranscriptionService` injects `TranscriptionRepository` and `ContentRenderer`.
- **Benefit**: Easier testing (can inject mocks) and flexible configuration.

#### **3. Singleton Pattern (Creational)**
- **Purpose**: Ensure a class has only one instance (e.g., database connection).
- **Implementation**:
  - `MongoManager` (`src/database/mongo_manager.py`) strictly ensures one connection pool.
  - `ConfigManager` (`src/core/config.py`) manages global configuration.

#### **4. Adapter Pattern (Structural)**
- **Purpose**: Allow incompatible interfaces to work together.
- **Implementation**:
  - `AudioService` (`backend/services/audio_service.py`) adapts various audio inputs (WebM, raw bytes) into the standardized PCM format required by the transcriber.
  - **Adapters**: `WebMAudioAdapter`, `PCMPassthroughAdapter` implement the `AudioProcessorPort` interface.

#### **5. Facade Pattern (Structural)**
- **Purpose**: Provide a simplified interface to a complex subsystem.
- **Implementation**:
  - `SocketHandler` (`backend/services/socket_handler.py`) acts as a Facade for the entire real-time pipeline (Audio -> VAD -> Transcriber -> Buffer -> Client).
  - The client only interacts with simple events (`start_recording`, `audio_chunk`), unaware of the complexity behind.

#### **6. Strategy Pattern (Behavioral)**
- **Purpose**: Define a family of algorithms and make them interchangeable.
- **Implementation**:
  - **VAD Strategies**: `VADStrategy` interface allows swapping VAD algorithms (e.g., `ThresholdVADStrategy`).
  - **Content Rendering**: `ContentRenderer` selects between `FormattedContentStrategy`, `SegmentDocumentStrategy`, etc.
  - **Formatters**: `FormatterFactory` creates `MarkdownFormatter`, `DocxFormatter`, etc.

#### **7. Repository Pattern (Architecture)**
- **Purpose**: Abstraction of the data layer.
- **Implementation**:
  - `TranscriptionRepository` (`backend/repositories/transcription_repository.py`) handles all MongoDB interactions.
  - The rest of the app usually interfaces with the Repository, not the DB driver directly.

#### **8. Observer Pattern (Behavioral)**
- **Purpose**: Define a subscription mechanism to notify multiple objects about events.
- **Implementation**:
  - **Socket.IO Events**: The `register_socket_events` function sets up observers (`sio.on(...)`) that react to client events.
  - **Frontend State**: React hooks (`useRecording`) observe socket events to update the UI.
  - **AudioGraph**: Uses a callback/observer (`onAudioData`) to notify when pcm data is ready.

---

### Frontend Patterns

#### **1. Builder / Factory Pattern**
- **Purpose**: Construct complex objects step-by-step or based on type.
- **Implementation**:
  - `AudioGraph` (`web/services/AudioGraph.ts`): Builds the Web Audio API graph (Source -> Gain -> Analyser -> Processor).
  - `createGraph()` method acts as a factory for the nodes.

#### **2. Singleton / Facade Pattern**
- **Purpose**: Global access point to a service.
- **Implementation**:
  - `ApiClient` (`web/services/ApiClient.ts`): Singleton instance that provides a simple API for backend calls, hiding `fetch` complexity and headers logic.
  - Usage: `ApiClient.getInstance().getLatestTranscription()`.

---

## 3. SOLID Principles Check

- **SRP (Single Responsibility Principle)**:
  - **Refactored**: `socket_handler.py` was formerly a "God Object". Now it delegates audio to `AudioService`, VAD to `VADService`, and persistence to `TranscriptionRepository`.
  - **Frontend**: `useRecording` hook delegated audio graph construction to `AudioGraph` service.

- **OCP (Open/Closed Principle)**:
  - **VAD**: New VAD algorithms can be added by implementing `VADStrategy` without changing `socket_handler.py`.
  - **Formatters**: New output formats can be added to `src/transcription/formatters.py` without changing the usage code.

- **LSP (Liskov Substitution Principle)**:
  - `RivaLiveFactory` and `LocalBatchFactory` can be substituted wherever `TranscriptionEnvironmentFactory` is expected.

- **ISP (Interface Segregation Principle)**:
  - `AudioProcessorPort` exposes only `to_pcm`.
  - Service methods are specific to their domain.

- **DIP (Dependency Inversion Principle)**:
  - Backend Routers depend on `TranscriptionService` (injected), not concrete Repositories.
  - `SocketHandler` depends on `VADStrategy` (abstraction), not `ThresholdVADStrategy` (concretion) directly (it's injected/configured).

---

## 4. Directory Structure (Refactored)

```
.
├── backend/
│   ├── services/           # Business Logic Layer
│   │   ├── audio_service.py          # Adapter Pattern
│   │   ├── vad_service.py            # Strategy Pattern
│   │   ├── transcription_service.py  # Service Layer
│   │   └── socket_handler.py         # Facade (Refactored)
│   ├── routers/            # Controller Layer
│   │   └── transcriptions.py         # Uses Dependency Injection
│   └── repositories/       # Data Access Layer
│       └── transcription_repository.py
│
├── web/
│   ├── services/           # Frontend Services
│   │   ├── AudioGraph.ts             # Builder Pattern
│   │   └── ApiClient.ts              # Singleton/Facade
│   └── hooks/
│       └── useRecording.ts           # Uses AudioGraph
```
