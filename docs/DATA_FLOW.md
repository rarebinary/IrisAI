# Data Flow

## Primary Data Path (Main Loop)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PER-FRAME DATA FLOW                              │
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌───────────────────────┐   │
│  │ scrcpy       │     │ State        │     │ StageManager          │   │
│  │ (60fps H264) │────▶│ Checker      │────▶│ (menu FSM)            │   │
│  │              │     │ Thread       │     │                       │   │
│  │ frame_buffer │     │ (daemon)     │     │ • start_game()        │   │
│  └──────┬───────┘     │              │     │ • end_game()          │   │
│         │             │ get_state()  │     │ • handle popups       │   │
│         │             └──────────────┘     └───────────────────────┘   │
│         │                                                               │
│         ▼                                                               │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      Main.main()                                 │  │
│  │                                                                   │  │
│  │  1. Get latest frame from scrcpy (frame + timestamp)              │  │
│  │  2. Check if frame changed (dedup by timestamp)                  │  │
│  │  3. If state=="lobby": check stop/pause signals                  │  │
│  │  4. Auto-pick first brawler if not yet picked                    │  │
│  │  5. Check run timer / cooldown (3min after target)               │  │
│  │  6. Print IPS every second                                       │  │
│  │  7. If state=="match": Play.main(frame, brawler, main, ft)      │  │
│  │  8. Monitor scrcpy freshness (reconnect if stale >15s)           │  │
│  │  9. Check for BS crash (every N secs)                            │  │
│  │ 10. manage_time_tasks(): state, no-detections, idle, pings       │  │
│  │ 11. Throttle to max_ips if configured                            │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                  │                                      │
│                                  ▼                                      │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      Play.main(frame)                             │  │
│  │                                                                   │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │  │
│  │  │ Entity Detection│  │ Tile Detection  │  │ Ability Check   │  │  │
│  │  │ (YOLO ONNX)     │  │ (YOLO ONNX)     │  │ (HSV pixels)    │  │  │
│  │  │                  │  │                  │  │                  │  │  │
│  │  │ player: [x1,y1..]│  │ walls: [[x1,y1],│  │ super_ready: T/F│  │  │
│  │  │ enemy: [x1,y1..] │  │         ...]    │  │ gadget_ready: T/F│  │  │
│  │  │ teammate: [...]  │  │ bushes: [...]  │  │ hyper_ready: T/F│  │  │
│  │  └────────┬─────────┘  └────────┬────────┘  └────────┬────────┘  │  │
│  │           │                     │                     │            │  │
│  │           ▼                     ▼                     ▼            │  │
│  │  ┌──────────────────────────────────────────────────────────────┐  │  │
│  │  │                   Play.loop()                                 │  │
│  │  │  Build context dict:                                           │  │
│  │  │   entities, walls, abilities, ranges, hit_circles,            │  │
│  │  │   poi.json_gas, joystick, loop_count, game_state...           │  │
│  │  │                                                                │  │
│  │  │  interpret_iris_code(context) → movement (x, y)               │  │
│  │  └──────────────────────────┬───────────────────────────────────┘  │
│  │                             │                                      │
│  │                             ▼                                      │
│  │  ┌──────────────────────────────────────────────────────────────┐  │
│  │  │               Post-processing                                 │  │
│  │  │  • unstuck_movement_if_needed() (progressive angle rotation)   │  │
│  │  │  • Clamp movement to JOYSTICK_RADIUS × ratio                  │  │
│  │  │  • Use abilities if ready and script says so                  │  │
│  │  │  • publish_debug_view() via shared memory                     │  │
│  │  └──────────────────────────┬───────────────────────────────────┘  │
│  │                             │                                      │
│  │                             ▼                                      │
│  │  ┌──────────────────────────────────────────────────────────────┐  │
│  │  │               WindowController.move(x, y)                     │  │
│  │  │  Scale (x,y) by JOYSTICK_RADIUS=75                           │  │
│  │  │  Send touch_down(anchor) + touch_move(target) via ADB        │  │
│  │  │  or scrcpy control socket                                    │  │
│  │  └──────────────────────────────────────────────────────────────┘  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## State Checker Flow

```
┌──────────────┐
│ State Checker│
│ Thread       │
│ (daemon)     │
└──────┬───────┘
       │ every N seconds (configurable)
       ▼
┌──────────────────┐
│ get_state(frame) │
│                  │
│ 1. Check end     │
│    results       │
│ 2. Check lobby   │
│ 3. Check match   │
│    making        │
│ 4. Check brawler │
│    selection     │
│ 5. Check shop    │
│ 6. Check popup   │
│ 7. Check brawl   │
│    pass          │
│ 8. Check star    │
│    road          │
│ 9. Check prestige│
│    milestone     │
│ 10. Check nano   │
│     noodles      │
│ 11. Check star   │
│     drops (4)    │
│ 12. Check trophy │
│     reward       │
│ 13. Check idle/  │
│     disconnect   │
│ 14. Default:     │
│     "match"      │
└────────┬─────────┘
         │
         ▼
    Shared state
    updated: current_state
```

