# Modal Gemini Inference

This project provides a Modal-based inference service using Google's Gemini AI model. It allows you to deploy and run Gemini text generation remotely using Modal's serverless platform.

## Prerequisites

- Python 3.12+
- Poetry for dependency management
- A Modal account
- A Google AI API key for Gemini

## Setup

### 1. Install Dependencies

Make sure you have Poetry installed, then install the project dependencies:

```bash
poetry install
```

### 2. Modal Account Setup

1. Create a Modal account at [modal.com](https://modal.com)
2. Install and authenticate the Modal CLI:
   ```bash
   poetry run modal token new
   ```

### 3. Configure Gemini API Secret

You need to set up a Modal secret with your Gemini API key:

1. Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a Modal secret named `gemini-secret` with your API key:
   ```bash
   poetry run modal secret create gemini-secret GEMINI_API_KEY=your_api_key_here
   ```

## Running the Project

### Local Development

To run the inference function locally (which will execute remotely on Modal):

```bash
poetry run modal run dependencies.py
```

### Deploy to Modal

To deploy the app to Modal for persistent hosting:

```bash
poetry run modal run dependencies.py
```

## How It Works

- The `inference` function accepts text input and returns Gemini's generated response
- The function runs on Modal's serverless infrastructure with the specified dependencies
- The Gemini API key is securely stored as a Modal secret
- The example uses the `gemini-1.5-flash` model for fast text generation

## Project Structure

- `dependencies.py` - Main Modal app with inference function
- `pyproject.toml` - Poetry configuration and dependencies
- `poetry.lock` - Locked dependency versions

## Environment Variables

The following environment variable is required and automatically loaded from the Modal secret:

- `GEMINI_API_KEY` - Your Google AI API key for accessing Gemini models
