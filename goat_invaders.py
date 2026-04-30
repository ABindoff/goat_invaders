#!/usr/bin/env python3
"""
★ GOAT INVADERS ★
Defend the Australian farm from invasive species!

Desktop  controls:  A / D  or  ← / →   move   |   SPACE  shoot   |   ESC  quit
Android  controls:  on-screen buttons (left / fire / right)

Requires:  Python 3.8+  and  pygame   (pip install pygame)
"""

import pygame
import sys
import random
import array as _arr
import math
import os
import asyncio

pygame.init()

# ─── Android detection ────────────────────────────────────────────────────────
ANDROID = sys.platform == "android"

# Audio init (can fail silently on some Android devices)
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    AUDIO = True
except Exception:
    AUDIO = False

# ─── Game canvas (always low-res — scaled up for chunky look) ─────────────────
GW, GH = 240, 270          # game canvas size in "game-pixels"
CANVAS = pygame.Surface((GW, GH))
CLOCK  = pygame.time.Clock()
FPS    = 60

# ─── Display — adapt to screen size on Android ───────────────────────────────
if ANDROID:
    # Full-screen; reserve a strip at the bottom for touch buttons
    WIN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    SCREEN_W, SCREEN_H = WIN.get_size()
    BTN_STRIP = max(110, SCREEN_H // 7)          # height of touch-button area
    _avail_h  = SCREEN_H - BTN_STRIP
    PX        = min(SCREEN_W // GW, _avail_h // GH)
    GAME_X    = (SCREEN_W - GW * PX) // 2        # centre game canvas
    GAME_Y    = (_avail_h - GH * PX) // 2
else:
    PX        = 3
    BTN_STRIP = 0
    SCREEN_W  = GW * PX
    SCREEN_H  = GH * PX
    GAME_X    = 0
    GAME_Y    = 0
    WIN       = pygame.display.set_mode((SCREEN_W, SCREEN_H))

pygame.display.set_caption("★  GOAT  INVADERS  ★")

# ─── CGA / VGA palette ────────────────────────────────────────────────────────
_PAL = {
    '.': None,
    'K': (  0,   0,   0),   # black
    'W': (255, 255, 255),   # white
    'G': (  0, 170,   0),   # green
    'g': ( 85, 255,  85),   # bright green
    'R': (170,   0,   0),   # dark red
    'r': (255,  85,  85),   # bright red
    'Y': (170, 170,   0),   # olive
    'y': (255, 255,  85),   # bright yellow
    'C': (  0, 170, 170),   # cyan
    'c': ( 85, 255, 255),   # bright cyan
    'M': (170,   0, 170),   # magenta
    'B': (  0,   0, 170),   # blue
    'b': ( 85,  85, 255),   # bright blue
    'D': ( 85,  85,  85),   # dark grey
    'L': (170, 170, 170),   # light grey
    'l': (210, 210, 210),   # lighter grey  (rabbit face)
    'T': (155, 118,  65),   # tan           (goat body)
    't': (220, 185, 128),   # light tan     (goat face)
    'A': ( 55, 135,  55),   # toad green
    'a': (115, 195,  95),   # light toad
    'O': (195,  75,  20),   # fox dark orange
    'o': (238, 148,  65),   # fox light orange
    'P': (218,  98,  88),   # salmon / pink (noses)
    'I': (238, 238, 238),   # near-white    (rabbit belly)
}

def _parse(rows):
    result = [[_PAL[ch] for ch in row] for row in rows]
    widths  = [len(r) for r in result]
    if len(set(widths)) != 1:
        raise ValueError(f"Sprite has uneven row widths: {widths}")
    return result

def _stamp(surf, sprite, x, y):
    for ry, row in enumerate(sprite):
        for rx, col in enumerate(row):
            if col is not None:
                nx, ny = x + rx, y + ry
                if 0 <= nx < GW and 0 <= ny < GH:
                    surf.set_at((nx, ny), col)

# ─── Sprites ──────────────────────────────────────────────────────────────────

GOAT_SPR = _parse([        # player  12 × 12
    "..T......T..",
    ".TT......TT.",
    ".tttttttttt.",
    "TttWKttKWttT",
    "TttttttttttT",
    "TtttttPPtttT",
    ".TttttttttT.",
    ".TTTTTTTTTT.",
    "..TT....TT..",
    "..TT....TT..",
    ".TTT....TTT.",
    ".TT......TT.",
])

RABBIT_SPR = _parse([      # 10 × 10  (bottom rows — 10 pts)
    ".LL....LL.",
    ".LL....LL.",
    ".LL....LL.",
    ".LLLLLLLL.",
    "LlllKllKlL",
    ".LllPPllL.",
    ".LLLLLLLL.",
    "LLllllllLL",
    ".LL....LL.",
    ".ll....ll.",
])

FOX_SPR = _parse([         # 12 × 10  (middle rows — 20 pts)
    ".OO......OO.",
    ".OO......OO.",
    "OOooooooooOO",
    "OoooKooKoooO",
    "OooooooooooO",
    "OoooWWWWoooO",
    ".OoWWPPWWoO.",
    "..OoooooooO.",
    "..OO....OO..",
    "..OO....OO..",
])

TOAD_SPR = _parse([        # 12 × 10  (top rows — 30 pts)
    "..AAAAAAAA..",
    ".AaaaaaaaaA.",
    ".AaWaaaaWaA.",
    "AaaKaaaKaaaA",
    "AaaaaaaaaaaA",
    ".AaAaOOaAaA.",
    ".AaaaaaaaaA.",
    "..AAAAAAAA..",
    ".AAa....aAA.",
    "AAa......aAA",
])

SPR_W = {"rabbit": len(RABBIT_SPR[0]), "fox": len(FOX_SPR[0]), "toad": len(TOAD_SPR[0])}
SPR_H = {"rabbit": len(RABBIT_SPR),   "fox": len(FOX_SPR),    "toad": len(TOAD_SPR)}
ENEMY_SPRITES = {"rabbit": RABBIT_SPR, "fox": FOX_SPR, "toad": TOAD_SPR}
ENEMY_POINTS  = {"rabbit": 10,         "fox": 20,       "toad": 30}

# ─── Sound ────────────────────────────────────────────────────────────────────
def _beep(freq, ms, vol=0.22):
    sr   = 22050
    n    = int(sr * ms / 1000)
    half = max(1, sr // max(1, freq) // 2)
    buf  = _arr.array('h', [
        int(32767 * vol * (1 if (i // half) % 2 == 0 else -1))
        for i in range(n)
    ])
    return pygame.mixer.Sound(buffer=buf)

if AUDIO:
    try:
        SND_SHOOT = _beep(880,  70)
        SND_HIT   = _beep(220, 160)
        SND_DIE   = _beep(110, 450)
        SND_MARCH = [_beep(f, 90) for f in (440, 330, 275, 220)]
        SND_WIN   = _beep(660, 600)
    except Exception:
        AUDIO = False

def play(snd):
    if AUDIO:
        try:
            snd.play()
        except Exception:
            pass

# ─── Fonts (drawn at low-res → chunky when upscaled) ─────────────────────────
FONT_SM = pygame.font.Font(None, 12)
FONT_LG = pygame.font.Font(None, 20)

def draw_text(surf, text, x, y, colour=(255, 255, 255), font=None):
    (font or FONT_SM).render(text, False, colour)
    surf.blit((font or FONT_SM).render(text, False, colour), (x, y))

# ─── Grid constants ───────────────────────────────────────────────────────────
COLS      = 8
ROWS      = 5
CELL_W    = 26
CELL_H    = 22
GRID_X0   = (GW - COLS * CELL_W) // 2
GRID_Y0   = 28
ROW_TYPES = ["toad", "toad", "fox", "fox", "rabbit"]

# ─── Gameplay constants ───────────────────────────────────────────────────────
PLAYER_SPEED      = 2
BULLET_SPEED      = 4
EBULLET_SPEED     = 2
STEP_X            = 2
STEP_Y            = 6
MARCH_INTERVAL_MS = 600
MARCH_MIN_MS      = 80
SHOOT_INTERVAL_MS = 1500
INVINCIBLE_MS     = 2000

PLAYER_Y = GH - 26
GROUND_Y = GH - 18

COL_BG      = (  0,   0,   0)
COL_GROUND  = (  0, 170,   0)
COL_SCORE   = (255, 255,  85)
COL_PBULLET = (255, 255, 255)
COL_EBULLET = (255, 255,  85)
COL_EXPLODE = [(255,255,85),(255,140,0),(255,85,85),(170,0,0)]

# ─────────────────────────────────────────────────────────────────────────────
# GAME OBJECTS
# ─────────────────────────────────────────────────────────────────────────────

class Player:
    W, H = len(GOAT_SPR[0]), len(GOAT_SPR)

    def __init__(self):
        self.x  = GW // 2 - self.W // 2
        self.y  = PLAYER_Y
        self.lives  = 3
        self.score  = 0
        self.hi     = 0
        self.bullet = None
        self.invincible_until = 0
        self.alive  = True

    def draw(self, surf):
        if not self.alive:
            return
        t = pygame.time.get_ticks()
        if self.invincible_until > t and (t // 100) % 2 == 0:
            return
        _stamp(surf, GOAT_SPR, self.x, self.y)

    def move(self, dx):
        self.x = max(0, min(GW - self.W, self.x + dx))

    def shoot(self):
        if self.bullet is None:
            self.bullet = [self.x + self.W // 2, self.y - 1]
            play(SND_SHOOT)

    def update_bullet(self):
        if self.bullet:
            self.bullet[1] -= BULLET_SPEED
            if self.bullet[1] < 0:
                self.bullet = None

    def hit(self):
        t = pygame.time.get_ticks()
        if t < self.invincible_until:
            return
        self.lives -= 1
        self.invincible_until = t + INVINCIBLE_MS
        play(SND_DIE)
        if self.lives <= 0:
            self.alive = False


class EnemyGrid:
    def __init__(self, level=1):
        self.enemies    = [[ROW_TYPES[r] for c in range(COLS)] for r in range(ROWS)]
        self.ox         = 0
        self.oy         = 0
        self.dir        = 1
        self.level      = level
        self.march_idx  = 0
        self._next_march = pygame.time.get_ticks()
        self._next_shoot = pygame.time.get_ticks() + 1000
        self.bullets    = []

    def alive_count(self):
        return sum(1 for r in self.enemies for k in r if k)

    def _alive_cells(self):
        return [(r, c) for r in range(ROWS) for c in range(COLS) if self.enemies[r][c]]

    def _col_bounds(self):
        cols = [c for _, c in self._alive_cells()]
        return (min(cols), max(cols)) if cols else (0, COLS - 1)

    def _bottom_shooters(self):
        result = []
        for c in range(COLS):
            for r in range(ROWS - 1, -1, -1):
                if self.enemies[r][c]:
                    result.append((r, c))
                    break
        return result

    def cell_rect(self, row, col):
        kind = self.enemies[row][col]
        if not kind:
            return None
        sw = SPR_W[kind]
        sh = SPR_H[kind]
        cx = GRID_X0 + col * CELL_W + self.ox + (CELL_W - sw) // 2
        cy = GRID_Y0 + row * CELL_H + self.oy + (CELL_H - sh) // 2
        return (cx, cy, sw, sh)

    def _march_interval(self):
        n     = self.alive_count()
        total = ROWS * COLS
        frac  = n / total if total else 1
        base  = max(MARCH_MIN_MS, int(MARCH_INTERVAL_MS * frac))
        return max(MARCH_MIN_MS, base // max(1, self.level))

    def update(self):
        t = pygame.time.get_ticks()

        if t >= self._next_march:
            lc, rc = self._col_bounds()
            left_x  = GRID_X0 + lc * CELL_W + self.ox
            right_x = GRID_X0 + rc * CELL_W + SPR_W.get(
                          self.enemies[0][rc] or "rabbit", 10) + self.ox

            if   self.dir ==  1 and right_x + STEP_X > GW - 2:
                self.oy += STEP_Y;  self.dir = -1
            elif self.dir == -1 and left_x  - STEP_X < 2:
                self.oy += STEP_Y;  self.dir =  1
            else:
                self.ox += self.dir * STEP_X

            play(SND_MARCH[self.march_idx % 4])
            self.march_idx      += 1
            self._next_march     = t + self._march_interval()

        if t >= self._next_shoot:
            shooters = self._bottom_shooters()
            if shooters:
                r, c = random.choice(shooters)
                rect = self.cell_rect(r, c)
                if rect:
                    self.bullets.append([rect[0] + rect[2]//2, rect[1] + rect[3]])
            self._next_shoot = t + max(400, SHOOT_INTERVAL_MS - self.level * 100)

        self.bullets = [[bx, by + EBULLET_SPEED] for bx, by in self.bullets if by < GH]

    def draw(self, surf):
        for r in range(ROWS):
            for c in range(COLS):
                kind = self.enemies[r][c]
                if not kind:
                    continue
                rect = self.cell_rect(r, c)
                if rect:
                    _stamp(surf, ENEMY_SPRITES[kind], rect[0], rect[1])
        for bx, by in self.bullets:
            pygame.draw.rect(surf, COL_EBULLET, (bx - 1, by - 3, 2, 4))
            pygame.draw.rect(surf, (255, 255, 255), (bx, by - 2, 1, 2))


class Explosion:
    DURATION = 500

    def __init__(self, x, y, size=10):
        self.x     = x
        self.y     = y
        self.size  = size
        self.start = pygame.time.get_ticks()

    @property
    def done(self):
        return pygame.time.get_ticks() - self.start > self.DURATION

    def draw(self, surf):
        t    = pygame.time.get_ticks() - self.start
        frac = t / self.DURATION
        n    = max(1, int(self.size * (1 - frac * 0.5)))
        col  = COL_EXPLODE[min(len(COL_EXPLODE) - 1, int(frac * len(COL_EXPLODE)))]
        for dx, dy in [(-n,0),(n,0),(0,-n),(0,n),(-n,-n),(n,-n),(-n,n),(n,n)]:
            px, py = self.x + dx, self.y + dy
            if 0 <= px < GW and 0 <= py < GH:
                surf.set_at((px, py), col)
        if frac < 0.6:
            surf.set_at((self.x, self.y), (255, 255, 255))

# ─────────────────────────────────────────────────────────────────────────────
# DRAWING HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def draw_title(surf):
    surf.fill(COL_BG)
    random.seed(42)
    for _ in range(60):
        surf.set_at((random.randint(0, GW-1), random.randint(0, GH-1)),
                    random.choice([(255,255,255),(170,170,170),(85,85,85)]))
    random.seed()

    draw_text(surf, "GOAT INVADERS",  GW//2 - 42,  40, ( 85,255, 85), FONT_LG)
    draw_text(surf, "DEFEND THE FARM",GW//2 - 44,  58, (255,255, 85), FONT_SM)

    for i, (_, spr, label) in enumerate([
        ("toad",   TOAD_SPR,   "= 30 PTS  CANE TOAD"),
        ("fox",    FOX_SPR,    "= 20 PTS  FOX"),
        ("rabbit", RABBIT_SPR, "= 10 PTS  RABBIT"),
    ]):
        _stamp(surf, spr,  30, 82 + i * 20)
        draw_text(surf, label, 50, 83 + i * 20)

    if ANDROID:
        draw_text(surf, "TOUCH CONTROLS ON-SCREEN", GW//2 - 68, 150, ( 85,255,255), FONT_SM)
    else:
        draw_text(surf, "A/D or ARROWS:  MOVE",     GW//2 - 55, 150, ( 85,255,255), FONT_SM)
        draw_text(surf, "SPACE:  SHOOT",             GW//2 - 36, 162, ( 85,255,255), FONT_SM)
        draw_text(surf, "ESC:  QUIT",                GW//2 - 28, 174, ( 85,255,255), FONT_SM)

    _stamp(surf, GOAT_SPR, GW//2 - 6, 196)
    t = pygame.time.get_ticks()
    if (t // 500) % 2 == 0:
        draw_text(surf, "-- PRESS SPACE TO START --", GW//2 - 66, 222, (255,255,85), FONT_SM)
    draw_text(surf, "v1.0  MADE IN TASMANIA", 10, GH - 14, (85,85,85), FONT_SM)


def draw_hud(surf, player, level):
    pygame.draw.rect(surf, (0, 0, 85), (0, 0, GW, 18))
    draw_text(surf, f"SCORE {player.score:05d}", 4,  4, COL_SCORE,      FONT_SM)
    draw_text(surf, f"HI    {player.hi:05d}",    4, 11, (170, 170,  0), FONT_SM)
    draw_text(surf, f"LVL {level}", GW//2 - 14,  4, ( 85,255,255),      FONT_SM)
    lx = GW - 4
    for _ in range(player.lives):
        lx -= 10
        surf.set_at((lx + 3, 4), _PAL['T'])
        surf.set_at((lx + 6, 4), _PAL['T'])
        pygame.draw.rect(surf, _PAL['t'], (lx + 2, 6, 7, 5))
        pygame.draw.rect(surf, _PAL['T'], (lx + 2, 11, 2, 3))
        pygame.draw.rect(surf, _PAL['T'], (lx + 7, 11, 2, 3))
    pygame.draw.rect(surf, COL_GROUND, (0, GROUND_Y, GW, 2))
    for gx in range(4, GW, 14):
        surf.set_at((gx,     GROUND_Y - 1), COL_GROUND)
        surf.set_at((gx + 1, GROUND_Y - 2), (0, 170, 0))
        surf.set_at((gx + 2, GROUND_Y - 1), COL_GROUND)


def draw_game_over(surf, score, hi, win=False):
    ov = pygame.Surface((GW, GH), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 160))
    surf.blit(ov, (0, 0))
    if win:
        draw_text(surf, "FARM  SAVED!",      GW//2-34, GH//2-30, ( 85,255, 85), FONT_LG)
        draw_text(surf, "ALL PESTS DEFEATED",GW//2-50, GH//2-10, (255,255, 85), FONT_SM)
    else:
        draw_text(surf, "GAME  OVER",        GW//2-29, GH//2-30, (255, 85, 85), FONT_LG)
        draw_text(surf, "THE PESTS WON!",    GW//2-36, GH//2-10, (255,255, 85), FONT_SM)
    draw_text(surf, f"SCORE: {score:05d}",   GW//2-30, GH//2+ 8, (255,255,255), FONT_SM)
    draw_text(surf, f"HI:    {hi:05d}",      GW//2-30, GH//2+18, (255,255, 85), FONT_SM)
    if (pygame.time.get_ticks() // 600) % 2 == 0:
        draw_text(surf, "PRESS SPACE TO PLAY AGAIN", GW//2-66, GH//2+34, (85,255,255), FONT_SM)


def draw_touch_buttons(win_surf, t_left, t_right):
    """Draw on-screen controls in the BTN_STRIP area at the bottom of WIN."""
    pad  = 8
    by   = SCREEN_H - BTN_STRIP + pad
    bh   = BTN_STRIP - pad * 2
    bw   = (SCREEN_W - pad * 4) // 3
    mid_y = by + bh // 2
    r    = 14   # border radius

    btn_data = [
        (pad,                  t_left,  (0,100,0),  (0,200,0),  "◀"),
        (pad*2 + bw,           False,   (130,0,0),  (255,85,85),"●"),
        (pad*3 + bw * 2,       t_right, (0,100,0),  (0,200,0),  "▶"),
    ]
    font_size = max(20, bh // 2)
    btn_font  = pygame.font.Font(None, font_size)

    for bx, active, fill_col, border_col, label in btn_data:
        col = tuple(min(255, c + 40) for c in fill_col) if active else fill_col
        pygame.draw.rect(win_surf, col,        (bx, by, bw, bh), border_radius=r)
        pygame.draw.rect(win_surf, border_col, (bx, by, bw, bh), 3, border_radius=r)
        txt = btn_font.render(label, True, border_col)
        win_surf.blit(txt, (bx + bw//2 - txt.get_width()//2,
                            mid_y   - txt.get_height()//2))


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def new_game(level, hi):
    p = Player()
    p.hi = hi
    return p, EnemyGrid(level=level), []


async def main():
    state  = "title"
    level  = 1
    hi     = 0
    player, grid, explosions = new_game(level, hi)

    stars = [(random.randint(0, GW-1), random.randint(20, GH-1),
              random.choice([(255,255,255),(170,170,170),(85,85,85)]))
             for _ in range(55)]

    # Touch state — track which fingers are in which zone
    touch_left     = False
    touch_right    = False
    fingers_left   = set()   # finger IDs holding the left button
    fingers_right  = set()   # finger IDs holding the right button

    def _touch_zone(norm_x, norm_y):
        """Map normalised finger position → 'left'/'fire'/'right'/'game'."""
        real_y = norm_y * SCREEN_H
        if real_y > SCREEN_H - BTN_STRIP:          # inside button strip
            if   norm_x < 0.33: return "left"
            elif norm_x > 0.67: return "right"
            else:               return "fire"
        return "game"

    while True:
        CLOCK.tick(FPS)

        # ── Events ───────────────────────────────────────────────────────────
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            # ── Keyboard ─────────────────────────────────────────────────────
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if state == "title" and ev.key == pygame.K_SPACE:
                    level  = 1
                    player, grid, explosions = new_game(level, hi)
                    state  = "playing"
                elif state in ("over", "win") and ev.key == pygame.K_SPACE:
                    level  = level + 1 if state == "win" else 1
                    player, grid, explosions = new_game(level, hi)
                    state  = "playing"
                elif state == "playing" and ev.key == pygame.K_SPACE:
                    player.shoot()

            # ── Touch / finger ───────────────────────────────────────────────
            if ev.type == pygame.FINGERDOWN:
                zone = _touch_zone(ev.x, ev.y)
                if state == "title":
                    level  = 1
                    player, grid, explosions = new_game(level, hi)
                    state  = "playing"
                elif state in ("over", "win"):
                    level  = level + 1 if state == "win" else 1
                    player, grid, explosions = new_game(level, hi)
                    state  = "playing"
                elif state == "playing":
                    if zone == "left":
                        fingers_left.add(ev.fingerId);  touch_left  = True
                    elif zone == "right":
                        fingers_right.add(ev.fingerId); touch_right = True
                    else:   # fire button or tap anywhere in game area
                        player.shoot()

            if ev.type == pygame.FINGERUP:
                fingers_left.discard(ev.fingerId)
                fingers_right.discard(ev.fingerId)
                touch_left  = bool(fingers_left)
                touch_right = bool(fingers_right)

        # ── Playing input (keyboard + touch) ─────────────────────────────────
        if state == "playing":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]  or keys[pygame.K_a] or touch_left:
                player.move(-PLAYER_SPEED)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d] or touch_right:
                player.move(+PLAYER_SPEED)

        # ── Update ───────────────────────────────────────────────────────────
        if state == "playing":
            player.update_bullet()
            grid.update()
            explosions = [e for e in explosions if not e.done]

            # Player bullet vs enemies
            if player.bullet:
                bx, by = player.bullet
                for r in range(ROWS):
                    for c in range(COLS):
                        kind = grid.enemies[r][c]
                        if not kind:
                            continue
                        rect = grid.cell_rect(r, c)
                        if not rect:
                            continue
                        ex, ey, ew, eh = rect
                        if ex <= bx <= ex + ew and ey <= by <= ey + eh:
                            grid.enemies[r][c] = None
                            player.score += ENEMY_POINTS[kind]
                            player.hi     = hi = max(hi, player.score)
                            explosions.append(Explosion(ex+ew//2, ey+eh//2, 8))
                            player.bullet = None
                            play(SND_HIT)
                            break
                    else:
                        continue
                    break

            # Enemy bullets vs player
            if player.alive:
                new_ebs = []
                for bx, by in grid.bullets:
                    if (player.x <= bx <= player.x + player.W and
                            player.y <= by <= player.y + player.H):
                        player.hit()
                        explosions.append(Explosion(player.x+player.W//2,
                                                    player.y+player.H//2, 10))
                    else:
                        new_ebs.append([bx, by])
                grid.bullets = new_ebs

            # Enemies reach the ground
            for r, c in grid._alive_cells():
                rect = grid.cell_rect(r, c)
                if rect and rect[1] + rect[3] >= GROUND_Y:
                    player.alive = False
                    break

            if   grid.alive_count() == 0: play(SND_WIN);  state = "win"
            elif not player.alive:                         state = "over"

        # ── Draw ─────────────────────────────────────────────────────────────
        CANVAS.fill(COL_BG)

        if state == "title":
            draw_title(CANVAS)
        else:
            for sx, sy, sc in stars:
                CANVAS.set_at((sx, sy), sc)
            draw_hud(CANVAS, player, level)
            grid.draw(CANVAS)
            player.draw(CANVAS)
            for e in explosions:
                e.draw(CANVAS)
            if player.bullet:
                bx, by = player.bullet
                pygame.draw.rect(CANVAS, COL_PBULLET, (bx-1, by, 2, 5))
            if state in ("over", "win"):
                draw_game_over(CANVAS, player.score, hi, win=(state == "win"))

        # Scale low-res canvas → WIN
        WIN.fill((0, 0, 0))
        scaled = pygame.transform.scale(CANVAS, (GW * PX, GH * PX))
        WIN.blit(scaled, (GAME_X, GAME_Y))

        # Touch buttons drawn at real-pixel scale on WIN (Android only)
        if ANDROID and BTN_STRIP > 0:
            draw_touch_buttons(WIN, touch_left, touch_right)

        pygame.display.flip()
        await asyncio.sleep(0)   # yield to browser event loop (pygbag)


if __name__ == "__main__":
    asyncio.run(main())
