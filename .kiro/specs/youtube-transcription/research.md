# Research & Design Decisions

---
**Purpose**: Capture discovery findings, architectural investigations, and rationale that inform the technical design.
---

## Summary
- **Feature**: `youtube-transcription`
- **Discovery Scope**: New Feature / Complex Integration
- **Key Findings**:
  - yt-dlp is the industry-standard library for YouTube audio extraction with active maintenance
  - OpenAI Whisper API provides high-quality transcription with native Japanese and English support
  - GPT-4o can effectively perform text correction and formatting for transcription output
  - Web architecture should separate concerns: frontend UI, backend API, and worker processes

## Research Log

### YouTube Audio Extraction
- **Context**: Need reliable method to download audio from YouTube URLs
- **Sources Consulted**: 
  - https://github.com/yt-dlp/yt-dlp
  - yt-dlp documentation and API
- **Findings**:
  - yt-dlp is actively maintained fork of youtube-dl with better YouTube support
  - Supports audio-only extraction with format selection (M4A, MP3, WAV)
  - Handles various YouTube URL formats (standard, short links, playlists)
  - Provides metadata extraction (title, duration, channel)
  - Python library available for programmatic integration
  - Rate limiting and retry logic built-in
- **Implications**: 
  - yt-dlp is the recommended solution for YouTube audio extraction
  - Should use Python library interface rather than CLI subprocess calls
  - Need to handle extraction errors (copyright, geo-restriction, unavailable videos)

### Speech-to-Text Technology
- **Context**: Need accurate transcription for Japanese and English languages
- **Sources Consulted**:
  - https://platform.openai.com/docs/guides/speech-to-text
  - OpenAI Whisper API documentation
- **Findings**:
  - Multiple Whisper model options available:
    - `whisper-1`: Open-source model, supports 98 languages
    - `gpt-4o-transcribe`: Higher quality, supports prompting for context
    - `gpt-4o-mini-transcribe`: Cost-effective alternative with good quality
    - `gpt-4o-transcribe-diarize`: Speaker identification capability
  - Japanese and English are fully supported languages
  - File size limit: 25MB per request
  - Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, webm
  - Streaming API available for real-time transcription
  - Output formats: json, text, srt, vtt (subtitle formats)
  - Prompting capability to improve accuracy for domain-specific terms
- **Implications**:
  - Use `gpt-4o-mini-transcribe` for cost-effectiveness with acceptable quality
  - Upgrade to `gpt-4o-transcribe` if quality issues arise
  - Audio files may need chunking if longer than 60 minutes (requirement limit)
  - Can leverage prompting to improve accuracy for specific terminology

### LLM-based Text Correction
- **Context**: Transcription output may contain errors, need post-processing
- **Sources Consulted**: OpenAI GPT-4 API documentation
- **Findings**:
  - GPT-4o/GPT-4o-mini capable of text correction tasks
  - Can handle: typo correction, punctuation, paragraph formatting, grammar
  - Context window sufficient for transcripts up to 60 minutes
  - Can provide structured output with original/corrected comparison
- **Implications**:
  - Separate correction step after transcription
  - Prompt engineering needed for optimal correction results
  - May need chunking for very long transcripts

### Web Application Architecture Options
- **Context**: Need scalable architecture for audio processing workloads
- **Findings**:
  - YouTube audio download: 30-120 seconds for typical video
  - Whisper transcription: Real-time to 2x real-time processing
  - LLM correction: 10-30 seconds for typical transcript
  - Total processing time: 2-5 minutes for 10-minute video
- **Implications**:
  - Synchronous request-response unsuitable (timeout issues)
  - Need asynchronous job processing with status updates
  - WebSocket or polling for progress updates
  - Background worker architecture required

## Architecture Pattern Evaluation

| Option | Description | Strengths | Risks / Limitations | Notes |
|--------|-------------|-----------|---------------------|-------|
| Monolithic Sync | Single server handles all steps synchronously | Simple deployment, no queue infrastructure | Request timeouts, poor scalability, blocks server resources | Not recommended for 2-5 minute processing |
| Async Queue | Frontend → API → Queue → Worker → Database | Scalable, resilient, separates concerns | Requires queue infrastructure (Celery, RQ), more complex | Best for production deployment |
| Serverless | Cloud Functions for each processing step | Auto-scaling, pay-per-use | Cold start delays, execution time limits, vendor lock-in | Good for low-volume or prototype |
| Hybrid Polling | Frontend → API initiates background thread, polls for status | Simpler than full queue, async processing | Limited scalability, server resource usage | Good for MVP/prototype |

## Design Decisions

