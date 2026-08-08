"""
JARVIS Autonomous Agent Loop
Цикл: GOAL → PLAN → ACT → OBSERVE → EVALUATE → REPLAN → DONE
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.exceptions import ToolExecutionError, ToolNotFoundError
from core.tool_registry import ToolRegistry
from core.memory_manager import MemoryManager
from llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class AgentState:
    """Состояния автономного агента"""
    IDLE = "IDLE"
    THINKING = "THINKING"      # Планирование / Переоценка
    ACTING = "ACTING"          # Выполнение действия
    OBSERVING = "OBSERVING"    # Анализ результата (Vision)
    VERIFYING = "VERIFYING"    # Проверка успеха
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    STOPPED = "STOPPED"

class AutonomousAgent:
    """
    Автономный агент JARVIS.
    Управляет полным циклом выполнения задачи с самокоррекцией.
    """
    
    def __init__(self, registry: ToolRegistry, memory: MemoryManager, llm: OllamaClient):
        self.registry = registry
        self.memory = memory
        self.llm = llm
        
        self.state = AgentState.IDLE
        self.current_goal: Optional[str] = None
        self.current_plan: List[Dict[str, Any]] = []
        self.step_count = 0
        self.max_steps = 30
        self.stop_requested = False
        
        # Конфигурация моделей
        self.brain_model = "qwen3-coder:30b"
        self.vision_model = "qwen3-vl:8b"

    def run(self, goal: str) -> Dict[str, Any]:
        """Запуск автономного цикла выполнения задачи"""
        logger.info(f"[AGENT] Starting autonomous task: {goal}")
        self.current_goal = goal
        self.state = AgentState.THINKING
        self.step_count = 0
        self.stop_requested = False
        
        # Сохраняем цель в память
        self.memory.add_task_record(goal, status="started")
        
        try:
            # Начальное планирование
            self.current_plan = self._generate_initial_plan(goal)
            if not self.current_plan:
                raise Exception("Failed to generate initial plan")
            
            result = self._execution_loop()
            
            if result.get("status") == "success":
                self.memory.add_task_record(goal, status="completed", result=result)
                self.state = AgentState.SUCCESS
            else:
                self.memory.add_task_record(goal, status="failed", error=result.get("error"))
                self.state = AgentState.FAILED
                
            return result
            
        except Exception as e:
            logger.error(f"[AGENT] Critical error: {e}", exc_info=True)
            self.state = AgentState.FAILED
            return {"status": "failed", "error": str(e)}
        finally:
            self.state = AgentState.IDLE

    def stop(self):
        """Экстренная остановка цикла"""
        logger.warning("[AGENT] Stop requested")
        self.stop_requested = True
        self.state = AgentState.STOPPED

    def _execution_loop(self) -> Dict[str, Any]:
        """Основной цикл выполнения: Act → Observe → Evaluate → Replan"""
        
        while self.step_count < self.max_steps and not self.stop_requested:
            self.step_count += 1
            logger.info(f"[AGENT] Step {self.step_count}/{self.max_steps}")
            
            # 1. Выбор следующего действия из плана
            if not self.current_plan:
                # План пуст, нужно сгенерировать новый или завершить
                eval_result = self._evaluate_completion()
                if eval_result.get("done"):
                    return {"status": "success", "steps": self.step_count}
                else:
                    # Нужен реплан
                    self.current_plan = self._replan(eval_result.get("reason", "Stuck"))
                    if not self.current_plan:
                        return {"status": "failed", "error": "Replanning failed"}
                    continue

            next_step = self.current_plan.pop(0)
            
            # 2. Выполнение действия (ACT)
            self.state = AgentState.ACTING
            action_result = self._execute_step(next_step)
            
            if action_result.get("status") == "error":
                logger.warning(f"[AGENT] Action failed: {action_result.get('error')}")
                # Не прерываем сразу, даем шанс на исправление через Observation
            
            # 3. Наблюдение (OBSERVE) - если действие требовало визуальной проверки
            observation = None
            if next_step.get("needs_vision", False) or action_result.get("status") == "error":
                self.state = AgentState.OBSERVING
                observation = self._observe_screen()
                
                # 4. Верификация (VERIFY)
                self.state = AgentState.VERIFYING
                verify_result = self._verify_action(next_step, action_result, observation)
                
                if not verify_result.get("success"):
                    logger.warning(f"[AGENT] Verification failed: {verify_result.get('reason')}")
                    # Возвращаем шаг в начало плана или модифицируем план
                    self.current_plan.insert(0, self._create_retry_step(next_step, verify_result))
                    continue
            
            # 5. Оценка прогресса
            if self._is_goal_achieved():
                return {"status": "success", "steps": self.step_count, "result": action_result}

        if self.stop_requested:
            return {"status": "stopped", "steps": self.step_count}
        
        return {"status": "failed", "error": "Max steps reached", "steps": self.step_count}

    def _generate_initial_plan(self, goal: str) -> List[Dict[str, Any]]:
        """Генерация начального плана через LLM"""
        prompt = f"""
        Task: {goal}
        Available Tools: {self.registry.list_tools()}
        
        Create a step-by-step plan. Return ONLY a JSON list of steps.
        Each step: {{"action": "tool_name", "args": {{...}}, "needs_vision": true/false}}
        """
        
        try:
            response = self.llm.generate(self.brain_model, prompt, json_mode=True)
            return response.get("plan", [])
        except Exception as e:
            logger.error(f"Plan generation failed: {e}")
            return []

    def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение одного шага через Tool Registry"""
        action = step.get("action")
        args = step.get("args", {})
        
        logger.info(f"[EXECUTOR] Executing: {action} with {args}")
        
        try:
            result = self.registry.execute(action, args)
            return {"status": "success", "data": result}
        except ToolNotFoundError:
            return {"status": "error", "error": f"Unknown tool: {action}"}
        except ToolExecutionError as e:
            return {"status": "error", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _observe_screen(self) -> Dict[str, Any]:
        """Скриншот + Vision анализ текущего состояния"""
        logger.info("[VISION] Capturing screen for observation...")
        
        # Получаем скриншот через инструмент
        try:
            screenshot_data = self.registry.execute("screenshot", {})
            
            # Отправляем в Vision модель
            prompt = "Analyze the current screen. What do you see? What is the active window? Are there any popups or errors?"
            analysis = self.llm.generate_vision(self.vision_model, screenshot_data, prompt)
            
            return {"success": True, "data": analysis}
        except Exception as e:
            logger.error(f"Observation failed: {e}")
            return {"success": False, "error": str(e)}

    def _verify_action(self, step: Dict, result: Dict, observation: Optional[Dict]) -> Dict[str, Any]:
        """Проверка успешности действия"""
        # Простая эвристика: если нет ошибки выполнения и есть подтверждение vision - успех
        if result.get("status") == "success":
            if observation and observation.get("success"):
                # Можно добавить LLM проверку: "Did the action achieve the expected result?"
                pass
            return {"success": True}
        
        return {"success": False, "reason": result.get("error", "Unknown error")}

    def _replan(self, reason: str) -> List[Dict[str, Any]]:
        """Генерация нового плана на основе текущей ситуации"""
        prompt = f"""
        Original Goal: {self.current_goal}
        Previous Plan Failed Reason: {reason}
        Current State: {self._observe_screen()}
        
        Generate a NEW plan to achieve the goal avoiding previous mistakes.
        Return JSON list of steps.
        """
        try:
            response = self.llm.generate(self.brain_model, prompt, json_mode=True)
            return response.get("plan", [])
        except Exception as e:
            logger.error(f"Replanning failed: {e}")
            return []

    def _create_retry_step(self, original_step: Dict, error_info: Dict) -> Dict:
        """Создание шага повторной попытки с коррекцией"""
        # Логика умной повторной попытки (например, смещение координат при ошибке клика)
        retry_step = original_step.copy()
        retry_step["retry_count"] = retry_step.get("retry_count", 0) + 1
        retry_step["last_error"] = error_info.get("reason")
        return retry_step

    def _evaluate_completion(self) -> Dict[str, Any]:
        """Оценка: достигнута ли цель?"""
        prompt = f"""
        Goal: {self.current_goal}
        Steps executed: {self.step_count}
        
        Is the goal fully achieved? Answer JSON: {{"done": true/false, "reason": "..."}}
        """
        try:
            return self.llm.generate(self.brain_model, prompt, json_mode=True)
        except:
            return {"done": False, "reason": "Unable to evaluate"}

    def _is_goal_achieved(self) -> bool:
        """Быстрая проверка флага достижения"""
        # Здесь можно добавить сложную логику проверки состояния памяти
        return False  # Заглушка, реальная логика в _evaluate_completion
