"""A static host that, like claude.ai, serves no archives (.zip / .whl): 404 for them."""
import functools, http.server, sys
class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path.split("?")[0].endswith((".zip", ".whl")):
            self.send_error(404, "no archives here")
            return
        super().do_GET()
http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[2])), functools.partial(H, directory=sys.argv[1])).serve_forever()
