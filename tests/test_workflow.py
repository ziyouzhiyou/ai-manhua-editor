"""
Workflow Engine Tests
"""
import pytest
import asyncio
from src.core.workflow_engine import WorkflowEngine, WorkflowTemplates, TaskNode, WorkflowStatus


@pytest.fixture
def engine():
    return WorkflowEngine()


@pytest.fixture
def mock_agent():
    async def agent(config, context, task_id):
        return {"success": True, "task_id": task_id}
    return agent


class TestWorkflowEngine:

    @pytest.mark.asyncio
    async def test_register_agent(self, engine, mock_agent):
        engine.register_agent("test_agent", mock_agent)
        assert "test_agent" in engine.agent_registry

    @pytest.mark.asyncio
    async def test_run_simple_workflow(self, engine, mock_agent):
        engine.register_agent("test_agent", mock_agent)

        workflow = WorkflowTemplates.standard_workflow()
        result = await engine.run_workflow(workflow)

        assert result["metadata"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_workflow_status(self, engine, mock_agent):
        engine.register_agent("test_agent", mock_agent)

        workflow = WorkflowTemplates.fast_workflow()
        result = await engine.run_workflow(workflow)

        workflow_id = result["workflow_id"]
        status = engine.get_workflow_status(workflow_id)

        assert status == WorkflowStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_parallel_execution(self, engine, mock_agent):
        engine.register_agent("test_agent", mock_agent)

        # Create workflow with parallel tasks
        workflow = WorkflowTemplates.standard_workflow()
        result = await engine.run_workflow(workflow)

        assert result["metadata"]["status"] == "completed"

    def test_workflow_templates(self):
        standard = WorkflowTemplates.standard_workflow()
        fast = WorkflowTemplates.fast_workflow()
        premium = WorkflowTemplates.premium_workflow()

        assert len(standard.tasks) > 0
        assert len(fast.tasks) > 0
        assert len(premium.tasks) > 0

        assert standard.id == "standard-ai-manhua"
        assert fast.id == "fast-ai-manhua"
        assert premium.id == "premium-ai-manhua"


class TestTaskNode:

    def test_task_creation(self):
        task = TaskNode(
            id="test",
            name="Test Task",
            agent_type="test_agent"
        )

        assert task.id == "test"
        assert task.status.value == "pending"

    def test_task_to_dict(self):
        task = TaskNode(
            id="test",
            name="Test Task",
            agent_type="test_agent"
        )

        data = task.to_dict()
        assert data["id"] == "test"
        assert data["name"] == "Test Task"
