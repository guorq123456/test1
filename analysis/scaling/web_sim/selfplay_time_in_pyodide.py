# selfplay_time.py inside Pyodide (run_py.js DIST this-file selfplay_time.py=/home/pyodide/selfplay_time.py
# ARGS.json=/home/pyodide/args.json): the page's runtime, numpy and models as the page loads them.
import json, os, sys
os.chdir("/home/pyodide/app")
args = json.loads(open("/home/pyodide/args.json").read()) + ["--out", "/out/result.json"]
sys.argv = ["selfplay_time.py"] + args
exec(compile(open("/home/pyodide/selfplay_time.py").read(), "selfplay_time.py", "exec"), {"__name__": "__main__"})
