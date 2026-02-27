# Resume Audit Project — Быстрый старт

## Что это

Проект для Claude Code, который создаёт инструментарий аудита и оптимизации резюме DA/PA.
Используется в менторинговой программе.

## Подготовка (5 минут)

1. Скопируй эту папку к себе
2. Положи исследование в `inputs/research.md`
3. Собери 10 топ-резюме PA → `inputs/resumes_pa/pa_01.txt` ... `pa_10.txt`
4. Собери 10 топ-резюме DA → `inputs/resumes_da/da_01.txt` ... `da_10.txt`

## Работа в Claude Code (по шагам)

### Шаг 1 — Анализ топ-резюме
```
Проанализируй все резюме в inputs/resumes_pa/ и inputs/resumes_da/. 
Следуй инструкциям из Шага 1 в CLAUDE.md. 
Результаты сохрани в analysis/
```

### Шаг 2 — Создание гайда
```
На основе analysis/ и inputs/research.md создай гайд для менти. 
Следуй инструкциям из Шага 2 в CLAUDE.md. 
Сохрани в outputs/guide.md
```

### Шаг 3 — Банк достижений
```
На основе analysis/ создай банк достижений. 
Следуй инструкциям из Шага 3 в CLAUDE.md. 
Сохрани в outputs/achievements_bank.md
```

### Шаг 4 — Промпт самопроверки
```
Создай промпт самопроверки для менти. 
Следуй инструкциям из Шага 4 в CLAUDE.md. 
Сохрани в outputs/self_check_prompt.md
```

### Шаг 5 — Системный промпт для Claude Project
```
Создай системный промпт для Claude Project. 
Следуй инструкциям из Шага 5 в CLAUDE.md. 
Сохрани в outputs/project_prompt.md
```

### Шаг 6 — Тестирование
```
Проведи аудит резюме из файла audit/test_resume.txt
```

## После завершения

1. `outputs/guide.md` → перенеси в Notion для менти
2. `outputs/achievements_bank.md` → перенеси в Notion (или дай как PDF)
3. `outputs/self_check_prompt.md` → выдавай менти как самостоятельный инструмент
4. `outputs/project_prompt.md` → вставь в Claude Project Instructions
5. `outputs/guide.md` + `outputs/achievements_bank.md` → загрузи в Claude Project Knowledge
