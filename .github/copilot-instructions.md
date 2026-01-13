# Imaichika Telegram Channel Profiler - AI Coding Assistant Instructions

## Project Overview
This is a Python-based system for analyzing Telegram channels using the Telethon client library. It extracts message data, performs NLP-based analysis, and generates group/channel profiles using semantic analysis and LLM integration.

## Architecture & Components

### Core Modules
- **`imaichika.py` / `test_name.py`**: Telegram data scrapers using Telethon client
  - Async-based message history retrieval with pagination
  - Proxy support (SOCKS5) for circumventing geo-blocking
  - Session management with `session_name` files for persistent login state
  - Configuration: API ID/Hash, channel username, message limits, proxy settings

- **`gemini.py`**: Statistical profiler for raw channel analysis
  - Garbage string detection (repeated chars, random ASCII)
  - NLP-based semantic tagging using `jieba` tokenization
  - Named entity extraction (phone numbers, crypto addresses)
  - User frequency analysis and word clouds

- **`gemini-qwen.py`**: Advanced LLM-powered profiler
  - Integrates Qwen-7B-Chat model with 8-bit quantization for efficiency
  - Replaces rule-based classification with contextual LLM analysis
  - Expects model files in `./Qwen-7B-Chat/` directory
  - Uses HuggingFace Hub with CN mirror endpoint (`https://hf-mirror.com`)

- **`download.py`**: Model downloading utility
  - Downloads Qwen-7B-Chat from HuggingFace using CN mirror
  - Supports resumable downloads with multi-threading

### Data Flow
```
Telegram Channel → GetHistoryRequest (Telethon)
                ↓
            JSON files (channel_*.json, nchannel_*.json)
                ↓
        gemini.py / gemini-qwen.py
                ↓
    Statistical Analysis + LLM Profiling → Reports
```

## Data Format & Storage

### Message JSON Structure
Each message object contains:
```json
{
  "id": <int>,           // Message ID
  "date": "<ISO datetime>",
  "sender_id": <int>,    // User ID
  "text": "<str>",       // Message content
  "reply_to": <int|null> // Reply target message ID
}
```

### File Naming Convention
- **`channel_*.json`**: Regular channel exports (indexed, incremental)
- **`nchannel_*.json`**: New/normalized channel exports (alternative naming)
- Files stored as JSON arrays at root directory level

## Key Patterns & Conventions

### 1. Async Telegram Operations
- All Telegram operations use `asyncio` with Telethon's async API
- Use `GetHistoryRequest` with pagination (`offset_id` parameter) for large histories
- Wrap requests in try-except blocks; retry with 10-second delays on network errors
- Example: `history = await client(GetHistoryRequest(peer=channel, offset_id=offset_id, limit=100))`

### 2. Proxy Configuration
```python
proxy = (socks.SOCKS5, '127.0.0.1', 7890, True)  # SOCKS5, host, port, auth_required
client = TelegramClient('session_name', api_id, api_hash, proxy=proxy)
```
- Omit proxy parameter if not needed: `client = TelegramClient(...)`

### 3. NLP Text Cleaning Pipeline
```python
# Garbage detection: repeated chars or long ASCII sequences
if re.search(r'(.)\1{4,}', text) or re.match(r'^[a-zA-Z]{5,}$', text):
    continue
# Tokenization with jieba + POS tagging
words_pos = pseg.cut(text)  # Returns (word, pos_tag) tuples
```

### 4. Environment-Specific Handling
- **Windows encoding**: Force UTF-8 for console output
  ```python
  import io
  sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
  ```
- **HuggingFace mirror**: Use CN endpoint for faster downloads
  ```python
  os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
  ```

### 5. LLM Integration (Qwen-7B-Chat)
- Load with 8-bit quantization for memory efficiency
- Pass system prompts in natural Chinese for better results
- Extract model outputs via tokenizer decoding
- Always use `trust_remote_code=True` for Qwen models
- Example:
  ```python
  quantization_config = BitsAndBytesConfig(load_in_8bit=True)
  model = AutoModelForCausalLM.from_pretrained(
      model_path, 
      quantization_config=quantization_config, 
      device_map="auto",
      trust_remote_code=True
  )
  ```

## Common Development Tasks

### Scraping a New Channel
1. Update `api_id`, `api_hash`, `channel_username` in scraper script
2. Set `output_file` to desired JSON filename
3. Configure `total_limit` and `limit_per_request` for message volume
4. Run: `python test_name.py` (handles login prompts interactively)
5. Data saves to `*.json` at project root

### Analyzing Channel Messages
1. Place message JSON file in project root
2. For statistical analysis: `python gemini.py` (edit `filepath` in code)
3. For LLM analysis: `python gemini-qwen.py` (ensure Qwen model downloaded)
4. Both output analysis reports to console (modify to save to file if needed)

### Debugging Failed Imports
- Check `requirements.txt` for dependency versions
- Common issues: `telethon`, `transformers`, `jieba`, `bitsandbytes`
- Install missing: `pip install -r requirements.txt`

## Testing Files
- **`test.py`, `test1.py`, `test2.py`**: Experimental/development scripts
- **`Untitled.ipynb`**: Jupyter notebook for interactive analysis (rarely used)
- Don't edit main modules based on test file patterns

## Critical Implementation Notes

### Telethon Best Practices
- Session files (`*.session`) persist authentication state—don't delete during development
- Always check `is_user_authorized()` before operating on protected channels
- Use `client.disconnect()` or async context manager to clean up sessions

### Error Handling
- Network timeouts: Implement exponential backoff, not just fixed delays
- Rate limiting: Telethon auto-throttles; 10-second sleep is standard retry
- Chinese character encoding: Always use `encoding='utf-8'` for file I/O

### Memory Optimization
- For large datasets (10k+ messages): Use streaming/batch processing
- 8-bit quantization in Qwen significantly reduces VRAM usage (≈7GB instead of 28GB)
- Avoid loading full model if only doing statistical analysis (gemini.py)

## Dependencies Summary
- **Core**: `telethon` (Telegram API), `transformers` (LLM), `torch` (inference)
- **NLP**: `jieba` (Chinese tokenization), `wordcloud` (visualization)
- **ML**: `bitsandbytes` (quantization), `huggingface-hub` (model downloading)
- **Utilities**: `socks` (proxy support), `matplotlib` (plotting)

## File Organization Best Practices
- Keep all `channel_*.json` and `nchannel_*.json` files at root (auto-scanned by analyzers)
- Analyzer scripts should parameterize filenames (currently hard-coded—refactor if adding new channels)
- Session files (`*.session-journal`) are auto-generated; safe to ignore in version control
