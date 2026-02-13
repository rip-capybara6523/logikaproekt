from math import hypot
from pygame import *
from random import randint
import socket
import threading
import struct

client  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("localhost", 5555))
other_players_balls = {}
my_id = None
player_img = image.load("images/гравець.png")
enemy_img = image.load("images/ворог.png")
bg = image.load("images/фон.jpg")
bg = transform.scale(bg,(700, 700))

# Клас кульки
class Ball:
    def __init__(self, x, y, radius, color, speed=0, img=None):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.speed = speed
        if img:
            self.img = img
            self.original_img = img
        else:
            self.img = None


    def move(self):
        keys = key.get_pressed()
        if keys[K_w]:
            self.y -= self.speed
        if keys[K_s]:
            self.y += self.speed
        if keys[K_a]:
            self.x -= self.speed
        if keys[K_d]:
            self.x += self.speed

    # ⬇️⬇️⬇️ 🔃🔃🔃
    def draw(self, center_x, center_y, scale):
        sx = int((self.x - center_x) * scale + WINDOW_SIZE[0] // 2)
        sy = int((self.y - center_y) * scale + WINDOW_SIZE[1] // 2)
        size = int(self.radius * scale)
        if self.img:
            self.img = transform.scale(self.original_img, (size*2, size*2))
            window.blit(self.img, (sx-size, sy-size))
        else:
            draw.circle(window, self.color, (sx, sy), int(self.radius * scale))


    def collidecircle(self, other):
        distance = hypot(self.x - other.x, self.y - other.y)
        return distance <= self.radius + other.radius

    # ⬇️⬇️⬇️
    def draw_center(self, scale):
        size = int(self.radius * scale)
        sx, sy = WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2
        if self.img:
            self.img = transform.scale(self.original_img, (size * 2, size * 2))
            window.blit(self.img, (sx - size, sy - size))
        else:
            draw.circle(window, self.color, (sx, sy), int(self.radius * scale))

def recv_full(sock, size):
    data = b''
    while len(data) < size:
        packet = sock.recv(size - len(data))
        if not packet:
            return None
        data += packet
    return data


def receive_data():
    global my_id, other_players_balls

    while True:
        try:
            header = recv_full(client, 1)
            if not header:
                break

            packet_type = struct.unpack("!B", header)[0]

            # Тип 1 = мій ID
            if packet_type == 1:
                my_id = struct.unpack("!I", recv_full(client, 4))[0]
                print("My ID:", my_id)

            # Тип 3 = стан гри
            elif packet_type == 3:
                count = struct.unpack("!I", recv_full(client, 4))[0]

                current_ids = set()

                for _ in range(count):
                    pid, x, y, r = struct.unpack("!Ifff", recv_full(client, 16))
                    current_ids.add(pid)

                    if pid == my_id:
                        continue

                    if pid not in other_players_balls:
                        other_players_balls[pid] = Ball(x, y, r, (255, 0, 0), img = enemy_img)
                    else:
                        b = other_players_balls[pid]
                        b.x, b.y, b.radius = x, y, r

                for pid in list(other_players_balls.keys()):
                    if pid not in current_ids:
                        del other_players_balls[pid]

        except Exception as e:
            print("Receive error:", e)
            break

threading.Thread(target=receive_data, daemon=True).start()
# Налаштування
WINDOW_SIZE = 700, 500 # ⬅️🔃
PLAYER_SPEED = 10 # ⬅️

# Pygame
init()
window = display.set_mode(WINDOW_SIZE)
clock = time.Clock()

# Гравець (був ball)
player = Ball(0, 0, 20, (0, 255, 0), PLAYER_SPEED, player_img)# ⬅️🔃

# ⬇️⬇️⬇️
# Інші кульки
balls = [
    Ball(
        randint(-2000, 2000),
        randint(-2000, 2000),
        10,
        (randint(0, 255), randint(0, 255), randint(0, 255))
    )
    for _ in range(300)
]

# Основний цикл
running = True
while running:
    for e in event.get():
        if e.type == QUIT:
            running = False

    window.blit(bg,(0,0))

    # Масштаб (чим більший гравець — тим менший зум)
    scale = max(0.3, min(50 / player.radius, 1.5))

    # Рух гравця
    player.move()

    # Малювання гравця
    player.draw_center(scale)

    # Кульки
    to_remove = []
    for ball in balls:
        if player.collidecircle(ball):
            to_remove.append(ball)
            player.radius += int(ball.radius * 0.2)
        else:
            ball.draw(player.x, player.y, scale)

    for ball in to_remove:
        balls.remove(ball)

    packet = struct.pack("!Bfff", 2, player.x, player.y, player.radius)
    client.sendall(packet)
    for ball in list(other_players_balls.values()):
        ball.draw(player.x, player.y, scale)

    for pid,ball in list(other_players_balls.items()):
        if player.collidecircle(ball):
            if ball.radius > player.radius + 2:
                print("ти програв")
                running = False
            elif player.radius > ball.radius + 2:
                del other_players_balls[pid]
                player.radius += int(ball.radius * 0.2)
    display.update()
    clock.tick(60)

quit()