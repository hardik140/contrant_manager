# Contract Clause Detection System - Enhanced Features

This document outlines the enhanced features implemented to improve the contract clause detection and analysis system.

## 🚀 Key Improvements

### 1. Text Normalization Service (`services/text_normalizer.py`)

**Purpose**: Standardize and clean contract text for better analysis accuracy.

**Features**:
- Date standardization (various formats → `[DATE]`)
- Currency normalization (different formats → `[AMOUNT]`)
- Party name masking (`Company Inc.` → `[PARTY]`)
- Whitespace and artifact removal (headers, footers, page numbers)
- Entity extraction (dates, amounts, sections, parties)

**Usage**:
```python
from services.text_normalizer import normalize_contract_text

normalized_text, stats = normalize_contract_text(
    raw_text,
    mask_parties=True,
    standardize_dates=True,
    normalize_currencies=True
)
```

### 2. Enhanced Clause Analysis with Provenance

**New Response Format**:
```json
{
  "status": "partial",
  "explanation": "User clause mentions insurance but lacks coverage details",
  "suggestion": "Add 'for the full lease period' and specify property coverage",
  "provenance": {
    "method": "llm",
    "confidence": 0.85,
    "processing_time_ms": 420,
    "model_used": "gemini-1.5-flash",
    "fallback_used": false,
    "error_occurred": false
  }
}
```

### 3. LLM Circuit Breaker & Retry Logic

**Features**:
- Automatic retry with exponential backoff
- Circuit breaker prevents cascading failures (5 failures → 5-minute timeout)
- Graceful fallback when LLM is unavailable

**Implementation**:
```python
# Circuit breaker automatically handles:
response_text, success = call_llm_with_retry(model, prompt, max_retries=3)
```

### 4. Enhanced File Extraction with Metadata

**New Features**:
- Extraction metadata (method used, OCR flag, file size)
- Text normalization integrated into extraction pipeline
- Better error handling and logging

**Response includes**:
```json
{
  "extraction_metadata": {
    "extraction_method": "pdf_direct",
    "ocr_used": false,
    "file_size": 245760,
    "file_ext": ".pdf"
  }
}
```

### 5. Structured Logging & Metrics

**Added throughout the system**:
- Request/response logging with timing
- Processing method tracking (LLM vs embedding vs rules)
- Error classification and tracking
- Performance metrics collection

### 6. Enhanced API Responses

**All endpoints now include**:
- Processing provenance and confidence scores
- Error classification and recovery information
- Performance timing data
- Method attribution (rule-based, embedding, LLM)

## 🧪 Testing

### Run Enhanced Features Test
```bash
cd backend
python test_enhanced_features.py
```

**Test Coverage**:
- ✅ Text normalization with entity extraction
- ✅ Enhanced clause analysis with provenance
- ✅ Enhanced clause detection with metadata
- ✅ Circuit breaker functionality
- ✅ Error handling scenarios

### Run API Tests
```bash
# Start server first
python main.py

# In another terminal
python test_detect_clauses.py
python test_clause_analyzer.py
```

## 🔧 Configuration

### Environment Variables
```env
GEMINI_API_KEY=your_gemini_api_key
MONGO_URI=mongodb://localhost:27017/
```

### Logging Configuration
- Default level: `INFO`
- Automatic structured logging in all services
- Error tracking with stack traces

### Circuit Breaker Settings
- Failure threshold: 5 consecutive failures
- Timeout: 5 minutes (300 seconds)
- States: closed → open → half-open → closed

## 📊 Performance Improvements

### Before vs After
| Feature | Before | After |
|---------|--------|-------|
| Error Handling | Basic try/catch | Structured with fallbacks |
| LLM Reliability | No retry logic | 3 retries + circuit breaker |
| Text Quality | Raw extraction | Normalized + cleaned |
| API Responses | Basic data only | Full provenance + confidence |
| Logging | Print statements | Structured logging |
| Failure Recovery | Manual intervention | Automatic fallbacks |

### Typical Performance
- Clause detection: ~200-500ms per document
- Single clause analysis: ~300-800ms
- Text normalization: ~50-100ms
- OCR fallback: ~2-5s per page

## 🎯 Usage Examples

### 1. Analyze Single Clause Pair
```python
POST /api/analyze-clause/
{
  "reference_clause": "Tenant must maintain insurance during lease period",
  "user_clause": "Tenant shall maintain insurance"
}

Response:
{
  "status": "partial",
  "explanation": "Missing lease period specification",
  "suggestion": "Add 'during the full lease period'",
  "provenance": {
    "method": "llm",
    "confidence": 0.75,
    "processing_time_ms": 340
  }
}
```

### 2. Detect Clauses from Contract
```python
POST /api/detect-clauses/
{
  "text": "1. TERM: This lease is for 12 months. 2. RENT: $1500/month..."
}

Response: [
  {
    "id": 1,
    "title": "TERM",
    "text": "This lease is for 12 months.",
    "provenance": {
      "method": "hybrid",
      "confidence": 0.9,
      "processing_time_ms": 45
    },
    "extraction_method": "standard",
    "ocr_used": false
  }
]
```

### 3. Upload Contract with Enhanced Extraction
```python
POST /api/upload-contract/
# File upload

Response:
{
  "id": "contract_id",
  "summary": "Contract summary...",
  "filename": "contract.pdf",
  "extraction_metadata": {
    "extraction_method": "pdf_direct",
    "ocr_used": false,
    "file_size": 245760
  }
}
```

## 🛠️ Troubleshooting

### Common Issues

1. **LLM Circuit Breaker Open**
   - Wait 5 minutes or restart service
   - Check `GEMINI_API_KEY` environment variable
   - Monitor logs for API quota issues

2. **Embedding Model Load Failure**
   - System falls back to rule-based segmentation
   - Install `sentence-transformers`: `pip install sentence-transformers`
   - Check available memory (model requires ~500MB)

3. **OCR Processing Slow**
   - Normal for scanned PDFs (2-5s per page)
   - Reduce image DPI in `ocr_service.py` if needed
   - Consider preprocessing images separately

### Health Checks
```bash
# Check server health
curl http://localhost:8000/health

# Check circuit breaker status
# Monitor logs for "Circuit breaker" messages
```

## 🔮 Future Enhancements

### Planned Improvements
1. **FAISS Vector Store**: Fast similarity search for large policy databases
2. **Async Processing**: Background task queue for heavy operations  
3. **Confidence Tuning**: Machine learning model to calibrate confidence scores
4. **Multi-language Support**: Extend text normalization for different languages
5. **Real-time Monitoring**: Prometheus/Grafana dashboard for system metrics

### Performance Optimizations
1. **LLM Response Caching**: Cache identical prompt results
2. **Embedding Caching**: Store computed embeddings for reuse
3. **Batch Processing**: Process multiple clauses in single LLM call
4. **Model Quantization**: Reduce memory usage of embedding models

---

## 📝 Change Log

### v2.0.0 - Enhanced Features Release
- ✅ Added text normalization service
- ✅ Implemented LLM circuit breaker and retry logic
- ✅ Enhanced API responses with provenance data
- ✅ Added structured logging throughout
- ✅ Improved error handling and fallback mechanisms
- ✅ Updated file extraction with metadata
- ✅ Created comprehensive test suite

### v1.0.0 - Initial Release
- Basic clause detection and analysis
- PDF/DOCX text extraction with OCR fallback
- MongoDB storage
- FastAPI endpoints
