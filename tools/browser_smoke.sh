#!/usr/bin/env bash
set -euo pipefail

base_url=${1:?base URL}
screenshot=${2:?screenshot output path}
transcript=${3:?transcript output path}
session=oj-vwzl-e2e
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_media="$root/tests/fixtures/synthetic_source.mp4"
reference_image="$root/tests/fixtures/synthetic_reference.png"
words_json="$root/tests/fixtures/word_timings.json"

mkdir -p "$(dirname "$screenshot")" "$(dirname "$transcript")"
exec > >(tee "$transcript") 2>&1

agent-browser --session "$session" open "$base_url"
agent-browser --session "$session" snapshot -i
agent-browser --session "$session" upload '#source' "$source_media"
agent-browser --session "$session" upload '#reference_1' "$reference_image"
agent-browser --session "$session" upload '#words' "$words_json"
agent-browser --session "$session" fill '#identity' 'Synthetic fixture performer'
agent-browser --session "$session" fill '#seed' '50'
agent-browser --session "$session" check '#rights'
agent-browser --session "$session" is checked '#rights'
agent-browser --session "$session" click '#submit'
agent-browser --session "$session" wait --text 'job_id'
agent-browser --session "$session" get text '#output'
agent-browser --session "$session" eval 'run.click(); "clicked"'
agent-browser --session "$session" wait 7000
agent-browser --session "$session" get text '#output'
agent-browser --session "$session" get count '#output a[href$="/generated"]'
agent-browser --session "$session" get count '#output a[href$="/final"]'
agent-browser --session "$session" get count '#output a[href$="/side_by_side"]'
agent-browser --session "$session" network requests --filter '/api/'
agent-browser --session "$session" screenshot --full "$screenshot"
agent-browser --session "$session" close

python3 - "$transcript" "$root" "$(dirname "$screenshot")" <<'PY'
from pathlib import Path
import sys

transcript, workspace, output_dir = sys.argv[1:]
path = Path(transcript)
text = path.read_text(encoding="utf-8")
for original, label in sorted(
    ((workspace, "<workspace>"), (output_dir, "<output-dir>")),
    key=lambda item: len(item[0]),
    reverse=True,
):
    text = text.replace(original, label)
text = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
path.write_text(text, encoding="utf-8")
PY
