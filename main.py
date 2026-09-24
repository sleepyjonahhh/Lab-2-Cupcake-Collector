import asyncio
import math
import os
import random
import sys
from array import array
from io import BytesIO
from urllib.request import Request, urlopen
import pygame

W, H = 900, 675
FPS = 60
GROUND_Y = 618

GRAVITY = 2200
MOVE_ACCEL = 5200
MAX_SPEED = 330
FRICTION = 4200
AIR_CONTROL = 0.75
JUMP_VEL = -820
DOUBLE_JUMP_VEL = -720
SPRING_VEL = -1250
MAX_FALL = 1100
COYOTE_TIME = 0.10
JUMP_BUFFER = 0.12

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE_DIR, "assets")
HIGHSCORE_FILE = os.path.join(BASE_DIR, "highscore.txt")
SPRITE_URLS = {
    "cupcake.png": "https://cdn.phototourl.com/member/2026-09-24-fc1c500d-e327-44f3-82c6-a2add28de56f.webp",
    "chicken.png": "https://cdn.phototourl.com/member/2026-09-24-ca537e9f-b78b-409f-b6df-7736d5cd8897.webp",
}

OUTLINE = (40, 36, 30)
GRASS = (115, 191, 46)
GRASS_DARK = (86, 150, 36)
GRASS_LIGHT = (160, 222, 90)
DIRT = (222, 216, 149)
DIRT_DARK = (196, 184, 118)
CRUMBLE = (205, 150, 95)
CRUMBLE_DARK = (160, 108, 62)
CLOUD = (250, 252, 255)
CLOUD_SHADE = (205, 228, 238)
WHITE = (255, 255, 255)
PINK = (242, 120, 140)
GOLD = (255, 205, 60)

COURSES = [
    {
        "name": "Sunny Steps",
        "target": 8,
        "time": 60,
        "platforms": [
            (60, 520, 150, "static"),
            (270, 440, 130, "static"),
            (460, 370, 130, "static"),
            (660, 300, 160, "static"),
            (430, 230, 120, "static"),
            (180, 280, 150, "static"),
            (20, 190, 130, "static"),
            (700, 160, 140, "static"),
            (330, 120, 130, "static"),
        ],
        "springs": [],
        "spikes": [],
    },
    {
        "name": "Cloud Cruise",
        "target": 10,
        "time": 60,
        "platforms": [
            (40, 500, 130, "static"),
            (740, 500, 130, "static"),
            (230, 470, 110, "move", 170, 0, 4.0),
            (430, 420, 110, "move", 0, -140, 4.0),
            (620, 360, 110, "move", -130, 0, 3.5),
            (60, 300, 140, "static"),
            (720, 280, 140, "static"),
            (260, 220, 110, "move", 170, 0, 4.5),
            (390, 120, 140, "static"),
        ],
        "springs": [(830, GROUND_Y)],
        "spikes": [],
    },
    {
        "name": "Crumble Canyon",
        "target": 10,
        "time": 55,
        "platforms": [
            (20, 420, 120, "static"),
            (200, 500, 100, "crumble"),
            (360, 430, 100, "crumble"),
            (520, 500, 100, "crumble"),
            (680, 430, 100, "crumble"),
            (780, 320, 110, "static"),
            (560, 260, 100, "crumble"),
            (380, 210, 100, "crumble"),
            (200, 270, 100, "crumble"),
            (30, 200, 110, "static"),
            (400, 105, 120, "static"),
            (660, 150, 100, "move", 110, 0, 4.0),
        ],
        "springs": [(450, GROUND_Y)],
        "spikes": [],
    },
]


def make_placeholder_image(name):
    if name == "background.png":
        surf = pygame.Surface((W, H), pygame.SRCALPHA)
        for y in range(H):
            r = min(255, 160 + y * 0.2)
            g = min(255, 205 + y * 0.15)
            b = min(255, 245 + y * 0.05)
            pygame.draw.line(surf, (int(r), int(g), int(b)), (0, y), (W, y))
        for x in range(0, W + 80, 140):
            pygame.draw.ellipse(surf, (255, 255, 255, 180), (x, 40, 110, 36))
            pygame.draw.ellipse(surf, (255, 255, 255, 180), (x + 28, 22, 120, 40))
        pygame.draw.rect(surf, (125, 193, 76), (0, GROUND_Y, W, H - GROUND_Y))
        pygame.draw.rect(surf, (90, 75, 55), (0, GROUND_Y + 20, W, H - GROUND_Y - 20))
        return surf

    if name == "cupcake.png":
        surf = pygame.Surface((34, 34), pygame.SRCALPHA)
        for xx in range(3, 31):
            pygame.draw.rect(surf, (255, 180, 150), (xx, 8, 1, 1))
        pygame.draw.rect(surf, (245, 170, 140), (6, 10, 22, 10))
        pygame.draw.rect(surf, (249, 206, 131), (7, 11, 20, 8))
        pygame.draw.rect(surf, (255, 192, 200), (4, 7, 26, 6))
        pygame.draw.rect(surf, (255, 200, 90), (8, 18, 18, 7))
        pygame.draw.rect(surf, (120, 80, 40), (10, 25, 14, 7))
        pygame.draw.rect(surf, (255, 160, 110), (15, 0, 4, 9))
        for px, py, col in [
            (6, 8, (80, 160, 220)),
            (9, 9, (255, 80, 120)),
            (18, 7, (80, 200, 120)),
            (24, 8, (255, 220, 100)),
            (13, 11, (255, 110, 140)),
            (20, 12, (90, 120, 220)),
        ]:
            pygame.draw.rect(surf, col, (px, py, 2, 2))
        return surf

    if name == "chicken.png":
        surf = pygame.Surface((64, 64), pygame.SRCALPHA)
        body = (128, 122, 110)
        dark = (90, 82, 74)
        beak = (255, 150, 60)
        gold = (255, 192, 60)
        shadow = (68, 61, 56)
        pygame.draw.rect(surf, dark, (18, 12, 28, 8))
        pygame.draw.rect(surf, body, (12, 18, 40, 20))
        pygame.draw.rect(surf, shadow, (16, 22, 32, 12))
        pygame.draw.rect(surf, dark, (11, 30, 42, 16))
        pygame.draw.rect(surf, body, (16, 34, 32, 10))
        pygame.draw.rect(surf, gold, (22, 30, 7, 5))
        pygame.draw.rect(surf, gold, (35, 30, 7, 5))
        pygame.draw.rect(surf, beak, (40, 24, 8, 4))
        pygame.draw.rect(surf, dark, (13, 20, 4, 4))
        pygame.draw.rect(surf, dark, (43, 20, 4, 4))
        pygame.draw.rect(surf, dark, (18, 46, 8, 10))
        pygame.draw.rect(surf, dark, (38, 46, 8, 10))
        pygame.draw.rect(surf, dark, (24, 50, 16, 6))
        return surf

    surf = pygame.Surface((64, 64), pygame.SRCALPHA)
    pygame.draw.rect(surf, (130, 130, 180), (8, 8, 48, 48), border_radius=10)
    pygame.draw.rect(surf, (230, 190, 70), (16, 16, 32, 32), border_radius=8)
    return surf


