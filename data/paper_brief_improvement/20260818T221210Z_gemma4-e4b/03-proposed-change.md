## Rationale
The current instructions for `key_findings` are too passive; they merely ask the model to list "primary metrics or results." However, high-quality scientific briefs (as demonstrated by the diagnosis summary) do not just list data points; they synthesize a finding *and* its immediate implication. By modifying this section's prompt, we force the model to act as an interpreter of the raw data, ensuring that every listed key finding is presented with enough context or significance statement derived from the text (e.g., "X was found in Y areas, suggesting Z risk"). This elevates the brief from a mere summary of results to a true synthesis of scientific impact.

## Proposed change
Modify the description for `key_findings` within the `# Output fields` section.

**Old Text:**
```markdown
### `key_findings` (required)

A short list (typically two or three items) of primary metrics or results. Do not dump every table.
```

**New Text:**
```markdown
### `key_findings` (required)

A short, synthesized list (typically two to four items) detailing the most impactful primary metrics or results. Each finding must state the result and its immediate significance or implication as described by the authors in the text. Do not simply list data points; synthesize the key takeaway.
```

## Expected effect on G-Eval criteria
**faithfulness:** Improve. By requiring the model to explicitly link a finding to its *significance* (which must still be grounded in the source text), we force a deeper, more accurate understanding of the paper's core message, reducing the risk of listing isolated data points without context.

**completeness:** Improve. The change guides the model toward capturing the full scope of an impactful finding—the result *and* its meaning—making the brief feel richer and more complete in conveying scientific insight.

**conciseness:** No effect. While the instruction is slightly longer, it improves information density by ensuring that every bullet point carries both factual weight and interpretive value, maintaining conciseness without sacrificing depth.

**topic_agnostic:** No effect. The change relates purely to the structural requirement of synthesis for a field, not the nature or topic of the science being summarized.