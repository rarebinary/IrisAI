# Game State Machine

## State Definitions

States are detected by `state_finder.py` via OpenCV template matching, then dispatched to `StageManager` handlers.

```
                    ┌──────────────────────────────┐
                    │           LOBBY               │
                    │  idle screen, ready to queue   │
                    │  Handler: start_game()         │
                    │    → check trophy/wins targets │
                    │    → switch brawler if needed  │
                    │    → press "play" button       │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │       MATCH_MAKING            │
                    │  searching for opponent       │
                    │  Handler: (auto, no action)   │
                    │  waits for state to change    │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────┴───────────────┐
                    │                              │
                    ▼                              ▼
     ┌──────────────────────────┐    ┌──────────────────────────┐
     │       MATCH              │    │   BRAWLER_SELECTION      │
     │  gameplay in progress    │    │  (may appear after       │
     │  Handler: Play.main()    │    │   match found)           │
      │    → run YOLO detection  │    │  Handler: (no-op)               │
      │    → execute .iris code  │    │  brawler selected by            │
      │    → send touch commands │    │  start_game() → LobbyAutomation │
     └───────────┬──────────────┘    └──────────────────────────┘
                 │
                 ▼
     ┌──────────────────────────┐
     │   END_VICTORY / END_     │
     │   DEFEAT / END_DRAW /    │
     │   END_TRIO_SHOWDOWN_X    │
     │                          │
     │  Handler: end_game()     │
     │    → TrophyObserver      │
     │    → "play again" click  │
     │    → check loss limits   │
     └───────────┬──────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
┌──────────────┐     ┌────────────────┐
│ STAR_DROP    │     │   (optional)   │
│ (4 types)    │     │                │
│ Handler:     │     │ TROPHY_REWARD  │
│ click_star_  │     │ PRESTIGE       │
│ drop()       │     │ NANO_NOODLES   │
└──────────────┘     │ SHOP           │
                     │ POPUP          │
                     └───────┬────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │    LOBBY       │ ←─ return to start
                    └────────────────┘
```

## State Detection Priority (state_finder.py)

`get_state(screenshot)` checks templates in this order:

1. **End-of-match results** — `find_game_result()` checks `images/end_results/`
   - Victory: `victory.png` (template match, threshold 0.75)
   - Defeat: `defeat.png`
   - Draw: `draw.png`
   - Showdown 1st-4th: `1st.png` → `4th.png` (threshold `SHOWDOWN_PLACE_THRESHOLD = 0.9`)
2. **Lobby** — `lobby_menu.png`
3. **Matchmaking** — `exit_match_making.png`
4. **Brawler selection** — `brawler_menu_heart.png`
5. **Shop** — `powerpoint.png`
6. **Offer popup** — `close_popup.png`
7. **Brawl pass** — `brawl_pass_house.png`
8. **Star road** — `go_back_arrow.png`
9. **Prestige milestone** — `prestige_continue.png`
10. **Nano Noodles** — specific `DAILY WINS` title signature from real emulator captures (`nano_noodles_daily_wins.png`, threshold 0.8)
11. **Star drops** — 4 named types: `star_drop_regular`, `star_drop_angelic`, `star_drop_demonic`, `star_drop_starr_nova`
12. **Trophy reward** — `trophies_screen.png`
13. **Android app not responding** — `app_not_responding.png`; releases controls and restarts Brawl Stars immediately.
14. **Cannot rejoin battle** — `cannot_rejoin_battle.png`; releases controls and presses `RELOAD`.
15. **Loading** — loading logo or launch icon; inference and movement remain paused.
16. **Match intro** — centered `VS` signature; controls stay released until gameplay begins.
17. **Spectating** — bottom-right `Following:` signature; controls stay released while the player is dead.
18. **Idle/disconnect** — current dialog-title crop in `idle_disconnect.png` (threshold 0.6). The main loop handles this state immediately instead of waiting for the normal no-detection timer.
19. **Default:** `"match"` (assume in-game if nothing else matches)

`match_making` is a healthy waiting state, not a stuck condition. After Play Again,
reaching `match_making`, `loading`, `match_intro`, or `brawler_selection` hands
control back to the normal state loop without restarting Brawl Stars. A restart is
reserved for cases where no matchmaking progress is detected within the timeout.

## StageManager States Dict

```python
self.states = {
    'shop': self.quit_shop,
    'brawler_selection': lambda: 0,  # no-op (handled by start_game)
    'popup': self.close_pop_up,
    'match': lambda: 0,  # handled by Play.main()
    'loading': lambda: 0,
    'match_intro': lambda: 0,
    'spectating': lambda: 0,
    'match_making': lambda: 0,  # auto-wait
    'lobby': self.start_game,
    'star_drop_regular': lambda: self.click_star_drop("regular"),
    'star_drop_angelic': lambda: self.click_star_drop("angelic"),
    'star_drop_demonic': lambda: self.click_star_drop("demonic"),
    'star_drop_starr_nova': lambda: self.click_star_drop("starr_nova"),
    'trophy_reward': lambda: self.window_controller.press("proceed"),
    'prestige_milestone': lambda: self.window_controller.press("continue_or_equip"),
    'end_draw': self.end_game,
    'end_victory': self.end_game,
    'end_defeat': self.end_game,
    'end_trio_showdown_0': self.end_game,
    'end_trio_showdown_1': self.end_game,
    'end_trio_showdown_2': self.end_game,
    'end_trio_showdown_3': self.end_game,
    'nano_noodles': self.click_nano_noodles,
    'idle_disconnect': self.handle_idle_disconnect,
    'app_not_responding': self.handle_app_not_responding,
    'cannot_rejoin_battle': self.handle_cannot_rejoin_battle,
}
```

## Key State Transitions

### start_game() (lobby → match_making)
```
1. Wait 3s for API update (early_access)
2. If pending brawler switch: try LobbyAutomation.select_brawler()
   → on failure, rotate brawler to end of queue and retry
3. If current brawler reached target trophies/wins:
   → find next brawler in queue
   → if none left, stop bot
4. Handle play order rotation
5. Send match webhook ping if due (matches_since_last_webhook_ping)
6. Click "proceed" button at configured coordinates
```

### end_game() (end_screen → lobby)
```
1. Loop up to 35s while state starts with "end"
2. After 25s, parse game result via TrophyObserver.parse_game_result()
3. Calculate trophy delta via TrophyObserver.add_trophies()
   → updates win/lose streaks, applies trophy floors
4. Save to match_history.csv
5. Send to remote API (unless localhost)
6. If victory and play_again_on_win: click "play_again" button
   → treat matchmaking/loading/match intro as successful progress
   → continue waiting through the normal state loop instead of restarting
7. If defeat/draw:
   → increment loss counter
   → if max_losses exceeded → rotate to next brawler
   → if max_consecutive_losses exceeded → _rotate_to_lowest_trophy_brawler()
   → if end screen visible >35s → restart BS
8. After loss limits: _rotate_to_lowest_trophy_brawler() reorders queue
```

### Trophy/Win Targets
Configured per brawler in the queue (via Web UI). When a brawler reaches its target, the bot automatically switches to the next brawler in the queue. When all brawlers have met their targets, the bot stops.

### Pause/Stop Behavior
Stop/pause signals are **only honored when state == "lobby"**. This prevents interrupting an active match. Pausing in-lobby means the bot won't queue for the next match but completes any current match first.
