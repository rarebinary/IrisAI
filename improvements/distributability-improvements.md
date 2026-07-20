# Améliorations de Distribuabilité - Spécification Détaillée

## Contexte

Le bot est **exclusivement macOS** aujourd'hui. C'est un choix assumé, pas un bug. Mais même pour macOS, l'installation est trop complexe pour un utilisateur non-développeur. Ce doc couvre ce qu'il faut pour qu'un utilisateur macOS puisse lancer le bot en **une commande** après avoir cloné le repo.

---

## 1. Installation en une commande

### Problème actuel
- `setup.py` fait de l'installation impérative post-`setup()` (lignes 148-252) : installe torch, onnxruntime, adbutils, av selon la plateforme, lance `nvidia-smi`, demande confirmation interactive → **casse `pip install` standard**
- `requirements.txt` incomplet (manque torch, onnxruntime variants, adbutils, av)
- Pas de script d'installation guidé

### Solution attendue

#### A. Refactorer `setup.py` pour être déclaratif
- Garder seulement les métadonnées (name, version, packages, entry_points)
- Déplacer toute la logique d'installation conditionnelle dans un script séparé `install.py`
- Utiliser `extras_require` dans `setup.cfg` / `pyproject.toml` :
  ```toml
  [project.optional-dependencies]
  cpu = ["torch", "onnxruntime"]
  cuda = ["torch[cuda]", "onnxruntime-gpu"]
  coreml = ["torch", "onnxruntime-silicon"]
  directml = ["torch", "onnxruntime-directml"]
  full = ["torch", "onnxruntime", "adbutils", "av", "easyocr", ...]
  ```

#### B. Créer `install.py` (point d'entrée unique)
```bash
python install.py [--cpu|--cuda|--coreml|--directml] [--no-adb] [--dev]
```
Ce script doit :
1. Détecter la plateforme (macOS Apple Silicon / Intel, Windows, Linux)
2. Détecter GPU dispo (Metal sur macOS, CUDA sur NVIDIA, DirectML sur Windows)
3. Proposer le bon profil d'installation avec explication claire
4. Installer les dépendances via `pip` (pas `subprocess pip`)
5. Télécharger les modèles EasyOCR (~1.2 Go) si absents
6. Vérifier ADB installé et dans PATH, sinon proposer `brew install android-platform-tools` (macOS) / lien Windows / `apt` Linux
7. Créer un fichier `.env` avec template des tokens
8. Lancer `validate_configs()` (voir stability doc) pour vérifier que tout est bon

#### C. Point d'entrée `pyla` via `entry_points`
Dans `setup.cfg` / `pyproject.toml` :
```toml
[project.scripts]
pyla = "main:cli_entry_point"
```
Créer `cli_entry_point()` dans `main.py` qui :
- Parse args (`--config`, `--no-webui`, `--no-discord`, `--port`, `--install`)
- Si `--install` → lance `install.py`
- Sinon lance le bot normal

### Critères de validation
- `git clone ... && cd ... && python install.py` → bot prêt à l'emploi en < 5 min
- `pip install -e . && pyla` → fonctionne
- Aucune interaction manuelle requise (sauf choix GPU si ambigu)

---

## 2. Gestion des modèles ONNX et EasyOCR

### Problème actuel
- Modèles ONNX (30+15+10 Mo) versionnés dans `models/` → repo gros
- EasyOCR modèles (3 × ~50-75 Mo) versionnés → clone = 300+ Mo
- Pas de vérification d'intégrité (hash)
- Pas de mise à jour automatique

### Solution attendue

#### A. Modèles ONNX
- Sortir de git (ajouter `models/*.onnx` dans `.gitignore`)
- Créer `models/manifest.json` :
  ```json
  {
    "mainInGameModel.onnx": {"url": "https://...", "sha256": "..."},
    "tileDetector.onnx": {"url": "https://...", "sha256": "..."},
    "closeTileDetector.onnx": {"url": "https://...", "sha256": "..."}
  }
  ```
