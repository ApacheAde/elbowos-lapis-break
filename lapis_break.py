#!/usr/bin/env python3
"""Lapis Break — original ElbowOS neon vertical billiards. Python 3 + pygame."""
from __future__ import annotations

import math
import os
import random
import subprocess
import sys
from pathlib import Path

import pygame

TITLE = "LAPIS BREAK"
OUT = Path("/home/workdir/artifacts/LAPIS_BREAK_ElbowOS.mp4")
W, H, FPS, SECONDS = 1080, 1920, 30, 15
FRAMES = FPS * SECONDS
R = 28
FRICTION = 0.988
MIN_V = 0.12

# table felt
TX, TY, TW, TH = 90, 260, 900, 1480
POCKETS = [
    (TX, TY), (TX + TW / 2, TY - 8), (TX + TW, TY),
    (TX, TY + TH), (TX + TW / 2, TY + TH + 8), (TX + TW, TY + TH),
]
PR = 46
PALETTE = [
    (80, 210, 255), (255, 196, 64), (255, 92, 160), (90, 255, 170),
    (180, 120, 255), (255, 120, 70), (70, 140, 255), (255, 240, 210),
]


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class Ball:
    def __init__(self, x, y, color, cue=False):
        self.x, self.y, self.vx, self.vy = x, y, 0.0, 0.0
        self.color, self.cue, self.live = color, cue, True

    def moving(self):
        return abs(self.vx) + abs(self.vy) > MIN_V


class Game:
    def __init__(self, seed=20260925):
        self.rng = random.Random(seed)
        self.score = 0
        self.t = 0
        self.flash = 0
        self.aim = -math.pi / 2
        self.power = 16.0
        self.shots = 0
        self.sparks = []
        self.reset_rack()

    def reset_rack(self):
        self.balls = [Ball(TX + TW / 2, TY + TH - 220, (240, 248, 255), True)]
        cx, cy = TX + TW / 2, TY + 280
        n, i = 0, 0
        for row in range(4):
            for col in range(row + 1):
                x = cx + (col - row / 2) * (R * 2.12)
                y = cy + row * (R * 1.86)
                self.balls.append(Ball(x, y, PALETTE[i % len(PALETTE)]))
                i += 1
                n += 1

    def all_still(self):
        return all((not b.live) or (not b.moving()) for b in self.balls)

    def cue(self):
        return self.balls[0]

    def shoot(self, ang, pwr):
        c = self.cue()
        if not c.live:
            c.live, c.x, c.y = True, TX + TW / 2, TY + TH - 220
        c.vx, c.vy = math.cos(ang) * pwr, math.sin(ang) * pwr
        self.shots += 1

    def autoplay(self):
        if not self.all_still() or self.t < 18:
            return
        c = self.cue()
        targets = [b for b in self.balls[1:] if b.live]
        if not targets:
            self.reset_rack()
            return
        tgt = min(targets, key=lambda b: dist((c.x, c.y), (b.x, b.y)))
        ang = math.atan2(tgt.y - c.y, tgt.x - c.x)
        ang += self.rng.uniform(-0.12, 0.12)
        self.aim = ang
        self.shoot(ang, self.rng.uniform(14, 22))

    def collide(self):
        live = [b for b in self.balls if b.live]
        for i, a in enumerate(live):
            for b in live[i + 1 :]:
                dx, dy = b.x - a.x, b.y - a.y
                d = math.hypot(dx, dy) or 0.001
                if d >= R * 2:
                    continue
                nx, ny = dx / d, dy / d
                overlap = R * 2 - d
                a.x -= nx * overlap * 0.5
                a.y -= ny * overlap * 0.5
                b.x += nx * overlap * 0.5
                b.y += ny * overlap * 0.5
                dvx, dvy = a.vx - b.vx, a.vy - b.vy
                rel = dvx * nx + dvy * ny
                if rel <= 0:
                    continue
                a.vx -= rel * nx
                a.vy -= rel * ny
                b.vx += rel * nx
                b.vy += rel * ny
                self.sparks.append([ (a.x + b.x) / 2, (a.y + b.y) / 2, 8])

    def walls_pockets(self):
        for b in self.balls:
            if not b.live:
                continue
            for px, py in POCKETS:
                if dist((b.x, b.y), (px, py)) < PR - 6:
                    b.live = False
                    b.vx = b.vy = 0
                    if b.cue:
                        self.score = max(0, self.score - 15)
                    else:
                        self.score += 80
                        self.flash = 10
                    break
            if not b.live:
                continue
            if b.x < TX + R:
                b.x, b.vx = TX + R, abs(b.vx) * 0.86
            if b.x > TX + TW - R:
                b.x, b.vx = TX + TW - R, -abs(b.vx) * 0.86
            if b.y < TY + R:
                b.y, b.vy = TY + R, abs(b.vy) * 0.86
            if b.y > TY + TH - R:
                b.y, b.vy = TY + TH - R, -abs(b.vy) * 0.86

    def step(self, auto=True):
        self.t += 1
        if auto:
            self.autoplay()
        for b in self.balls:
            if not b.live:
                continue
            b.x += b.vx
            b.y += b.vy
            b.vx *= FRICTION
            b.vy *= FRICTION
            if not b.moving():
                b.vx = b.vy = 0
        self.collide()
        self.walls_pockets()
        self.sparks = [[x, y, n - 1] for x, y, n in self.sparks if n > 1]
        if self.flash:
            self.flash -= 1
        if sum(1 for b in self.balls[1:] if b.live) == 0 and self.all_still():
            self.reset_rack()