## Menu Lifecycle Flow

```
                    ┌──────────┐
                    │  LOBBY   │
                    │          │
                    │ start    │
                    │ game()   │
                    └────┬─────┘
                         │ press "play"
                         ▼
                   ┌───────────┐
              ┌───▶│ MATCH     │◀──── wait for match
              │    │ MAKING    │
              │    └─────┬─────┘
              │          │ match found
              │          ▼
              │    ┌──────────┐
              │    │ MATCH    │  ←─ Play.main() runs here
              │    │          │
              │    └─────┬────┘
               │          │ match ends
               │          ▼
               │    ┌──────────┐
               │    │ END      │
               │    │ SCREEN   │
               │    │ (timeout │
               │    │  >35s →  │
               │    │ restart  │
               │    │  BS)     │
               │    └──────┬───┘
              │           │
              │     ┌─────┴──────┐
              │     │            │
              │   Victory     Defeat/Draw
              │     │            │
              │  "Play Again"    │ check losses
              │     │            │
              │     └──┬─────────┘
              │        │
              │   ┌────┴────┐
              │   │  STAR   │
              │   │  DROPS  │── optional reward screens
              │   │  SHOP   │
              │   │  TROPHY │
              │   └────┬────┘
              │        │
              └────────┘
```

## Thread Communication

```
┌─────────────────────────────────────────────────────────────────────┐
│                     INTER-THREAD COMMUNICATION                       │
│                                                                      │
│  MAIN LOOP THREAD         STATE CHECKER THREAD    SCRCPY THREAD     │
│  ┌─────────────────┐      ┌──────────────────┐    ┌──────────────┐  │
│  │ Main.main()     │      │ state_checker()  │    │ scrcpy       │  │
│  │                 │      │                  │    │ stream_loop  │  │
│  │ Reads:          │      │ Reads:           │    │              │  │
│  │ • latest_frame  │      │ • latest_frame   │    │ Writes:      │  │
│  │ • current_state │      │                  │    │ • frame to   │  │
│  │                 │      │ Writes:          │    │   listeners  │  │
│  │ Writes:         │      │ • current_state  │    └──────────────┘  │
│  │ • touch cmds    │      │                  │                      │
│  │   to ADB/scrcpy │      └──────────────────┘                      │
│  └─────────────────┘                                                │
│         │                      │                                     │
│         │     RuntimeControl   │  (threading.Event)                  │
│         │     ┌──────────────┐ │                                     │
│         │     │ stop_event   │ │                                     │
│         └─────│ pause_event  │─┘                                     │
│               │ state        │                                       │
│               └──────────────┘                                       │
│                      ▲                                               │
│                      │                                               │
│         ┌────────────┴────────────┐                                  │
│         │                         │                                  │
│   ┌───────────┐           ┌────────────┐                             │
│   │ Flask Web │           │  Discord   │                             │
│   │  UI       │           │  Bot      │                             │
│   │           │           │           │                             │
│   │ Sets:     │           │ Commands: │                             │
│   │ • stop    │           │ /start    │                             │
│   │ • pause   │           │ /stop     │                             │
│   │ • start   │           │ /pause    │                             │
│   └───────────┘           └────────────┘                             │
│                                                                      │
│  DEBUG VIEW (separate process via shared memory)                    │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ DebugViewPublisher (main process)                            │   │
│  │   publish(frame, detection_data)                             │   │
│  │     → writes detection JSON to shared memory seg             │   │
│  │     → copies frame bytes to shared memory seg                │   │
│  │                                                              │   │
│  │ DebugViewWorker (subprocess)                                 │   │
│  │   reads shared memory → renders OpenCV overlay → shows      │   │
│  │   Optionally: records MP4 clip via DebugClipRecorder         │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Remote API Flow

```
┌──────────┐     POST /api/results     ┌──────────────┐
│ IrisAI   │──────────────────────────▶│ API Server   │
│ (client) │      {brawler, result,    │ (remote)     │
│          │       trophies, ...}      │              │
│          │                           │ Brawlify     │
│          │◀──────────────────────────│/BS API       │
│          │     {player_info,         │              │
│          │      brawler_stats, ...}   │              │
└──────────┘                           └──────────────┘

Note: When api_base_url = "localhost", cloud features are disabled
(match results not sent, early access login bypassed).
```

## Webhook Notification Flow

```
┌──────────┐  WIN/LOSS/IDLE event   ┌──────────────┐  ┌──────────────┐
│ IrisAI   │──────────────────────▶│ Discord       │  │ Telegram     │
│          │     notify_user()     │ Webhook       │  │ Bot          │
│          │                       │ (with screen- │  │ (with screen- │
│          │                       │  shot)       │  │  shot)       │
└──────────┘                       └──────────────┘  └──────────────┘

Configured in cfg/webhook_config.toml:
- webhook_url: Discord webhook URL
- bot_token: Discord bot token (for slash commands)
- telegram_token/telegram_chat_id: Telegram notifications
- ping_settings: ping interval, minimum trophy threshold
```
