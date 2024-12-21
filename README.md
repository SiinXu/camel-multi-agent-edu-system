# Multi-Agent Education System

An intelligent education system powered by multiple AI agents to provide personalized learning experiences.

## System Architecture

The system consists of three main agents:

1. **Teacher Agent**: Creates lesson plans, evaluates progress, and provides feedback
2. **Student Agent**: Handles student interactions, questions, and tracks learning progress
3. **Crawler Agent**: Gathers and validates educational resources from trusted sources

## Project Structure

```
multi-agent-edu-system/
├── backend/            # FastAPI backend
│   ├── main.py        # Main FastAPI application
│   └── agents/        # AI agents implementation
├── frontend/          # React frontend
│   └── src/          # React source code
```

## Setup Instructions

### Backend Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Run the backend server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm start
   ```

## Environment Variables

Create a `.env` file in the backend directory with the following variables:

```
OPENAI_API_KEY=your_api_key
DATABASE_URL=sqlite:///./study_records.db
```

## Features

- Personalized learning paths
- Intelligent tutoring system
- Automated resource gathering
- Progress tracking and analytics
- Real-time feedback and assessment

## License

MIT License
