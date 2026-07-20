# Améliorations de Stabilité - Spécification Détaillée

## Contexte

Le bot fonctionne avec 5-6 threads concurrents partageant de la mémoire sans synchronisation. Des bugs de concurrence, des timeouts réseau manquants, une config fragile et des `sys.exit()` tuent le bot régulièrement. Ce document liste chaque point à corriger avec la localisation exacte dans le code.

---

## 1. Synchronisation des Threads (Race Conditions)

### Problème
Plusieurs threads lisent/écrivent les mêmes variables sans locks :
- `WindowController.are_we_moving` (lignes 131, 304-318, 320-324 dans `window_controller.py`)
- `WindowController.last_joystick_pos` (lignes 110, 311, 318, 324)
- `cached_toml` global dans `utils.py` (ligne 108)
- `cached_templates` global dans `state_finder.py` (lignes 47-57)
- `_last_data_cache` et `_last_frame_time` dans `Play` (lignes 751-752, 810) avec `ThreadPoolExecutor`

### Solution attendue
Créer un module `threading_utils.py` avec :
- `ThreadSafeDict` wrapper pour `cached_toml` et `cached_templates` utilisant `threading.RLock`
- `@thread_safe` decorator pour méthodes critiques
- `AtomicBool` et `AtomicValue` pour `are_we_moving`, `last_joystick_pos`

Dans `window_controller.py` :
- Ajouter `self._move_lock = threading.RLock()` dans `__init__`
- Protéger toutes les lectures/écritures de `are_we_moving` et `last_joystick_pos` avec ce lock
- Dans `reconnect_scrcpy()`, prendre le lock avant de modifier l'état

Dans `utils.py` :
- Remplacer `cached_toml = {}` par `ThreadSafeDict()`

Dans `state_finder.py` :
- Remplacer `cached_templates = {}` par `ThreadSafeDict()`

Dans `play.py` :
- Ajouter `self._cache_lock = threading.RLock()`
- Protéger `_last_data_cache` et `_last_frame_time` dans `main()` et les workers du ThreadPoolExecutor

### Critères de validation
- Exécuter le bot 2h sans crash de concurrence
- Lancer 10 threads qui modifient `are_we_moving` simultanément → état toujours cohérent

---

## 2. Timeouts sur tous les appels réseau

### Problème
Tous les `requests.get/post` sans timeout (13 occurrences) peuvent bloquer indéfiniment :

| Fichier | Ligne | Code |
|---------|-------|------|
| `utils.py` | 319 | `requests.post(url)` |
| `utils.py` | 346 | `requests.post(url, json=...)` |
| `utils.py` | 360 | `requests.get(brawlers_url)` |
| `utils.py` | 371 | `requests.get(icon_url)` |
| `utils.py` | 390 | `requests.get(url)` |
| `utils.py` | 545 | `requests.get(url)` |
| `utils.py` | 555 | `requests.get(url)` |
| `utils.py` | 589 | `requests.get(url)` |
| `utils.py` | 600 | `requests.get(url)` |
| `api/api.py` | 9 | `requests.get(brawlers_url).json()['list']` (au import !) |
| `api/api.py` | 13 | `requests.get(icon_url)` |
| `trophy_observer.py` | 210 | `requests.post(f'https://{api_base_url}/api/matches', json=payload)` |
| `webui/services.py` | 61 | `requests.get(url, params=params)` |

### Solution attendue
1. Créer `network.py` avec :
   - `DEFAULT_TIMEOUT = 15` (secondes)
   - `make_request(method, url, **kwargs)` qui ajoute `timeout=DEFAULT_TIMEOUT` automatiquement
   - Retry avec backoff exponentiel (3 essais : 1s, 2s, 4s)
   - Logging des timeouts/erreurs sans crasher

2. Remplacer tous les appels directs par `network.make_request(...)`

3. Dans `api/api.py` : déplacer l'import-time request dans une fonction `load_brawlers_data()` appelée au démarrage avec gestion d'erreur

### Critères de validation
- Couper le réseau → le bot log "timeout" et continue au lieu de freezer
- Serveur lent (10s réponse) → timeout après 15s, retry, puis fallback

---

## 3. Configuration robuste (fallbacks partout)

