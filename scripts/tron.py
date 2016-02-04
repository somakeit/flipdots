#!/usr/bin/env python2

import time
import gevent
import random
from flask import Flask
from flask import redirect, url_for, request
from gevent.wsgi import WSGIServer
from FlipdotAPI.FlipdotMatrix import FlipdotMatrix
from FlipdotAPI.FlipdotMatrix import FlipdotImage
from dns import resolver
from dns import reversename

app = Flask(__name__)
app.debug = True

STARTED = time.time()

# Publicly visible IP
MYIP = "sr-flipdot"

# HTTP Port
PORT = 8080

# Frames Per Second
FPS = 25

# round time. put this game in an outside while loop and just restart it
ROUND_TIME = 300

# reserved pixels at the top
TOP = 1

WIDTH = 120
HEIGHT = 16

matrix = FlipdotMatrix(
     udpHostsAndPorts = [
         ("sr-flipdot", 2323),
     ],
     imageSize = (WIDTH, HEIGHT),
     transposed = False,
)

class Player(object):
    def __init__(self, game, player_id, ip):
        self.game = game
        self.player_id = player_id
        self.reset()
        self.kills = 0
        self.deaths = 0
        self.longest = 0
        self.ip = ip

    def reset(self):
        self.x = random.randint(1, 118)
        self.y = random.randint(1, 14)
        self.dir = random.randint(0, 3)
        self.path = []

    def draw(self):
        self.game.set_pixel(self.x, self.y)

    def set_dir(self, dir):
        if self.dir == 0 and dir == 2:
            return
        if self.dir == 2 and dir == 0:
            return
        if self.dir == 1 and dir == 3:
            return
        if self.dir == 3 and dir == 1:
            return
        self.dir = dir

    def step(self):
        if self.dir == 0:
            self.y -= 1
        elif self.dir == 1:
            self.x += 1
        elif self.dir == 2:
            self.y += 1
        elif self.dir == 3:
            self.x -= 1
        if self.game.is_set(self.x, self.y):
            for x, y in self.path:
                self.deaths += 1
                self.game.del_pixel(x, y)
            self.reset()
            return

        self.path.append((self.x, self.y))
        if len(self.path) > self.longest:
            self.longest = len(self.path)
        self.draw()

class Game(object):
    def __init__(self, width, height, matrix):
        self.players = {}
        self.matrix = matrix
        self.width = width
        self.height = height

    def ensure_join(self, player_id, ip):
        if not player_id in self.players:
            self.players[player_id] = Player(self, player_id, ip)

    def set_dir(self, player_id, dir):
        self.players[player_id].set_dir(dir)

    def reset_white(self):
        black = FlipdotImage.newBlackFlipdotImage(self.width, self.height)
        self.matrix.show(black)
        white = FlipdotImage.newWhiteFlipdotImage(self.width, self.height)
        self.matrix.show(white)

    def set_pixel(self, x, y):
        self.image.getLine(y)[x] = FlipdotImage.BLACKPIXEL

    def del_pixel(self, x, y):
        self.image.getLine(y)[x] = FlipdotImage.WHITEPIXEL

    def is_set(self, x, y):
        return self.image.getSinglePixel(x, y) == FlipdotImage.BLACKPIXEL

    def flush(self):
        self.matrix.show(self.image)

    def start(self):
        print "resetting game"
        self.image = FlipdotImage.newWhiteFlipdotImage(
            self.width, self.height)
        self.reset_white()
        for x in xrange(self.width):
            for y in xrange(TOP):
                self.set_pixel(x, y)
            self.set_pixel(x, self.height-1)
        for y in xrange(self.height):
            self.set_pixel(0,  y)
            self.set_pixel(self.width - 1, y)
        for player in self.players.itervalues():
            player.reset()
            player.draw()
        #self.image.blitTextAtPosition("join this game", xPos=5, yPos=2)
        #self.image.blitTextAtPosition("http://%s:%d/" % (MYIP, PORT), xPos=5, yPos=9)
        self.flush()

    def step(self):
        #print "step"
        for player in self.players.itervalues():
            player.step()
        remaining = ROUND_TIME - (time.time() - STARTED)
        self.image.blitTextAtPosition("%03d" % remaining, xPos=1, yPos=0)

        if time.time() - STARTED > ROUND_TIME:
            #This is the end
            winner = self.players[self.players.keys()[0]]
            for player in self.players.itervalues():
                if player.longest > winner.longest:
                    winner = player
            try:
                winner_name = str(resolver.query(reversename.from_address(winner.ip), "PTR")[0]).split(".")[0]
            except resolver.NoAnswer:
                winner_name = winner.ip
            self.image.blitTextAtPosition("Winner: " + str(winner_name), xPos=1, yPos=1)
            self.image.blitTextAtPosition("Length: " + str(winner.longest), xPos=1, yPos=7)
        
        self.flush()

