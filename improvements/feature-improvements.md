# Nouvelles Fonctionnalités - Puissance & Intelligence

Ce doc liste des fonctionnalités à forte valeur ajoutée pour rendre le bot plus performant, adaptatif et compétitif. Chaque feature : **but**, **approche technique**, **effort estimé**, **dépendances**.

---

## 1. Détection & Adaptation de Carte (Map Awareness)

### But
Le bot ne connaît pas la map. Il joue pareil sur Gem Grab, Brawl Ball, Showdown, Knockout, Hot Zone, etc. Adapter le comportement à la map = énorme gain de winrate.

### Approche technique
- **Détection map** : Template matching sur éléments uniques au chargement (nom de map en haut, layout distinctif). 15-20 maps actuelles → ~20 templates.
- **Base de données maps** : JSON avec méta par map : `lanes`, `zones_de_controle`, `spawn_points`, `powerup_spawns`, `bush_positions`, `wall_clusters`, `symmetry`.
- **Intégration playstyle** : Contexte `game_state["map_name"]`, `game_state["map_meta"]` dispo dans `.pyla`.

```python
# Exemple usage dans playstyle
map_meta = game_state.get("map_meta", {})
if map_meta.get("name") == "Double Swoosh":
    # Lane control critique
    movement = control_center_lane()
elif map_meta.get("name") == "Layer Cake":
    # Bush control
    movement = deny_bush_access()
```

### Effort
- **Templates** : 2-3 jours (capture + calibrage)
- **Détection** : 1 jour (réutilise `state_finder.py`)
- **Intégration** : 2 jours (contexte + doc playstyle)
- **Total** : ~1 semaine

### Dépendances
- `state_finder.py` (existant)
- Nouveaux fichiers : `maps/map_database.json`, `maps/detector.py`

---

## 2. Scouting Adversaire & Contre-Pick Dynamique

### But
Avant le match, analyser la compo ennemie (brawlers, star powers, gadgets, gears) et adapter : choix de brawler, playstyle, build.

### Approche technique
- **Source de données** : API Brawlify / BS API via player tag ennemis (dispo dans `trophy_observer.py` via match history)
- **Analyse** : Classer la compo ennemie (poke, contrôle, assassin, tank, thrower, hybride)
- **Contre-pick** : Table de matchups par brawler (ex: vs thrower → pick long range / mobility ; vs assassin → pick peel / tank)
- **Application** : Dans `stage_manager.py:start_game()`, avant de picker, si slot libre → choisir meilleur contre-pick dispo dans la queue

### Données nécessaires
```json
// brawlers_matchups.json
{
  "shelly": {
    "counters": ["colt", "brock", "piper", "byron"],
    "countered_by": ["bull", "el primo", "rosa", "frank"],
    "synergies": ["gene", "tara", "sandy"],
    "map_preferences": ["open", "mid_range"]
  }
}
```

### Effort
- **API scouting** : 2 jours (intégration Brawlify, cache)
- **Logique matchup** : 3 jours (algo + données)
- **Intégration queue** : 1 jour
- **Total** : ~1.5 semaine

### Dépendances
- `trophy_observer.py` (player tags)
- `webui/services.py` (API Brawlify existante)
- Nouveaux fichiers : `matchups/`, `scouting/`

---

## 3. Gestion Avancée Supers / Gadgets / Hypercharges (Ability Manager)

### But
Aujourd'hui : utilisation basique (si prêt + en range → fire). Objectif : gestion tactique - économie, setup, combo, bait, zoning.

### Approche technique
Créer `ability_manager.py` avec classe `AbilityManager` :

