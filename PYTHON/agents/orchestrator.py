"""
orchestrator.py — Agent orchestration, planner/executor ayrimi, tool routing
"""
import json
import time
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class AgentTask:
    id: str
    agent: str
    action: str
    params: dict = field(default_factory=dict)
    status: str = "pending"
    result: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class AgentOrchestrator:
    """
    Ajan orkestrasyonu:
    - Planlayici: is sirasini belirler
    - Yurutucu: her ajanin tool'unu cagirir
    - Geri bildirim: basari/basarisizlik kaydet
    """

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._tasks: List[AgentTask] = []
        self._feedback: Dict[str, List[dict]] = {}
        self._scoreboard: Dict[str, dict] = {}

    def register_tool(self, agent: str, tool: Callable):
        self._tools[agent] = tool

    def plan(self, symbol: str, context: dict) -> List[AgentTask]:
        """Ajan calisma sirasini planla."""
        plan = [
            AgentTask(id=f"{symbol}_E", agent="E", action="macro_regime", params={"symbol": symbol}),
            AgentTask(id=f"{symbol}_B", agent="B", action="technical_signal", params={"symbol": symbol}),
            AgentTask(id=f"{symbol}_C", agent="C", action="news_score", params={"symbol": symbol}),
            AgentTask(id=f"{symbol}_D", agent="D", action="risk_check", params={"symbol": symbol}),
            AgentTask(id=f"{symbol}_F", agent="F", action="anomaly_check", params={"symbol": symbol}),
            AgentTask(id=f"{symbol}_G", agent="G", action="memory_query", params={"symbol": symbol}),
            AgentTask(id=f"{symbol}_H", agent="H", action="backtest_metrics", params={"symbol": symbol}),
            AgentTask(id=f"{symbol}_A", agent="A", action="final_decision", params={"symbol": symbol, "context": context}),
        ]
        self._tasks.extend(plan)
        return plan

    def execute(self, task: AgentTask) -> dict:
        """Tek bir gorevi calistir."""
        tool = self._tools.get(task.agent)
        if not tool:
            task.status = "error"
            task.result = {"error": f"Tool not found for agent {task.agent}"}
            return task.result

        try:
            task.status = "running"
            result = tool(task.params)
            task.status = "completed"
            task.result = result
            task.completed_at = datetime.now(timezone.utc)
            self._record_feedback(task, success=True)
        except Exception as e:
            task.status = "error"
            task.result = {"error": str(e)}
            self._record_feedback(task, success=False)
        return task.result

    def run_all(self, symbol: str, context: dict) -> dict:
        """Bir sembol icin tum ajani calistir, son karari dondur."""
        plan = self.plan(symbol, context)
        for task in plan:
            self.execute(task)
        # Son gorev A'nin karari
        a_task = next((t for t in plan if t.agent == "A"), None)
        return a_task.result if a_task else {"status": "NO_DECISION"}

    def _record_feedback(self, task: AgentTask, success: bool):
        if task.agent not in self._feedback:
            self._feedback[task.agent] = []
        self._feedback[task.agent].append({
            "task": task.action,
            "success": success,
            "time": datetime.now(timezone.utc).isoformat(),
        })
        # Scoreboard guncelle
        if task.agent not in self._scoreboard:
            self._scoreboard[task.agent] = {"total": 0, "success": 0}
        self._scoreboard[task.agent]["total"] += 1
        if success:
            self._scoreboard[task.agent]["success"] += 1

    def get_scoreboard(self) -> dict:
        return {
            agent: {
                "total": s["total"],
                "success": s["success"],
                "rate": round(s["success"] / s["total"], 3) if s["total"] > 0 else 0,
            }
            for agent, s in self._scoreboard.items()
        }

    def get_pending_tasks(self) -> List[AgentTask]:
        return [t for t in self._tasks if t.status == "pending"]

    def get_completed_tasks(self) -> List[AgentTask]:
        return [t for t in self._tasks if t.status in ("completed", "error")]