g = Game(WIDTH, HEIGHT, matrix)

def game():
    while 1:
        g.start()
        last_time = time.time()
        while 1:
            new_time = time.time()
            sleep_time = ((1000.0 / FPS) - (new_time - last_time)) / 1000.0
            if sleep_time > 0:
                gevent.sleep(sleep_time)
            last_time = new_time
            g.step()

@app.route('/')
def index():
    player_id = random.randint(0, 2**64)
    return redirect(url_for('player', player_id=player_id))

@app.route('/c/<player_id>/<int:dir>')
def controller(player_id, dir):
    g.ensure_join(player_id, request.remote_addr)
    g.set_dir(player_id, dir)
    return 'ok'

@app.route('/c/<player_id>/')
def player(player_id):
    g.ensure_join(player_id, request.remote_addr)
    return """
<html>
<head>
    <meta name="viewport" content="user-scalable=no, target-densityDpi=device-dpi, initial-scale=1.0" />
    <script src="http://code.jquery.com/jquery-1.10.2.min.js"></script>
    <script>
        /*! Tocca.js v0.0.7 || Gianluca Guarini */
        !function(a,b){"use strict";if("function"!=typeof a.createEvent)return!1;var c,d,e,f,g,h="undefined"!=typeof jQuery,i=!!("ontouchstart"in window)&&navigator.userAgent.indexOf("PhantomJS")<0,j=function(a,b,c){for(var d=b.split(" "),e=d.length;e--;)a.addEventListener(d[e],c,!1)},k=function(a){return a.targetTouches?a.targetTouches[0]:a},l=function(b,e,f,g){var i=a.createEvent("Event");if(g=g||{},g.x=c,g.y=d,g.distance=g.distance,h)jQuery(b).trigger(e,g);else{i.originalEvent=f;for(var j in g)i[j]=g[j];i.initEvent(e,!0,!0),b.dispatchEvent(i)}},m=!1,n=b.SWIPE_TRESHOLD||80,o=b.TAP_TRESHOLD||200,p=b.TAP_PRECISION/2||30,q=0;i=b.JUST_ON_TOUCH_DEVICES?!0:i,j(a,i?"touchstart":"mousedown",function(a){var b=k(a);e=c=b.pageX,f=d=b.pageY,m=!0,q++,clearTimeout(g),g=setTimeout(function(){e>=c-p&&c+p>=e&&f>=d-p&&d+p>=f&&!m&&l(a.target,2===q?"dbltap":"tap",a),q=0},o)}),j(a,i?"touchend touchcancel":"mouseup",function(a){var b=[],g=f-d,h=e-c;if(m=!1,-n>=h&&b.push("swiperight"),h>=n&&b.push("swipeleft"),-n>=g&&b.push("swipedown"),g>=n&&b.push("swipeup"),b.length)for(var i=0;i<b.length;i++){var j=b[i];l(a.target,j,a,{distance:{x:Math.abs(h),y:Math.abs(g)}})}}),j(a,i?"touchmove":"mousemove",function(a){var b=k(a);c=b.pageX,d=b.pageY})}(document,window);
    </script>
    <style>
        td.control {
            width: 200px;
            height: 200px;
            background: #eee;
            text-align: center;
        }
    </style>
</head>
<body>
    <table>
        <tr>
            <td></td>
            <td class='control' data-dir='0'>UP</td>
            <td></td>
        </tr>
        <tr>
            <td class='control' data-dir='3'>LEFT</td>
            <td></td>
            <td class='control' data-dir='1'>RIGHT</td>
        </tr>
        <tr>
            <td></td>
            <td class='control' data-dir='2'>DOWN</td>
            <td></td>
        </tr>
    </table>
    <br/>
    made by <a href='http://dividuum.de/'>dividuum</a>
    <script>
        function move(dir) {
            $.ajax({
                url: dir + '',
                cache: false
            });
        }
        $(function() {
            $(".control").on('tap',function() { move($(this).data('dir')); });
        });
        document.addEventListener('keydown', function(event) {
            if(event.keyCode == 37) {
                move(3)
            }
            else if(event.keyCode == 39) {
                move(1)
            }
            else if(event.keyCode == 38) {
                move(0)
            }
            else if(event.keyCode == 40) {
                move(2)
            }
        });
    </script>
</body>
"""

def web():
    http_server = WSGIServer(('', PORT), app)
    http_server.serve_forever()

if __name__ == "__main__":
    print "Start"
    a = gevent.spawn(web)
    b = gevent.spawn(game)
    while time.time() - STARTED < ROUND_TIME:
        gevent.sleep(1)
    a.kill()
    b.kill()
