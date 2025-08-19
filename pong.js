const canvas = document.getElementById('pong');
const ctx = canvas.getContext('2d');

// Game settings
const PADDLE_WIDTH = 15;
const PADDLE_HEIGHT = 100;
const BALL_RADIUS = 10;
const PLAYER_X = 20;
const AI_X = canvas.width - PADDLE_WIDTH - 20;
const PADDLE_SPEED = 6;
const BALL_SPEED = 6;

let playerY = (canvas.height - PADDLE_HEIGHT) / 2;
let aiY = (canvas.height - PADDLE_HEIGHT) / 2;
let ball = {
    x: canvas.width / 2,
    y: canvas.height / 2,
    vx: BALL_SPEED * (Math.random() < 0.5 ? 1 : -1),
    vy: BALL_SPEED * (Math.random() * 2 - 1)
};
let playerScore = 0;
let aiScore = 0;

// Draw paddle
function drawPaddle(x, y) {
    ctx.fillStyle = "#fff";
    ctx.fillRect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT);
}

// Draw ball
function drawBall() {
    ctx.beginPath();
    ctx.arc(ball.x, ball.y, BALL_RADIUS, 0, Math.PI * 2);
    ctx.fillStyle = "#fff";
    ctx.fill();
    ctx.closePath();
}

// Draw net
function drawNet() {
    ctx.fillStyle = "#fff";
    for (let i = 10; i < canvas.height; i += 30) {
        ctx.fillRect(canvas.width/2 - 2, i, 4, 20);
    }
}

// Draw scores
function drawScores() {
    ctx.font = "32px Arial";
    ctx.fillText(playerScore, canvas.width/4, 50);
    ctx.fillText(aiScore, canvas.width*3/4, 50);
}

// Move AI paddle (basic AI: follow the ball's y)
function moveAI() {
    let target = ball.y - (PADDLE_HEIGHT / 2);
    if (aiY < target) {
        aiY += PADDLE_SPEED;
    } else if (aiY > target) {
        aiY -= PADDLE_SPEED;
    }
    // Clamp within bounds
    aiY = Math.max(0, Math.min(canvas.height - PADDLE_HEIGHT, aiY));
}

// Ball and paddle collision detection
function collide(x, y) {
    return (
        ball.x + BALL_RADIUS > x &&
        ball.x - BALL_RADIUS < x + PADDLE_WIDTH &&
        ball.y + BALL_RADIUS > y &&
        ball.y - BALL_RADIUS < y + PADDLE_HEIGHT
    );
}

// Reset ball to center
function resetBall(direction) {
    ball.x = canvas.width / 2;
    ball.y = canvas.height / 2;
    ball.vx = BALL_SPEED * direction;
    ball.vy = BALL_SPEED * (Math.random() * 2 - 1);
}

// Game loop
function gameLoop() {
    // Move ball
    ball.x += ball.vx;
    ball.y += ball.vy;

    // Top/bottom wall collision
    if (ball.y - BALL_RADIUS < 0) {
        ball.y = BALL_RADIUS;
        ball.vy = -ball.vy;
    } else if (ball.y + BALL_RADIUS > canvas.height) {
        ball.y = canvas.height - BALL_RADIUS;
        ball.vy = -ball.vy;
    }

    // Paddle collision
    if (collide(PLAYER_X, playerY)) {
        ball.x = PLAYER_X + PADDLE_WIDTH + BALL_RADIUS;
        ball.vx = -ball.vx;
        // Add some randomness/spin
        let deltaY = ball.y - (playerY + PADDLE_HEIGHT / 2);
        ball.vy = deltaY * 0.25;
    }

    if (collide(AI_X, aiY)) {
        ball.x = AI_X - BALL_RADIUS;
        ball.vx = -ball.vx;
        let deltaY = ball.y - (aiY + PADDLE_HEIGHT / 2);
        ball.vy = deltaY * 0.25;
    }

    // Score
    if (ball.x < 0) {
        aiScore++;
        resetBall(1);
    } else if (ball.x > canvas.width) {
        playerScore++;
        resetBall(-1);
    }

    moveAI();

    // Draw everything
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawNet();
    drawPaddle(PLAYER_X, playerY);
    drawPaddle(AI_X, aiY);
    drawBall();
    drawScores();

    requestAnimationFrame(gameLoop);
}

// Player paddle follows mouse
canvas.addEventListener('mousemove', function(e) {
    const rect = canvas.getBoundingClientRect();
    let mouseY = e.clientY - rect.top;
    playerY = mouseY - PADDLE_HEIGHT / 2;
    // Clamp within bounds
    playerY = Math.max(0, Math.min(canvas.height - PADDLE_HEIGHT, playerY));
});

// Start game
gameLoop();