def load_image(name):
    url = SPRITE_URLS.get(name)
    if url:
        try:
            request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=8) as response:
                data = response.read()
            try:
                image = pygame.image.load(BytesIO(data), "sprite.webp").convert_alpha()
            except pygame.error:
                from PIL import Image

                webp = Image.open(BytesIO(data)).convert("RGBA")
                image = pygame.image.fromstring(webp.tobytes(), webp.size, "RGBA")
            image = image.convert_alpha()
            image.lock()
            for y in range(image.get_height()):
                for x in range(image.get_width()):
                    r, g, b, a = image.get_at((x, y))
                    if r >= 245 and g >= 245 and b >= 245:
                        image.set_at((x, y), (r, g, b, 0))
            image.unlock()
            return image
        except (ImportError, OSError, pygame.error):
            pass

    path = os.path.join(ASSET_DIR, name)
    if not os.path.exists(path):
        return make_placeholder_image(name)
    try:
        return pygame.image.load(path).convert_alpha()
    except pygame.error:
        return make_placeholder_image(name)


def scale_to_height(img, h):
    w = max(1, round(img.get_width() * h / img.get_height()))
    return pygame.transform.scale(img, (w, h))


def load_highscore():
    try:
        with open(HIGHSCORE_FILE) as f:
            return int(f.read().strip() or 0)
    except (OSError, ValueError):
        return 0


def save_highscore(v):
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            f.write(str(v))
    except OSError:
        pass


class Sfx:
    def __init__(self):
        self.ok = False
        self.sounds = {}
        try:
            pygame.mixer.pre_init(22050, -16, 1, 512)
            pygame.mixer.init()
            self.rate, _, self.channels = pygame.mixer.get_init()
            self.ok = True
        except pygame.error:
            return
        self.sounds["jump"] = self.tone([520, 780], 0.09, "square", 0.18)
        self.sounds["double"] = self.tone([700, 1050], 0.09, "square", 0.16)
        self.sounds["collect"] = self.tone([880, 1175, 1568], 0.16, "square", 0.2)
        self.sounds["gold"] = self.tone([1047, 1319, 1568, 2093], 0.28, "square", 0.2)
        self.sounds["spring"] = self.tone([220, 880], 0.2, "sine", 0.3)
        self.sounds["hurt"] = self.tone([300, 120], 0.25, "square", 0.22)
        self.sounds["crumble"] = self.noise(0.18, 0.15)
        self.sounds["clear"] = self.tone(
            [523, 659, 784, 1047, 1319], 0.6, "square", 0.18
        )
        self.sounds["lose"] = self.tone([440, 330, 220, 110], 0.7, "square", 0.18)

    def _make(self, samples):
        if self.channels == 2:
            samples = [s for s in samples for _ in (0, 1)]
        return pygame.mixer.Sound(buffer=array("h", samples).tobytes())

    def tone(self, freqs, dur, wave, vol):
        n = int(self.rate * dur)
        out, phase = [], 0.0
        for i in range(n):
            t = i / n
            seg = (
                min(int(t * (len(freqs) - 1)), len(freqs) - 2) if len(freqs) > 1 else 0
            )
            if len(freqs) > 1:
                local = t * (len(freqs) - 1) - seg
                f = freqs[seg] + (freqs[seg + 1] - freqs[seg]) * local
            else:
                f = freqs[0]
            phase += f / self.rate
            s = math.sin(phase * 2 * math.pi)
            if wave == "square":
                s = 1.0 if s >= 0 else -1.0
            env = min(1.0, i / 200) * (1 - t) ** 1.5
            out.append(int(s * env * vol * 32767))
        return self._make(out)

    def noise(self, dur, vol):
        n = int(self.rate * dur)
        return self._make(
            [int(random.uniform(-1, 1) * (1 - i / n) * vol * 32767) for i in range(n)]
        )

    def play(self, name):
        if self.ok and name in self.sounds:
            self.sounds[name].play()


