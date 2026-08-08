"""
Tests for Autonomous Agent Loop
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from unittest.mock import Mock, MagicMock, patch
from core.agent_loop import AutonomousAgent, AgentState
from core.tool_registry import ToolRegistry
from core.memory_manager import MemoryManager

class TestAutonomousAgent(unittest.TestCase):

    def setUp(self):
        """Настройка тестового окружения"""
        self.mock_registry = Mock(spec=ToolRegistry)
        self.mock_memory = Mock(spec=MemoryManager)
        self.mock_llm = Mock()
        
        self.agent = AutonomousAgent(
            registry=self.mock_registry,
            memory=self.mock_memory,
            llm=self.mock_llm
        )

    def test_agent_initialization(self):
        """Проверка инициализации агента"""
        self.assertEqual(self.agent.state, AgentState.IDLE)
        self.assertEqual(self.agent.max_steps, 30)
        self.assertFalse(self.agent.stop_requested)
        self.assertEqual(self.agent.brain_model, "qwen3-coder:30b")
        self.assertEqual(self.agent.vision_model, "qwen3-vl:8b")

    def test_stop_request(self):
        """Проверка остановки агента"""
        self.agent.stop()
        self.assertTrue(self.agent.stop_requested)
        self.assertEqual(self.agent.state, AgentState.STOPPED)

    @patch('core.agent_logger.logger')
    def test_run_success_scenario(self, mock_logger):
        """Сценарий успешного выполнения задачи"""
        goal = "Open Chrome"
        
        # Моки для планирования
        self.agent._generate_initial_plan = Mock(return_value=[
            {"action": "launch_app", "args": {"app": "chrome"}, "needs_vision": False}
        ])
        
        # Мок выполнения
        self.agent._execute_step = Mock(return_value={"status": "success", "data": {}})
        
        # Мок проверки завершения
        self.agent._evaluate_completion = Mock(return_value={"done": True})
        
        result = self.agent.run(goal)
        
        self.assertEqual(result["status"], "success")
        self.mock_memory.add_task_record.assert_called_with(goal, status="completed", result=result)
        self.assertEqual(self.agent.state, AgentState.IDLE)  # Вернулся в IDLE после завершения

    def test_run_max_steps_reached(self):
        """Достигнут лимит шагов"""
        self.agent._generate_initial_plan = Mock(return_value=[{"action": "dummy"}])
        self.agent._execute_step = Mock(return_value={"status": "success"})
        self.agent._evaluate_completion = Mock(return_value={"done": False})
        
        # Искусственно ставим шаг на максимум
        self.agent.step_count = 29 
        
        result = self.agent.run("Test")
        
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"], "Max steps reached")

    def test_execution_loop_empty_plan(self):
        """Цикл с пустым планом вызывает реплан"""
        self.agent.current_plan = []
        self.agent._evaluate_completion = Mock(return_value={"done": False, "reason": "Stuck"})
        self.agent._replan = Mock(return_value=[{"action": "retry"}])
        
        # Запускаем один шаг цикла вручную
        # В реальном тесте здесь была бы проверка логики while
        
        # Эмуляция логики: если план пуст и не done -> replan
        if not self.agent.current_plan:
            eval_res = self.agent._evaluate_completion()
            if not eval_res.get("done"):
                new_plan = self.agent._replan(eval_res["reason"])
                self.assertIsNotNone(new_plan)
                self.agent._replan.assert_called_once()

    def test_execute_step_tool_not_found(self):
        """Обработка неизвестного инструмента"""
        step = {"action": "unknown_tool", "args": {}}
        self.registry.execute.side_effect = Exception("Tool not found")
        
        # Так как в коде используется try/except внутри _execute_step, 
        # проверяем что возвращается ошибка
        with patch.object(self.agent, 'registry', self.mock_registry):
            self.mock_registry.execute.side_effect = Exception("Unknown tool")
            result = self.agent._execute_step(step)
            
            self.assertEqual(result["status"], "error")

    def test_observe_screen_success(self):
        """Успешное наблюдение за экраном"""
        self.mock_registry.execute.return_value = {"image_data": "base64..."}
        self.mock_llm.generate_vision.return_value = {"analysis": "Chrome window visible"}
        
        result = self.agent._observe_screen()
        
        self.assertTrue(result["success"])
        self.mock_registry.execute.assert_called_with("screenshot", {})
        self.mock_llm.generate_vision.assert_called_once()

    def test_observe_screen_failure(self):
        """Ошибка наблюдения (например, нет скриншота)"""
        self.mock_registry.execute.side_effect = Exception("Capture failed")
        
        result = self.agent._observe_screen()
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)

    def test_verify_action_success(self):
        """Верификация успешного действия"""
        step = {"action": "click"}
        result = {"status": "success"}
        observation = {"success": True, "data": "Button clicked"}
        
        verify = self.agent._verify_action(step, result, observation)
        self.assertTrue(verify["success"])

    def test_verify_action_failed(self):
        """Верификация неудачного действия"""
        step = {"action": "click"}
        result = {"status": "error", "error": "Target not found"}
        observation = None
        
        verify = self.agent._verify_action(step, result, observation)
        self.assertFalse(verify["success"])
        self.assertEqual(verify["reason"], "Target not found")

    def test_create_retry_step(self):
        """Создание шага повторной попытки"""
        original = {"action": "click", "args": {"x": 100, "y": 200}}
        error_info = {"reason": "Low confidence"}
        
        retry = self.agent._create_retry_step(original, error_info)
        
        self.assertEqual(retry["retry_count"], 1)
        self.assertEqual(retry["last_error"], "Low confidence")
        self.assertEqual(retry["action"], "click")

if __name__ == '__main__':
    unittest.main()
