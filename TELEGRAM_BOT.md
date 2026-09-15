# 🤖 Telegram Bot Integration

Super Intelligent Agent sekarang **bisa disambungkan ke Telegram Bot**! 

## 📋 Fitur Telegram Bot

Bot Telegram yang terintegrasi memiliki fitur:

### Commands Tersedia:
- `/start` - Welcome message dan pengenalan bot
- `/help` - Menampilkan daftar command
- `/status` - Cek status agent (active, memory loaded, tools ready)
- `/reset` - Reset sesi percakapan user
- **Pesan biasa** - Interaksi langsung dengan AI Agent

### Features:
✅ **Multi-user support** - Setiap user punya session terpisah  
✅ **Conversation history** - Bot mengingat konteks percakapan  
✅ **Agent integration** - Terhubung ke Planner → Reasoner → Executor → Reflector  
✅ **Tool execution** - Bisa menjalankan tools (search, calculate, dll)  
✅ **Thinking process** - Menampilkan proses berpikir sebagai spoiler  
✅ **Error handling** - Graceful error handling dengan user-friendly messages  

---

## 🚀 Cara Setup

### 1. Buat Bot di Telegram

1. Buka Telegram dan cari **@BotFather**
2. Kirim command `/newbot`
3. Ikuti instruksi:
   - Beri nama bot (contoh: `SuperAgent Bot`)
   - Beri username (contoh: `super_intelligent_bot`)
4. **Simpan token** yang diberikan (format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Set Environment Variable

Buat file `.env` di root project:

```bash
cp .env.example .env
```

Edit `.env` dan tambahkan token:

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# API Keys (minimal satu)
OPENAI_API_KEY=sk-your-openai-api-key
# atau
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
```

### 3. Install Dependencies

```bash
cd apps/api
pip install -r requirements.txt
```

Package `python-telegram-bot` sudah ditambahkan ke requirements.txt.

### 4. Jalankan Bot

**Option A: Jalankan hanya Telegram Bot**
```bash
cd apps/api
python -m src.scripts.run_telegram_bot
```

**Option B: Jalankan bersama API Server**
```bash
# Terminal 1: API Server
cd apps/api
uvicorn src.main:app --reload --port 8000

# Terminal 2: Telegram Bot
cd apps/api
python -m src.scripts.run_telegram_bot
```

---

## 💡 Contoh Penggunaan

### User mengirim pesan:
```
User: Cari informasi terbaru tentang AI agents
```

### Bot akan:
1. Menerima pesan
2. Mengirim ke Agent Core
3. Agent memproses dengan:
   - **Planner**: Break down task
   - **Reasoner**: Chain-of-thought analysis
   - **Executor**: Jalankan search tool
   - **Reflector**: Evaluasi hasil
4. Mengirim response ke Telegram
5. (Opsional) Mengirim thinking process sebagai spoiler

### Output di Telegram:
```
🤖 Berikut informasi terbaru tentang AI agents:

[Hasil pencarian dan analisis lengkap]

||🧠 Proses berpikir:
1. Menganalisis query user
2. Menggunakan web_search tool
3. Mengumpulkan informasi dari 5 sumber
4. Menyintesis jawaban||
```

---

## 🛠️ Kustomisasi

### Ubah Welcome Message
Edit file `apps/api/src/services/telegram_bot.py`, method `start_command()`:

```python
async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_message = "Custom message Anda di sini"
    await update.message.reply_html(welcome_message)
```

### Tambah Command Baru
Tambahkan handler di method `run()`:

```python
self.application.add_handler(CommandHandler("custom", self.custom_command))
```

Lalu buat method handler:

```python
async def custom_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Custom response")
```

### Session Management
Session user disimpan di memory (`self.user_sessions`). 
Untuk production, ganti dengan database:

```python
# Ganti in-memory storage dengan Redis/PostgreSQL
from src.memory.long_term import LongTermMemory

session = await self.memory.get_session(user_id)
```

---

## 🔒 Security Best Practices

1. **Jangan commit token** ke Git
2. Gunakan **webhook** untuk production (bukan polling)
3. Implementasi **rate limiting** per user
4. Validasi **user ID** untuk akses tertentu
5. Gunakan **HTTPS** untuk webhook

---

## 🐳 Deploy dengan Docker

Update `docker-compose.yml` untuk include Telegram Bot:

```yaml
services:
  api:
    # ... existing config
  
  telegram-bot:
    build:
      context: .
      dockerfile: infra/docker/Dockerfile.api
    command: python -m src.scripts.run_telegram_bot
    env_file:
      - .env
    depends_on:
      - api
      - redis
      - postgres
```

---

## 📊 Arsitektur

```
┌─────────────┐
│   Telegram  │
│    Users    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  TelegramBotService │
│  - handle_message   │
│  - user_sessions    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│     AgentLoop       │
│  - Planner          │
│  - Reasoner         │
│  - Executor         │
│  - Reflector        │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   Tools & Memory    │
│  - Web Search       │
│  - Code Execution   │
│  - Vector DB        │
└─────────────────────┘
```

---

## ❓ Troubleshooting

### Bot tidak merespon
- Cek token di `.env`
- Pastikan bot sudah di-start di @BotFather
- Cek log error

### Error "TELEGRAM_BOT_TOKEN tidak ditemukan"
```bash
export TELEGRAM_BOT_TOKEN='your_token_here'
```

### Agent tidak berfungsi
- Cek API keys (OpenAI/Anthropic/Google)
- Lihat log untuk detail error
- Jalankan dalam demo mode (tanpa agent core)

---

## 🎯 Next Steps

1. ✅ **Setup bot** - Dapatkan token dari @BotFather
2. ✅ **Test locally** - Jalankan dan kirim pesan
3. 🔲 **Add custom tools** - Integrasikan dengan tools Anda
4. 🔲 **Deploy to production** - Gunakan webhook + HTTPS
5. 🔲 **Add analytics** - Track usage & performance

**Selamat! Bot Telegram Anda siap digunakan!** 🎉
