# AI Troubleshooting Agent

The **AI Troubleshooting Agent** is a microservices-based application designed to assist with network troubleshooting (specifically Cisco ACI) using an LLM-powered agentic workflow.

## Overview

The system consists of three main components:
1.  **Frontend**: A Streamlit application that provides a chat interface for users to interact with the agent.
2.  **Backend**: A FastAPI service hosting the LangGraph orchestrator and agent logic.
3.  **LLM**: External Large Language Model providers (e.g., OpenAI, Gemini) that power the agent's reasoning.

## Quick Start

### Prerequisites
- Docker and Docker Compose installed.
- An OpenAI API Key (or other provider key) set in your environment.

### Running the Application

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd agent_langchain_antigravity_ralph
    ```

2.  **Set up Environment**:
    Create a `.env` file in the `backend` directory or use the root `.env` if configured.
    ```bash
    OPENAI_API_KEY=sk-...
    ```

3.  **Start Services**:
    ```bash
    docker-compose up --build
    ```

4.  **Access the Application**:
    - **Frontend**: Open [http://localhost:8501](http://localhost:8501) in your browser.
    - **Backend API Docs**: Open [http://localhost:8000/docs](http://localhost:8000/docs).

## Architecture

### High-Level Data Flow

```mermaid
graph LR
    %% Define Nodes with Shapes
    User([User]) -->|Interacts :8501| FE["Frontend (Streamlit)"]
    FE -->|HTTP Request / SSE :8000| BE["Backend (FastAPI)"]
    BE -->|Invokes| Orch["Orchestrator (LangGraph)"]
    Orch -->|Queries| LLM[LLM Provider]
    
    %% Define Subgraph
    subgraph Docker ["Docker Network"]
        direction LR
        FE
        BE
    end

    %% Styling Classes
    classDef external fill:#f9f9f9,stroke:#333,stroke-width:2px,color:#333;
    classDef dockerNode fill:#e1f5fe,stroke:#0277bd,stroke-width:2px,color:#01579b;
    classDef logicNode fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#e65100;
    classDef container fill:#ffffff,stroke:#0277bd,stroke-width:2px,stroke-dasharray: 5 5;

    %% Apply Classes
    class User external;
    class FE,BE dockerNode;
    class Orch,LLM logicNode;
    class Docker container;
```

### Agentic Workflow

The backend uses **LangGraph** to orchestrate the agent's behavior.

```mermaid
graph TD
    Start([Start]) --> Router{Router}
    
    Router -->|General Query| DirectResp[Direct Response]
    Router -->|Troubleshooting| Tools[Tool Execution]
    
    Tools -->|Result| Agent[Agent Reasoning]
    Agent --> Router
    
    DirectResp --> End([End])
```
