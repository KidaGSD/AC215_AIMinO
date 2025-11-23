# Task Parser Handbook

Goal: convert a single user instruction into one or more subtasks.

Inputs:
- `user_input`: the current natural language instruction from the user.
- `history`: optional, a compact text summary of recent events in this session
  (previous user queries, agent messages, and executed commands). Use it to
  keep the plan consistent with what has already been done.

Return JSON of the form:
```
{
  "tasks": [
    {"task_description": "...", "worker_type": "layer_panel" | "view_zoom"}
  ]
}
```

Guidelines:
- Split combined requests into multiple tasks, preserving order.
- Use `history` to infer implicit context (e.g., previously mentioned layers,
  camera locations, or prior successes/failures) when it helps disambiguate
  the current `user_input`. Do not repeat tasks that are clearly already
  completed unless the user asks to change them.
- Map layer visibility / panel requests to `layer_panel`.
- Map camera / zoom requests to `view_zoom`.
- If the sentence cannot be understood, return an empty list.

Examples:
- "show nuclei layer" → tasks: `[{"task_description":"show nuclei layer","worker_type":"layer_panel"}]`
- "hide cells and center on 100,200" → two tasks: hide (layer_panel) then center (view_zoom).
