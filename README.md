# Contract Intelligence Suite

A comprehensive contract management application powered by AI that provides intelligent document summarization, policy comparison, and RAG-enhanced clause detection capabilities.

## Features

- **AI-Powered Document Summarization**: Upload contracts and get intelligent summaries using Google's Gemini AI
- **RAG-Enhanced Clause Detection**: Advanced clause identification powered by Retrieval-Augmented Generation (RAG) with FAISS vector search over 948 legal provisions from the Indian Contract Act
- **Policy Comparison**: Compare contracts against company policies to identify compliance issues using semantic similarity and vector embeddings
- **Modern Web Interface**: Built with Next.js 15 and React 19 with a responsive design
- **File Upload Support**: Supports PDF and DOCX file formats
- **Real-time Processing**: Fast document processing with loading states and error handling

## Tech Stack

### Frontend
- **Next.js 15** with App Router
- **React 19** with TypeScript
- **Tailwind CSS** with custom components
- **Shadcn/ui** component library
- **Lucide React** for icons

### Backend
- **FastAPI** for high-performance API
- **Google Gemini AI** for document analysis
- **RAG (Retrieval-Augmented Generation)** for intelligent clause detection
- **FAISS Vector Database** for semantic search across 948 legal provisions
- **Sentence Transformers** (all-mpnet-base-v2) for high-quality embeddings
- **MongoDB** for data storage
- **Python** with async/await support

## Prerequisites

Before running this application, make sure you have the following installed:

- **Node.js** (v18 or higher)
- **Python** (v3.8 or higher)
- **MongoDB** (local or cloud instance)
- **Google AI API Key** (for Gemini integration)

## Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd contrant_manager
```

### 2. Frontend Setup

Install Node.js dependencies:
```bash
npm install
# or
yarn install
# or
pnpm install
```

### 3. Backend Setup

Navigate to the backend directory and install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the backend directory with the following variables:
```env
GOOGLE_API_KEY=your_google_gemini_api_key
MONGODB_URL=your_mongodb_connection_string
```

### 5. Build FAISS Legal Index (One-Time Setup)

Initialize the RAG vector database with legal provisions:
```bash
cd backend
python build_legal_index.py
```

This builds a FAISS index with 948 legal provisions from the Indian Contract Act, enabling semantic search for clause detection. The index files are stored in `backend/index/`.

## Running the Application

### Start the Backend Server

From the `backend` directory:

**Option 1: Using Python directly**
```bash
python main.py
```

**Option 2: Using Uvicorn**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Note:** On startup, the backend automatically preprocesses all policies and initializes the RAG pipeline for optimal performance.

**Option 3: Using the start scripts**
```bash
# On Windows
start.bat

# On Linux/Mac
./start.sh
```

The backend API will be available at: `http://localhost:8000`

### Start the Frontend Development Server

From the root directory:
```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

The frontend will be available at: `http://localhost:3000`

## API Endpoints

- `GET /` - API root endpoint
- `GET /health` - Health check endpoint
- `POST /api/contracts/summarize` - Upload and summarize contracts
- `POST /api/compare/policy` - Compare contracts against policies using RAG
- `POST /api/clauses/detect` - Detect and analyze clauses using RAG-powered semantic search
- `GET /api/policies/` - Retrieve available policies

## Usage

1. **Document Summarization**:
   - Navigate to the Summarizer page
   - Upload a PDF or DOCX contract file
   - Get an AI-generated summary of key contract terms

2. **Policy Comparison**:
   - Navigate to the Comparison page
   - Upload both a contract file and a policy document
   - Get detailed analysis of compliance and discrepancies powered by RAG

3. **RAG-Based Clause Detection**:
   - The system automatically detects clauses using semantic search
   - Each clause is matched against 948 legal provisions via FAISS vector similarity
   - Relevant legal context is retrieved and augmented with LLM analysis
   - Provides compliance status, risk assessment, and actionable recommendations

## Project Structure

```
contrant_manager/
├── src/                    # Frontend source code
│   ├── app/               # Next.js app directory
│   ├── components/        # Reusable UI components
│   └── lib/              # Utility functions
├── backend/               # Python FastAPI backend
│   ├── routes/           # API route handlers
│   ├── services/         # Business logic services (RAG, clause analysis)
│   ├── models/           # Data models
│   ├── database/         # Database configuration
│   ├── index/            # FAISS vector database (948 legal provisions)
│   │   ├── faiss.index   # Vector similarity index
│   │   ├── ids.npy       # Clause identifiers
│   │   └── act_clauses.jsonl  # Legal provision metadata
│   └── policies/         # Policy documents for comparison
└── public/               # Static assets
```

## Development

### Frontend Development
- The frontend uses Next.js with TypeScript
- Styling is done with Tailwind CSS
- UI components are built with Shadcn/ui
- File uploads are handled with multipart forms

### Backend Development
- The backend uses FastAPI with async/await
- Document processing supports PDF and DOCX formats
- AI integration uses Google's Gemini model with deterministic configuration
- RAG pipeline uses Sentence Transformers (all-mpnet-base-v2) for embeddings
- FAISS IndexFlatIP provides fast semantic similarity search
- Clause detection combines vector retrieval with LLM analysis
- CORS is configured for local development

## Building for Production

### Frontend Build
```bash
npm run build
npm run start
```

### Backend Production
```bash
pip install -r requirements.txt
python build_legal_index.py  # Ensure FAISS index is built
uvicorn main:app --host 0.0.0.0 --port 8000
```

## How RAG Powers Clause Detection

The system uses Retrieval-Augmented Generation (RAG) to provide intelligent clause analysis:

1. **Embedding Generation**: Contract clauses are converted to 768-dimensional vectors using Sentence Transformers
2. **Semantic Search**: FAISS IndexFlatIP searches 948 legal provisions for the most relevant matches
3. **Context Retrieval**: Top-K similar provisions are retrieved with similarity scores
4. **LLM Augmentation**: Retrieved legal context is combined with the clause and sent to Gemini
5. **Analysis**: The LLM analyzes compliance, risks, and recommendations using the augmented context
6. **Deterministic Output**: Temperature=0 ensures consistent results for identical queries
7. **Caching**: Hash-based caching provides instant responses for repeated queries

This RAG approach combines the precision of semantic search with the reasoning capabilities of LLMs, resulting in accurate and context-aware legal analysis.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.