def draw(surf, g, fonts):
    fl, fm, fs = fonts
    t = g.t
    for y in range(0, H, 6):
        k = y / H
        c = (
            max(0, min(255, int(6 + 18 * k + 8 * math.sin(t * 0.03 + y * 0.01)))),
            max(0, min(255, int(10 + 28 * k))),
            max(0, min(255, int(28 + 50 * k))),
        )
        pygame.draw.rect(surf, c, (0, y, W, 6))
    # gold rail
    pygame.draw.rect(surf, (196, 150, 48), (TX - 36, TY - 36, TW + 72, TH + 72), border_radius=40)
    pygame.draw.rect(surf, (12, 48, 92), (TX - 10, TY - 10, TW + 20, TH + 20), border_radius=28)
    pygame.draw.rect(surf, (18, 92, 128), (TX, TY, TW, TH), border_radius=18)
    # felt grain
    for i in range(12):
        yy = TY + 40 + i * 120
        pygame.draw.line(surf, (28, 110, 148), (TX + 20, yy), (TX + TW - 20, yy), 1)
    for px, py in POCKETS:
        pygame.draw.circle(surf, (6, 8, 16), (int(px), int(py)), PR)
        pygame.draw.circle(surf, (40, 30, 20), (int(px), int(py)), PR, 3)
    # aim line
    c = g.cue()
    if c.live and g.all_still():
        ex = c.x + math.cos(g.aim) * 240
        ey = c.y + math.sin(g.aim) * 240
        pygame.draw.line(surf, (180, 230, 255), (int(c.x), int(c.y)), (int(ex), int(ey)), 3)
    for x, y, n in g.sparks:
        pygame.draw.circle(surf, (255, 255, 210), (int(x), int(y)), 4 + n)
    for b in g.balls:
        if not b.live:
            continue
        pygame.draw.circle(surf, (0, 0, 0), (int(b.x + 3), int(b.y + 5)), R)
        pygame.draw.circle(surf, b.color, (int(b.x), int(b.y)), R)
        pygame.draw.circle(surf, (255, 255, 255), (int(b.x - 8), int(b.y - 9)), 7)
        if not b.cue:
            pygame.draw.circle(surf, (20, 24, 40), (int(b.x), int(b.y)), 8)
    if g.flash:
        glow = pygame.Surface((W, H), pygame.SRCALPHA)
        glow.fill((80, 180, 255, 40))
        surf.blit(glow, (0, 0))
    bar = pygame.Surface((W, 170), pygame.SRCALPHA)
    bar.fill((4, 10, 28, 220))
    surf.blit(bar, (0, 0))
    surf.blit(fl.render(TITLE, True, (120, 220, 255)), (40, 16))
    surf.blit(fs.render("ElbowOS  ·  Python 3 neon billiards", True, (170, 200, 230)), (44, 96))
    sc = fm.render(f"SCORE  {g.score:04d}", True, (255, 210, 80))
    surf.blit(sc, (W - sc.get_width() - 40, 28))
    foot = pygame.Surface((W, 96), pygame.SRCALPHA)
    foot.fill((4, 10, 28, 220))
    surf.blit(foot, (0, H - 96))
    tag = fs.render("x.com/ElbowOS", True, (120, 220, 255))
    surf.blit(tag, (W - tag.get_width() - 40, H - 64))
    hint = fs.render("drag to aim  ·  click to break", True, (140, 170, 200))
    surf.blit(hint, (40, H - 64))


def record(out: Path = OUT) -> Path:
    pygame.init()
    pygame.font.init()
    surf = pygame.Surface((W, H))
    try:
        fonts = (
            pygame.font.SysFont("dejavusans", 70, bold=True),
            pygame.font.SysFont("dejavusans", 40, bold=True),
            pygame.font.SysFont("dejavusans", 28),
        )
    except Exception:
        fonts = (pygame.font.Font(None, 78), pygame.font.Font(None, 46), pygame.font.Font(None, 32))
    g = Game()
    tmp = out.with_suffix(".tmp.mp4")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "20", "-preset", "veryfast", "-movflags", "+faststart", str(tmp),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    assert proc.stdin
    for _ in range(FRAMES):
        g.step(auto=True)
        draw(surf, g, fonts)
        proc.stdin.write(pygame.image.tostring(surf, "RGB"))
    proc.stdin.close()
    err = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
    rc = proc.wait()
    pygame.quit()
    if rc != 0 or not tmp.exists() or tmp.stat().st_size < 1000:
        raise RuntimeError(f"ffmpeg failed ({rc}): {err[-800:]}")
    tmp.replace(out)
    return out


def play():
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((W // 2, H // 2))
    pygame.display.set_caption(TITLE)
    canvas = pygame.Surface((W, H))
    clock = pygame.time.Clock()
    fonts = (
        pygame.font.SysFont("dejavusans", 70, bold=True),
        pygame.font.SysFont("dejavusans", 40, bold=True),
        pygame.font.SysFont("dejavusans", 28),
    )
    g = Game()
    dragging = False
    run = True
    while run:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                run = False
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                run = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                dragging = True
            elif e.type == pygame.MOUSEBUTTONUP and dragging:
                dragging = False
                if g.all_still():
                    mx, my = pygame.mouse.get_pos()
                    mx, my = mx * 2, my * 2
                    g.aim = math.atan2(my - g.cue().y, mx - g.cue().x)
                    g.shoot(g.aim, 18)
        if dragging and g.all_still():
            mx, my = pygame.mouse.get_pos()
            g.aim = math.atan2(my * 2 - g.cue().y, mx * 2 - g.cue().x)
        g.step(auto=False)
        draw(canvas, g, fonts)
        screen.blit(pygame.transform.smoothscale(canvas, (W // 2, H // 2)), (0, 0))
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    if "--play" in sys.argv:
        play()
    else:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        path = record()
        print(path)
        print("bytes", path.stat().st_size)
