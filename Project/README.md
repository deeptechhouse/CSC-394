# AI-Powered Exam System

An intelligent exam system that generates essay questions in real-time using AI and evaluates student responses with detailed feedback.

## Overview

This system addresses the challenges of modern education by:
- Generating unique essay questions for each student using AI
- Providing real-time grading with detailed rubrics
- Offering constructive feedback to help students learn
- Supporting asynchronous online exams without question leakage

## Features

- **Dynamic Question Generation**: Questions are generated on-the-fly using LLM, ensuring each student gets a unique exam
- **Essay-Style Questions**: Tests deep understanding through comprehensive essay questions
- **AI-Powered Grading**: Responses are evaluated using detailed rubrics with constructive feedback
- **Web-Based Interface**: Easy-to-use web interface for students and professors
- **Detailed Feedback**: Students receive criterion-by-criterion feedback with strengths, weaknesses, and suggestions

## Setup

### Prerequisites

- Python 3.8 or higher
- Together.ai API key

### Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your Together.ai API key:
   ```
   TOGETHER_API_KEY=your_api_key_here
   ```

### Running the Application

Start the server:
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload
```

The application will be available at `http://localhost:8000`

## Usage

1. **Create an Exam**: Navigate to the "Create New Exam" page and provide:
   - Student ID
   - Subject Domain (e.g., "Computer Science", "History")
   - Number of questions
   - Optional professor instructions

2. **Take the Exam**: Students answer essay questions one at a time, with background information provided for context.

3. **View Results**: After completing all questions, students can view detailed grading results with:
   - Overall score and percentage
   - Criterion-by-criterion breakdown
   - Strengths and weaknesses
   - Constructive suggestions

## Architecture

### Components

- **models.py**: Data models for questions, responses, and grades
- **prompts.py**: Prompt templates for LLM interactions
- **llm_client.py**: Client for Together.ai API integration
- **question_generator.py**: Generates exam questions using LLM
- **grader.py**: Grades student responses using LLM
- **main.py**: FastAPI server and web interface
- **config.py**: Configuration management

### Data Flow

1. Professor creates exam → Questions generated via LLM
2. Student takes exam → Responses submitted
3. Responses graded → LLM evaluates against rubric
4. Results displayed → Detailed feedback shown to student

## Configuration

Edit `.env` file or set environment variables:

- `TOGETHER_API_KEY`: Your Together.ai API key (required)
- `TOGETHER_MODEL`: Model to use (default: "mistralai/Mixtral-8x7B-Instruct-v0.1")
- `HOST`: Server host (default: "0.0.0.0")
- `PORT`: Server port (default: 8000)
- `DEBUG`: Debug mode (default: False)

## Notes

- The system uses in-memory storage for sessions. In production, use a database.
- Questions are generated in real-time, so each exam is unique.
- Grading uses detailed rubrics created alongside each question.
- State "P" indicates a highly satisfactory response (typically ≥80%).

## License

This project is for educational purposes.