- Dans `install.py` ou au premier lancement : télécharger si absent, vérifier SHA256, log progression
- Fournir un miroir de secours (GitHub Releases, HuggingFace, S3)

#### B. EasyOCR
- Ne pas versionner `models/easyocr/`
- Au premier usage d'EasyOCR (dans `lobby_automation.py` ou `utils.py:DefaultEasyOCR`) : télécharger via `easyocr.Reader` (qui le fait nativement) mais avec :
  - Progress bar visible
  - Vérification taille attendue
  - Cache dans `~/.cache/IrisAI/easyocr/` (pas dans le repo)

#### C. Commande de mise à jour modèles
```bash
pyla update-models
```
→ Re-télécharge manifest, compare versions, met à jour si nécessaire

### Critères de validation
- Clone repo = < 50 Mo
- Premier lancement télécharge modèles automatiquement avec barre de progression
- Modèle corrompu → re-téléchargement auto au lancement suivant

---

## 3. Configuration via variables d'environnement (12-factor)

### Problème actuel
Tokens Discord, Telegram, API Key Brawlify en clair dans `cfg/webhook_config.toml` et `cfg/login.toml` → risque si repo partagé, pas de séparation config/secrets.

### Solution attendue

#### A. Support `.env` prioritaire
Créer `config_loader.py` (voir stability doc) qui charge dans l'ordre :
1. Valeurs par défaut (code)
2. `cfg/*.toml` (config utilisateur)
3. Variables d'environnement `PYLA_*` (priorité max)

Mapping :
| TOML key | Env var | Description |
|----------|---------|-------------|
| `webhook_config.discord_bot_token` | `PYLA_DISCORD_BOT_TOKEN` | Token bot Discord |
| `webhook_config.discord_id` | `PYLA_DISCORD_USER_ID` | User ID autorisé |
| `webhook_config.discord_guild_id` | `PYLA_DISCORD_GUILD_ID` | Guild ID pour slash commands |
| `webhook_config.webhook_url` | `PYLA_DISCORD_WEBHOOK_URL` | Webhook notifications |
| `webhook_config.telegram_token` | `PYLA_TELEGRAM_BOT_TOKEN` | Token bot Telegram |
| `webhook_config.telegram_chat_id` | `PYLA_TELEGRAM_CHAT_ID` | Chat ID notifications |
| `login.api_key` | `PYLA_API_KEY` | Clé API cloud |
| `general_config.api_base_url` | `PYLA_API_BASE_URL` | URL API distante |

#### B. Fichier `.env.example` à la racine
```bash
# Discord (obligatoire pour bot slash commands)
PYLA_DISCORD_BOT_TOKEN=
PYLA_DISCORD_USER_ID=
PYLA_DISCORD_GUILD_ID=
PYLA_DISCORD_WEBHOOK_URL=

# Telegram (optionnel)
PYLA_TELEGRAM_BOT_TOKEN=
PYLA_TELEGRAM_CHAT_ID=

# API Cloud (optionnel)
PYLA_API_KEY=
PYLA_API_BASE_URL=https://api.pyla.example.com
```

#### C. Masquage dans Web UI
Dans `webui/services.py:1035` le masque `bot_token` cherche la clé `"bot_token"` mais le TOML a `"discord_bot_token"`. Corriger et masquer **toutes** les valeurs sensibles (tokens, API keys) dans l'API `/api/settings` → retourner `••••••••` au lieu de la valeur.

### Critères de validation
- Bot démarre avec seulement `.env` (pas de TOML webhook/login)
- Web UI affiche `••••••••` pour tous les secrets
- `git status` ne montre jamais de token en clair

---

## 4. Détection et adaptation automatique de la résolution

