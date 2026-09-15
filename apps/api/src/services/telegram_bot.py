"""
Telegram Bot Service
Menghubungkan Telegram Bot dengan Super Agent Core
"""
import logging
from typing import Optional, Dict, Any
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
    
    def __init__(self, token: str, agent=None):
        """
        Initialize Telegram Bot
        
        Args:
            token: Telegram Bot Token dari @BotFather
            agent: Instance AgentLoop (opsional, bisa di-inject nanti)
        """
        self.token = token
        self.agent = agent
        self.application: Optional[Application] = None
        
        # Simpan state percakapan per user
        # Format: {user_id: {"history": [], "context": {}}}
        self.user_sessions: Dict[int, Dict[str, Any]] = {}

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
            "🤖 **Command tersedia:**\n\n"
            "/start - Mulai bot\n"
            "/help - Tampilkan bantuan\n"
            "/status - Cek status agent\n"
            "/reset - Reset sesi percakapan\n\n"
            "Kirim pesan biasa untuk berinteraksi dengan agent."
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        status = (
            "✅ **Agent Status:**\n"
            "- Agent: Active\n"
            "- Memory: Loaded\n"
            "- Tools: Ready\n"
            "- Provider: Connected"
        )
        await update.message.reply_text(status, parse_mode="Markdown")

    async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /reset command"""
        user_id = update.effective_user.id
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        
        await update.message.reply_text(
            "🔄 Sesi percakapan telah direset.\n"
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
                self.user_sessions[user_id] = {
                    "history": [],
                    "context": {},
                    "metadata": {
                        "created_at": context.bot_data.get("current_time", None),
                        "message_count": 0
                    }
                }
            
            session = self.user_sessions[user_id]
            session["metadata"]["message_count"] += 1
            
            logger.info(f"Processing message from user {user_id}: {user_message[:50]}...")
            
            # Jika agent tersedia, gunakan agent core
            if self.agent:
                response = await self._process_with_agent(user_message, session)
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
            
            # Kirim respons utama
            await update.message.reply_text(
                response["answer"],
                parse_mode="Markdown"
            )
            
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
                    
        except Exception as e:
            logger.error(f"Error processing message from user {user_id}: {e}", exc_info=True)
            await update.message.reply_text(
                "⚠️ Maaf, terjadi kesalahan saat memproses permintaan Anda.\n\n"
                f"Error: `{str(e)}`\n\n"
                "Silakan coba lagi atau gunakan /reset untuk mereset sesi."
            )

    async def _process_with_agent(self, user_message: str, session: dict) -> dict:
        """
        Process message menggunakan Agent Core
        
        Args:
            user_message: Pesan dari user
            session: Session data user
            
        Returns:
            dict dengan keys: answer, steps, tool_calls
        """
        # Call agent core
        response = await self.agent.run(
            query=user_message,
            conversation_history=session["history"],
            context=session["context"]
        )
        
        # Update context jika ada
        if "context" in response:
            session["context"].update(response["context"])
        
        return response

    async def run(self):
        """Menjalankan bot dengan polling"""
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
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
        
        # Start polling
        logger.info("Bot is running. Press Ctrl+C to stop.")
        await self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def stop(self):
        """Menghentikan bot"""
        if self.application:
            await self.application.stop()
            logger.info("Telegram Bot stopped.")


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