class Platform:
    HEIGHT = 20

    def __init__(
        self, x, y, w, kind="static", dx=0, dy=0, period=4.0, solid_floor=False
    ):
        self.home = pygame.Rect(x, y, w, self.HEIGHT)
        self.rect = self.home.copy()
        self.prev = self.rect.copy()
        self.kind = kind
        self.dx, self.dy, self.period = dx, dy, period
        self.phase = random.uniform(0, math.tau) if kind == "move" else 0
        self.solid_floor = solid_floor
        self.state = "idle"
        self.timer = 0.0
        self.fall_vy = 0.0
        self.fall_y = 0.0
        self.shake = 0

    @property
    def active(self):
        return self.state in ("idle", "shaking")

    def update(self, dt, t, sfx):
        self.prev = self.rect.copy()
        if self.kind == "move":
            s = (math.sin(t * math.tau / self.period + self.phase) + 1) / 2
            self.rect.x = round(self.home.x + self.dx * s)
            self.rect.y = round(self.home.y + self.dy * s)
        elif self.kind == "crumble":
            if self.state == "shaking":
                self.timer -= dt
                self.shake = random.randint(-2, 2)
                if self.timer <= 0:
                    self.state = "falling"
                    self.fall_vy = 0
                    self.fall_y = self.rect.y
                    sfx.play("crumble")
            elif self.state == "falling":
                self.fall_vy += GRAVITY * 0.8 * dt
                self.fall_y += self.fall_vy * dt
                self.rect.y = int(self.fall_y)
                if self.rect.top > H:
                    self.state = "gone"
                    self.timer = 3.0
            elif self.state == "gone":
                self.timer -= dt
                if self.timer <= 0:
                    self.state = "idle"
                    self.rect = self.home.copy()
                    self.prev = self.rect.copy()
                    self.shake = 0

    def stepped_on(self):
        if self.kind == "crumble" and self.state == "idle":
            self.state = "shaking"
            self.timer = 0.45

    def draw(self, surf):
        if self.solid_floor or self.state == "gone":
            return
        r = self.rect.move(self.shake if self.state == "shaking" else 0, 0)
        if self.kind == "move":
            self._draw_cloud(surf, r)
        elif self.kind == "crumble":
            self._draw_block(
                surf,
                r,
                CRUMBLE,
                CRUMBLE_DARK,
                (214, 170, 80),
                (178, 132, 60),
                cracks=True,
            )
        else:
            self._draw_block(surf, r, DIRT, DIRT_DARK, GRASS, GRASS_DARK)

    @staticmethod
    def _draw_block(surf, r, body, body_dark, top, top_dark, cracks=False):
        pygame.draw.rect(surf, OUTLINE, r.inflate(6, 6))
        pygame.draw.rect(surf, body, r)
        pygame.draw.rect(surf, body_dark, (r.x, r.bottom - 5, r.w, 5))
        pygame.draw.rect(surf, top, (r.x, r.y, r.w, 8))
        for sx in range(r.x - 8, r.right, 12):
            pts = [(sx, r.y + 8), (sx + 6, r.y + 8), (sx + 12, r.y), (sx + 6, r.y)]
            clipped = [(max(r.x, min(r.right, px)), py) for px, py in pts]
            pygame.draw.polygon(surf, top_dark, clipped)
        pygame.draw.line(
            surf,
            GRASS_LIGHT if not cracks else (240, 200, 120),
            (r.x, r.y),
            (r.right - 1, r.y),
            2,
        )
        if cracks:
            for cx in range(r.x + 14, r.right - 8, 26):
                pygame.draw.lines(
                    surf,
                    OUTLINE,
                    False,
                    [(cx, r.y + 9), (cx + 4, r.y + 13), (cx - 2, r.bottom - 2)],
                    2,
                )

    @staticmethod
    def _draw_cloud(surf, r):
        base = r.inflate(0, 4)
        bumps = []
        n = max(2, r.w // 26)
        for i in range(n + 1):
            bx = r.x + i * r.w / n
            bumps.append((int(bx), r.y + 4, 13))
        for bx, by, rad in bumps:
            pygame.draw.circle(surf, OUTLINE, (bx, by), rad + 3)
        pygame.draw.rect(surf, OUTLINE, base.inflate(6, 6), border_radius=10)
        for bx, by, rad in bumps:
            pygame.draw.circle(surf, CLOUD, (bx, by), rad)
        pygame.draw.rect(surf, CLOUD, base, border_radius=8)
        pygame.draw.rect(
            surf,
            CLOUD_SHADE,
            (base.x + 4, base.bottom - 6, base.w - 8, 4),
            border_radius=3,
        )


class Spring:
    W, H = 44, 16

    def __init__(self, x, surface_y):
        self.rect = pygame.Rect(x, surface_y - self.H, self.W, self.H)
        self.squash = 0.0

    def update(self, dt):
        self.squash = max(0.0, self.squash - dt * 4)

    def draw(self, surf):
        h = int(self.H * (1 - 0.5 * self.squash))
        base_y = self.rect.bottom
        coil = pygame.Rect(self.rect.x + 8, base_y - h, self.W - 16, h)
        pygame.draw.rect(surf, OUTLINE, coil.inflate(4, 0))
        for yy in range(coil.y + 2, coil.bottom, 4):
            pygame.draw.line(
                surf, (190, 190, 200), (coil.x, yy), (coil.right - 1, yy), 2
            )
        pad = pygame.Rect(self.rect.x, base_y - h - 7, self.W, 8)
        pygame.draw.rect(surf, OUTLINE, pad.inflate(4, 4), border_radius=3)
        pygame.draw.rect(surf, (230, 60, 70), pad, border_radius=2)
        pygame.draw.line(
            surf, (255, 150, 150), (pad.x + 3, pad.y + 1), (pad.right - 4, pad.y + 1), 2
        )

    @property
    def top(self):
        return self.rect.bottom - int(self.H * (1 - 0.5 * self.squash)) - 7


class Spikes:
    SPIKE_H = 18

    def __init__(self, x, surface_y, w):
        self.rect = pygame.Rect(x, surface_y - self.SPIKE_H, w, self.SPIKE_H)
        self.hitbox = self.rect.inflate(-8, -6).move(0, 3)

    def draw(self, surf):
        n = max(1, self.rect.w // 16)
        sw = self.rect.w / n
        for i in range(n):
            x0 = self.rect.x + i * sw
            pts = [
                (x0, self.rect.bottom),
                (x0 + sw / 2, self.rect.y),
                (x0 + sw, self.rect.bottom),
            ]
            pygame.draw.polygon(surf, (200, 205, 215), pts)
            pygame.draw.polygon(surf, OUTLINE, pts, 2)
            pygame.draw.line(
                surf,
                WHITE,
                (x0 + sw / 2, self.rect.y + 3),
                (x0 + sw / 2 - 3, self.rect.bottom - 4),
                1,
            )


class Cupcake:
    SIZE = 40

    def __init__(self, img, gold_img, platform, offset_x, golden):
        self.platform = platform
        self.offset_x = offset_x
        self.golden = golden
        self.img = gold_img if golden else img
        self.lifetime = 6.0 if golden else 10.0
        self.age = 0.0
        self.bob = random.uniform(0, math.tau)
        self.value = 30 if golden else 10

    def anchor_rect(self):
        p = self.platform
        return p.home if p.kind == "crumble" else p.rect

    @property
    def rect(self):
        a = self.anchor_rect()
        y = a.top - self.SIZE - 6 + math.sin(self.age * 4 + self.bob) * 4
        return pygame.Rect(a.x + self.offset_x, int(y), self.SIZE, self.SIZE)

    def update(self, dt):
        self.age += dt
        return self.age < self.lifetime

    def draw(self, surf, t):
        remaining = self.lifetime - self.age
        if remaining < 2.0 and int(t * 12) % 2 == 0:
            return
        r = self.rect
        s = min(1.0, self.age * 6)
        img = self.img
        if s < 1:
            size = max(1, int(self.SIZE * s))
            img = pygame.transform.scale(self.img, (size, size))
        if self.golden:
            glow = pygame.Surface((70, 70), pygame.SRCALPHA)
            a = 70 + int(40 * math.sin(t * 6))
            pygame.draw.circle(glow, (255, 230, 120, a), (35, 35), 30)
            surf.blit(glow, glow.get_rect(center=r.center))
        surf.blit(img, img.get_rect(center=r.center))


class Particle:
    def __init__(self, x, y, color, vx=None, vy=None, life=None, size=None, grav=900):
        self.x, self.y = x, y
        self.vx = vx if vx is not None else random.uniform(-220, 220)
        self.vy = vy if vy is not None else random.uniform(-380, -80)
        self.life = self.max_life = (
            life if life is not None else random.uniform(0.4, 0.8)
        )
        self.size = size if size is not None else random.randint(3, 6)
        self.color = color
        self.grav = grav

    def update(self, dt):
        self.vy += self.grav * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surf):
        s = max(1, int(self.size * self.life / self.max_life + 1))
        pygame.draw.rect(surf, self.color, (int(self.x), int(self.y), s, s))


def render_outlined(font, text, color, outline=OUTLINE, px=2):
    base = font.render(text, True, color)
    out = pygame.Surface(
        (base.get_width() + px * 2, base.get_height() + px * 2), pygame.SRCALPHA
    )
    edge = font.render(text, True, outline)
    for ox in (-px, 0, px):
        for oy in (-px, 0, px):
            if ox or oy:
                out.blit(edge, (px + ox, px + oy))
    out.blit(base, (px, px))
    return out


class FloatText:
    def __init__(self, text, x, y, color, font):
        self.surf = render_outlined(font, text, color)
        self.x, self.y = x, y
        self.life = 0.8

    def update(self, dt):
        self.y -= 40 * dt
        self.life -= dt
        return self.life > 0

    def draw(self, surf):
        img = self.surf.copy()
        img.set_alpha(int(255 * max(0.0, self.life / 0.8)))
        surf.blit(img, img.get_rect(center=(int(self.x), int(self.y))))


class Chicken:
    HB_W, HB_H = 38, 36
    DRAW_H = 50

    def __init__(self, img, x, y):
        self.img_r = scale_to_height(img, self.DRAW_H)
        self.img_l = pygame.transform.flip(self.img_r, True, False)
        self.spawn = (x, y)
        self.reset()

    def reset(self):
        x, y = self.spawn
        self.x, self.y = float(x), float(y)
        self.vx = self.vy = 0.0
        self.facing = 1
        self.on_ground = False
        self.ground_plat = None
        self.coyote = 0.0
        self.jump_buf = 0.0
        self.air_jumps = 1
        self.drop_timer = 0.0
        self.invuln = 0.0
        self.squash = 0.0
        self.walk_t = 0.0

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.HB_W, self.HB_H)

    def request_jump(self):
        self.jump_buf = JUMP_BUFFER

    def cut_jump(self):
        if self.vy < -300:
            self.vy *= 0.55

    def hurt(self, from_x):
        self.invuln = 1.5
        self.vy = -560
        self.vx = 380 if self.rect.centerx >= from_x else -380
        self.on_ground = False
        self.ground_plat = None

    def update(self, dt, keys, platforms, springs, game):
        if self.on_ground and self.ground_plat is not None and self.ground_plat.active:
            p = self.ground_plat
            self.x += p.rect.x - p.prev.x
            self.y += p.rect.y - p.prev.y

        direction = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (
            keys[pygame.K_LEFT] or keys[pygame.K_a]
        )
        accel = MOVE_ACCEL * (1 if self.on_ground else AIR_CONTROL)
        if direction:
            self.vx += direction * accel * dt
            self.facing = direction
        else:
            f = FRICTION * (1 if self.on_ground else 0.35) * dt
            self.vx = 0 if abs(self.vx) <= f else self.vx - math.copysign(f, self.vx)
        limit = MAX_SPEED if self.invuln < 1.2 else 420
        self.vx = max(-limit, min(limit, self.vx))

        if (
            (keys[pygame.K_DOWN] or keys[pygame.K_s])
            and self.on_ground
            and self.ground_plat is not None
            and not self.ground_plat.solid_floor
        ):
            self.drop_timer = 0.22
            self.on_ground = False
            self.ground_plat = None
            self.y += 2

        self.coyote = COYOTE_TIME if self.on_ground else max(0.0, self.coyote - dt)
        self.jump_buf = max(0.0, self.jump_buf - dt)
        self.drop_timer = max(0.0, self.drop_timer - dt)
        self.invuln = max(0.0, self.invuln - dt)
        self.squash *= max(0.0, 1 - dt * 10)

        if self.jump_buf > 0:
            if self.coyote > 0:
                self.vy = JUMP_VEL
                self.on_ground = False
                self.ground_plat = None
                self.coyote = 0
                self.jump_buf = 0
                self.squash = -0.35
                game.sfx.play("jump")
                game.dust(self.rect.midbottom, 6)
            elif self.air_jumps > 0:
                self.vy = DOUBLE_JUMP_VEL
                self.air_jumps -= 1
                self.jump_buf = 0
                self.squash = -0.3
                game.sfx.play("double")
                for _ in range(10):
                    game.particles.append(
                        Particle(
                            self.rect.centerx,
                            self.rect.bottom,
                            WHITE,
                            vx=random.uniform(-160, 160),
                            vy=random.uniform(40, 160),
                            life=0.35,
                            grav=0,
                        )
                    )

        self.vy = min(MAX_FALL, self.vy + GRAVITY * dt)

        self.x += self.vx * dt
        if self.x < 0:
            self.x, self.vx = 0, 0
        elif self.x > W - self.HB_W:
            self.x, self.vx = W - self.HB_W, 0

        prev_bottom = self.y + self.HB_H
        self.y += self.vy * dt
        if self.y < 50:
            self.y = 50
            self.vy = max(self.vy, 0)
            prev_bottom = min(prev_bottom, self.y + self.HB_H)
        was_on_ground = self.on_ground
        self.on_ground = False
        landed_on = None
        if self.vy >= 0:
            r = self.rect
            best = None
            for p in platforms:
                if not p.active:
                    continue
                if self.drop_timer > 0 and not p.solid_floor:
                    continue
                if r.right <= p.rect.left + 4 or r.left >= p.rect.right - 4:
                    continue
                if prev_bottom <= p.prev.top + 6 and r.bottom >= p.rect.top:
                    if best is None or p.rect.top < best.rect.top:
                        best = p
            if best is not None:
                self.y = best.rect.top - self.HB_H
                if not was_on_ground and self.vy > 400:
                    self.squash = min(0.4, self.vy / 2500)
                    game.dust(self.rect.midbottom, 5)
                self.vy = 0
                self.on_ground = True
                self.air_jumps = 1
                landed_on = best
                if best is not self.ground_plat:
                    best.stepped_on()
            r = self.rect
            for s in springs:
                if (
                    r.right > s.rect.left + 4
                    and r.left < s.rect.right - 4
                    and prev_bottom <= s.top + 8
                    and r.bottom >= s.top
                ):
                    self.y = s.top - self.HB_H
                    self.vy = SPRING_VEL
                    self.on_ground = False
                    landed_on = None
                    self.air_jumps = 1
                    self.squash = -0.5
                    s.squash = 1.0
                    game.sfx.play("spring")
                    break
        self.ground_plat = landed_on

        if self.on_ground and abs(self.vx) > 20:
            self.walk_t += dt * abs(self.vx) / 30
        else:
            self.walk_t = 0

    def draw(self, surf, t):
        if self.invuln > 0 and int(t * 20) % 2 == 0:
            return
        img = self.img_r if self.facing > 0 else self.img_l
        sq = self.squash
        w = int(img.get_width() * (1 + sq * 0.6))
        h = int(img.get_height() * (1 - sq * 0.6))
        img = pygame.transform.scale(img, (max(1, w), max(1, h)))
        if not self.on_ground:
            tilt = max(-18, min(18, -self.vy / 45)) * self.facing
            img = pygame.transform.rotate(img, tilt)
        bob = -abs(math.sin(self.walk_t)) * 4
        r = self.rect
        dest = img.get_rect(midbottom=(r.centerx, r.bottom + 3 + bob))
        surf.blit(img, dest)


