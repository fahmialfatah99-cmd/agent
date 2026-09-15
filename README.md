# Super Intelligent Agent

A next-generation AI agent framework with multi-provider support, advanced reasoning capabilities, and multi-agent orchestration.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js 15)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │   Chat   │  │Dashboard │  │ Settings │  │  Tools   │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ REST / WebSocket
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │  Auth    │  │Rate Limit│  │   CORS   │  │ Logging  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     ★ AGENT ENGINE ★                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Planner  │→ │ Reasoner │→ │ Executor │→ │Reflector │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│       ▲                                              │      │
│       └────────────── Feedback Loop ──────────────────┘      │
└─────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Memory     │    │    Tools     │    │  Providers   │
│ ┌──────────┐ │    │ ┌──────────┐ │    │ ┌──────────┐ │
│ │ Short    │ │    │ │ Search   │ │    │ │ OpenAI   │ │
│ │ Long     │ │    │ │ Code     │ │    │ │ Anthropic│ │
│ │ Episodic │ │    │ │ File     │ │    │ │ Google   │ │
│ │ Semantic │ │    │ │ API      │ │    │ │ Ollama   │ │
│ └──────────┘ │    │ └──────────┘ │    │ └──────────┘ │
└──────────────┘    └──────────────┘    └──────────────┘
```

## ✨ Features

### 🧠 Advanced Agent Core
- **Planner**: Breaks down complex goals into actionable steps
- **Reasoner**: Chain-of-thought and ReAct reasoning patterns
- **Executor**: Reliable tool execution with error handling
- **Reflector**: Self-evaluation and iterative improvement
- **Router**: Intent classification and task routing
- **Guardrails**: Safety filters and content moderation

### 🔌 Multi-Provider Support
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3, Claude 2)
- Google (Gemini Pro, Gemini Ultra)
- Mistral (Mistral Large, Mixtral)
- Groq (Ultra-fast inference)
- Ollama (Local models)
- Together AI (Open models)

### 💾 Memory System
- **Short-term**: Conversation buffer with sliding window
- **Long-term**: Vector database storage (Qdrant/Chroma)
- **Episodic**: Past interaction recall
- **Semantic**: Knowledge graph integration

### 🛠️ Extensible Tool System
- Web search (Tavily, Serper)
- Code execution (sandboxed)
- File operations (read/write/upload)
- API calls (REST/GraphQL)
- Custom user-defined tools

### 👥 Multi-Agent Orchestration
- **Swarm**: Decentralized agent collaboration
- **Supervisor**: Hierarchical task delegation
- **Message Protocol**: Inter-agent communication

### 📊 Evaluation & Monitoring
- Built-in benchmarks
- Performance metrics
- Cost tracking
- Latency monitoring

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL, Redis, Qdrant (or use Docker Compose)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd super-agent

# Install backend dependencies
cd apps/api
pip install -r requirements.txt

# Install frontend dependencies
cd ../web
npm install

# Setup environment variables
cp ../../.env.example .env
# Edit .env with your API keys
```

### Running Locally

```bash
# Option 1: Run services separately

# Terminal 1 - Backend
cd apps/api
uvicorn src.main:app --reload --port 8000

# Terminal 2 - Frontend
cd apps/web
npm run dev

# Option 2: Use Docker Compose
cd infra/docker
docker-compose up -d
```

### Environment Variables

```bash
# API Keys (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
GROQ_API_KEY=...

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/superagent
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333

# App Config
APP_ENV=development
SECRET_KEY=your-secret-key
LOG_LEVEL=INFO
```

## 📁 Project Structure

