import asyncio
import os
import random

import pygame

pygame.init()

WIDTH, HEIGHT = 800, 600
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Platformer with Cupcakes")
clock = pygame.time.Clock()

SKY = (111, 190, 201)
CITY = (190, 232, 211)
CITY_LINE = (132, 209, 190)
CLOUD = (247, 250, 220)
GRASS = (113, 201, 104)
GROUND = (232, 218, 157)
RED = (255, 0, 0)
PLATFORM = (178, 226, 164)
PLATFORM_TOP = (224, 241, 164)
PLATFORM_EDGE = (105, 176, 135)
YELLOW = (255, 223, 0)
WHITE = (255, 255, 255)

player_rect = pygame.Rect(380, 100, 40, 40)
player_vel_x = 0
player_vel_y = 0
player_speed = 6

GRAVITY = 0.8
JUMP_STRENGTH = -15
GAME_TIME = 60
is_grounded = False
jumps_used = 0

platforms = []


def load_sprite(filename, size, color):
    try:
        image = pygame.image.load(os.path.join("assets", filename)).convert_alpha()
        image.lock()
        for y in range(image.get_height()):
            for x in range(image.get_width()):
                r, g, b, a = image.get_at((x, y))
                if r >= 245 and g >= 245 and b >= 245:
                    image.set_at((x, y), (r, g, b, 0))
        image.unlock()
        return pygame.transform.scale(image, size)
    except (FileNotFoundError, pygame.error):
        image = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(image, color, image.get_rect())
        return image


player_image = load_sprite("chicken.png", (40, 40), RED)
cupcake_image = load_sprite("cupcake.png", (30, 30), YELLOW)

try:
    background_image = pygame.image.load(
        os.path.join("assets", "background.png")
    ).convert()
    background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))
except (FileNotFoundError, pygame.error):
    background_image = None


def make_platforms():
    new_platforms = [pygame.Rect(0, 550, WIDTH, 50)]
    rows = list(range(470, 90, -60))
    random.shuffle(rows)
    for index, y in enumerate(rows):
        width = random.randint(90, 140)
        lane_width = WIDTH / len(rows)
        x = int(index * lane_width + lane_width / 2 - width / 2)
        x += random.randint(-25, 25)
        x = max(25, min(WIDTH - width - 25, x))
        new_platforms.append(pygame.Rect(x, y, width, 18))
    return new_platforms


def make_cupcakes():
    new_cupcakes = []
    available_platforms = platforms[1:]
    random.shuffle(available_platforms)
    cupcake_platforms = available_platforms + random.sample(available_platforms, 3)
    for platform in cupcake_platforms:
        x = random.randint(platform.left, platform.right - 30)
        new_cupcakes.append(pygame.Rect(x, platform.top - 30, 30, 30))
    return new_cupcakes


def draw_background():
    if background_image is not None:
        screen.blit(background_image, (0, 0))
        return

    screen.fill(SKY)

    for x in range(-20, WIDTH + 40, 34):
        height = 35 + (x * 7 % 55)
        building = pygame.Rect(x, 425 - height, 25, height)
        pygame.draw.rect(screen, CITY, building)
        pygame.draw.rect(screen, CITY_LINE, building, 2)
        for window_y in range(building.y + 8, building.bottom - 4, 12):
            pygame.draw.rect(screen, CITY_LINE, (x + 5, window_y, 4, 5))
            pygame.draw.rect(screen, CITY_LINE, (x + 15, window_y, 4, 5))

    for x in range(-30, WIDTH + 50, 85):
        pygame.draw.ellipse(screen, CLOUD, (x, 360, 100, 45))
        pygame.draw.ellipse(screen, CLOUD, (x + 25, 342, 85, 58))

    pygame.draw.rect(screen, GRASS, (0, 425, WIDTH, 125))
    pygame.draw.line(screen, PLATFORM_TOP, (0, 425), (WIDTH, 425), 5)
    pygame.draw.rect(screen, GROUND, (0, 550, WIDTH, 50))


def reset_game():
    global player_rect, player_vel_x, player_vel_y, is_grounded, jumps_used
    global cupcakes, time_left, platforms, game_state
    player_rect = pygame.Rect(380, 500, 40, 40)
    player_vel_x = 0
    player_vel_y = 0
    is_grounded = False
    jumps_used = 0
    platforms = make_platforms()
    cupcakes = make_cupcakes()
    time_left = GAME_TIME
    game_state = "playing"


time_left = GAME_TIME
game_state = "playing"
reset_game()


async def game_loop():
    global player_vel_x, player_vel_y, is_grounded, jumps_used, time_left, game_state

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif game_state in ("win", "lose") and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    reset_game()
            elif game_state == "playing" and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game()
                elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE):
                    if is_grounded or jumps_used < 2:
                        player_vel_y = JUMP_STRENGTH
                        is_grounded = False
                        jumps_used += 1

        if game_state == "playing":
            keys = pygame.key.get_pressed()
            player_vel_x = 0

            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player_vel_x = -player_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player_vel_x = player_speed
            player_vel_y += GRAVITY
            player_rect.x += player_vel_x

            if player_rect.left < 0:
                player_rect.left = 0
            if player_rect.right > WIDTH:
                player_rect.right = WIDTH

            player_rect.y += round(player_vel_y)
            is_grounded = False

            for platform in platforms:
                if player_rect.colliderect(platform):
                    if player_vel_y > 0:
                        player_rect.bottom = platform.top
                        player_vel_y = 0
                        is_grounded = True
                        jumps_used = 0
                    elif player_vel_y < 0:
                        player_rect.top = platform.bottom
                        player_vel_y = 0

            if player_rect.bottom > 550:
                player_rect.bottom = 550
                player_vel_y = 0
                is_grounded = True
                jumps_used = 0

            for cupcake in cupcakes[:]:
                if player_rect.colliderect(cupcake):
                    cupcakes.remove(cupcake)

            time_left -= dt
            if not cupcakes:
                game_state = "win"
            elif time_left <= 0:
                game_state = "lose"

        draw_background()

        if game_state == "playing":
            for platform in platforms:
                if platform.top == 550:
                    continue
                pygame.draw.rect(screen, PLATFORM, platform)
                pygame.draw.rect(
                    screen, PLATFORM_TOP, (platform.x, platform.y, platform.width, 5)
                )
                pygame.draw.rect(screen, PLATFORM_EDGE, platform, 2)

            for cupcake in cupcakes:
                screen.blit(cupcake_image, cupcake)

            screen.blit(player_image, player_rect)

            font = pygame.font.Font(None, 30)
            score = font.render(
                f"Cupcakes left: {len(cupcakes)}   Time: {max(0, int(time_left))}",
                True,
                WHITE,
            )
            screen.blit(score, (15, 15))
        else:
            panel = pygame.Rect(120, 150, WIDTH - 240, 260)
            pygame.draw.rect(screen, (72, 145, 145), panel, border_radius=16)
            pygame.draw.rect(screen, PLATFORM_TOP, panel, 4, border_radius=16)

            font = pygame.font.Font(None, 62)
            message = "YOU WIN!" if game_state == "win" else "TIME'S UP!"
            title = font.render(message, True, WHITE)
            screen.blit(title, title.get_rect(center=(WIDTH // 2, 220)))

            small_font = pygame.font.Font(None, 30)
            prompt = small_font.render("Press SPACE to play again", True, WHITE)
            screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, 330)))

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(game_loop())
