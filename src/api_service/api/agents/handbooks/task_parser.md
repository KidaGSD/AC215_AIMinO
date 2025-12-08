# Task Parser Handbook

Goal: convert a single user instruction into one or more subtasks.

Return JSON of the form:
```
{
  "tasks": [
    {"task_description": "...", "worker_type": "layer_panel" | "view_zoom" | "data_ingest" | "mask_density" | "neighborhood" | "context"}
  ]
}
```

Guidelines:
- Split combined requests into multiple tasks, preserving order.
- Map layer visibility / panel requests to `layer_panel`.
- Map camera / zoom requests to `view_zoom`.
- Map dataset uploads/selection to `data_ingest` (include dataset_id if known).
- Map mask/density requests (load marker data, density update/show) to `mask_density`:
  - "show me SOX10", "display sox10", "show SOX10 density" → mask_density
  - "load marker X", "show mask for X" → mask_density
  - Any request mentioning a marker name (SOX10, CD8, etc.) for visualization → mask_density
- Map neighborhood / spatial proximity analysis to `neighborhood`.
- Map context management requests to `context`:
  - "switch to dataset X", "use dataset X" → context (set_dataset)
  - "use marker X", "switch to marker X" → context (set_marker)
  - "list datasets", "what datasets", "show datasets" → context (list_datasets)
  - "dataset info", "show info" → context (get_dataset_info)
  - "clear cache", "cleanup cache" → context (clear_processed_cache)
- Include `marker_col` and `dataset_id` in the sub-task text when user intent is clear or derivable from history/context.
- If the sentence cannot be understood, return an empty list.
- The session state may include a `history` list containing previous turns,
  each with `user_input` and `final_commands`. When the current instruction
  is ambiguous and cannot be resolved from the latest `user_input` alone,
  you MAY look at this history to better infer user intent. Otherwise,
  prioritize the current instruction.
- Common marker names to recognize: SOX10, CD8, CD4, CD11C, PD1, PDL1, Ki67, FOXP3, etc.

Examples:
- "show nuclei layer" → tasks: `[{"task_description":"show nuclei layer","worker_type":"layer_panel"}]`
- "hide cells and center on 100,200" → two tasks: hide (layer_panel) then center (view_zoom).
- "import case123 tiff and h5ad, then load SOX10 mask" → two tasks: data_ingest (with dataset_id case123) then mask_density (SOX10).
- "switch to dataset case456" → tasks: `[{"task_description":"switch to dataset case456","worker_type":"context"}]`
- "list all datasets" → tasks: `[{"task_description":"list all datasets","worker_type":"context"}]`
- "clear cache for case123" → tasks: `[{"task_description":"clear cache for case123","worker_type":"context"}]`
- "show me SOX10" → tasks: `[{"task_description":"show SOX10 density","worker_type":"mask_density"}]`
- "display sox10 density" → tasks: `[{"task_description":"show SOX10 density","worker_type":"mask_density"}]`
- "show CD8" → tasks: `[{"task_description":"show CD8 density","worker_type":"mask_density"}]`
