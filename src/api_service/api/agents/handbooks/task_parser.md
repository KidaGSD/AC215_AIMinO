# Task Parser Handbook

Goal: convert a single user instruction into one or more subtasks.

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
- Map layer visibility / panel requests to `layer_panel`.
- Map camera / zoom requests to `view_zoom`.
- If the sentence cannot be understood, return an empty list.

Examples:
- "show nuclei layer" → tasks: `[{"task_description":"show nuclei layer","worker_type":"layer_panel"}]`
- "hide cells and center on 100,200" → two tasks: hide (layer_panel) then center (view_zoom).
