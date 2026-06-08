# DevNest AI Learning Platform

DevNest is an AI-powered learning platform designed to support personalized student learning through authentication, quizzes, coding challenges, AI-assisted features, Firebase integration, and backend APIs.

## Overview

This repository contains the backend source code for the DevNest AI Learning Platform. The backend is responsible for handling authentication, user-related services, quizzes, challenges, AI features, code evaluation, Firebase storage/database integration, and API routing.

The project uses environment variables for sensitive configuration such as Firebase credentials, JWT settings, and AI API keys. Real secrets are not included in this repository.

## Features

- User authentication system
- JWT-based access and refresh token handling
- Firebase integration
- Firebase database and storage support
- Quiz module
- Coding challenge module
- AI route support
- Analytics route support
- Code judging/evaluation support using Judge0
- Rate limiting support
- Modular FastAPI-style backend structure
- Test files for authentication and AI functionality
- Environment variable configuration using `.env.example`

## Tech Stack

- Python
- FastAPI
- Firebase
- JWT Authentication
- Judge0 API
- OpenAI/Gemini API integration
- Pytest
- Environment-based configuration

## Project Structure

```text
app/
  auth.py
  config.py
  crud.py
  crud_submissions.py
  deps.py
  firebase.py
  firebase_db.py
  judge.py
  judge_service.py
  main.py
  middleware.py
  models.py
  schemas.py
  storage.py
  utils.py

  challenges/
    router.py
    schemas.py
    service.py

  quizzes/
    router.py
    schemas.py
    service.py

  routes/
    ai.py
    analytics.py

  services/
    ai_client.py
    rate_limiter.py

tests/
  test_auth.py

.env.example
.gitignore
requirements.txt
test_all_ai.py
README.md
