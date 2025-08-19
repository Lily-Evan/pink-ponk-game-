import pygame
import sys
import numpy as np
import random
import pickle

# Pygame setup
pygame.init()
WIDTH, HEIGHT = 800, 400
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RL Pong - Q-learning")
FPS = 60

# Game constants
PADDLE_WIDTH, PADDLE_HEIGHT = 12, 70
BALL_RADIUS = 10
PADDLE_SPEED = 7
BALL_SPEED = 5
AI_X = WIDTH - PADDLE_WIDTH - 20
PLAYER_X = 20

# Q-learning constants
NUM_BUCKETS = (12, 8, 2, 2, 8)  # discretization buckets: ball_x, ball_y, ball_vx, ball_vy, paddle_y
NUM_ACTIONS = 3  # up, down, stay
ALPHA = 0.2
GAMMA = 0.95
EPSILON = 1.0
MIN_EPSILON = 0.02
EPSILON_DECAY = 0.9997

# Discretization bounds
STATE_BOUNDS = [
    [0, WIDTH],           # ball x
    [0, HEIGHT],          # ball y
    [-BALL_SPEED, BALL_SPEED],  # ball vx
    [-BALL_SPEED, BALL_SPEED],  # ball vy
    [0, HEIGHT - PADDLE_HEIGHT] # paddle y
]

def discretize(value, value_min, value_max, buckets):
    if value <= value_min:
        return 0
    if value >= value_max:
        return buckets - 1
    ratio = (value - value_min) / (value_max - value_min)
    return int(ratio * (buckets - 1))

def get_state(ball, ai_paddle_y):
    bx, by = ball['x'], ball['y']
    bvx = ball['vx']
    bvy = ball['vy']
    py = ai_paddle_y
    state = (
        discretize(bx, STATE_BOUNDS[0][0], STATE_BOUNDS[0][1], NUM_BUCKETS[0]),
        discretize(by, STATE_BOUNDS[1][0], STATE_BOUNDS[1][1], NUM_BUCKETS[1]),
        0 if bvx < 0 else 1,  # ball vx: left or right
        0 if bvy < 0 else 1,  # ball vy: up or down
        discretize(py, STATE_BOUNDS[4][0], STATE_BOUNDS[4][1], NUM_BUCKETS[4])
    )
    return state

def init_q_table():
    return np.zeros(NUM_BUCKETS + (NUM_ACTIONS,))

def choose_action(q_table, state, epsilon):
    if np.random.rand() < epsilon:
        return random.randint(0, NUM_ACTIONS - 1)
    else:
        return np.argmax(q_table[state])

def update_q(q_table, state, action, reward, next_state, alpha=ALPHA, gamma=GAMMA):
    best_next = np.max(q_table[next_state])
    q_table[state + (action,)] += alpha * (reward + gamma * best_next - q_table[state + (action,)])

def draw(win, ball, player_paddle, ai_paddle, player_score, ai_score, font):
    win.fill((30, 30, 40))
    # Ball
    pygame.draw.circle(win, (255, 255, 255), (int(ball['x']), int(ball['y'])), BALL_RADIUS)
    # Paddles
    pygame.draw.rect(win, (0, 200, 255), (*player_paddle, PADDLE_WIDTH, PADDLE_HEIGHT))
    pygame.draw.rect(win, (255, 100, 0), (*ai_paddle, PADDLE_WIDTH, PADDLE_HEIGHT))
    # Scores
    score_text = font.render(f"{player_score} : {ai_score}", True, (255,255,255))
    win.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 20))
    # Info
    info_text = font.render("Move mouse up/down to control. AI trains live!", True, (200,200,200))
    win.blit(info_text, (WIDTH//2 - info_text.get_width()//2, HEIGHT-40))
    pygame.display.flip()

def main():
    global EPSILON
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('consolas', 26)
    # Q-table
    q_table = init_q_table()
    # Scores
    player_score, ai_score = 0, 0

    # Player paddle
    player_y = (HEIGHT - PADDLE_HEIGHT) // 2
    # AI paddle
    ai_y = (HEIGHT - PADDLE_HEIGHT) // 2

    # Ball
    def reset_ball():
        angle = np.random.uniform(-0.7, 0.7)
        vx = BALL_SPEED * (1 if random.random() < 0.5 else -1)
        vy = BALL_SPEED * angle
        return {
            'x': WIDTH // 2,
            'y': HEIGHT // 2,
            'vx': vx,
            'vy': vy
        }
    ball = reset_ball()

    running = True
    prev_state = get_state(ball, ai_y)
    prev_action = 0
    ball_hittable = False  # Only reward at collision/miss

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Player paddle follows mouse
        mouse_y = pygame.mouse.get_pos()[1]
        player_y = np.clip(mouse_y - PADDLE_HEIGHT//2, 0, HEIGHT - PADDLE_HEIGHT)

        # AI: Q-learning agent
        state = get_state(ball, ai_y)
        action = choose_action(q_table, state, EPSILON)
        # Convert action to movement
        if action == 0:  # Up
            ai_y -= PADDLE_SPEED
        elif action == 1:  # Down
            ai_y += PADDLE_SPEED
        ai_y = np.clip(ai_y, 0, HEIGHT - PADDLE_HEIGHT)

        # Ball movement
        ball['x'] += ball['vx']
        ball['y'] += ball['vy']

        # Wall collisions
        if ball['y'] - BALL_RADIUS < 0:
            ball['y'] = BALL_RADIUS
            ball['vy'] *= -1
        elif ball['y'] + BALL_RADIUS > HEIGHT:
            ball['y'] = HEIGHT - BALL_RADIUS
            ball['vy'] *= -1

        # Player paddle collision
        if (PLAYER_X < ball['x'] - BALL_RADIUS < PLAYER_X + PADDLE_WIDTH and
            player_y < ball['y'] < player_y + PADDLE_HEIGHT):
            ball['x'] = PLAYER_X + PADDLE_WIDTH + BALL_RADIUS
            ball['vx'] *= -1

        # AI paddle collision
        reward = -0.01  # small negative reward each timestep
        hit = False
        miss = False
        if (AI_X < ball['x'] + BALL_RADIUS < AI_X + PADDLE_WIDTH and
            ai_y < ball['y'] < ai_y + PADDLE_HEIGHT):
            ball['x'] = AI_X - BALL_RADIUS
            ball['vx'] *= -1
            reward = 1.0
            hit = True
            ball_hittable = False
        elif ball['x'] + BALL_RADIUS >= WIDTH:
            reward = -1.0
            ai_score += 1
            miss = True
            ball = reset_ball()
            ball_hittable = False
        elif (AI_X < ball['x'] + BALL_RADIUS < AI_X + PADDLE_WIDTH):  # Ball is at AI paddle's x
            ball_hittable = True

        # Player miss
        if ball['x'] - BALL_RADIUS <= 0:
            player_score += 1
            ball = reset_ball()
            ball_hittable = False

        # Q-learning update
        next_state = get_state(ball, ai_y)
        update_q(q_table, prev_state, prev_action, reward, next_state)
        prev_state = state
        prev_action = action

        # Epsilon decay
        if EPSILON > MIN_EPSILON:
            EPSILON *= EPSILON_DECAY

        # Draw everything
        player_paddle = [PLAYER_X, int(player_y)]
        ai_paddle = [AI_X, int(ai_y)]
        draw(WIN, ball, player_paddle, ai_paddle, player_score, ai_score, font)

    pygame.quit()
    # Optionally, save Q-table for re-loading
    with open("q_table.pkl", "wb") as f:
        pickle.dump(q_table, f)

if __name__ == '__main__':
    main()