### Problème actuel
Coordonnées en dur pour 1920×1080 :
- `play.py:22` : `brawl_stars_width, brawl_stars_height = 1920, 1080`
- `window_controller.py:12` : même chose
- `window_controller.py:267` : `joystick_x, joystick_y = 220 * ratio, 870 * ratio`
- `stage_manager.py:242` : `noodle_x, noodle_y = 960, 740`
- `buttons_config.toml` : positions absolues en pixels

### Solution attendue

#### A. Détection résolution au démarrage
Dans `WindowController.__init__()` ou `discover_device()` :
```python
# Via ADB
output = self.device.shell("wm size")
# Output: "Physical size: 1080x1920" ou "Override size: 720x1280"
width, height = parse_wm_size(output)
self.screen_width = width
self.screen_height = height
self.width_ratio = width / 1920.0
self.height_ratio = height / 1080.0
```

#### B. Système de coordonnées relatives
Créer `coords.py` :
```python
class RelativeCoord:
    """x, y en % de la largeur/hauteur de référence (1920x1080)"""
    def __init__(self, x_pct: float, y_pct: float):
        self.x_pct = x_pct / 1920.0
        self.y_pct = y_pct / 1080.0
    
    def to_absolute(self, width: int, height: int) -> tuple[int, int]:
        return (int(self.x_pct * width), int(self.y_pct * height))

# Usage
ATTACK_BTN = RelativeCoord(1750, 950)  # 91%, 88%
# À l'usage:
x, y = ATTACK_BTN.to_absolute(wc.screen_width, wc.screen_height)
```

#### C. Migration `buttons_config.toml`
Changer le format :
```toml
# Avant (absolu)
attack = {x=1750, y=950}

# Après (relatif, compatible)
attack = {x_pct=0.911, y_pct=0.880}
# Ou garder x/y pour compat, ajouter x_pct/y_pct optionnels
```

Au chargement : si `x_pct` présent → priorité, sinon calculer depuis `x` en assumant 1920×1080.

#### D. Templates d'état (images)
Les images dans `images/states/` sont en 1920×1080. Options :
1. **Redimensionner à la volée** dans `state_finder.py:load_template()` → `cv2.resize(template, (screen_w, screen_h))`
2. **Générer les templates** au premier lancement pour la résolution détectée (plus précis)
3. **Fournir des packs** par résolution courante (720p, 1080p, 1440p)

Recommandation : option 1 (simple, suffit pour template matching normalisé) + option 3 pour les utilisateurs avancés.

### Critères de validation
- Bot lancé sur émulateur 720p (1280×720) → clique au bon endroit
- Bot lancé sur téléphone 1080p (1080×2340 portrait) → fonctionne (rotation gérée)
- Changement résolution à chaud (adb `wm size`) → détecté au prochain `discover_device()`

---

## 5. Scripts de lancement et raccourcis macOS

### Problème actuel
L'utilisateur doit faire `python main.py` dans le terminal. Pas d'icône, pas de menu, pas de logs accessibles.

### Solution attendue

#### A. `run.command` (double-cliquable macOS)
À la racine du repo :
```bash
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate && pip install -e .
python -m pyla "$@"
```
Rendre exécutable : `chmod +x run.command`

#### B. `.app` bundle macOS (optionnel, pour plus tard)
Utiliser `py2app` ou `Platypus` pour créer `IrisAI.app` avec :
- Icône personnalisée
- Terminal optionnel (caché par défaut, visible via menu "Window > Show Logs")
- Auto-update via Sparkle

#### C. Lancement au login (LaunchAgent)
Fournir `com.pyla.ai.plist` template pour `~/Library/LaunchAgents/` :
- Démarrage auto si `AUTO_START=true` dans `.env`
- Redémarrage sur crash
- Logs redirigés vers `~/Library/Logs/IrisAI/`

---

## 6. Documentation utilisateur (pas développeur)

