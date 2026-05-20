import asyncio
import logging
from datetime import datetime

from crewai import Crew, Process

from agents.analyst import build_analyst
from agents.fact_checker import build_fact_checker
from agents.researcher import build_researcher
from agents.writer import build_writer
from crew.callbacks import ProgressListener
from crew.tasks import build_tasks
from db.adapter import get_pool
from ws.manager import manager

logger = logging.getLogger(__name__)


async def run_research(session_id: str, topic: str):
    loop = asyncio.get_running_loop()
    listener = ProgressListener(session_id, manager.broadcast, loop)

    researcher = build_researcher()
    analyst = build_analyst()
    fact_checker = build_fact_checker()
    writer = build_writer()

    tasks = build_tasks(researcher, analyst, fact_checker, writer, topic)

    crew = Crew(
        agents=[researcher, analyst, fact_checker, writer],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    try:
        result = await asyncio.to_thread(crew.kickoff)

        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO reports (session_id, topic, content, created_at) "
                "VALUES ($1, $2, $3, $4)",
                session_id,
                topic,
                str(result),
                datetime.now().isoformat(),
            )
            await conn.execute(
                "UPDATE sessions SET status='complete' WHERE id=$1",
                session_id,
            )

        await manager.broadcast(
            session_id,
            {
                "type": "complete",
                "report_id": session_id,
                "timestamp": datetime.now().isoformat(),
            },
        )

    except Exception as e:
        logger.exception("run_research failed for session %s", session_id)
        await manager.broadcast(
            session_id,
            {
                "type": "error",
                "message": str(e),
                "recoverable": False,
            },
        )
        try:
            pool = get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE sessions SET status='failed' WHERE id=$1",
                    session_id,
                )
        except Exception:
            pass
    finally:
        listener.cleanup()
