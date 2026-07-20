# Nouvelles Fonctionnalités - Puissance & Intelligence

Ce doc liste des fonctionnalités à forte valeur ajoutée pour rendre le bot plus performant, adaptatif et compétitif. Chaque feature est décrite avec : **but**, **approche technique**, **effort estimé**, **dépendances**.

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
- **Analyse** : Classe la compo ennemie (poke, contrôle, assassin, tank, thrower, hybride)
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

## 3. Gestion Avancée des Supers / Gadgets / Hypercharges (Ability Manager)

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
| `area` / `spawnable` | Placer au centre de masse ennemie, ou zone de contrôle objectif |
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
| Signal | Interpretation |
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
  - Supers/gadgets gaspillés (tir dans mur, hors range, pas de cible)
  - Positioning sous-optimal (loin de l'objectif, dans bush connu ennemi)
  - Manque de coordination (allié engage seul, pas de follow)
  - Erreurs de pick (brawler contre la compo adverse / map)

### Format de sortie
Rapport Markdown/HTML par match :
```markdown
## Match Analysis - Perte 2-3 Gem Grab - Double Swoosh

### Top 3 Erreurs
1. **Mort évitable (3:42)** - Tu es rentré dans le bush ennemi sans vision. Mort par Amber.
   → Fix: Activer `check_bush_before_enter` dans playstyle, ou utiliser gadget vision.

2. **Super gaspillé (5:12)** - Shelly super tiré dans le mur à 2 tiles de l'ennemi.
   → Fix: Ajouter check `is_enemy_hittable` avant super (déjà dispo, pas utilisé).

3. **Pas de peel (6:03)** - Ton Colt s'est fait dive par Bull + El Primo. Tu étais à 400px sans réagir.
   → Fix: Activer team_coordination.peel_for_low_hp_allies.

### Stats
- Win prob à 3:00 : 68% → Perte due à 2 morts tardives évitables
- Super efficiency : 34% (cible: >60%)
- Time in safe zone : 72% (cible: >85%)
```

### Effort
- **Enregistrement structuré** : 2 jours (étendre `debug_view.py` / `debug_clip_recorder.py`)
- **Analyseur** : 5 jours (rules engine + patterns)
- **Rapport UI** : 2 jours (intégration Web UI onglet "Analysis")
- **Total** : ~1.5 semaine

---

## 8. Mode Tournoi / Scrims (Competitive Features)

### But
Fonctionnalités pour les équipes qui veulent scrim / tournoi avec le bot.

### Fonctionnalités
| Feature | Description |
|---------|-------------|
| **Draft Assistant** | Interface Web UI pour ban/pick : suggestions en temps réel selon méta, compo allies/ennemis |
| **Pause/Resume synchronisé** | Commande Discord `/pause_all` / `/resume_all` pour arrêter tous les bots de l'équipe en même temps |
| **Replay partagé** | Upload auto des replays vers dossier partagé (Google Drive / S3 / Discord) avec nommage standardisé |
| **Stats équipe** | Dashboard agrégé : winrate par compo, par map, par côté (blue/red), synergy scores |
| **Anti-strat** | Détection patterns adversaires (toujours même engage, même pick) → suggestions contre |

### Effort
- **Draft Assistant** : 1 semaine (UI + logique)
- **Pause sync** : 2 jours (Discord bot + RuntimeManager)
- **Replay upload** : 2 jours
- **Dashboard équipe** : 1 semaine
- **Total** : ~3 semaines

---

## 9. Support Multi-Comptes / Multi-Devices (Farm & Progression)

### But
Faire progresser plusieurs comptes en parallèle (gem farming, star drops, mastery, ranked push).

### Fonctionnalités
| Feature | Description |
|---------|-------------|
| **Device Pool** | Gérer N appareils (émulateurs/téléphones) depuis une UI unique |
| **Account Scheduler** | Planifier : Compte A 6h-10h, Compte B 10h-14h, etc. Rotation auto |
| **Progression Tracker** | Suivi objectifs par compte : trophées, mastery, star drops, ranked rank |
| **Resource Allocation** | Assigner appareils aux comptes selon priorité (push ranked > farm > mastery) |
| **Cloud Sync** | Sync queue, config, stats entre instances via API centrale |

### Architecture
```
Central Coordinator (API + DB)
    │
    ├── Device 1 (emulator) → Bot Instance A → Account 1
    ├── Device 2 (phone)    → Bot Instance B → Account 2
    ├── Device 3 (emulator) → Bot Instance C → Account 3
    └── ...
```
Chaque instance bot = `pyla --device-id=X --account=Y` avec config isolée.

### Effort
- **Coordinator API** : 1 semaine (FastAPI + PostgreSQL + Web UI)
- **Instance isolation** : 3 jours (config par device/account)
- **Scheduler UI** : 1 semaine
- **Total** : ~3 semaines

---

## 10. Deck Tracker & Meta Analyzer (Intelligence Externe)

### But
Suivre la méta globale : winrates par brawler, par map, par mode, par trophées. Adapter les picks/playstyles automatiquement.

### Sources de données
- **Brawlify API** : Leaderboards, profils top joueurs
- **Brawl Stars API** (officielle) : Battle logs publics
- **Propriétaire** : Agrégation de nos propres matchs (anonymisés)

### Fonctionnalités
| Feature | Description |
|---------|-------------|
| **Meta Dashboard** | Web UI : tier list dynamique, winrate par map/mode, pick/ban rates |
| **Auto-Pick Meta** | `stage_manager.py` consulte meta avant pick → choisit brawler optimal |
| **Playstyle Selector** | Change `.pyla` actif selon map/mode/compo (ex: map fermée → `close_range_aggro.pyla`) |
| **Counter-Pick Live** | Pendant draft (si mode tournoi) : suggère pick/ban en temps réel |

### Effort
- **Collecte données** : 1 semaine (scripts + scheduling)
- **Analyse + Dashboard** : 1 semaine
- **Intégration bot** : 3 jours
- **Total** : ~2.5 semaines

---

## Priorisation Suggérée (Impact / Effort)

| # | Feature | Impact | Effort | Ratio | Priorité |
|---|---------|--------|--------|-------|----------|
| 1 | Map Detection + Map Meta | ⭐⭐⭐⭐⭐ | ⭐⭐ | 2.5 | **HIGH** |
| 2 | Ability Manager (Super/Gadget/Hyper) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 1.7 | **HIGH** |
| 3 | Positioning / Zone Control | ⭐⭐⭐⭐ | ⭐⭐⭐ | 1.3 | **HIGH** |
| 4 | Team Coordination | ⭐⭐⭐⭐ | ⭐⭐⭐ | 1.3 | **MEDIUM** |
| 5 | Scouting / Counter-Pick | ⭐⭐⭐⭐ | ⭐⭐⭐ | 1.3 | **MEDIUM** |
| 6 | Replay Analysis | ⭐⭐⭐ | ⭐⭐ | 1.5 | **MEDIUM** |
| 7 | Parameter Optimization (CMA-ES) | ⭐⭐⭐ | ⭐⭐ | 1.5 | **MEDIUM** |
| 8 | Multi-Account / Device Pool | ⭐⭐⭐ | ⭐⭐⭐⭐ | 0.75 | **LOW** |
| 9 | Tournament/Scrim Features | ⭐⭐⭐ | ⭐⭐⭐ | 1.0 | **LOW** |
| 10 | Full RL Policy | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 1.0 | **R&D** |
| 11 | Meta Analyzer | ⭐⭐⭐ | ⭐⭐⭐ | 1.0 | **LOW** |

---

## Roadmap Technique Recommandée

### Sprint 1-2 (Semaines 1-4) : Foundations Puissance
1. **Map Detection** + base de données 10 maps principales
2. **Ability Manager** core + logiques top 10 brawlers meta
3. **Positioning Evaluator** basique (contrôle objectif + safety)

### Sprint 3-4 (Semaines 5-8) : Coordination & Intelligence
4. **Team Coordinator** (inférence intent + follow/peel)
5. **Scouting + Counter-Pick** (intégration Brawlify)
6. **Replay Analyzer** (enregistrement structuré + règles de base)

### Sprint 5-6 (Semaines 9-12) : Optimisation & Polish
7. **Parameter Optimization** (CMA-ES sur playstyles existants)
8. **Meta Analyzer** (collecte + dashboard)
9. **Polish** : bugs, edge cases, docs playstyle nouvelles variables

### Sprint 7+ (Semaines 13+) : R&D & Scale
10. **RL Policy Network** (recherche, pas production immédiate)
11. **Multi-Account Coordinator** (si demande)
12. **Tournament Features** (si équipe competitive)

---

## Nouvelles Variables de Contexte pour Playstyles (à documenter)

Ajouter dans `play.py` contexte pour que les `.pyla` puissent utiliser les nouveaux systèmes :

```python
# Dans Play.loop() context dict :
'map_name': current_map_name,
'map_meta': map_meta_dict,           # lanes, bushes, walls, objectives, symmetry
'ability_manager': ability_manager,  # evaluate_super(), evaluate_gadget(), evaluate_hyper()
'position_eval': position_evaluator, # score_position(pos, role), find_best_position()
'team_coordinator': team_coordinator,# analyze_teammates(), should_follow_engage(), should_peel()
'scout_data': scout_data,            # enemy_composition, recommended_picks, enemy_playstyle
'game_phase': "early" | "mid" | "late",
'objective_state': {...},            # gem_count, ball_possession, zone_progress, time_left
'my_role': "aggro" | "control" | "support" | "defense" | "objective",
```

Chaque variable doit avoir une fallback safe (None / default) pour compatibilité playstyles existants.