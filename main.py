from gcode import gcodeWriter
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

# Positioning settings
UP_Z = 44.0
DOWN_Z = 41.0 

assert UP_Z > DOWN_Z

# Feeds n speeds
CUT_SPEED = 300
TRAVEL = 20000

# Optimization settings
CLOSE_THRESH = 0.001

# Output settings
FILE_PATH = "/home/pi/gcode_files/output.gcode"

PORT = 6767

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # read content length
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode("utf-8")

        # parse form data
        data = urllib.parse.parse_qs(body)

        # get "name" parameter
        name = data.get("name", [""])[0]

        print(f"Received name: {name}, Generating gcode...")

        gc = gcodeWriter(UP_Z=UP_Z, DOWN_Z=DOWN_Z, TRAVEL=TRAVEL, CUT_SPEED=CUT_SPEED, CLOSE_THRESH=CLOSE_THRESH)

        gcode = gc.write_gcode(name)
        with open(FILE_PATH, "w") as f:
            f.write(gcode)  

        r = requests.post(f"http://localhost/printer/print/start?filename={FILE_PATH.split('/')[-1]}")
        if r.status_code == 200:
            print("Print started.")
        else:
            print(f"Failed to start print with status code {r.status_code}")

        print("Done!")

        # send response
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Listening on port {PORT}...")
    server.serve_forever()

if __name__ == "__main__":
    run()