### Decision: Use Async Queue Architecture with Background Workers
- **Context**: Processing time 2-5 minutes makes synchronous handling impractical
- **Alternatives Considered**:
  1. Synchronous processing - rejected due to timeout issues
  2. Serverless - rejected due to cold start delays and execution limits
  3. Hybrid polling - considered for MVP but less scalable
- **Selected Approach**: Backend API + Task Queue + Worker Processes
  - API receives requests, creates jobs, returns job ID
  - Workers process jobs asynchronously
  - Frontend polls job status or uses WebSocket for real-time updates
  - Database stores job state and results
- **Rationale**: 
  - Handles long-running processes gracefully
  - Scales horizontally by adding workers
  - Resilient to failures with retry logic
  - Standard pattern for this type of workload
- **Trade-offs**: 
  - Benefits: Scalability, resilience, user experience
  - Compromises: Increased architectural complexity, infrastructure requirements
- **Follow-up**: Choose task queue (Celery recommended for Python)

### Decision: Use yt-dlp Python Library
- **Context**: Need reliable YouTube audio extraction
- **Alternatives Considered**:
  1. youtube-dl - outdated, slower updates
  2. yt-dlp CLI subprocess - less control, harder error handling
  3. Direct YouTube API - violates ToS, unreliable
- **Selected Approach**: yt-dlp Python library with embedded mode
- **Rationale**: 
  - Active maintenance and YouTube compatibility
  - Programmatic control and error handling
  - Metadata extraction included
- **Trade-offs**:
  - Benefits: Reliability, maintainability
  - Compromises: Dependency on third-party library
- **Follow-up**: Monitor yt-dlp updates, implement error handling for extraction failures

### Decision: Use gpt-4o-mini-transcribe with Upgrade Path
- **Context**: Balance cost and quality for transcription
- **Alternatives Considered**:
  1. whisper-1 - lower cost but lower quality
  2. gpt-4o-transcribe - highest quality but higher cost
  3. gpt-4o-transcribe-diarize - adds speaker labels but unnecessary
- **Selected Approach**: Start with gpt-4o-mini-transcribe, allow upgrade to gpt-4o-transcribe per-request
- **Rationale**: Cost-effective baseline with quality upgrade option
- **Trade-offs**: 
  - Benefits: Cost optimization, flexibility
  - Compromises: May need reprocessing if quality insufficient
- **Follow-up**: Monitor transcription quality metrics, implement model selection in UI

### Decision: Implement LLM Correction as Separate Optional Step
- **Context**: Transcription may have errors, users want readable output
- **Alternatives Considered**:
  1. Always apply correction - adds cost/time
  2. Skip correction entirely - lower quality output
  3. Optional correction (selected) - user choice
- **Selected Approach**: Separate correction step, user-initiated after reviewing transcription
- **Rationale**: Gives users control, saves cost when correction not needed
- **Trade-offs**: 
  - Benefits: User control, cost savings, transparency
  - Compromises: Extra step in UX
- **Follow-up**: Design clear UX for reviewing and triggering correction

### Decision: Support Multiple Export Formats (TXT, SRT, VTT)
- **Context**: Users need different formats for various use cases
- **Selected Approach**: Generate TXT by default, offer SRT/VTT conversion
- **Rationale**: SRT/VTT useful for video subtitles, TXT for general use
- **Follow-up**: Implement format conversion logic, validate subtitle timing accuracy

## Risks & Mitigations

- **Risk 1**: YouTube may block or rate-limit requests
  - **Mitigation**: Implement exponential backoff, rotate user agents, respect rate limits
  
- **Risk 2**: Whisper API may have latency or availability issues
  - **Mitigation**: Implement retry logic, timeout handling, fallback to whisper-1 if gpt-4o unavailable
  
- **Risk 3**: Long videos (approaching 60-minute limit) may exceed OpenAI file size limits (25MB)
  - **Mitigation**: Implement audio compression, chunking strategy, warn users of limits upfront
  
- **Risk 4**: LLM correction may change meaning or remove important context
  - **Mitigation**: Show before/after comparison, allow user to revert, document correction behavior

- **Risk 5**: Queue/worker infrastructure adds operational complexity
  - **Mitigation**: Use managed services (Redis, AWS SQS) where possible, implement health checks and monitoring

## References

- [yt-dlp GitHub Repository](https://github.com/yt-dlp/yt-dlp) - YouTube downloader documentation and examples
- [OpenAI Speech-to-Text Guide](https://platform.openai.com/docs/guides/speech-to-text) - Whisper API documentation and best practices
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference) - API endpoints and parameters
- [Celery Documentation](https://docs.celeryq.dev/) - Distributed task queue for Python