### Problème
Accès direct `config["key"]` au lieu de `config.get("key", default)` → `KeyError` si fichier incomplet. 27 occurrences identifiées.

### Solution attendue
Créer `config_loader.py` avec :
```python
def get_config(path: str, key: str, default: Any, expected_type: type = None) -> Any:
    """Charge TOML, retourne default si clé manquante, valide le type, log un warning."""
```

Remplacer systématiquement :
- `load_toml_as_dict("cfg/xyz.toml")["key"]` → `get_config("cfg/xyz.toml", "key", DEFAULT_VALUE)`

Définir les `DEFAULT_VALUE` pour chaque clé dans un dictionnaire central `CONFIG_DEFAULTS` dans `config_loader.py`.

### Exemples de clés à sécuriser (priorité haute)
| Fichier | Ligne | Clé | Default suggéré |
|---------|-------|-----|-----------------|
| `main.py` | 75 | `max_ips` | 30 |
| `main.py` | 106 | `run_for_minutes` | 60 |
| `main.py` | 107 | `ping_every_x_minutes` | 0 |
| `detect.py` | 151 | `used_threads` | `auto` |
| `detect.py` | 162 | `cpu_or_gpu` | `auto` |
| `utils.py` | 203 | `player_tag` | `""` |
| `stage_manager.py` | 44 | `play_again_on_win` | `True` |
| `stage_manager.py` | 70 | `ping_every_x_match` | 0 |
| `stage_manager.py` | 73-74 | `player_tag`, `ping_when_stuck` | `""`, `True` |
| `window_controller.py` | 44 | `emulator_port` | 5555 |
| `window_controller.py` | 91 | `brawl_stars_package` | `com.supercell.brawlstars` |
| `lobby_automation.py` | 16 | `idle_reconnect` | (de buttons_config) |
| `lobby_automation.py` | 57 | `brawlers_menu` | (de buttons_config) |
| `lobby_automation.py` | 126 | `select_brawler` | (de buttons_config) |
| `trophy_observer.py` | 64 | `trophies_multiplier` | 1.0 |
| `utils.py` | 434-436 | `discord_id`, `discord_bot_token`, `discord_guild_id` | `""` |
| `utils.py` | 610 | `wall_model_classes` | `["wall", "bush", "close_bush"]` |
| `time_management.py` | 16 | `self.thresholds[check_type]` | KeyError si clé absente |
| `time_management.py` | 7 | `self.states = {key: time.time() for key in self.thresholds.keys()}` | fragile |

### Critères de validation
- Supprimer n'importe quelle clé du TOML → bot démarre avec les defaults, log un warning
- Fichier TOML complètement vide → bot démarre avec tous les defaults

---

## 4. Remplacer sys.exit() par gestion d'état gracieuse

### Problème
Deux `sys.exit()` tuent tout le process (Flask + Discord + threads) :
- `main.py:153` dans `restart_brawl_stars()` si restart échoue
- `stage_manager.py:176` dans `start_game()` si file vide

### Solution attendue
Utiliser `RuntimeManager` (existant dans `webui/runtime.py`) avec états :
- `IDLE` → `RUNNING` → `PAUSED` / `STOPPING` → `IDLE`
- `ERROR` → `IDLE` (après notification)

Dans `main.py:restart_brawl_stars()` :
- Au lieu de `sys.exit(1)` : `self.runtime_control.request_stop()`, `self.runtime_control.mark_error("Restart BS failed")`, notifier utilisateur, retourner

Dans `stage_manager.py:start_game()` :
- Au lieu de `sys.exit(0)` : `self.runtime_control.request_stop()`, `mark_completed("All targets reached")`, retourner

Le thread principal dans `Main.main()` doit vérifier `should_stop()` à chaque itération (déjà fait) et sortir proprement de la boucle.

### Critères de validation
- File vide → bot s'arrête, Flask UI reste accessible, Discord bot répond encore
- Échec restart BS → bot s'arrête avec état ERROR, UI accessible, notification envoyée

---

## 5. Gestion des valeurs None au démarrage

### Problème
Certaines variables initialisées à `None` utilisées dans calculs mathématiques :
- `TrophyObserver.current_trophies` = `None` (ligne 35) → `add_trophies()` fait `None >= 1000` → `TypeError`

