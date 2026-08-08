# JARVIS PROJECT CONTEXT

## Цель проекта

Jarvis — локальный Desktop AI Agent для Windows 11.

Цель:
Создать автономного помощника уровня Iron Man JARVIS.

Он должен:
- понимать голосовые команды
- разговаривать
- видеть экран
- управлять компьютером
- запускать программы
- выполнять задачи
- писать код
- иметь долговременную память
- работать локально через Ollama


# Архитектура

## Core Agent

core/

Отвечает за мозг агента.

Компоненты:

agent.py
Главный цикл:

User Input
↓
Planning
↓
Execution
↓
Checking
↓
Memory


planner.py

Использует LLM для:
- анализа задачи
- разбиения на шаги
- выбора действий


executor.py

Выполняет действия:

- keyboard
- mouse
- windows
- tools


checker.py

Проверяет:
- успешно ли выполнена задача
- ошибки
- повтор действий


policy.py

Безопасность:

- оценка риска
- разрешение опасных действий


# LLM

llm/

Используется Ollama.


Модели:

Brain:
gpt-oss:20b

Использование:
- архитектура
- планирование
- анализ


Coder:
qwen2.5-coder:14b

Использование:
- генерация кода
- исправление ошибок


Memory:
nomic-embed-text

Использование:
- поиск по знаниям
- RAG


# Memory

memory/

SQLite база:

jarvis.db

Хранит:

- историю разговоров
- действия
- результаты
- предпочтения пользователя


Будущее:
- vector memory
- semantic search
- long term memory


# Voice

voice/

listener.py

Speech To Text.


speaker.py

Text To Speech.


# Vision

vision/

Задача:

- анализ экрана
- распознавание объектов
- понимание интерфейса


# Automation

automation/

Управление Windows:

keyboard.py
mouse.py
windows.py


# Этапы разработки


## Current version

Jarvis v0.1

Есть:
- базовый Agent Loop
- Ollama
- Planner
- Executor
- GUI
- Voice
- Memory foundation


## Jarvis v0.2

Цель:

Стабильное ядро агента.

Добавить:

- нормальный Tool Registry
- систему навыков Skills
- улучшенный Planner
- обработку ошибок
- логирование действий


## Jarvis v0.3

Память:

- долгосрочная память
- embeddings
- поиск прошлых решений
- контекст пользователя


## Jarvis v0.4

Computer Control:

- управление окнами
- анализ экрана
- компьютерное зрение
- безопасные действия


## Jarvis v0.5

Autonomous Agent:

- самостоятельное выполнение задач
- циклы проверки
- самоисправление


## Jarvis v1.0

Полноценный Desktop AI Agent:

- голос
- зрение
- память
- инструменты
- планирование
- автономность


# Правила разработки

1. Не переписывать проект полностью.
2. Улучшать поэтапно.
3. Перед изменением анализировать существующий код.
4. Сохранять совместимость.
5. Без облачных API.
6. Использовать локальный Ollama.