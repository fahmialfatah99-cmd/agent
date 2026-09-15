# Super Intelligent Agent

Lebih canggih dari OpenClaw dan Hermes Agent - Agent AI dengan kemampuan Planning, Reasoning, Execution, dan Reflection.

## 🏗️ Arsitektur

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                     │
│              Tailwind + Framer Motion + shadcn/ui           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (FastAPI)                    │
│                  WebSocket Support for Streaming            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Agent Core Loop                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Planner  │→ │ Reasoner │→ │ Executor │→ │ Reflector│    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│    Memory     │   │    Tools      │   │  Providers    │
│  Short/Long   │   │   Registry    │   │ Multi-LLM     │
└───────────────┘   └───────────────┘   └───────────────┘
```

## 🚀 Fitur Utama

### 1. **Multi-Provider LLM**
- ✅ OpenAI (GPT-4, GPT-3.5)
- ✅ Anthropic (Claude)
- ✅ Google (Gemini)
- ✅ Ollama (Local models)
- ✅ Easy to extend dengan provider custom

### 2. **Agent Core (Planner → Reasoner → Executor → Reflector)**
- **Planner**: Memecah goal kompleks menjadi langkah-langkah terstruktur
- **Reasoner**: Analisis mendalam dengan chain-of-thought
- **Executor**: Eksekusi tool dan action dengan error handling
- **Reflector**: Self-reflection dan continuous improvement

### 3. **Memory System**
- Short-term memory (working memory)
- Long-term memory (dengan vector embeddings)
- Conversation memory
- Consolidation mechanism

### 4. **Tool System**
- Registry-based tool management
- Auto-discovery
- Function wrapping decorator
- Built-in tools: search, calculate, time, dll.

### 5. **Real-time Streaming**
- WebSocket support untuk live updates
- Event-driven architecture
- Progress tracking

## 📁 Struktur Project

```
super-intelligent-agent/
├── apps/
│   ├── api/              # FastAPI backend
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── services/
│   │   └── requirements.txt
│   └── web/              # Next.js frontend
│       ├── components/
│       ├── pages/
│       └── package.json
├── packages/
│   ├── core/             # Core agent logic
│   │   ├── providers/    # LLM providers
│   │   ├── agent/        # Planner, Reasoner, Executor, Reflector
│   │   ├── memory/       # Memory systems
│   │   └── tools/        # Tool registry
│   ├── shared/           # Shared types & config
│   └── tools/            # Additional tools
├── infra/
│   ├── docker/           # Docker configuration
│   └── k8s/              # Kubernetes manifests
├── scripts/              # Utility scripts
└── tests/                # Test suite
```

## 🛠️ Tech Stack

### Backend
- Python 3.12+
- FastAPI
- Pydantic v2
- httpx (async HTTP)

### Frontend
- Next.js 15
- TypeScript
- Tailwind CSS
- Framer Motion
- shadcn/ui

### Database & Storage
- PostgreSQL (relational data)
- Qdrant (vector database)
- Redis (caching & sessions)

### Infrastructure
- Docker & Docker Compose
- Kubernetes ready
- Deployable ke Fly.io / Railway / Vercel

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone <repository>
cd super-intelligent-agent

# Install backend dependencies
pip install -r apps/api/requirements.txt

# Install frontend dependencies
cd apps/web && npm install
```

### 2. Environment Setup

Buat file `.env`:
```bash
LLM_API_KEY=your_api_key_here
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agent_db
REDIS_URL=redis://localhost:6379
```

### 3. Run with Docker (Recommended)

```bash
docker-compose -f infra/docker/docker-compose.yml up -d
```

### 4. Run Manually

**Backend:**
```bash
cd apps/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd apps/web
npm run dev
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/providers/configure` | Configure LLM provider |
| POST | `/agents/create` | Create new agent |
| POST | `/agents/{id}/run` | Run agent with goal |
| GET | `/agents/{id}/status` | Get agent status |
| POST | `/agents/{id}/reset` | Reset agent |
| DELETE | `/agents/{id}` | Delete agent |
| GET | `/tools/list` | List available tools |
| WS | `/ws/agents/{id}` | WebSocket streaming |

## 💡 Contoh Penggunaan

### Via API

```python
import requests

# Configure provider
requests.post("http://localhost:8000/providers/configure", json={
    "provider_type": "openai",
    "api_key": "sk-...",
    "model": "gpt-4"
})

# Create agent
requests.post("http://localhost:8000/agents/create?agent_id=my-agent", json={
    "provider_type": "openai",
    "model": "gpt-4"
})

# Run agent
response = requests.post("http://localhost:8000/agents/my-agent/run", json={
    "goal": "Research about quantum computing and summarize key concepts",
    "context": "Focus on practical applications"
})

print(response.json())
```

### Via Python SDK (Coming Soon)

```python
from super_agent import Agent, ProviderType

agent = Agent(
    provider_type=ProviderType.OPENAI,
    model="gpt-4",
    enable_reflection=True
)

result = await agent.run(
    goal="Analyze market trends for AI startups",
    context="Focus on Southeast Asia region"
)

print(result.plan)
print(result.execution_history)
```

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=packages/core
```

## 📊 Monitoring & Evaluation

- Built-in reflection system untuk self-improvement
- Execution history tracking
- Memory statistics
- Performance metrics

## 🔐 Security

- API key management via environment variables
- CORS configuration
- Input validation dengan Pydantic
- Rate limiting (to be implemented)

## 🤝 Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Inspired by ReAct paper (Reasoning + Acting)
- Concepts from Reflexion framework
- Architecture patterns from modern AI agents

---

**Built with ❤️ by Super Intelligent Agent Team**