### Fichiers à créer
| Fichier | Contenu |
|---------|---------|
| `GETTING_STARTED.md` | 5 min pour premier lancement : prérequis, install, config tokens, lancer |
| `TROUBLESHOOTING.md` | Erreurs fréquentes : ADB not found, modèle manquant, permission USB, port occupé, etc. |
| `CONFIG_REFERENCE.md` | Tous les paramètres TOML expliqués simplement avec exemples |
| `PLAYSTYLE_GUIDE.md` | Comment créer/modifier un `.pyla`, variables dispo, exemples |

### Intégration dans Web UI
- Bouton "Help" → ouvre `GETTING_STARTED.md` rendu en HTML
- Page "Status" → lien "Troubleshooting" contextuel selon l'erreur affichée

---

## 7. Mise à jour automatique (self-update)

### Solution attendue
Commande `pyla self-update` qui :
1. `git fetch origin`
2. Compare `HEAD` vs `origin/main`
3. Si nouveau commit : `git pull`, `pip install -e . --upgrade`, `pyla update-models`
4. Redémarre le bot (via RuntimeManager)

Pour les builds figés (Nuitka) : vérifier version sur GitHub Releases, télécharger nouveau binaire, remplacer l'actuel.

---

## 8. Build Nuitka fiabilisé

### Problème actuel
`setup.py` a du code Nuitka-specific (monkey-patch `inspect.getfile`, détection `__compiled__`) mais pas de config dédiée.

### Solution attendue
Créer `build_nuitka.py` séparé :
```python
# build_nuitka.py
import subprocess
import sys

cmd = [
    sys.executable, "-m", "nuitka",
    "--standalone",
    "--follow-imports",
    "--enable-plugin=tk-inter",  # si GUI
    "--include-package=onnxruntime",
    "--include-package=easyocr",
    "--include-data-dir=images=images",
    "--include-data-dir=cfg=cfg",
    "--include-data-dir=playstyles=playstyles",
    "--include-data-dir=models=models",  # si on garde les modèles embarqués
    "--macos-create-app-bundle",
    "--macos-app-name=IrisAI",
    "--macos-app-icon=assets/icon.icns",
    "main.py"
]
subprocess.run(cmd, check=True)
```

Ajouter dans `pyproject.toml` :
```toml
[tool.nuitka]
# config déclarative si nuitka la supporte
```

### Critères de validation
- `python build_nuitka.py` → produit `dist/IrisAI.app` (macOS) ou `dist/IrisAI.exe` (Windows) ou `dist/IrisAI.bin` (Linux)
- L'app/binaire lancé sur machine vierge (sans Python, sans repo) → fonctionne
- Taille < 500 Mo

---

## Ordre d'implémentation recommandé

1. **`install.py` + `setup.py` clean + `requirements.txt` complet** (base)
2. **`config_loader.py` + support `.env` + masquage Web UI** (sécurité config)
3. **Détection résolution auto + coords relatives** (compatibilité appareils)
4. **Manifest modèles ONNX + téléchargement auto** (repo léger)
5. **`run.command` + docs utilisateur** (accessibilité)
6. **`build_nuitka.py` + self-update** (distribution binaire)
7. **LaunchAgent macOS + .app bundle** (polish)

---

## Tests de validation distribuables

Chaque étape doit pouvoir être testée sur :
- macOS Apple Silicon (M1/M2/M3) - cible principale
- macOS Intel (compatibilité)
- Optionnel : Windows 10/11, Ubuntu 22.04+ (pour futurs ports)

Checklist par release :
- [ ] `git clone && python install.py` → succès sans interaction
- [ ] Bot démarre avec seulement `.env` renseigné
- [ ] Émulateur 720p → bot clique correctement
- [ ] Modèles manquants → téléchargés auto au premier lancement
- [ ] `pyla self-update` → met à jour et redémarre
- [ ] Binaire Nuitka lancé sur machine vierge → fonctionne