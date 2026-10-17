import sys
sys.argv = ["puct_cost.py"] + __import__("json").loads(open("/home/pyodide/args.json").read())
exec(compile(open("/home/pyodide/app/analysis/scaling/puct_cost.py").read(), "puct_cost.py", "exec"), {"__name__": "__main__", "__file__": "/home/pyodide/app/analysis/scaling/puct_cost.py"})
