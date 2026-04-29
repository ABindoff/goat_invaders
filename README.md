# 🐐 Goat Invaders

A retro Space Invaders-style arcade game where you defend an Australian farm from invasive species using a goat armed with a peashooter.

## Features

- **Pixel-perfect VGA aesthetics** — Intentionally blocky 16-bit graphics
- **Three invasive species** — Cane toads (30 pts), foxes (20 pts), rabbits (10 pts)
- **Procedurally generated sound** — Square-wave synthesized audio (no external files)
- **Cross-platform** — Windows/Mac/Linux desktop and Android phones
- **Progressive difficulty** — Enemies march faster as you advance through levels

## Desktop

### Requirements
- Python 3.8+
- pygame (`pip install pygame`)

### Run
```bash
python goat_invaders.py
```

**Controls:**
- `A` / `D` or arrow keys: Move
- Space: Shoot
- Esc: Quit

## Mobile (Android APK)

The game auto-detects Android and displays on-screen touch buttons.

### Build via GitHub Actions (recommended)
1. Push code to GitHub
2. GitHub Actions automatically builds the APK on every push
3. Download from **Actions** tab → **build-apk** artifact

### Build locally
```bash
pip install buildozer cython
buildozer android debug
```

The APK will be in `bin/`.

## Game Rules

1. Invaders march left/right and drop every time they hit a wall
2. Destroy all enemies to advance to the next level (enemies move faster)
3. If enemies reach the bottom, game over
4. You have 3 lives; collect points for each kill
5. Enemies fire randomly; get hit to lose a life (brief invincibility)

## Files

```
.
├── goat_invaders.py          Main game (desktop + Android)
├── buildozer.spec            Android build config
├── .github/
│   └── workflows/
│       └── build-apk.yml     GitHub Actions APK builder
└── README.md                 This file
```

## Technical Notes

- **Canvas:** 240×270 game-pixels, upscaled 3× on desktop
- **Android:** Full-screen with touch controls in a bottom button strip
- **Audio:** Generated via square-wave synthesis (no files needed)
- **Package ID:** `au.github.bindoffa.goatinvaders`

## License

Open source — make it your own!

---

**Made in Tasmania** 🦘
