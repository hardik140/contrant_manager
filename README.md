# Contract Intelligence Suite

A comprehensive contract management application powered by AI that provides intelligent document summarization and policy comparison capabilities.

## Features

- **AI-Powered Document Summarization**: Upload contracts and get intelligent summaries using Google's Gemini AI
- **Policy Comparison**: Compare contracts against company policies to identify compliance issues
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
- `POST /api/compare/policy` - Compare contracts against policies

## Usage

1. **Document Summarization**:
   - Navigate to the Summarizer page
   - Upload a PDF or DOCX contract file
   - Get an AI-generated summary of key contract terms

2. **Policy Comparison**:
   - Navigate to the Comparison page
   - Upload both a contract file and a policy document
   - Get detailed analysis of compliance and discrepancies

## Project Structure

```
contrant_manager/
├── src/                    # Frontend source code
│   ├── app/               # Next.js app directory
│   ├── components/        # Reusable UI components
│   └── lib/              # Utility functions
├── backend/               # Python FastAPI backend
│   ├── routes/           # API route handlers
│   ├── services/         # Business logic services
│   ├── models/           # Data models
│   └── database/         # Database configuration
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
- AI integration uses Google's Gemini model
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
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.
