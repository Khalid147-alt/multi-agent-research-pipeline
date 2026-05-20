import asyncio
import logging
from datetime import datetime
from typing import Awaitable, Callable

from crewai.events import (
    AgentExecutionCompletedEvent,
    AgentExecutionStartedEvent,
    BaseEventListener,
    ToolUsageFinishedEvent,
    ToolUsageStartedEvent,
    crewai_event_bus,
)

logger = logging.getLogger(__name__)

# Map agent roles (as defined in agents/*.py) to a stable display label + ordinal
# for percent-complete calculation.
_AGENT_PROGRESS = {
    "Senior Research Analyst": ("Researcher", 0),
    "Critical Data Analyst": ("Analyst", 1),
    "Fact Checker": ("Fact Checker", 2),
    "Technical Writer": ("Writer", 3),
}

BroadcastFn = Callable[[str, dict], Awaitable[None]]


class ProgressListener(BaseEventListener):
    """Subscribes to crewai_event_bus and rebroadcasts agent/tool events
    over the per-session WebSocket using the wire format declared in AGENTS.md.

    Instantiate once per session. Call .cleanup() in a finally block so handlers
    don't leak across sessions.
    """

    def __init__(self, session_id: str, broadcast: BroadcastFn, loop: asyncio.AbstractEventLoop):
        self.session_id = session_id
        self.broadcast = broadcast
        self.loop = loop
        self._handlers: list[tuple[type, Callable]] = []
        super().__init__()

    def setup_listeners(self, bus):
        # We register lambdas so we can record (event_type, handler) tuples for
        # later .off(). The bus's .on() decorator returns the handler unchanged.
        def register(event_type, handler):
            bus.on(event_type)(handler)
            self._handlers.append((event_type, handler))

        def on_agent_start(_source, event: AgentExecutionStartedEvent):
            role = getattr(event.agent, "role", "")
            label, idx = _AGENT_PROGRESS.get(role, (role, 0))
            self._emit({
                "type": "agent_start",
                "agent": label,
                "task": str(getattr(event, "task_prompt", "") or "")[:120],
                "percent": int((idx / 4) * 100),
                "timestamp": datetime.now().isoformat(),
            })

        def on_agent_finish(_source, event: AgentExecutionCompletedEvent):
            role = getattr(event.agent, "role", "")
            label, idx = _AGENT_PROGRESS.get(role, (role, 0))
            self._emit({
                "type": "agent_finish",
                "agent": label,
                "preview": str(getattr(event, "output", "") or "")[:150],
                "percent": int(((idx + 1) / 4) * 100),
                "timestamp": datetime.now().isoformat(),
            })

        def on_tool_start(_source, event: ToolUsageStartedEvent):
            role = getattr(event, "agent_role", "") or ""
            label, _ = _AGENT_PROGRESS.get(role, (role, 0))
            self._emit({
                "type": "tool_use",
                "agent": label,
                "tool": getattr(event, "tool_name", "") or "",
                "preview": str(getattr(event, "tool_args", "") or "")[:80],
                "timestamp": datetime.now().isoformat(),
            })

        def on_tool_end(_source, event: ToolUsageFinishedEvent):
            role = getattr(event, "agent_role", "") or ""
            label, _ = _AGENT_PROGRESS.get(role, (role, 0))
            self._emit({
                "type": "tool_result",
                "agent": label,
                "tool": getattr(event, "tool_name", "") or "",
                "preview": str(getattr(event, "output", "") or "")[:120],
                "timestamp": datetime.now().isoformat(),
            })

        register(AgentExecutionStartedEvent, on_agent_start)
        register(AgentExecutionCompletedEvent, on_agent_finish)
        register(ToolUsageStartedEvent, on_tool_start)
        register(ToolUsageFinishedEvent, on_tool_end)

    def _emit(self, event: dict):
        # crewai event handlers run on the worker thread that's executing
        # crew.kickoff(), so we hop back to the FastAPI event loop.
        try:
            asyncio.run_coroutine_threadsafe(
                self.broadcast(self.session_id, event), self.loop
            )
        except Exception as exc:
            logger.warning("ProgressListener emit failed: %s", exc)

    def cleanup(self):
        for event_type, handler in self._handlers:
            try:
                handlers = crewai_event_bus._handlers.get(event_type, [])
                if handler in handlers:
                    handlers.remove(handler)
            except Exception as exc:
                logger.debug("listener cleanup: %s", exc)
        self._handlers.clear()
