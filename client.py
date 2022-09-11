import socket
import sys
import pyglet
import copy
import time
import atexit

HOST = sys.argv[1]
PORT = 32752
if len(sys.argv) > 2 and sys.argv[2].isdigit():
    PORT = int(sys.argv[2])
screen = pyglet.window.Window(640, 500, "Multiplayer Burrito (Client)")
keys = pyglet.window.key.KeyStateHandler()
screen.push_handlers(keys)
burrito_left = pyglet.image.load("sprites/burrito_left.png")
burrito_right = pyglet.image.load("sprites/burrito_right.png")
sprite_lookup = {0:burrito_left, 1:burrito_right}
images = []
permanent_items = []
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
atexit.register(s.close)

def parse_initial(response):
    chunks = response.decode("utf-8").split(",")
    rects = []
    for chunk in chunks:
        attributes = chunk.split(" ")
        rects.append(pyglet.shapes.Rectangle(int(attributes[0]), int(attributes[1]), int(attributes[2]), int(attributes[3]), color=(int(attributes[4]),int(attributes[5]),int(attributes[6]))))
    return copy.copy(rects)

def parse_response(response):
    if not response:
        return []
    chunks = response.decode("utf-8").split(",")
    images_temp = []
    for chunk in chunks:
        if chunk[0] == "r":
            attributes = chunk[1:].split(" ")
            images_temp.append(pyglet.shapes.Rectangle(float(attributes[0]), float(attributes[1]), float(attributes[2]), float(attributes[3]), color=(int(attributes[4]),int(attributes[5]),int(attributes[6]))))
        else:
            attributes = chunk.split(" ")
            images_temp.append({"image":float(attributes[0]), "x":float(attributes[1]), "y":float(attributes[2])})
    return copy.copy(images_temp)

def recieve_message(s):
    data = b""
    while True:
        data += s.recv(1024)
        print(data)
        if (b" "+data)[-1:] == b";": #space added on the back to insure no indexerror
            break
    return data[:-1] #remove semicolon for convenience

def update(dt):
    global images
    global permanent_items
    global previous_keys
    data = ""
    for key in keys.keys():
        if keys[key]:
            data += str(key)+","
    data = data[:-1]+";"
    print(data)
    print(keys)
    s.sendall(data.encode("utf-8"))
    response = recieve_message(s)
    images = parse_response(response)
    previous_keys = copy.copy(keys)

@screen.event
def on_draw():
    screen.clear()
    for item in images:
        if isinstance(item, dict):
            sprite_lookup[item["image"]].blit(item["x"], item["y"])
        else:
            item.draw()
    pyglet.shapes.Rectangle(120, 250, 50, 100, color=(115,255,255)).draw()
    for item in permanent_items:
        item.draw()


print(f"Attempting connection to {HOST} on port {PORT}")
s.connect((HOST, PORT))
previous_keys = None
response = recieve_message(s)
permanent_items = parse_initial(response)

pyglet.clock.schedule_interval(update, 1/120)
pyglet.app.run()