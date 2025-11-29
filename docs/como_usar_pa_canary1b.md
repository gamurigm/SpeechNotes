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