# Graphify Knowledge Graph

A graph of the entire codebase was built using graphify at `graphify-out/`.

## Graph Stats

- **Nodes:** 2,598
- **Edges:** 5,464
- **Communities:** 124
- **Extraction:** 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS
- **File types:** 107 code files analyzed (code-only mode)

## Output Files

| File | Purpose |
|------|---------|
| `graphify-out/graph.json` | Raw graph data (NetworkX-compatible) |
| `graphify-out/GRAPH_REPORT.md` | Full audit report with communities, god nodes, bridges |
| `graphify-out/.graphify_analysis.json` | Analysis data (communities, cohesion, god nodes) |
| `graphify-out/cost.json` | Token cost tracker |
| `graphify-out/.graphify_labels.json` | Community label mappings |

## God Nodes (most connected)

These are the most central abstractions in the codebase:

| Node | Edges | Description |
|------|-------|-------------|
| `_read_text` | 82 | File reading utility (graphify skill base) |
| `dispatch_command` | 58 | CLI dispatch hub (graphify) |
| `_make_id` | 52 | ID generation (graphify) |
| `WebDataService` | 51 | Web UI data layer |
| `_rebuild_code` | 46 | Graph rebuild orchestrator (graphify) |
| **`Play`** | **46** | **Core in-game AI — project's main class** |
| `_file_stem` | 44 | Path utility (graphify) |
| **`load_toml_as_dict`** | **38** | **Config loading — most connected project utility** |

## Project-Specific Communities

These communities contain the actual project code (not graphify skill files):

| Community | Hub | Nodes | Description |
|-----------|-----|-------|-------------|
| 9 | WebDataService | 7 | Web UI data layer |
| 10 | Play | 43 | In-game AI engine |
| 12 | utils.py | 42 | Shared utilities |
| 14 | main.py | 15 | Entry point orchestrator |
| 16 | Flask/webui | 15 | Web UI app + runtime |
| 17 | skeleton.py | 38 | Playstyle script reference |
| 31 | debug_view.py | 13 | Debug overlay |
| 32 | LobbyAutomation | 27 | OCR brawler selection |
| 46 | ControlSender | 22 | scrcpy control injection |
| 47 | TrophyObserver | 7 | Trophy tracking |
| 57 | state_finder.py | 16 | Game state detection |
| 65 | DiscordBot | 3 | Discord commands |
| 66 | WindowController | 14 | ADB + scrcpy controller |
| 72 | Client (scrcpy) | 7 | scrcpy core client |
| 90-91 | scrcpy init/const | 12 | scrcpy module infrastructure |

## Surprising Connections

Edges the graph discovered that cross project boundaries:

- `WindowController` → `DebugViewPublisher`: Window control feeds debug visualization
- `DiscordBot` → `WindowController`: Discord bot needs screenshot capability
- `WebUI → DiscordBot`: Web UI backend bridges to Discord bot for status

## Using the Graph

### Query (if graphify CLI available)
```bash
graphify query "How does Play.detect() work?"
graphify query "What touches WindowController?" --dfs
```

### Community Exploration
To explore a specific community's nodes:
```bash
graphify explain "Play"
graphify path "LobbyAutomation" "StageManager"
```

### Manual Graph Access (Python)
```python
import json, networkx as nx
from pathlib import Path

data = json.loads(Path("graphify-out/graph.json").read_text())
G = nx.node_link_graph(data)

# Find all functions in a file
play_nodes = [n for n in G.nodes if 'play_' in n]
print(f"Play module has {len(play_nodes)} nodes")

# Find neighbors of a node
neighbors = list(G.neighbors("play_play"))
print(f"Play.main connects to: {neighbors}")
```