```
super-agent/
├── apps/
│   ├── web/                        # Next.js frontend
│   │   ├── src/
│   │   │   ├── app/                # App Router pages
│   │   │   │   ├── (chat)/         # Main chat interface
│   │   │   │   ├── (dashboard)/    # Analytics & metrics
│   │   │   │   └── (settings)/     # Configuration UI
│   │   │   ├── components/
│   │   │   │   ├── ui/             # Primitive components
│   │   │   │   ├── chat/           # Chat-specific components
│   │   │   │   ├── agent/          # Agent visualization
│   │   │   │   └── layout/         # Layout components
│   │   │   ├── hooks/              # React hooks
│   │   │   ├── stores/             # Zustand state management
│   │   │   ├── services/           # API clients
│   │   │   ├── lib/                # Utilities
│   │   │   └── types/              # TypeScript types
│   │   └── package.json
│   │
│   └── api/                        # FastAPI backend
│       ├── src/
│       │   ├── main.py             # Application entry point
│       │   ├── config/             # Configuration management
│       │   ├── api/                # API layer
│       │   │   ├── router.py       # Root router
│       │   │   ├── deps.py         # Dependencies
│       │   │   ├── middleware/     # Auth, rate limiting, CORS
│       │   │   └── routes/         # Endpoint handlers
│       │   ├── core/               # ★ Agent Engine
│       │   │   ├── agent.py        # Orchestrator
│       │   │   ├── planner.py      # Task decomposition
│       │   │   ├── reasoner.py     # Reasoning engine
│       │   │   ├── executor.py     # Tool execution
│       │   │   ├── reflector.py    # Self-reflection
│       │   │   ├── router.py       # Intent classification
│       │   │   └── guardrails.py   # Safety filters
│       │   ├── providers/          # LLM providers
│       │   ├── memory/             # Memory systems
│       │   ├── tools/              # Tool implementations
│       │   ├── multi_agent/        # Multi-agent orchestration
│       │   ├── eval/               # Evaluation & metrics
│       │   └── models/             # Pydantic schemas
│       └── pyproject.toml
│
├── packages/
│   ├── shared-types/               # Shared TypeScript types
│   └── ui-kit/                     # Reusable UI components
│
├── infra/
│   ├── docker/
│   │   ├── Dockerfile.api
│   │   ├── Dockerfile.web
│   │   └── docker-compose.yml
│   └── k8s/                        # Kubernetes manifests
│
├── scripts/
│   ├── seed.py                     # Database seeding
│   └── migrate.py                  # Database migrations
│
├── tests/                          # Test suite
├── turbo.json                      # Turborepo configuration
├── .env.example                    # Environment template
└── README.md
```

## 📖 API Documentation

### Chat Endpoints

#### POST `/api/v1/chat/completions`
Send a message to the agent.

```json
{
  "message": "What's the weather in Tokyo?",
  "agent_id": "default",
  "provider": "openai",
  "model": "gpt-4-turbo",
  "stream": true
}
```

#### GET `/api/v1/chat/history/{session_id}`
Retrieve conversation history.

### Agent Endpoints

#### GET `/api/v1/agents`
List all available agents.

#### POST `/api/v1/agents`
Create a new agent with custom configuration.

#### PUT `/api/v1/agents/{agent_id}`
Update agent configuration.

#### DELETE `/api/v1/agents/{agent_id}`
Delete an agent.

### Provider Endpoints

#### GET `/api/v1/providers`
List configured providers.

#### POST `/api/v1/providers/test`
Test provider connectivity.

### Tool Endpoints

#### GET `/api/v1/tools`
List available tools.

#### POST `/api/v1/tools/register`
Register a custom tool.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_agent.py

# Run frontend tests
cd apps/web && npm test
```

## 🎯 Usage Examples

### Basic Chat

```python
from src.core.agent import Agent
from src.providers.openai import OpenAIProvider

provider = OpenAIProvider(api_key="sk-...")
agent = Agent(provider=provider)

response = await agent.chat("Help me write a Python function to sort a list")
print(response.content)
```

### Multi-Step Task

```python
from src.core.agent import Agent
from src.memory.long_term import LongTermMemory

memory = LongTermMemory(vector_store="qdrant")
agent = Agent(memory=memory, enable_reflection=True)

response = await agent.chat(
    "Research the latest AI trends and summarize them in 3 bullet points"
)
print(response.steps)  # Shows planning steps
print(response.reflection)  # Shows self-evaluation
```

### Custom Tool

```python
from src.tools.base import BaseTool, tool

@tool
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    # Implementation here
    return f"Weather in {city}: Sunny, 25°C"

agent.register_tool(get_weather)
```

## 📈 Monitoring & Evaluation

The agent includes built-in evaluation metrics:

- **Task Success Rate**: Percentage of successfully completed tasks
- **Average Steps**: Mean number of steps per task
- **Token Usage**: Total tokens consumed
- **Latency**: Response time percentiles
- **Cost**: Estimated cost per provider

Access the dashboard at `http://localhost:3000/dashboard`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Inspired by LangChain, AutoGen, and CrewAI
- Built with ❤️ using FastAPI and Next.js
