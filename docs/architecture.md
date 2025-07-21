# Architecture Overview

## System Architecture

The Job Search Assistant follows a layered architecture pattern designed for modularity, extensibility, and maintainability. The system is built around AI-powered workflows that process job-related information and provide intelligent recommendations.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │   Streamlit UI  │  │   Web Pages     │  │   API       │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Workflow Orchestration                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │ Job Evaluation  │  │     Resume      │  │ Interview   │  │
│  │   Workflow      │  │  Customization  │  │ Preparation │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Agent Layer                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │  Extraction     │  │  Evaluation     │  │ Generation  │  │
│  │   Agents        │  │   Agents        │  │   Agents    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Tool Layer                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │  Schema         │  │  Validation     │  │  Formatting │  │
│  │  Extraction     │  │   Tools         │  │   Tools     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Core Layer                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │  Job Evaluation │  │  Resume         │  │  Business   │  │
│  │    Logic        │  │  Customization  │  │   Logic     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │
│  │  Configuration  │  │  LLM Clients    │  │Observability│  │
│  │   Management    │  │   (Anthropic)   │  │  (Langfuse) │  │
│  └─────────────────┘  └─────────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. User Interface Layer
- **Streamlit UI**: Interactive web interface for job evaluation
- **Documentation**: Static GitHub Pages documentation
- **Future**: RESTful API endpoints for programmatic access

### 2. Workflow Orchestration Layer
- **LangGraph Workflows**: Complex multi-step AI processes
- **State Management**: Pydantic models for workflow state
- **Error Handling**: Graceful degradation and recovery

### 3. Agent Layer
- **Specialized Agents**: AI components for specific tasks
- **Prompt Management**: Centralized prompt versioning
- **Decision Making**: Context-aware AI reasoning

### 4. Tool Layer
- **Extraction Tools**: Parse unstructured data into structured format
- **Validation Tools**: Ensure data quality and consistency
- **Utility Tools**: Common operations and formatting

### 5. Core Layer
- **Business Logic**: Domain-specific rules and algorithms
- **Data Models**: Pydantic models for type safety
- **Evaluation Logic**: Criteria matching and scoring

### 6. Infrastructure Layer
- **Configuration**: TOML-based environment-specific settings
- **LLM Integration**: Anthropic Claude API integration
- **Observability**: Langfuse monitoring and analytics

## Data Flow

### Job Evaluation Process
```
1. User Input (Job Posting Text)
   ↓
2. Input Validation
   ↓
3. Information Extraction (LLM + Tools)
   ↓
4. Criteria Evaluation (Business Logic)
   ↓
5. Recommendation Generation (Business Logic)
   ↓
6. User Output (Structured Recommendation)
```

### Configuration Flow
```
1. Environment Detection (APP_ENV)
   ↓
2. Base Configuration Load (base.toml)
   ↓
3. Environment Overrides (dev.toml, prod.toml)
   ↓
4. Environment Variable Overrides
   ↓
5. Validation and Type Safety
   ↓
6. Application Usage
```

## Technology Stack

### Core Technologies
- **Python 3.11+**: Primary development language
- **LangGraph**: Workflow orchestration and state management
- **Pydantic**: Data validation and type safety
- **Streamlit**: Web interface framework

### AI/ML Stack
- **Anthropic Claude**: Primary LLM for AI tasks
- **Langfuse**: LLM observability and monitoring
- **Structured Output**: JSON schema extraction and validation

### Development Tools
- **uv**: Python package management
- **pytest**: Testing framework
- **mypy**: Type checking
- **pre-commit**: Code quality automation