### Solution attendue
- Initialiser `current_trophies = 0` au lieu de `None`
- Ou ajouter garde : `if self.current_trophies is None: self.current_trophies = 0` au début de `add_trophies()`

Autres risques similaires à auditer :
- `Play.brawler_ranges[brawler]` (ligne 524) → `KeyError` si brawler absent
- `Play.brawlers_info[brawler]['ignore_walls_for_attacks']` (lignes 259, 267) → `KeyError`
- `Play.brawlers_info[brawler]['hold_attack']` (ligne 267) → `KeyError`
- `StageManager.brawlers_pick_data[0]` (lignes 125, 394) → `IndexError` si liste vide
- `get_brawler_stats` retour `(None, None)` puis `[2]` (ligne 299) → `IndexError`

### Approche générale
Partout où un dict/array est accédé sans certitude d'existence :
- Utiliser `.get(key, default)` pour dicts
- Vérifier `len(list) > 0` avant `[0]`
- Fournir defaults sensés dans les structures de données

### Critères de validation
- Démarrer bot avec `brawlers_info.json` incomplet → pas de crash
- File d'attente vidée entre deux checks → gestion propre

---

## 6. Fuites de ressources

### Problème
| Fichier | Ligne | Description |
|---------|-------|-------------|
| `webui/services.py` | 670-696 | Fichier temp `.__upload__<filename>` leak si crash entre save et cleanup |
| `debug_view.py` | 156-158 | Shared memory recreé à chaque changement shape sans unlink garanti |
| `trophy_observer.py` | 97-98 | `to_csv()` réécrit tout le CSV à chaque match (lent, usure disque) |

