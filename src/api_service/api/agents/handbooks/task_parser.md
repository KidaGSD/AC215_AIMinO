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
- The session state may include a `history` list containing previous turns,
  each with `user_input` and `final_commands`. When the current instruction
  is ambiguous and cannot be resolved from the latest `user_input` alone,
  you MAY look at this history to better infer user intent. Otherwise,
  prioritize the current instruction.

Examples:
- "show nuclei layer" → tasks: `[{"task_description":"show nuclei layer","worker_type":"layer_panel"}]`
- "hide cells and center on 100,200" → two tasks: hide (layer_panel) then center (view_zoom).
