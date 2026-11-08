# page_time.py inside Pyodide (run_py.js DIST this-file page_time.py=/home/pyodide/page_time.py
# ARGS.json=/home/pyodide/args.json bot-frozen7.txt=/home/pyodide/field.txt): the page's runtime, numpy and models as
# the page loads them. ARGS.json is page_time.py's argument list without --out (and --field /home/pyodide/field.txt).
import json, os, sys
os.chdir("/home/pyodide/app")
args = json.loads(open("/home/pyodide/args.json").read()) + ["--out", "/out/result.json"]
sys.argv = ["page_time.py"] + args
exec(compile(open("/home/pyodide/page_time.py").read(), "page_time.py", "exec"), {"__name__": "__main__"})