```python
class AbilityManager:
    def __init__(self, brawler_info, context):
        self.brawler = brawler_info["name"]
        self.super_type = brawler_info.get("super_type")
        self.gadgets = brawler_info.get("gadgets", [])
        self.hypercharge = brawler_info.get("hypercharge")
    
    def evaluate_super(self, enemies, teammates, walls, game_state) -> SuperDecision:
        """
        Returns: SKIP | FIRE_NOW | SAVE_FOR_COMBO | USE_FOR_ZONING | USE_FOR_ESCAPE
        """
    
    def evaluate_gadget(self, ...) -> GadgetDecision:
        ...
```

#### Logiques par type de super
| Type | Logique |
|------|---------|
| `projectile` | Prédire trajectoire ennemie, lead shot, wall bounce |
| `area` / `spawnable` | Placer au centre de masse ennemie, ou zone contrôle objectif |
| `charge` | Engager seulement si kill garanti ou escape |
| `self_buff` | Activer avant fight, pas pendant |
| `mobility` | Gap close OU escape, jamais au milieu |
| `heal` / `shield` | Proactif si HP équipe < seuil |

#### État persistant
`persistent_data["super_intent"] = "zoning"` / `"combo"` / `"escape"` → cohérence multi-frames.

### Intégration playstyle
```python
# Dans .pyla
super_decision = ability_manager.evaluate_super(enemies, teammates, walls, game_state)
if super_decision == "FIRE_NOW":
    use_super()
elif super_decision == "SAVE_FOR_COMBO":
    wait_for_combo_setup()
```

### Effort
- **Core manager** : 3 jours
- **Logiques par brawler** : 5-7 jours (itératif, commencer par top 20 meta)
- **Intégration** : 1 jour
- **Total** : ~2 semaines

### Dépendances
- `brawlers_info.json` (étendu avec `super_type`, `gadgets`, `hypercharge`)
- `play.py` (contexte existant)

---

## 4. Positionning Avancé & Control de Zone (Zone Control)

### But
Le bot bouge "vers l'ennemi" ou "vers le coéquipier". Objectif : contrôle d'espace, denial de bush, contrôle d'objectif (gem, ball, zone, hot zone), positioning défensif/offensif selon état du match.

### Approche technique
Créer `positioning.py` avec `PositionEvaluator` :

```python
class PositionEvaluator:
    def __init__(self, map_meta, game_mode, game_state):
        self.map_meta = map_meta
        self.mode = game_mode
        self.state = game_state  # gem_count, ball_possession, zone_progress, time_remaining
    
    def score_position(self, pos: tuple, role: str) -> float:
        """
        Score 0-1 pour une position donnée.
        Role: "aggro" | "control" | "support" | "defense" | "objective"
        """
        score = 0
        # Facteurs :
        # - Distance aux ennemis (danger)
        # - Distance aux coéquipiers (support)
        # - Couverture murs/bush (safety)
        # - Contrôle objectif (gem mine, ball, zone)
        # - Accès powerups
        # - Ligne de vue sur zones clés
        # - Distance au poison (showdown/knockout)
        return score
    
    def find_best_position(self, current_pos, role, radius=300) -> tuple:
        # Échantillonne positions autour, retourne la mieux scorée
        ...
```

### Rôles dynamiques selon match state
| Game Mode | Early Game | Mid Game | Late Game (avantage) | Late Game (désavantage) |
|-----------|------------|----------|---------------------|------------------------|
| Gem Grab | Control mid | Control mid + deny | Aggro carry | Defense + wait for mistake |
| Brawl Ball | Control mid | Ball control / defense | Push avec ball | Intercept + counter |
| Hot Zone | Zone control | Zone control | Expand control | Contest aggressively |
| Knockout | Survival | Trade favorably | Zone control + trade | Play safe, wait for gas |
| Showdown | Loot + position | Mid control | Agro low HP | Third party |

### Intégration playstyle
```python
# Dans .pyla
position_eval = game_state["position_evaluator"]
best_pos = position_eval.find_best_position(player_pos, my_role)
movement = move_toward(best_pos)
```