### Solution attendue
- `import_playstyle` : utiliser `tempfile.NamedTemporaryFile(delete=False)` + `try/finally` avec `os.unlink`
- `debug_view.py` : tracker les shared memory créés, `close()` + `unlink()` dans `__del__` ou context manager
- `trophy_observer.py` : batch writes (accumuler en mémoire, flush toutes les 5 min ou à l'arrêt) ou utiliser `mode='a'` pour append

---

## 7. Credentials en dur / sécurité

### Problème
`webui/services.py:60` : `params = {'username': username, "API-Key": "apikeyhaha"}` → clé API en dur envoyée à chaque requête.

### Solution attendue
- Lire depuis variable d'environnement `PYLA_API_KEY` ou config TOML non versionnée
- Ne jamais logger/commiter la vraie clé

---

## 8. Détection résolution & coordonnées relatives (stabilité multi-appareils)

### Problème
Résolution 1920×1080 en dur dans `play.py:22` et `window_controller.py:12`. Coordonnées joystick/boutons en pixels absolus. Sur émulateur 720p ou téléphone 1080×2400 → clics à côté.

### Solution attendue
- Au démarrage : `adb shell wm size` → détecter résolution réelle
- Calculer `width_ratio = real_width / 1920`, `height_ratio = real_height / 1080`
- Stocker tous les coords dans config en **pourcentages** (0.0-1.0) ou en "unités de référence 1920x1080"
- Au moment du clic : `real_x = config_x * width_ratio`, `real_y = config_y * height_ratio`
- Mettre à jour `buttons_config.toml`, `lobby_config.toml` avec coords normalisées

---

## 9. Gestion d'erreurs ONNX (modèles corrompus/absents)

### Problème
`detect.py:195` : `ort.InferenceSession()` sans try/except. Si modèle manquant/corrompu/incompatible → crash sans message clair.

### Solution attendue
```python
try:
    self.model = ort.InferenceSession(self.model_path, sess_options=so, providers=[onnx_provider])
except Exception as e:
    logger.error(f"Failed to load ONNX model {self.model_path}: {e}")
    raise ModelLoadError(f"Cannot load {self.model_path}: {e}")
```

Ajouter validation au chargement :
- Vérifier que `self.model.get_inputs()` non vide
- Vérifier shape attendue
- Fallback provider (CUDA → CoreML → DirectML → CPU) déjà implémenté mais sans logging clair

---

## 10. Module-level blocking I/O (import-time crash)

### Problème
`api/api.py:8-17` : `requests.get()` au niveau module → tout `import api` bloque sur réseau et crash si indisponible.

### Solution attendue
Déplacer dans fonction `load_brawlers_data()` appelée explicitement au démarrage avec timeout + retry + fallback cache local.

---

## 11. Race condition frame callback / reconnect

### Problème
`window_controller.py:118-124` : callback `on_frame` capturé par closure avec `self.frame_lock`. Dans `reconnect_scrcpy()` (lignes 180-184), nouveau listener créé avec nouveau lock. Pendant la fenêtre stop/start, frames peuvent être perdues ou écrites sur ancien lock.

### Solution attendue
- Utiliser un seul `frame_lock` partagé, ne pas le recréer
- Ou : atomic swap du listener avec `threading.Event` pour synchroniser stop/start

---

## 12. scrcpy.Client.last_frame data race

### Problème
`scrcpy/core.py:244` : `self.last_frame = frame` sans lock. Non lu par l'app (WindowController utilise son propre callback) mais data race quand même.

### Solution attendue
Ajouter `self._frame_lock = threading.Lock()` dans `scrcpy.Client.__init__`, protéger écriture/lecture de `last_frame`.

---

## Ordre d'implémentation recommandé

1. **`network.py` + timeouts partout** (impact immédiat, facile)
2. **`config_loader.py` + fallbacks config** (élimine crashes config)
3. **`threading_utils.py` + locks critiques** (stabilité core)
4. **Remplacement `sys.exit()` par RuntimeManager** (UX)
5. **Init None-safety + dict.get() partout** (robustesse)
6. **Fix ressources leaks + credentials + ONNX error handling** (propreté)
7. **Détection résolution auto + coords النسبية** (compatibilité appareils)
8. **Fix import-time I/O + frame callback race** (correctness)

---

## Tests de validation par feature

Chaque correction doit pouvoir être testée indépendamment :

| Feature | Test |
|---------|------|
| Thread locks | Stress test : 10 threads modifient `are_we_moving` 1000x → état cohérent |
| Network timeouts | `tc qdisc add dev lo root netem delay 20000ms` → bot log timeout, continue |
| Config fallbacks | Supprimer clé random du TOML → bot démarre, warning loggé |
| sys.exit removal | Vider queue → bot STOPPED, Flask UI up, Discord up |
| None safety | `brawlers_info.json` vide → bot démarre |
| Resolution detect | Lancer sur émulateur 720p → joystick/boutons cliquent au bon endroit |
| ONNX error handling | Corrompre `.onnx` → message d'erreur clair, fallback CPU tenté |

---

## Fichiers à créer / modifier (résumé)

| Fichier | Action |
|---------|--------|
| `threading_utils.py` | **Nouveau** - ThreadSafeDict, AtomicBool, AtomicValue, @thread_safe |
| `network.py` | **Nouveau** - make_request avec timeout/retry/logging |
| `config_loader.py` | **Nouveau** - get_config, CONFIG_DEFAULTS |
| `window_controller.py` | Modifier - locks, resolution detection, coord scaling |
| `utils.py` | Modifier - ThreadSafeDict pour cached_toml, credentials depuis env |
| `state_finder.py` | Modifier - ThreadSafeDict pour cached_templates |
| `play.py` | Modifier - locks pour cache, None-safety dict access |
| `main.py` | Modifier - remplacer sys.exit par runtime_control |
| `stage_manager.py` | Modifier - remplacer sys.exit, vérifier len() avant [0] |
| `trophy_observer.py` | Modifier - current_trophies=0, batch CSV writes |
| `detect.py` | Modifier - try/except ONNX load, validation |
| `api/api.py` | Modifier - déplacer request dans fonction |
| `scrcpy/core.py` | Modifier - lock pour last_frame |
| `webui/services.py` | Modifier - tempfile pour upload, API key depuis env |
| `time_management.py` | Modifier - .get() pour thresholds |
| `lobby_automation.py` | Modifier - .get() pour buttons config |

---

## Compatibilité descendante

- Tous les changements sont internes (pas d'API publique modifiée)
- Playstyles `.pyla` inchangés
- Formats TOML/JSON inchangés (seules valeurs par défaut ajoutées)
- Web UI existante continue de fonctionner