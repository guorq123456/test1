import sys
sys.argv = ["profile_cost.py"] + __import__("json").loads(open("/home/pyodide/args.json").read())
exec(compile(open("/home/pyodide/app/analysis/scaling/profile_cost.py").read(), "profile_cost.py", "exec"), {"__name__": "__main__", "__file__": "/home/pyodide/app/analysis/scaling/profile_cost.py"})