class Game:
    def __init__(self):
        self.sfx = Sfx()
        pygame.init()
        pygame.display.set_caption("Cupcake Collector")
        self.screen = pygame.display.set_mode((W, H))
        self.clock = pygame.time.Clock()

        self.bg = pygame.transform.scale(load_image("background.png").convert(), (W, H))
        cup = load_image("cupcake.png")
        self.cupcake_img = pygame.transform.scale(cup, (Cupcake.SIZE, Cupcake.SIZE))
        gold = self.cupcake_img.copy()
        gold.fill((90, 70, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
        self.gold_img = gold
        self.icon_img = pygame.transform.scale(cup, (30, 30))
        self.big_cupcake = pygame.transform.scale(cup, (110, 110))
        self.chicken_img = load_image("chicken.png")
        self.big_chicken = scale_to_height(self.chicken_img, 100)
        pygame.display.set_icon(self.icon_img)

        self.font_big = pygame.font.Font(None, 84)
        self.font_med = pygame.font.Font(None, 44)
        self.font_small = pygame.font.Font(None, 30)
        self.font_tiny = pygame.font.Font(None, 24)

        self.highscore = load_highscore()
        self.state = "title"
        self.t = 0.0
        self.new_run()

    def new_run(self):
        self.score = 0
        self.course_index = 0
        self.loop = 0
        self.new_record = False
        self.load_course()

    def load_course(self):
        data = COURSES[self.course_index % len(COURSES)]
        self.loop = self.course_index // len(COURSES)
        self.course_name = data["name"] + (f"  +{self.loop}" if self.loop else "")
        self.target = data["target"] + self.loop * 3
        self.time_left = max(30.0, data["time"] - self.loop * 8)
        self.collected = 0

        self.ground = Platform(-50, GROUND_Y, W + 100, solid_floor=True)
        self.platforms = [self.ground]
        for spec in data["platforms"]:
            x, y, w, kind = spec[:4]
            if kind == "move":
                dx, dy, period = spec[4:7]
                period = period * (0.85**self.loop)
                self.platforms.append(Platform(x, y, w, "move", dx, dy, period))
            else:
                self.platforms.append(Platform(x, y, w, kind))
        self.springs = [Spring(x, y) for x, y in data["springs"]]
        self.spikes = [Spikes(x, y, w) for x, y, w in data["spikes"]]

        self.player = Chicken(self.chicken_img, 14, GROUND_Y - Chicken.HB_H)
        self.cupcakes = []
        self.particles = []
        self.texts = []
        self.spawn_timer = 0.6
        self.banner_timer = 2.2
        self.shake = 0.0

    def spawn_cupcake(self):
        candidates = [p for p in self.platforms if p.state != "gone"]
        for _ in range(30):
            if random.random() < 0.15:
                plat = self.ground
                a = pygame.Rect(20, GROUND_Y, W - 40, 20)
            else:
                others = [p for p in candidates if not p.solid_floor]
                if not others:
                    return
                plat = random.choice(others)
                a = plat.home if plat.kind == "crumble" else plat.rect
            if a.w < Cupcake.SIZE + 6:
                continue
            if plat.solid_floor:
                offset = random.randint(a.x, a.right - Cupcake.SIZE) - plat.rect.x
            else:
                offset = random.randint(3, a.w - Cupcake.SIZE - 3)
            c = Cupcake(
                self.cupcake_img, self.gold_img, plat, offset, random.random() < 0.12
            )
            cr = c.rect
            if any(cr.inflate(10, 30).colliderect(s.rect) for s in self.spikes):
                continue
            if any(cr.colliderect(s.rect.inflate(0, 40)) for s in self.springs):
                continue
            if any(cr.inflate(40, 40).colliderect(o.rect) for o in self.cupcakes):
                continue
            if math.dist(cr.center, self.player.rect.center) < 150:
                continue
            self.cupcakes.append(c)
            for _ in range(8):
                self.particles.append(
                    Particle(
                        cr.centerx,
                        cr.centery,
                        (255, 240, 200),
                        vx=random.uniform(-90, 90),
                        vy=random.uniform(-90, 90),
                        life=0.4,
                        size=3,
                        grav=0,
                    )
                )
            return

    def dust(self, pos, n):
        for _ in range(n):
            self.particles.append(
                Particle(
                    pos[0] + random.uniform(-12, 12),
                    pos[1] - 2,
                    (235, 228, 200),
                    vx=random.uniform(-120, 120),
                    vy=random.uniform(-120, -20),
                    life=0.3,
                    size=4,
                    grav=300,
                )
            )

    def burst(self, pos, golden):
        colors = (
            [GOLD, (255, 240, 150), WHITE]
            if golden
            else [PINK, (255, 190, 200), (80, 160, 230), (250, 210, 60), (90, 180, 90)]
        )
        for _ in range(26 if golden else 16):
            self.particles.append(Particle(pos[0], pos[1], random.choice(colors)))

    async def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 1 / 30)
            self.t += dt
            self.handle_events()
            self.update(dt)
            self.draw()
            pygame.display.flip()
            await asyncio.sleep(0)

    def handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.quit()
            if e.type == pygame.KEYDOWN:
                k = e.key
                if self.state == "title":
                    if k in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                        self.new_run()
                        self.state = "playing"
                    elif k == pygame.K_ESCAPE:
                        self.quit()
                elif self.state == "playing":
                    if k in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                        self.player.request_jump()
                    elif k in (pygame.K_p, pygame.K_ESCAPE):
                        self.state = "paused"
                    elif k == pygame.K_r:
                        self.new_run()
                elif self.state == "paused":
                    if k in (pygame.K_p, pygame.K_ESCAPE, pygame.K_RETURN):
                        self.state = "playing"
                    elif k == pygame.K_q:
                        self.state = "title"
                elif self.state == "clear":
                    if (
                        k in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER)
                        and self.state_timer <= 0
                    ):
                        if self.course_index >= len(COURSES) - 1:
                            self.state = "title"
                            self.new_run()
                        else:
                            self.course_index += 1
                            self.load_course()
                            self.state = "playing"
                elif self.state == "gameover":
                    if (
                        k
                        in (
                            pygame.K_RETURN,
                            pygame.K_SPACE,
                            pygame.K_r,
                            pygame.K_KP_ENTER,
                        )
                        and self.state_timer <= 0
                    ):
                        self.new_run()
                        self.state = "playing"
                    elif k == pygame.K_ESCAPE:
                        self.state = "title"
            if e.type == pygame.KEYUP and self.state == "playing":
                if e.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    self.player.cut_jump()

    def update(self, dt):
        if self.state in ("clear", "gameover"):
            self.state_timer -= dt
            self.particles = [p for p in self.particles if p.update(dt)]
            if self.state == "clear" and random.random() < 0.3:
                self.particles.append(
                    Particle(
                        random.uniform(0, W),
                        -10,
                        random.choice([PINK, GOLD, (90, 180, 230), WHITE]),
                        vx=random.uniform(-40, 40),
                        vy=random.uniform(50, 150),
                        life=4,
                        size=6,
                        grav=60,
                    )
                )
            return
        if self.state == "title":
            for p in self.platforms:
                p.update(dt, self.t, self.sfx)
            return
        if self.state != "playing":
            return

        self.banner_timer = max(0.0, self.banner_timer - dt)
        self.time_left -= dt
        self.shake = max(0.0, self.shake - dt)

        for p in self.platforms:
            p.update(dt, self.t, self.sfx)
        for s in self.springs:
            s.update(dt)

        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self.platforms, self.springs, self)
        pr = self.player.rect

        if self.player.invuln <= 0:
            for s in self.spikes:
                if pr.colliderect(s.hitbox):
                    self.player.hurt(s.rect.centerx)
                    self.sfx.play("hurt")
                    self.shake = 0.3
                    self.time_left = max(0.0, self.time_left - 3.0)
                    for _ in range(14):
                        self.particles.append(
                            Particle(pr.centerx, pr.centery, (90, 80, 70))
                        )
                    break

        alive = []
        for c in self.cupcakes:
            if pr.inflate(6, 6).colliderect(c.rect.inflate(-6, -6)):
                gained = c.value
                self.score += gained
                self.collected += 1
                if c.golden:
                    self.time_left += 3
                self.burst(c.rect.center, c.golden)
                self.sfx.play("gold" if c.golden else "collect")
                label = f"+{gained}"
                if c.golden:
                    label += " +3s"
                self.texts.append(
                    FloatText(
                        label,
                        c.rect.centerx,
                        c.rect.top - 8,
                        GOLD if c.golden else WHITE,
                        self.font_small,
                    )
                )
            elif c.update(dt):
                alive.append(c)
            else:
                cr = c.rect
                for _ in range(6):
                    self.particles.append(
                        Particle(
                            cr.centerx,
                            cr.centery,
                            (200, 200, 200),
                            vx=random.uniform(-60, 60),
                            vy=random.uniform(-60, 10),
                            life=0.4,
                            size=3,
                            grav=0,
                        )
                    )
        self.cupcakes = alive

        self.spawn_timer -= dt
        max_on_screen = 3 + min(2, self.loop)
        if self.spawn_timer <= 0:
            if len(self.cupcakes) < max_on_screen:
                self.spawn_cupcake()
            self.spawn_timer = random.uniform(1.0, 2.2)

        self.particles = [p for p in self.particles if p.update(dt)]
        self.texts = [t for t in self.texts if t.update(dt)]

        if self.collected >= self.target:
            self.clear_bonus = int(self.time_left)
            self.score += self.clear_bonus
            self.state = "clear"
            self.state_timer = 0.8
            self.sfx.play("clear")
            self.update_highscore()
        elif self.time_left <= 0:
            self.time_left = max(0.0, self.time_left)
            self.lose_reason = "Time's up!"
            self.state = "gameover"
            self.state_timer = 0.8
            self.sfx.play("lose")
            self.update_highscore()

    def update_highscore(self):
        if self.score > self.highscore:
            self.highscore = self.score
            self.new_record = True
            save_highscore(self.score)

    def draw(self):
        world = pygame.Surface((W, H))
        world.blit(self.bg, (0, 0))
        if self.state == "title":
            self.screen.blit(world, (0, 0))
            self.draw_title()
            return
        for s in self.spikes:
            s.draw(world)
        for p in self.platforms:
            p.draw(world)
        for s in self.springs:
            s.draw(world)
        for c in self.cupcakes:
            c.draw(world, self.t)
        if self.state != "title":
            self.player.draw(world, self.t)
        for p in self.particles:
            p.draw(world)
        for t in self.texts:
            t.draw(world)

        ox = oy = 0
        if self.shake > 0:
            ox, oy = random.randint(-5, 5), random.randint(-5, 5)
        self.screen.fill(OUTLINE)
        self.screen.blit(world, (ox, oy))

        self.draw_hud()
        if self.state == "paused":
            self.draw_panel("PAUSED", ["P / Esc  -  resume", "Q  -  quit to title"])
        elif self.state == "clear":
            action = (
                "Play Again"
                if self.course_index >= len(COURSES) - 1
                else "Press ENTER for the next course"
            )
            self.draw_panel(
                "CONGRATULATIONS!",
                [
                    "You completed the course!",
                    f"Time:  {int(self.time_left)}s",
                    f"Score:  {self.score}",
                    "",
                    action,
                ],
                color=GOLD,
            )
        elif self.state == "gameover":
            lines = [
                self.lose_reason,
                f"Final score:  {self.score}",
                f"Time:  {int(self.time_left)}s",
                (
                    "NEW HIGH SCORE!"
                    if self.new_record
                    else f"High score:  {self.highscore}"
                ),
                "",
                "ENTER - try again     Esc - title",
            ]
            self.draw_panel("GAME OVER", lines, color=(255, 120, 110))
        elif self.banner_timer > 0:
            a = min(1.0, self.banner_timer / 0.5)
            img = render_outlined(self.font_big, self.course_name, WHITE, px=3)
            sub = render_outlined(
                self.font_small, f"Collect {self.target} cupcakes!", GOLD
            )
            img.set_alpha(int(255 * a))
            sub.set_alpha(int(255 * a))
            self.screen.blit(img, img.get_rect(center=(W // 2, H // 2 - 60)))
            self.screen.blit(sub, sub.get_rect(center=(W // 2, H // 2)))

    def draw_hud(self):
        self.screen.blit(
            render_outlined(self.font_med, f"{self.score}", WHITE), (14, 10)
        )
        self.screen.blit(
            render_outlined(self.font_tiny, f"HI {self.highscore}", (230, 240, 255)),
            (16, 46),
        )

        cx = W // 2
        prog = render_outlined(
            self.font_med, f"{self.collected} / {self.target}", WHITE
        )
        self.screen.blit(self.icon_img, (cx - prog.get_width() // 2 - 38, 12))
        self.screen.blit(prog, (cx - prog.get_width() // 2, 12))
        bar = pygame.Rect(cx - 110, 50, 220, 12)
        pygame.draw.rect(self.screen, OUTLINE, bar.inflate(6, 6), border_radius=4)
        pygame.draw.rect(self.screen, (120, 110, 100), bar, border_radius=3)
        fill = bar.copy()
        fill.w = int(bar.w * min(1.0, self.collected / self.target))
        if fill.w:
            pygame.draw.rect(self.screen, PINK, fill, border_radius=3)

        tl = max(0, math.ceil(self.time_left))
        color = (255, 110, 100) if tl <= 10 and int(self.t * 4) % 2 == 0 else WHITE
        timg = render_outlined(self.font_med, f"{tl}s", color)
        self.screen.blit(timg, (W - 150 - timg.get_width(), 12))

    def draw_panel(self, title, lines, color=WHITE):
        shade = pygame.Surface((W, H), pygame.SRCALPHA)
        shade.fill((20, 30, 40, 140))
        self.screen.blit(shade, (0, 0))
        panel = pygame.Rect(0, 0, 560, 110 + 38 * len(lines))
        panel.center = (W // 2, H // 2)
        pygame.draw.rect(self.screen, OUTLINE, panel.inflate(10, 10), border_radius=14)
        pygame.draw.rect(self.screen, (252, 246, 222), panel, border_radius=10)
        pygame.draw.rect(
            self.screen, (230, 218, 170), panel.inflate(-12, -12), 3, border_radius=8
        )
        t = render_outlined(self.font_big, title, color, px=3)
        self.screen.blit(t, t.get_rect(center=(panel.centerx, panel.y + 52)))
        for i, line in enumerate(lines):
            img = self.font_small.render(line, True, OUTLINE)
            self.screen.blit(
                img, img.get_rect(center=(panel.centerx, panel.y + 110 + i * 38))
            )

    def draw_title(self):
        title = render_outlined(self.font_big, "CUPCAKE COLLECTOR", PINK, px=4)
        self.screen.blit(title, title.get_rect(center=(W // 2, 120)))
        self.screen.blit(
            self.big_cupcake, self.big_cupcake.get_rect(center=(W // 2 + 120, 260))
        )
        self.screen.blit(
            self.big_chicken, self.big_chicken.get_rect(center=(W // 2 - 110, 270))
        )

        lines = [
            ("Objective: collect cupcakes and finish the course", WHITE),
            ("Move: A / D or arrows", WHITE),
            ("Jump: Space / W / Up   Double jump enabled", WHITE),
            ("Down arrow: go down", WHITE),
            ("Cupcake: +10   Gold cupcake: +30", GOLD),
        ]
        rendered = [render_outlined(self.font_small, txt, col) for txt, col in lines]
        max_w = max(img.get_width() for img in rendered)
        line_h = rendered[0].get_height()
        pad_x = 26
        pad_y = 18
        box = pygame.Rect(
            0,
            0,
            max_w + pad_x * 2,
            len(lines) * line_h + (len(lines) - 1) * 4 + pad_y * 2,
        )
        box.center = (W // 2, 430)
        shade = pygame.Surface(box.size, pygame.SRCALPHA)
        pygame.draw.rect(shade, (30, 60, 70, 120), shade.get_rect(), border_radius=14)
        self.screen.blit(shade, box)

        for i, img in enumerate(rendered):
            x = box.centerx - img.get_width() // 2
            y = box.y + pad_y + i * (line_h + 4)
            self.screen.blit(img, (x, y))

        if int(self.t * 2) % 2 == 0:
            s = render_outlined(self.font_med, "Press ENTER to start", WHITE, px=3)
            self.screen.blit(s, s.get_rect(center=(W // 2, 560)))
        hs = render_outlined(
            self.font_tiny, f"High score: {self.highscore}", (230, 240, 255)
        )
        self.screen.blit(hs, (14, 14))

    def quit(self):
        pygame.quit()
        sys.exit()


async def main():
    game = Game()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())
