"""
Telegram Bot Service
Menghubungkan Telegram Bot dengan Super Agent Core
"""
import asyncio
import json
import logging
import os
import signal
from typing import Optional, Dict, Any, List
from telegram import Update, ForceReply
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

logger = logging.getLogger(__name__)

# Import agent core (akan di-setup nanti)
# from src.core.agent import AgentLoop
# from src.config.settings import settings


class TelegramBotService:
    """Service untuk menjalankan Telegram Bot yang terhubung ke Agent Core"""
    
    def __init__(self, token: str, agent=None, memory_dir: Optional[str] = None):
        """
        Initialize Telegram Bot
        
        Args:
            token: Telegram Bot Token dari @BotFather
            agent: Instance AgentLoop (opsional, bisa di-inject nanti)
            memory_dir: Direktori untuk persistensi memory per-user
        """
        self.token = token
        self.agent = agent
        self.application: Optional[Application] = None
        self.memory_dir = memory_dir or os.path.expanduser("~/.agent/memory")
        
        # Simpan state percakapan per user
        # Format: {user_id: {"history": [], "context": {}}}
        self.user_sessions: Dict[int, Dict[str, Any]] = {}
        os.makedirs(self.memory_dir, exist_ok=True)

    def _user_session_path(self, user_id: int) -> str:
        """Path file session untuk sebuah user."""
        return os.path.join(self.memory_dir, f"user_{user_id}.json")

    def _create_user_session(self, user_id: int) -> Dict[str, Any]:
        """Membuat session baru untuk user, load memory persisten bila ada."""
        from core.memory import MemoryManager
        memory_manager = MemoryManager()
        session_path = self._user_session_path(user_id)
        data = {}
        if os.path.exists(session_path):
            try:
                with open(session_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("memory_entries"):
                    memory_manager.long_term.load_from_dict({"entries": data["memory_entries"]})
            except Exception:
                data = {}

        return {
            "history": data.get("history", []),
            "context": data.get("context", {}),
            "metadata": {
                "created_at": data.get("metadata", {}).get("created_at"),
                "message_count": data.get("metadata", {}).get("message_count", 0),
            },
            "memory_manager": memory_manager,
        }

    def _save_user_session(self, user_id: int, session: Dict[str, Any]) -> None:
        """Menyimpan session + memory user ke file JSON."""
        try:
            persist_mgr = session.get("memory_manager")
            memory_entries = []
            if persist_mgr:
                memory_entries = persist_mgr.long_term.to_dict().get("entries", [])

            with open(self._user_session_path(user_id), "w", encoding="utf-8") as f:
                json.dump({
                    "history": session.get("history", [])[-40:],
                    "context": session.get("context", {}),
                    "metadata": session.get("metadata", {}),
                    "memory_entries": memory_entries,
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        welcome_message = (
            f"Hi {user.mention_html()}! 👋\n\n"
            f"Saya adalah **Super Intelligent Agent**.\n"
            f"Saya bisa membantu Anda dengan:\n"
            f"- Menjawab pertanyaan kompleks\n"
            f"- Melakukan pencarian web\n"
            f"- Eksekusi kode\n"
            f"- Analisis data\n\n"
            f"Ketik apapun untuk memulai!"
        )
        await update.message.reply_html(
            welcome_message,
            reply_markup=ForceReply(selective=True),
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "🤖 *Command tersedia:*\n\n"
            "/start - Mulai bot\n"
            "/help - Tampilkan bantuan\n"
            "/status - Cek status agent & tools\n"
            "/reset - Reset sesi percakapan\n"
            "/remember <fakta> - Simpan fakta ke memori jangka panjang\n"
            "/recall <kata kunci> - Cari memori yang tersimpan\n\n"
            "*Kemampuan tambahan:*\n"
            "Saya bisa membaca/menulis/mengedit file, menjalankan perintah shell, "
            "mencari kode, mengelola proses, dan fetch web.\n\n"
            "Contoh: \"baca file ~/agent/README.md\", \"cari fungsi calculate di src\", "
            "\"jalankan ls -la di /home\", \"fetch https://example.com\"."
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def remember_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /remember command"""
        user_id = update.effective_user.id
        text = update.message.text.replace("/remember", "", 1).strip()
        if not text:
            await update.message.reply_text(
                "Gunakan: /remember <fakta yang ingin disimpan>"
            )
            return

        session = self.user_sessions.get(user_id)
        if not session:
            session = self._create_user_session(user_id)
            self.user_sessions[user_id] = session

        memory_manager = session.get("memory_manager")
        if memory_manager:
            memory_manager.remember(text, importance=0.7)
            self._save_user_session(user_id, session)

        self.user_sessions[user_id]["history"].append(
            {"role": "user", "content": text}
        )
        await update.message.reply_text(
            f"🧠 Fakta disimpan ke memori jangka panjang:\n\n_{text}_"
        )

    async def recall_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /recall command"""
        user_id = update.effective_user.id
        query = update.message.text.replace("/recall", "", 1).strip()

        session = self.user_sessions.get(user_id)
        if not session:
            session = self._create_user_session(user_id)
            self.user_sessions[user_id] = session

        memory_manager = session.get("memory_manager")
        if not memory_manager:
            await update.message.reply_text("Memori tidak tersedia.")
            return

        if not query:
            entries = memory_manager.long_term.search_by_importance(
                min_importance=0.3, limit=10
            )
        else:
            entries = memory_manager.recall(query, limit=10)

        if not entries:
            await update.message.reply_text("🔍 Tidak ada memori yang cocok.")
            return

        lines = []
        for i, entry in enumerate(entries, 1):
            content = str(entry.content).replace("\n", " ")
            imp = entry.importance
            lines.append(f"{i}. {content} (penting: {imp:.1f})")
        await update.message.reply_text(
            f"🧠 *Memori ditemukan:*\n\n" + "\n".join(lines),
            parse_mode="Markdown",
        )

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        tools = []
        tool_names = "tidak tersedia"
        try:
            from core.tools import registry
            tools = registry.list_tools()
            tool_names = ", ".join(t.definition.name for t in tools)
        except Exception:
            pass

        status = (
            f"✅ *Agent Status:*\n"
            f"- Agent: Active\n"
            f"- Memory: Persisted\n"
            f"- Tools ({len(tools)}): {tool_names}\n"
            f"- Provider: Connected"
        )
        await update.message.reply_text(status, parse_mode="Markdown")

    async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /reset command"""
        user_id = update.effective_user.id
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        # Hapus file session persisten
        try:
            os.remove(self._user_session_path(user_id))
        except (OSError, FileNotFoundError):
            pass
        
        await update.message.reply_text(
            "🔄 Sesi percakapan telah direset (riwayat & memori sementara dibersihkan).\n"
            "Memori jangka panjang tidak dihapus — gunakan /recall untuk melihatnya.\n"
            "Silakan kirim pesan baru untuk memulai."
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle pesan biasa dari user
        
        Alur:
        1. Terima pesan dari user
        2. Ambil/buat session user
        3. Kirim ke Agent Core untuk diproses
        4. Kembalikan response ke Telegram
        """
        user_id = update.effective_user.id
        user_message = update.message.text
        
        if not user_message:
            return

        # Typing indicator
        await update.message.chat.send_action(action="typing")

        try:
            # Dapatkan atau buat session untuk user ini
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = self._create_user_session(user_id)
            
            session = self.user_sessions[user_id]
            session["metadata"]["message_count"] += 1
            
            # Persist memory setelah setiap pesan agar aman dari restart
            self._save_user_session(user_id, session)
            
            logger.info(f"Processing message from user {user_id}: {user_message[:50]}...")
            
            # Jika agent tersedia, gunakan agent core
            if self.agent:
                response = await asyncio.wait_for(
                    self._process_with_agent(user_message, session),
                    timeout=120.0
                )
            else:
                # Fallback response jika agent belum di-setup
                response = {
                    "answer": f"🤖 [Demo Mode]\n\n"
                              f"Pesan Anda: {user_message}\n\n"
                              f"Agent core belum diinisialisasi.\n"
                              f"Setup agent untuk respons penuh.",
                    "steps": ["Demo mode active"],
                    "tool_calls": []
                }
            
            # Update history
            session["history"].append({"role": "user", "content": user_message})
            session["history"].append({"role": "assistant", "content": response["answer"]})
            
            # Batasi history agar tidak terlalu panjang (max 20 messages)
            if len(session["history"]) > 40:
                session["history"] = session["history"][-40:]
            
            # Kirim respons utama (teks biasa — hindari parse_mode yang bisa gagal)
            await update.message.reply_text(response["answer"])

            # Jika ada intermediate steps, kirim sebagai spoiler (thinking process)
            if response.get("steps") and len(response["steps"]) > 0:
                steps_text = "🧠 *Proses berpikir:*\n"
                for i, step in enumerate(response["steps"], 1):
                    step_content = str(step).replace("*", "\\*").replace("_", "\\_")
                    steps_text += f"{i}. {step_content}\n"
                
                # Kirim sebagai spoiler jika tidak terlalu panjang
                if len(steps_text) < 4000:
                    await update.message.reply_text(
                        f"||{steps_text}||",
                        parse_mode="MarkdownV2"
                    )
                    
        except asyncio.TimeoutError:
            logger.warning(f"Timeout processing message from user {user_id}")
            await update.message.reply_text(
                "⚠️ Permintaan terlalu lama diproses (timeout).\n"
                "Silakan coba lagi atau gunakan /reset untuk mereset sesi."
            )
        except Exception as e:
            logger.error(f"Error processing message from user {user_id}: {e}", exc_info=True)
            await update.message.reply_text(
                "⚠️ Maaf, terjadi kesalahan saat memproses permintaan Anda.\n"
                "Silakan coba lagi atau gunakan /reset untuk mereset sesi."
            )

    async def _process_with_agent(self, user_message: str, session: dict) -> dict:
        """
        Process message menggunakan ReAct tool-calling loop (setara opencode).
        
        Alur:
        1. Kirim pesan + definisi tools ke model
        2. Jika model meminta tool_call → eksekusi tool, beri hasil ke model
        3. Ulangi hingga model menjawab tanpa tool_call atau mencapai batas iterasi
        
        Returns:
            dict dengan keys: answer, steps, tool_calls
        """
        from core.providers import Message
        from core.tools import registry

        memory_context = self._collect_memory_context(session)

        system_prompt = (
            "Kamu adalah Super Intelligent Agent dengan akses ke sistem Linux "
            "(file, shell, proses, jaringan), pencarian kode, dan internet (web_fetch).\n\n"
            "Pedoman:\n"
            "- Jawab dalam bahasa Indonesia kecuali diminta lain.\n"
            "- Jika butuh fakta/operasi nyata, PAKAI tool yang tersedia, jangan berasumsi.\n"
            "- Untuk membaca/menulis/mengedit file, gunakan tool filesystem.\n"
            "- Untuk perintah shell, gunakan linux_shell_execute.\n"
            "- Ringkas dan langsung ke inti jawaban."
        )
        if memory_context:
            system_prompt += f"\n\nIngatan dari sesi sebelumnya:\n{memory_context}"

        messages: List[Any] = [Message(role="system", content=system_prompt)]
        for item in session.get("history", [])[-20:]:
            messages.append(
                Message(role=item.get("role", "user"), content=item.get("content", ""))
            )
        messages.append(Message(role="user", content=user_message))

        tool_schemas = self._build_tool_schemas(registry)

        max_rounds = 8
        used_tools: List[Dict[str, Any]] = []

        for _ in range(max_rounds):
            response = await asyncio.wait_for(
                self.agent.provider.chat_completion(
                    messages,
                    temperature=0.3,
                    tools=tool_schemas,
                    tool_choice="auto",
                ),
                timeout=90.0,
            )

            message = response.choices[0]["message"]
            tool_calls = message.get("tool_calls")

            if not tool_calls:
                return {
                    "answer": message.get("content") or "",
                    "steps": used_tools,
                    "tool_calls": used_tools,
                }

            # Model ingin memakai tool → eksekusi
            messages.append(
                Message(
                    role="assistant",
                    content=message.get("content") or "",
                    tool_calls=tool_calls,
                )
            )

            for tc in tool_calls:
                fn = tc.get("function", {})
                name = fn.get("name", "")
                try:
                    args = json.loads(fn.get("arguments", "{}") or "{}")
                except json.JSONDecodeError:
                    args = {}
                args = args if isinstance(args, dict) else {}

                logger.info(f"Tool call: {name}({args})")
                result = await registry.execute_tool(name, **args)

                tool_result_text = ""
                if result.success:
                    tool_result_text = json.dumps(
                        result.output, ensure_ascii=False, default=str
                    )
                else:
                    tool_result_text = f"ERROR: {result.error}"

                tool_result_text = tool_result_text[:8000]

                used_tools.append({"name": name, "args": args, "output": tool_result_text[:500]})
                messages.append(
                    Message(
                        role="tool",
                        content=tool_result_text,
                        tool_call_id=tc.get("id", ""),
                    )
                )

        return {
            "answer": "⚠️ Proses mencapai batas iterasi tool. "
                      "Silakan coba permintaan yang lebih spesifik.",
            "steps": used_tools,
            "tool_calls": used_tools,
        }

    def _build_tool_schemas(self, registry) -> List[Dict[str, Any]]:
        """Convert registry tool definitions to OpenAI function-calling schemas."""
        schemas = []
        for definition in registry.list_tools():
            props = {}
            required = []
            for p in definition.parameters:
                props[p.name] = {
                    "type": p.type,
                    "description": p.description,
                    **(
                        {"enum": p.enum}
                        if p.enum
                        else {}
                    ),
                }
                if p.required:
                    required.append(p.name)
            schemas.append({
                "type": "function",
                "function": {
                    "name": definition.name,
                    "description": definition.description,
                    "parameters": {
                        "type": "object",
                        "properties": props,
                        "required": required,
                    },
                },
            })
        return schemas

    def _collect_memory_context(self, session: dict) -> str:
        """Collect persisted long-term memories for the user session."""
        memory_manager = session.get("memory_manager")
        if memory_manager is None:
            return ""
        important = memory_manager.long_term.search_by_importance(
            min_importance=0.6, limit=8
        )
        if not important:
            return ""
        return "\n".join(f"- {m.content}" for m in important)

    async def run(self):
        """Menjalankan bot dengan polling (async, kompatibel dengan asyncio.run)"""
        logger.info("Starting Telegram Bot...")
        
        self.application = (
            Application.builder()
            .token(self.token)
            .build()
        )
        
        # Register handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("reset", self.reset_command))
        self.application.add_handler(CommandHandler("remember", self.remember_command))
        self.application.add_handler(CommandHandler("recall", self.recall_command))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        # Async lifecycle (bukan run_polling yang bersifat blocking)
        self._stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self._stop_event.set)
            except (NotImplementedError, RuntimeError):
                pass
        
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES
        )
        
        logger.info("Bot is running. Press Ctrl+C to stop.")
        await self._stop_event.wait()
        
        # Graceful shutdown
        await self.stop()

    async def stop(self):
        """Menghentikan bot secara graceful"""
        if not self.application:
            return
        try:
            if self.application.updater.running:
                await self.application.updater.stop()
            if self.application.running:
                await self.application.stop()
            await self.application.shutdown()
            logger.info("Telegram Bot stopped.")
        except Exception as e:
            logger.error(f"Error while stopping bot: {e}")


def create_telegram_bot(agent=None) -> Optional[TelegramBotService]:
    """
    Factory function untuk membuat instance Telegram Bot
    
    Args:
        agent: Instance AgentLoop (opsional)
        
    Returns:
        TelegramBotService instance atau None jika token tidak ditemukan
    """
    # Import settings di sini untuk menghindari circular import
    try:
        from src.config.settings import settings
        token = settings.TELEGRAM_BOT_TOKEN
    except (ImportError, AttributeError):
        import os
        token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logger.warning(
            "TELEGRAM_BOT_TOKEN tidak ditemukan. "
            "Set environment variable TELEGRAM_BOT_TOKEN untuk mengaktifkan bot."
        )
        return None
    
    logger.info("Telegram Bot service created successfully.")
    return TelegramBotService(token=token, agent=agent)
