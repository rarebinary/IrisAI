# Detection Models

## YOLO ONNX Models

### mainInGameModel.onnx
- **Source:** YOLOv8 (trained externally)
- **Input:** 640×640 letterbox RGB
- **Output classes:** player, enemy, teammate
- **Usage:** Real-time entity detection per frame
- **Provider priority:** CUDA → CoreML → DirectML → CPU
- **Detection:** Returns bounding boxes per class, filtered by NMS and confidence threshold

### tileDetector.onnx
- **Input:** 640×640 letterbox RGB (full frame) or centered-crop region
- **Output classes:** wall tiles (configurable: 3 or 5 classes per `bot_config.toml`)
- **Usage:** Full-screen wall/bush detection (or centered if `centered_wall_detection=true`)
- **Throttled:** Runs every N frames (config: `wall_detection_delay` in `timer_frequencies`)
- **Output:** Array of wall tile center coordinates, separated into walls and bushes by `process_tile_data()`

### closeTileDetector.onnx
- **Input:** 640×640 centered on player (cropped region)
- **Output classes:** same as tileDetector
- **Usage:** Alternative wall detection mode when `centered_wall_mode = true` in config
- **Benefit:** Focuses compute on area around player, useful for lower-end devices

## Detection Pipeline

```
Frame (1920×1080)
    │
    ├──→ Entity Detection (every frame)
    │     Letterbox resize → 640×640
    │     ONNX inference (CUDA → CoreML → DirectML → CPU)
    │     Per-class NMS postprocessing (_numpy_nms)
    │     Scale boxes to original dimensions
    │     Cached until frame changes
    │
    └──→ Tile Detection (every N frames, background thread or parallel)
          Parallel: ThreadPoolExecutor (2 workers) runs entity + tile together
          Full-frame or centered-crop
          ONNX inference
          Extract wall/bush positions
          process_tile_data() → separate walls and bushes
          Cached until next detection

HSV-based checks (every N frames, configurable intervals):
    ├── Super ready → crop region, count HSV pixels, compare to super_pixels_minimum
    ├── Gadget ready → crop region, count HSV pixels, compare to gadget_pixels_minimum
    ├── Hypercharge ready → crop region, count HSV pixels, compare to hypercharge_pixels_minimum
    ├── Poison gas → crop 1.5× area around player, HSV masking → directional dict
    └── Idle screen → center-area gray pixel counting (HSV range)
```

## Model Files

Located in `models/`:

| File | Size | Format | Purpose |
|------|------|--------|---------|
| `mainInGameModel.onnx` | ~30MB | ONNX | Entity detection |
| `tileDetector.onnx` | ~15MB | ONNX | Full-frame wall/bush |
| `closeTileDetector.onnx` | ~10MB | ONNX | Centered wall/bush |
| `easyocr/craft_mlt_25k.pth` | ~75MB | PyTorch | CRAFT text detection |
| `easyocr/english_g2.pth` | ~50MB | PyTorch | English recognition |
| `easyocr/latin_g2.pth` | ~50MB | PyTorch | Latin recognition |

## Wall Model Classes

The wall model can output 3 or 5 classes (set via `wall_model_classes` in `bot_config.toml`):
- **3-class**: open, wall, bush
- **5-class**: open, wall, bush, water, obstacle

Current wall model files are auto-verified via MD5 hash against the latest versions.

## Detection Configuration

| Parameter | Location | Default | Description |
|-----------|----------|---------|-------------|
| `entity_detection_confidence` | bot_config.toml | 0.5 | YOLO entity confidence threshold |
| `wall_detection_confidence` | bot_config.toml | 0.5 | YOLO wall confidence threshold |
| `process_every_n_frames` | general_config.toml | 2 | Process every Nth frame |
| `wall_detection` | time_tresholds.toml → timer_frequencies | 2 | Run wall det. every N frames |
| `super` | time_tresholds.toml → timer_frequencies | 5 | Check super every N frames |
| `hypercharge` | time_tresholds.toml → timer_frequencies | 5 | Check hypercharge every N frames |
| `gadget` | time_tresholds.toml → timer_frequencies | 5 | Check gadget every N frames |
| `used_threads` | general_config.toml | auto | Thread pool workers (`auto` = min(max(2, CPU//2), 6)) |
| `centered_wall_detection` | bot_config.toml | false | Use centered wall crop |
| `perceived_tile_size` | bot_config.toml | 80 | Wall tile pixel size |
| `super_pixels_minimum` | bot_config.toml | 100 | Min HSV pixels for super ready |
| `gadget_pixels_minimum` | bot_config.toml | 100 | Min HSV pixels for gadget ready |
| `hypercharge_pixels_minimum` | bot_config.toml | 100 | Min HSV pixels for hypercharge ready |
| `idle_pixels_minimum` | bot_config.toml | 500 | Min gray pixels for idle detection |

## EasyOCR

Used by `LobbyAutomation` for brawler name OCR:
- CRAFT text detection model (`craft_mlt_25k.pth`)
- English recognition model (`english_g2.pth`)
- Latin fallback (`latin_g2.pth`)
- Lazy-initialized singleton with thread safety (`DefaultEasyOCR`)
- Configurable scale factor for performance/accuracy trade-off
