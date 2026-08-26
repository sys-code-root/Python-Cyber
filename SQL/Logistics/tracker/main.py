import asyncio
from faststream.rabbit import TestRabbitBroker

import config
from consumers import broker, app, logger

async def main():
    async with TestRabbitBroker(broker):
        await app.run()

if __name__ == "__main__":
    logger.info("Initializing Headless Systems Context...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Process terminated clean by operator command.")