### Effort
- **Core evaluator** : 3 jours
- **Méta par mode/map** : 4 jours (data-driven)
- **Intégration** : 1 jour
- **Total** : ~1.5 semaine

---

## 5. Team Coordination & Communication Implicite

### But
3v3 = coordination. Le bot ne "voit" pas les intentions des alliés. Objectif : inférer leurs actions et s'adapter (follow engage, peel, trade, setup combo).

### Approche technique
Analyser `teammate_data` chaque frame :

```python
class TeamCoordinator:
    def analyze_teammates(self, teammates, enemies, game_state) -> TeamIntent:
        intents = []
        for tm in teammates:
            intent = self.infer_intent(tm, enemies, game_state)
            intents.append(intent)
        
        # Déduire intention collective
        return self.synthesize_team_intent(intents)
    
    def infer_intent(self, teammate, enemies, game_state):
        # Basé sur : movement vector, distance ennemis, HP, super ready, position relative
        # Returns: "engage" | "retreat" | "farm" | "objective" | "peel" | "setup_combo"
        ...
    
    def should_follow_engage(self, team_intent) -> bool:
        # Si 2+ allies engage + nous avons super/gadget pour follow-up
        ...
    
    def should_peel(self, team_intent) -> bool:
        # Si allié low HP + ennemis sur lui
        ...
```

### Signaux observables
| Signal | Interprétation |
|--------|----------------|
| Mouvement vers ennemis + super ready | Engage imminent |
| Mouvement vers alliés low HP | Peel / heal |
| Stationnaire dans bush + ennemis proches | Ambush / wait |
| Mouvement vers objectif (gem/ball/zone) | Objective play |
| Recul soudain + HP bas | Retreat |

### Actions dérivées
- **Follow engage** : Se positionner pour combo (ex: Gene pull + notre super)
- **Peel** : Se mettre entre allié low HP et ennemis
- **Trade** : Si allié engage et meurt, punir l'ennemi qui a over-extend
- **Setup combo** : Attendre que allié initie (ex: Tara super) → follow immédiat

### Effort
- **Analyseur intent** : 3 jours
- **Logiques de réponse** : 3 jours
- **Intégration** : 1 jour
- **Total** : ~1.5 semaine

---

## 6. Apprentissage par Renforcement (RL) pour Playstyles

### But
Remplacer les `.pyla` scriptés par des politiques apprises, ou au moins optimiser les paramètres des playstyles existants (seuils, poids, timings).

### Approche technique

#### Phase 1 : Parameter Optimization (CMA-ES / Optuna)
- Définir espace de paramètres par playstyle (ex: `aggro_threshold`, `retreat_hp_pct`, `super_save_frames`, `zone_weight`)
- Fonction de récompense : `win_rate * 100 - avg_match_time * 0.1 - deaths * 5`
- Lancer optimisation en parallèle sur multiple comptes/émulateurs
- Sauvegarder meilleurs params par brawler/map/mode

#### Phase 2 : Policy Network (PPO / SAC)
- Observation space : entities (pos, hp, super), walls, bushes, gas, objectives, time, score
- Action space : movement (8 directions + stop) + abilities (attack, super, gadget, hyper)
- Reward shaping : +1 kill, +0.5 assist, +2 objective control, -1 death, -0.5 damage taken, +0.1 survival/time
- Entraînement : self-play + vs scripted baselines
- Export : ONNX pour inférence dans `play.py` (remplace `interpret_pyla_code`)

### Infrastructure requise
- **Parallel runner** : Lancer N instances headless (via `max_ips` bas, pas de debug view)
- **Replay buffer** : Stockage transitions (SQLite / LMDB)
- **Trainer** : Processus séparé (GPU) qui lit buffer, met à jour policy, push nouveau modèle
- **Hot-reload** : `play.py` recharge modèle ONNX à la volée sans redémarrer

### Effort
- **Phase 1 (params)** : 1 semaine (infrastructure + quelques runs)
- **Phase 2 (policy)** : 3-6 semaines (R&D, itératif)
- **Total** : 1-2 mois pour version viable

