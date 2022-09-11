import socket
import sys
import time
import threading
import json
import pyglet
import atexit
import copy
from collections import defaultdict

HOST = socket.gethostname()
PORT = 32752
if len(sys.argv) > 1 and sys.argv[1].isdigit():
    PORT = int(sys.argv[1])

keys = pyglet.window.key.KeyStateHandler()

screen = pyglet.window.Window(640, 500, "Multiplayer Burrito")
screen.set_visible(False)
screen.push_handlers(keys)
burrito_right = pyglet.image.load("sprites/burrito_right.png")
burrito_left = pyglet.image.load("sprites/burrito_left.png")

gravity = 0.7
friction = 0.1
percent_per_hit = 3

class State():
    def __init__(self):
        self.connected = threading.Lock()
        self.connected.acquire()
        self.platforms = []
        self.client_sprites = ";"
        self.projectiles = []
        self.client_keys_lock = threading.Lock()
        self.client_sprites_lock = threading.Lock()
        self.player1 = Player(burrito_right, 200, 300)
        self.player2 = Player(burrito_left, 300, 300)
        self.player1.keys = keys
        self.player2.keys = defaultdict(lambda:False)


class Player(pyglet.sprite.Sprite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vx = 0
        self.vy = 0
        self.keys = None
        self.on_ground = True
        self.held_up_last_frame = False
        self.double_jump = True
        self.attackcooldown = 0
        self.times_hit = 0

class AttackBox(pyglet.shapes.Rectangle):
    def __init__(self, player, opponent, offset_x, offset_y, width, height):
        super().__init__(player.x+offset_x, player.y+offset_y, width, height, color=(255,0,0))
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.player = player
        self.opponent = opponent
        self.lifespan = 10
    def tick(self):
        self.x = self.player.x + self.offset_x
        self.y = self.player.y + self.offset_y
        self.lifespan -= 1
    def calculate_knockback(self, player):
        distance_x = (player.x+player.width/2)-(self.player.x+self.player.width/2)
        distance_y = (player.y+player.height/2)-(self.player.y+self.player.height/2)
        total_kb = (1+player.times_hit*percent_per_hit/10)
        return (total_kb*distance_x/(abs(distance_x)+abs(distance_y)), total_kb*distance_y/(abs(distance_x)+abs(distance_y)))
def iscolliding(rect1, rect2): #copied from Multiplayer Duck
	if (rect1.x + rect1.width > rect2.x and
		rect1.x < rect2.x + rect2.width and
		rect1.y + rect1.height > rect2.y and
		rect1.y < rect2.y + rect2.height):  
		return True

def recieve_message(s):
    data = b""
    while True:
        data += s.recv(1024)
        if (b" "+data)[-1:] == b";": #space added on the back to insure no indexerror
            break
    return data[:-1] #remove semicolon for convenience

def parse_message(message):
    chunks = message.decode("utf-8").split(",")
    keys_temp = defaultdict(lambda:False)
    for chunk in chunks:
        if chunk == '':
            continue
        keys_temp[int(chunk)] = True
    state.client_keys_lock.acquire()
    state.player2.keys = copy.copy(keys_temp)
    state.client_keys_lock.release()

def server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print(f"Binding {socket.gethostbyname(socket.getfqdn())} on port {PORT}")
        s.bind((HOST, PORT))
        atexit.register(s.close)
        s.listen()
        conn, addr = s.accept()
        state.connected.release()
        with conn:
            print(f"Connected")
            message = ""
            for platform in state.platforms:
                message += f"{platform.x} {platform.y} {platform.width} {platform.height} {platform.color[0]} {platform.color[1]} {platform.color[2]},"
            message = message[:-1] + ";"
            conn.sendall(message.encode("utf-8"))
            while True:
                time.sleep(1/120)
                data = recieve_message(conn)
                parse_message(data)
                state.client_sprites_lock.acquire()
                conn.sendall(state.client_sprites.encode("utf-8"))
                state.client_sprites_lock.release()

def game():
    screen.set_visible(True)
    pyglet.clock.schedule_interval(update, 1/60)
    pyglet.app.run()

def update(dt): #code from Multiplayer Duck
    for player in state.player1, state.player2:
        other_player = [state.player1,state.player2]
        other_player.remove(player)
        other_player = other_player[0]
        player.y += player.vy
        player.on_ground = False
        isfalling = (player.vy < 0)
        redo = True #this is so you will be pushed out of platforms continually until you aren't in any
        while redo:
            redo = False
            for platform in state.platforms:
                if iscolliding(player, platform):
                    if isfalling:
                        player.y = platform.y + platform.height
                        player.on_ground = True
                        player.doublejump = True
                        player.vy = 0
                    else:
                        player.y = platform.y - player.height
                        player.vy = 0

        player.x += player.vx
        ismovingleft = (player.vx < 0)
        redo = True #this is so you will be pushed out of platforms continually until you aren't in any
        while redo:
            redo = False
            for platform in state.platforms:
                if iscolliding(player, platform):
                    redo = True
                    if ismovingleft:
                        player.x = platform.x + platform.width
                        player.vx = 0
                    else:
                        player.x = platform.x - player.width
                        player.vx = 0

        if player.keys[pyglet.window.key.UP] and (player.on_ground or (player.double_jump and not player.held_up_last_frame)):
            player.vy = 10
            if not player.on_ground:
                player.double_jump = False
        player.held_up_last_frame = player.keys[pyglet.window.key.UP]

        if player.keys[pyglet.window.key.LEFT] and not player.keys[pyglet.window.key.RIGHT]:
            player.image = burrito_left
            if player.vx > -4:
                player.vx -= 0.2

        if player.keys[pyglet.window.key.RIGHT] and not player.keys[pyglet.window.key.LEFT]:
            player.image = burrito_right
            if player.vx < 4:
                player.vx += 0.2

        if player.keys[pyglet.window.key.Z] and player.attackcooldown <= 0:
            player.attackcooldown = 30
            if player.keys[pyglet.window.key.LEFT]:
                attack_rect = AttackBox(player, other_player, -20, player.height-20, 20, 10)
            elif player.keys[pyglet.window.key.RIGHT]:
                attack_rect = AttackBox(player, other_player, player.width, player.height-20, 20, 10)
            elif player.keys[pyglet.window.key.UP]:
                attack_rect = AttackBox(player, other_player, -5, player.height+5, 10+player.width, 5)
            else:
                attack_rect = AttackBox(player, other_player, 0, 0, player.width, player.height)
            state.projectiles.append(attack_rect)

        player.attackcooldown -= 1
        if player.on_ground:
            if player.vx < 0:
                player.vx = min(player.vx+friction, 0)
            elif player.vx > 0:
                player.vx = max(player.vx-friction, 0)
        player.vy -= gravity
        player.vy = max(-10, player.vy)

    for projectile in state.projectiles:
        projectile.tick()
        if iscolliding(projectile, projectile.opponent):
            projectile.opponent.times_hit += 1
            knockback = projectile.calculate_knockback(projectile.opponent)
            projectile.opponent.vx = knockback[0]
            projectile.opponent.vy = knockback[1]
        if projectile.lifespan < 1:
            del state.projectiles[state.projectiles.index(projectile)]

    if state.player1.y < 0:
        print("player one totally died")
        exit()
    if state.player2.y < 0:
        print("player two totally died")
        exit()

@screen.event
def on_draw():
    screen.clear()
    for platform in state.platforms:
        platform.draw()

    state.client_sprites_lock.acquire()
    state.client_sprites = ""
    for sprite in state.player1, state.player2:
        if sprite.image == burrito_left:
            state.client_sprites += f"0 {sprite.x} {sprite.y},"
        else:
            state.client_sprites += f"1 {sprite.x} {sprite.y},"
        sprite.draw()

    for projectile in state.projectiles:
        projectile.draw()
        state.client_sprites += f"r{projectile.x} {projectile.y} {projectile.width} {projectile.height} {projectile.color[0]} {projectile.color[1]} {projectile.color[2]},"
    state.client_sprites = state.client_sprites[:-1] + ";"
    state.client_sprites_lock.release()

state = State()
state.platforms.append(pyglet.shapes.Rectangle(120, 250, 400, 50, color=(215,200,255)))
state.platforms.append(pyglet.shapes.Rectangle(120, 250, 50, 100, color=(115,255,255)))

communication_thread = threading.Thread(target=server)
game_thread = threading.Thread(target=game)

communication_thread.start()
state.connected.acquire()

game_thread.start()

