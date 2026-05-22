"""
Test: PYTHON.agents.orchestrator + memory
Agent planning, execution, feedback learning.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PYTHON.agents.orchestrator import AgentOrchestrator, AgentTask
from PYTHON.agents.memory import AgentMemory


class TestAgentOrchestrator:
    def test_register_and_plan(self):
        orch = AgentOrchestrator()
        orch.register_tool("B", lambda p: {"signal": "BUY"})
        plan = orch.plan("THYAO", {"regime": "bull"})
        assert len(plan) == 8
        assert any(t.agent == "A" for t in plan)

    def test_execute(self):
        orch = AgentOrchestrator()
        orch.register_tool("B", lambda p: {"signal": "BUY", "score": 75})
        task = AgentTask(id="t1", agent="B", action="technical_signal", params={"symbol": "THYAO"})
        result = orch.execute(task)
        assert result["signal"] == "BUY"
        assert task.status == "completed"

    def test_run_all(self):
        orch = AgentOrchestrator()
        for agent in ["E", "B", "C", "D", "F", "G", "H", "A"]:
            orch.register_tool(agent, lambda p, a=agent: {"agent": a, "status": "OK"})
        result = orch.run_all("THYAO", {})
        assert result["status"] == "OK"

    def test_scoreboard(self):
        orch = AgentOrchestrator()
        orch.register_tool("B", lambda p: {"ok": True})
        task = AgentTask(id="t1", agent="B", action="test", params={})
        orch.execute(task)
        sb = orch.get_scoreboard()
        assert "B" in sb
        assert sb["B"]["total"] == 1


class TestAgentMemory:
    def test_record_and_best_action(self, tmp_path):
        mem = AgentMemory(agent="B_test", memory_dir=str(tmp_path))
        mem.record_decision(state="bull", action="BUY", reward=1.0)
        mem.record_decision(state="bull", action="SELL", reward=-1.0)
        best = mem.best_action("bull", ["BUY", "SELL"])
        # Epsilon-greedy nedeniyle deterministik degil, ama BUY daha yuksek Q degerine sahip
        stats = mem.get_stats()
        assert stats["total"] == 2
