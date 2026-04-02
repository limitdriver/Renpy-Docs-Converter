# Ren'Py Script Converter

A simple GUI tool for converting Google Docs screenplay text into Ren'Py script format.

## Usage

Paste your script text into the left panel and click **Convert →**. The Ren'Py output appears on the right with syntax highlighting. Use the **Copy** button to copy it to your clipboard.

### Syntax Rules

| Input | Output |
|---|---|
| `> This is narration.` | `"This is narration."` |
| `Quiet Woman: Hello there.` | `qwoman "Hello there."` |
| `???: ...` | `mystery "..."` |
| Continuation line (no prefix) | uses last speaker |
| `>` line | resets speaker to narration |

Blank lines are preserved in the output. Smart/curly quotes are automatically converted to ASCII.

### Character Map

The **Character Map** tab lets you define `Display Name: variable` mappings, one per line. These are saved to `character_map.json` next to the executable. Unknown names fall back to `lowercased_underscored` variable names.

## Download

Grab the latest `RenpyConverter.exe` from the [Releases](../../releases) page. No installation needed.

## Running from Source

Requires Python 3.10+ (stdlib only, no extra packages).

```
python converter.py
```
