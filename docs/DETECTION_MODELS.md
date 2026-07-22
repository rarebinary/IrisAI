# Detection Models

## YOLO ONNX Models

### mainInGameModel.onnx
- **Source:** YOLOv8 (trained externally)
- **Input:** 640×640 letterbox RGB
- **Output classes:** player, enemy, teammate (3 classes)
- **Usage:** Real-time entity detection per frame
- **Provider priority:** CoreML → CPU on macOS
- **Postprocessing:** `_numpy_nms` with IOU threshold 0.6, confidence threshold 0.6 (hardcoded minimum)
- **Returns:** `{"player": [[x1,y1,x2,y2], ...], "enemy": [...], "teammate": [...]}`

### tileDetector.onnx
- **Input:** 640×640 letterbox RGB (full frame)
- **Output classes:** `["wall", "bush", "close_bush"]` (configurable via `wall_model_classes`)
- **Usage:** Full-screen wall/bush detection
- **Throttled:** Runs every N seconds (config: `wall_detection` in `time_tresholds.toml`, current value 0.15s)
- **Update mechanism:** SHA-256 hash verified against API, auto-download on mismatch

### closeTileDetector.onnx
- **Input:** 640×640 centered on player (cropped region)
- **Output classes:** same as tileDetector
- **Usage:** Alternative wall detection when `centered_wall_detection=true`
- **Note:** This model is **never auto-updated** (only tileDetector has update checks)

## Detection Pipeline

Inference runs only while the state machine reports `match`. Lobby, loading, and recovery alerts release the joystick and skip the models.

```
Frame (1920×1080)
    │
    ├──→ Entity Detection (every frame)
    │     Letterbox resize → 640×640
    │     ONNX inference (CoreML → CPU)
    │     Per-class NMS postprocessing (_numpy_nms)
    │     Scale boxes to original dimensions
    │     Cached until frame changes
    │
    └──→ Tile Detection (every N seconds, parallel with entity if due)
          Parallel: ThreadPoolExecutor (2 workers) runs entity + tile
          Full-frame or centered-crop (config: centered_wall_detection)
          ONNX inference
          Extract wall/bush positions
          process_tile_data() → separate walls and bushes
          Cached until next detection

HSV-based checks (every N frames, configurable intervals):
    ├── Super ready → crop area (1460,830)-(1560,930), count HSV pixels (yellow: 17,170,200)-(27,255,255)
    ├── Gadget ready → crop area (1580,930)-(1700,1050), count HSV pixels (green: 57,219,165)-(62,255,255)
    ├── Hypercharge ready → crop area (1350,940)-(1450,1050), count HSV pixels (purple: 137,158,159)-(179,255,255)
    ├── Poison gas → crop 1.5× area around player, HSV masking (30,90,221)-(57,114,235) → directional dict
    └── Idle screen → center-area gray pixel counting HSV (0,0,10)-(30,60,67)
```

## Model Files

Located in `models/`:

| File | Size | Format | Purpose | Auto-Update |
|------|------|--------|---------|-------------|
| `mainInGameModel.onnx` | ~30MB | ONNX | Entity detection | ❌ No |
| `tileDetector.onnx` | ~15MB | ONNX | Full-frame wall/bush | ✅ SHA-256 check |
| `closeTileDetector.onnx` | ~10MB | ONNX | Centered wall/bush | ❌ No |
| `easyocr/craft_mlt_25k.pth` | ~75MB | PyTorch | CRAFT text detection | — |
| `easyocr/english_g2.pth` | ~50MB | PyTorch | English recognition | — |
| `manifest.json` | — | JSON | Model metadata (URLs, hashes) | — |

## Detection Configuration

| Parameter | Config File | Current Value | Code Default | Description |
|-----------|------------|---------------|-------------|-------------|
| `entity_detection_confidence` | bot_config.toml | 0.5 | 0.5 | YOLO entity confidence threshold |
| `wall_detection_confidence` | bot_config.toml | 0.7 | 0.5 | ⚠️ Mismatch |
| `wall_detection` | time_tresholds.toml | 0.15 | 2 frames | ⚠️ 13× difference from default |
| `super` | time_tresholds.toml | 0.15 | 5 frames | ⚠️ 33× difference |
| `hypercharge` | time_tresholds.toml | 0.15 | 5 frames | ⚠️ 33× difference |
| `gadget` | time_tresholds.toml | 0.15 | 5 frames | ⚠️ 33× difference |
| `used_threads` | general_config.toml | 4 | `auto` | Thread pool workers |
| `centered_wall_detection` | bot_config.toml | false | False | Use centered wall crop |
| `perceived_tile_size` | bot_config.toml | 75 | 80 | Wall tile pixel size |
| `super_pixels_minimum` | bot_config.toml | 1800 | 100 | ⚠️ 18× difference |
| `gadget_pixels_minimum` | bot_config.toml | 1300 | 100 | ⚠️ 13× difference |
| `hypercharge_pixels_minimum` | bot_config.toml | 1800 | 100 | ⚠️ 18× difference |
| `idle_pixels_minimum` | bot_config.toml | 75000 | 500 | ⚠️ 150× difference (effectively disables idle detection) |

## Provider Selection (detect.py)

Priority order:
1. `CoreMLExecutionProvider` on Apple Silicon
2. `CPUExecutionProvider` as the universal macOS fallback

`cpu_or_gpu = "cpu"` skips CoreML explicitly. `auto` and `coreml` try CoreML first and fall back cleanly when it is unavailable.

## EasyOCR

Used by `LobbyAutomation` as the fallback when native macOS Vision OCR is unavailable:
- CRAFT text detection model (`craft_mlt_25k.pth`)
- English recognition model (`english_g2.pth`)
- Lazy-initialized singleton with thread safety (`DefaultEasyOCR`)
- Configurable scale factor via `ocr_scale_down_factor` (0.6 current, 0.75 default, clamped 0.5-1.0)
- GPU disabled for OCR (always CPU)

## macOS Vision OCR

On macOS, brawler selection uses Apple's native Vision framework first. This
recognizes the current stylized in-game names more reliably and avoids loading
the PyTorch OCR detector during normal selection. Iris compiles
`native/macos_vision_ocr.swift` once into `.iris_runtime/bin/`; EasyOCR remains
the fallback when the native helper is unavailable.
