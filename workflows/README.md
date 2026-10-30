# Workflows

## `recastroom_h3_workflow.json`

ComfyUI API-format graph for a self-hosted runtime:

- MiniMax H3 Ref2VA
- BFSShotPlanner
- BFSShotH3ConditioningSimple
- Character Swap LoRA v1.1 at `1.0`
- Head Swap disabled
- 8-step Turbo
- source-audio conditioning
- SAM 3.1 `head + hands (keep mouth)` source blur
- MiniMax H3 Timed Audio
- MiniMax H3 Exact Audio Lock

The graph expects these generic input filenames:

```text
source.mp4
reference_1.png
reference_2.png
```

The app's prepare command rewrites those names and the prompt for each job.

The graph is designed for a single target performer. Split multi-shot or multi-person scenes before using it.

Advanced users can import a custom graph through the web UI. The replacement graph
must keep the Recast Room node contract: BFSShotPlanner `1189`, prompt node
`1152`, conditioning node `1177`, timed-audio node `200`, exact-audio-lock node
`201`, and the listed output nodes. This preserves source/reference routing,
rights enforcement, source blur, exact audio locking, and reviewable outputs.
