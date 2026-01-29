1.
stall SDK
uv
pip
uv add logfire
Copy
2. Authenticate your local environment
uv run logfire auth
Copy
Upon successful authentication, user credentials are stored in ~/.logfire/default.toml

3. Set your Logfire project
From the working directory where you will run your application, use the CLI to set the Logfire project:

uv run logfire projects use speechnotes
Copy
Creates a .logfire/ directory and stores your token locally—no environment variable needed.

4. Instrument your code
Try these examples to see data appear in the Live view. See the 
onboarding checklist
 to continue instrumenting your code.

Hello World
Pydantic AI
FastAPI

Show write token in code
uv
pip
uv add logfire 'pydantic_ai_slim[openai]'
Copy
from pydantic_ai import Agent
import logfire

logfire.configure()
logfire.instrument_pydantic_ai()

agent = Agent('openai:gpt-4o')

result = await agent.run(
    'How does pyodide let you run Python in the browser? (short answer please)'
)

print(f'output: {result.output}')


logfiretoken
pylf_v1_us_tkhT4ngKdxtQMQx8k0cR5GkR0Y4bpMkzTpDr47y6g0kv
***



2.

quiero usar cancary pero no quitar wisper sino tener los dos 

vamos primero aprobar quien es mejor reconociendo el lenguaje y sobre todo la salida de texto de la api usa esto:
Getting Started
Riva uses gRPC APIs. Instructions below demonstrate usage of canary-1b-asr model using Python gRPC client.

Prerequisites
You will need a system with Git and Python 3+ installed.

Install Riva Python Client
Bash

Copy
pip install nvidia-riva-client
Download Python Client
Download Python client code by cloning Python Client Repository.

Bash

Copy
git clone https://github.com/nvidia-riva/python-clients.git
Run Python Client
Make sure you have a speech file in Mono, 16-bit audio in WAV, OPUS and FLAC formats. If you have generated the API key, it will be auto-populated in the command. Open a command terminal and execute below command to transcribe audio. If you know the source language, it is recommended to pass source_language in custom configuration parameter.

Below command demonstrates transcription of English audio file.

Bash

Copy
python python-clients/scripts/asr/transcribe_file_offline.py \
    --server grpc.nvcf.nvidia.com:443 --use-ssl \
    --metadata function-id "b0e8b4a5-217c-40b7-9b96-17d84e666317" \
    --metadata "authorization" "Bearer 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" \
    --language-code en-US \
    --input-file <path_to_audio_file>
Below command demonstrates translation from English audio to Hindi.

Bash

Copy
python python-clients/scripts/asr/transcribe_file_offline.py \
    --server grpc.nvcf.nvidia.com:443 --use-ssl \
    --metadata function-id "b0e8b4a5-217c-40b7-9b96-17d84e666317" \
    --metadata "authorization" "Bearer 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" \
    --language-code en-US \
    --custom-configuration "target_language:hi-IN,task:translate" \
    --input-file <path_to_audio_file>
One can transcribe and translate supported languages by changing the source language via --language-code and target language via target_language parameter.

Support for gRPC clients in other programming languages
Riva uses gRPC APIs. Proto files can be downloaded from Riva gRPC Proto files and compiled to target language using Protoc compiler. Example Riva clients in C++ and Python languages are provided below.