### Dépendances
- `play.py` (refactor pour accepter policy network)
- Infrastructure multi-instance
- GPU pour training (ou cloud)

---

## 7. Replay Analysis & Auto-Amélioration

### But
Analyser les matchs perdus pour identifier patterns d'erreurs et suggérer corrections (playstyle, config, pick).

### Approche technique
- **Enregistrement** : `debug_view.py` enregistre déjà MP4 clips. Étendre pour sauver le match complet (positions, actions, events) en format structuré (JSON Lines / Protocol Buffers).
- **Analyseur post-match** : Script qui parse le replay et détecte :
  - Morts évitables (gaz, sur-extension, pas de peel)
  - Supers/gadgets gaspillés (tir dans mur, hors range)
  - Mauvais positioning (pas de zone control, isolation)
  - Manque de follow-up / peel
- **Rapport** : Générer résumé textuel + suggestions concrètes
  - "Tu meurs 40% du temps dans le gaz → augmenter `gas_avoidance_weight`"
  - "Super gâché 60% du temps → activer `super_save_for_combo`"
  - "Perte sur map X avec brawler Y → éviter ce pick sur cette map"

### Effort
- **Enregistrement structuré** : 2 jours
- **Analyseur patterns** : 4 jours (itératif, commencer par patterns simples)
- **Rapport & UI** : 2 jours
- **Total** : ~1.5 semaine

---

## 8. Kill Feed & Event Parsing (Game Sense)

### But
Le bot ne "voit" pas les kills/morts/enemy respawn. Il infère seulement via détection d'entités. Parser le kill feed (zone en haut à droite) donnerait info critique : qui a tué qui, avec quoi, respawn timers.

### Approche technique
- **OCR zone kill feed** : Région fixe haut-droite, EasyOCR ou Tesseract entraîné sur font Brawl Stars
- **Event parsing** : Regex sur texte "Player1 [icon] Player2" → killer, victim, weapon type
- **State tracking** : Maintenir `enemy_respawn_timers` dict, `teammate_respawn_timers`
- **Utilisation** : Savoir qu'un ennemi est mort → push agressif 8-10s ; savoir qu'un allié va respawn → wait pour engage

### Effort
- **Zone OCR** : 2 jours (calibrage région, font)
- **Parsing robuste** : 2 jours
- **Intégration timers** : 1 jour
- **Total** : ~1 semaine

---

## 9. Auto-Build Gadget / Star Power / Gear Selection

### But
Au chargement du match, choisir automatiquement le meilleur gadget / star power / gear selon : map, mode, compo ennemie, compo équipe.

### Approche technique
- **Base de données builds** : Par brawler, lister options avec tags situationnels
```json
{
  "shelly": {
    "gadgets": [
      {"name": "Fast Forward", "tags": ["mobility", "aggro", "open_maps"]},
      {"name": "Clay Pigeons", "tags": ["control", "defense", "bush_maps"]}
    ],
    "star_powers": [
      {"name": "Shell Shock", "tags": ["slow", "control", "teamfight"]},
      {"name": "Band-Aid", "tags": ["sustain", "solo", "showdown"]}
    ]
  }
}
```
- **Sélection** : Au `start_game()`, matcher tags contre contexte (map_meta, enemy_compo, ally_compo, mode)
- **Application** : Cliquer les bons boutons dans l'écran de sélection (déjà géré par `LobbyAutomation`)

### Effort
- **DB builds** : 3 jours (recherche méta, validation)
- **Sélection contextuelle** : 2 jours
- **Intégration lobby** : 1 jour
- **Total** : ~1 semaine

---

## 10. Anti-Ban / Humanization Avancé

### But
Réduire détection par analyse comportementale (patterns trop parfaits, timing identique, paths optimaux).

