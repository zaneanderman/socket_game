import socket
import sys
import threading
import pyglet
import copy
import time

HOST = sys.argv[1]
PORT = 32752
if len(sys.argv) > 2 and sys.argv[2].isdigit():
    PORT = int(sys.argv[2])
screen = pyglet.window.Window(640, 500, "Multiplayer Burrito")
keys = pyglet.window.key.KeyStateHandler()
screen.push_handlers(keys)
burrito_left = pyglet.image.load("sprites/burrito_left.png")
burrito_right = pyglet.image.load("sprites/burrito_right.png")
sprite_lookup = {0:burrito_left, 1:burrito_right}
drawables = []

connected = threading.Lock()
connected.acquire()

def client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print(f"Attempting connection to {HOST} on port {PORT}")
        s.connect((HOST, PORT))
        connected.release()
        previous_keys = None
        
        while True:
            time.sleep(1/120)
            data = ""
            for key in keys.keys():
                data += str(key)+","
            data = data[:-1]+";"
            s.sendall(data.encode("utf-8"))
            response = recieve_message(s)
            parse_response(response)
            previous_keys = copy.copy(keys)

def parse_response(response):
    global drawables
    sprites = response.decode("utf-8").split(",")
    drawables_temp = []
    for sprite in sprites:
        attributes = sprite.split(" ")
        drawables_temp.append({"image":int(attributes[0]), "x":int(attributes[1]), "y":int(attributes[2])})
        print(drawables)
    drawables = copy.copy(drawables_temp)

def recieve_message(s):
    data = b""
    while True:
        data += s.recv(1024)
        if (b" "+data)[-1:] == b";": #space added on the back to insure no indexerror
            break
    return data[:-1] #remove semicolon for convenience

def update(dt):
    print(drawables)
    pass

@screen.event
def on_draw():
    screen.clear()
    for item in drawables:
        print(f"drawing{item}")
        sprite_lookup[item["image"]].blit(item["x"], item["y"])

pyglet.clock.schedule_interval(update, 1/60.0)
communication_thread = threading.Thread(target=client)
game_thread = threading.Thread(target=pyglet.app.run)

communication_thread.start()
connected.acquire() #wait until connected to the server
game_thread.start()
communication_thread.join()
game_thread.join()