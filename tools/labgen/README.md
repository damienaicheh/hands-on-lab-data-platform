# LabGen

LabGen creates workshop starter snapshots from a single maintained source tree.

## Commands

```bash
python -m tools.labgen list
python -m tools.labgen generate
python -m tools.labgen generate --lab 1
python -m tools.labgen --verbose list
```

When `--verbose` is enabled, LabGen emits structured JSON logs to `stderr` for easier diagnostics and CI parsing.

## Manifest Notes

The `labs` section is optional.
If omitted (or empty), LabGen uses a default lab list equivalent to:

```json
"labs": [
	{ "id": "1" }
]
```

## Marker format (Python)

Use one starter block around the maintained solution code:

```python
# <lab id="1">
#|raise NotImplementedError("Complete this lab step.")
return completed_value
# </lab>
```

For a generated lab, previous labs keep the maintained solution code inside their lab blocks. The current lab and future labs keep only the `#|` starter payload.