### Techniques
| Technique | Description |
|-----------|-------------|
| **Jitter clicks** | Offset aléatoire ±5-10px sur coordonnées clics |
| **Micro-pauses** | Delais aléatoires 0.1-0.4s entre actions (attack, super, mouvement) |
| **Reaction delay** | Simuler temps de réaction humain (80-250ms) avant réagir à ennemi visible |
| **Imperfect paths** | Ne pas prendre le chemin optimal exact, légers détours |
| **Variable session length** | Sessions 30-70 min (pas fixes), pauses aléatoires 5-20 min entre sessions |
| **Mouse curve** | Mouvement joystick avec courbe de Bézier au lieu de linéaire |

### Intégration
- Configurable via `bot_config.toml` : `humanization_level = "low" | "medium" | "high" | "off"`
- Appliqué dans `window_controller.py` (clics) et `play.py` (décisions)

### Effort
- **Core humanization** : 3 jours
- **Config + tests** : 2 jours
- **Total** : ~1 semaine

---

## 11. Multi-Account / Farming Orchestrator

### But
Gérer plusieurs comptes simultanément (ou séquentiellement) pour farm trophées / star drops / event tokens.

### Approche
- **Account manager** : Liste comptes avec device_id / emulator_port / credentials
- **Scheduler** : Round-robin ou priorité (compte le plus bas en trophées d'abord)
- **Session rotation** : Compte A joue 45min → pause 15min → Compte B joue 45min...
- **Resource sharing** : Modèles ONNX, configs, playstyles partagés
- **Unified dashboard** : Web UI agrégée showing tous comptes

### Effort
- **Account manager** : 3 jours
- **Scheduler + rotation** : 2 jours
- **Dashboard multi-compte** : 3 jours
- **Total** : ~1.5 semaine

---

## 12. Tournament / Competitive Mode

### But
Mode "tryhard" pour tournois / push haut ladder : draft assist, counter-pick en temps réel, comms Discord intégrées, replay auto-save pour review.

### Features
- **Draft assistant** : Overlay showing best picks/bans vs équipe adverse connue
- **Live counter-pick** : Pendant pick phase, suggérer pick optimal en temps réel
- **Discord integration** : `/scrim` commande pour créer lobby, inviter équipe, share strat
- **Auto-replay save** : Tous matchs tournoi sauvés avec metadata (équipe, map, résultat)
- **Post-match review** : Génération automatique de clips clés (teamfights, throws, clutches)

### Effort
- **Draft logic** : 2 jours
- **Discord bot commands** : 2 jours
- **Replay system** : 3 jours
- **Review automation** : 3 jours
- **Total** : ~2 semaines

---

## Priorisation Suggérée (Impact / Effort)

| Priorité | Feature | Impact | Effort | Ratio |
|----------|---------|--------|--------|-------|
| 1 | **Ability Manager** | ⭐⭐⭐⭐⭐ | ⭐⭐ | 2.5 |
| 2 | **Map Awareness** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 1.7 |
| 3 | **Zone Control / Positioning** | ⭐⭐⭐⭐ | ⭐⭐⭐ | 1.3 |
| 4 | **Team Coordination** | ⭐⭐⭐⭐ | ⭐⭐⭐ | 1.3 |
| 5 | **Scouting / Counter-pick** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 1.0 |
| 6 | **Kill Feed Parsing** | ⭐⭐⭐ | ⭐⭐ | 1.5 |
| 7 | **Auto Build Selection** | ⭐⭐⭐ | ⭐⭐ | 1.5 |
| 8 | **Humanization / Anti-ban** | ⭐⭐⭐ | ⭐⭐ | 1.5 |
| 9 | **Replay Analysis** | ⭐⭐⭐ | ⭐⭐⭐ | 1.0 |
| 10 | **RL Optimization** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 1.0 |
| 11 | **Multi-Account** | ⭐⭐ | ⭐⭐⭐ | 0.7 |
| 12 | **Tournament Mode** | ⭐⭐ | ⭐⭐⭐⭐ | 0.5 |

---

## Architecture Modulaire Recommandée

Pour éviter le spaghetti code, organiser les nouvelles features en modules indépendants :

```
src/
├── maps/
│   ├── detector.py          # Détection map au chargement
│   ├── database.json        # Méta par map
│   └── __init__.py
├── scouting/
│   ├── analyzer.py          # Analyse compo ennemie
│   ├── matchups.json        # Table matchups
│   └── __init__.py
├── abilities/
│   ├── manager.py           # AbilityManager core
│   ├── logic/               # Logiques par type de super
│   │   ├── projectile.py
│   │   ├── area.py
│   │   ├── charge.py
│   │   ├── mobility.py
│   │   └── support.py
│   └── __init__.py
├── positioning/
│   ├── evaluator.py         # PositionEvaluator core
│   ├── roles.py             # Définitions rôles par mode
│   └── __init__.py
├── teamplay/
│   ├── coordinator.py       # TeamCoordinator
│   └── __init__.py
├── rl/
│   ├── optimizer.py         # Phase 1: param optimization
│   ├── trainer.py           # Phase 2: policy training
│   ├── policy_net.py        # Network definition
│   └── __init__.py
├── replay/
│   ├── recorder.py          # Enregistrement structuré
│   ├── analyzer.py          # Post-match analysis
│   └── __init__.py
├── humanization/
│   ├── click_jitter.py
│   ├── reaction_delay.py
│   ├── path_imperfection.py
│   └── __init__.py
├── killfeed/
│   ├── ocr.py
│   ├── parser.py
│   └── __init__.py
├── builds/
│   ├── database.json
│   ├── selector.py
│   └── __init__.py
└── multiaccount/
    ├── manager.py
    ├── scheduler.py
    └── __init__.py
```

Chaque module expose une API simple utilisée par `play.py` via le context dict. Exemple :

```python
# Dans play.py loop()
from maps import get_current_map_meta
from abilities import AbilityManager
from positioning import PositionEvaluator
from teamplay import TeamCoordinator

context = {
    ...
    'map_meta': get_current_map_meta(frame),
    'ability_manager': AbilityManager(brawler_info, context),
    'position_evaluator': PositionEvaluator(map_meta, game_mode, game_state),
    'team_coordinator': TeamCoordinator(),
    ...
}
```

---

## Tests de Validation par Feature

| Feature | Test Clé |
|---------|----------|
| Map Awareness | Lancer sur 5 maps différentes → comportement distinct observé |
| Scouting | Match vs compo connue → bot pick contre-pick optimal |
| Ability Manager | Super usage rate > 80% "bon timing" (validé manuellement) |
| Zone Control | Heatmap positions montre contrôle objectif vs random |
| Team Coord | 2v1 situations → bot peel/follow correct 70%+ |
| RL Params | Winrate +5% vs playstyle scripté après optimisation |
| Replay Analysis | 10 matchs → rapport identifie au moins 1 pattern correct |
| Kill Feed | Parse accuracy > 95% sur 100 events |
| Auto Build | 20 matchs → build choisi match contexte 90%+ |
| Humanization | Session 2h → pas de détection pattern (test manuel) |

---

## Ordre d'Implémentation Recommandé

1. **Ability Manager** (quick win, impact immédiat sur tous brawlers)
2. **Map Awareness** (fondamental pour toutes features suivantes)
3. **Zone Control / Positioning** (s'appuie sur map meta)
4. **Team Coordination** (s'appuie sur positioning)
5. **Scouting / Counter-pick** (améliore draft)
6. **Kill Feed + Build Selection** (quality of life)
7. **Humanization** (sécurité)
8. **Replay Analysis** (feedback loop)
9. **RL Optimization** (long terme, besoin infrastructure)
10. **Multi-Account / Tournament** (niche)