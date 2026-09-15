"""
Main entry point untuk menjalankan Telegram Bot
Jalankan dengan: python -m src.scripts.run_telegram_bot
"""
import asyncio
import logging
from src.services.telegram_bot import create_telegram_bot
from src.core.agent import AgentLoop
from src.config.settings import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function untuk menjalankan Telegram Bot"""
    
    logger.info("=" * 50)
    logger.info("🤖 Super Intelligent Agent - Telegram Bot")
    logger.info("=" * 50)
    
    # 1. Inisialisasi Agent Core
    logger.info("\n🧠 Initializing Agent Core...")
    
    try:
        agent = AgentLoop(
            provider_name=settings.DEFAULT_PROVIDER,
            model_name=settings.DEFAULT_MODEL,
            enable_tools=True,
            enable_memory=True,
        )
        logger.info("✅ Agent Core initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ Agent Core initialization failed: {e}")
        logger.info("Running in demo mode (without full agent capabilities)")
        agent = None
    
    # 2. Buat Telegram Bot Service
    logger.info("\n📱 Creating Telegram Bot Service...")
    
    bot_service = create_telegram_bot(agent=agent)
    
    if not bot_service:
        logger.error(
            "\n❌ Failed to create Telegram Bot.\n"
            "Please set TELEGRAM_BOT_TOKEN environment variable.\n\n"
            "Cara mendapatkan token:\n"
            "1. Buka Telegram dan cari @BotFather\n"
            "2. Kirim /newbot\n"
            "3. Ikuti instruksi untuk membuat bot\n"
            "4. Copy token yang diberikan\n"
            "5. Set sebagai environment variable:\n"
            "   export TELEGRAM_BOT_TOKEN='your_token_here'\n"
        )
        return
    
    logger.info("✅ Telegram Bot Service created")
    
    # 3. Jalankan Bot
    logger.info("\n🚀 Starting Telegram Bot...\n")
    logger.info("Bot commands:")
    logger.info("  /start  - Welcome message")
    logger.info("  /help   - Show help")
    logger.info("  /status - Check agent status")
    logger.info("  /reset  - Reset conversation")
    logger.info("\nPress Ctrl+C to stop the bot.\n")
    
    try:
        await bot_service.run()
    except KeyboardInterrupt:
        logger.info("\n\n⏹️  Stopping bot...")
        await bot_service.stop()
        logger.info("👋 Bot stopped successfully")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}", exc_info=True)
        if bot_service:
            await bot_service.stop()


if __name__ == "__main__":
    asyncio.run(main())
