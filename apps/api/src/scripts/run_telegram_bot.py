"""
Main entry point untuk menjalankan Telegram Bot
Jalankan dengan: python -m src.scripts.run_telegram_bot
"""
import asyncio
import logging
import os
import sys

# Add packages to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'packages')))

from src.services.telegram_bot import create_telegram_bot
from src.config.settings import settings
from core.agent import AgentLoop, AgentLoopConfig
from core.providers import ProviderType, ProviderConfig, create_provider

# Register tools (Linux system + opencode-equivalent) ke global registry
import core.tools.linux_agent  # noqa: F401  (auto-register 7 tools)
import core.tools.opencode_tools  # noqa: F401  (auto-register 4 tools)

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
        provider_config = ProviderConfig(
            provider_type=ProviderType.OPENAI,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL or "http://127.0.0.1:20128/v1",
            model=settings.DEFAULT_MODEL or "antigravity",
            temperature=0.7,
            max_tokens=2048,
        )
        provider = create_provider(provider_config.provider_type, provider_config)
        await provider.initialize()
        from core.tools import registry
        agent = AgentLoop(
            provider=provider,
            tool_registry=registry,
            config=AgentLoopConfig(
                enable_reflection=True,
                max_iterations=10,
            ),
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
