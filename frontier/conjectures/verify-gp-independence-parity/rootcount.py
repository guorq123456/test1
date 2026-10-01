import sys, subprocess
files = sys.argv[1:]
rows = []
for fn in files:
    for line in open(fn):
        k, n, cs = line.split()
        rows.append((int(k), int(n), cs))
script = []
for k, n, cs in rows:
    script.append(f"P=Polrev([{cs}]);print({k},\" \",{n},\" \",poldegree(P),\" \",polsturm(P),\" \",#polrootsreal(P),\" \",issquarefree(P),\" \",vecmin(Vec(P))>0);")
inp = "default(parisizemax, 4000000000);\n" + "\n".join(script) + "\n"
out = subprocess.run(['gp', '-q', '-s', '2000000000'], input=inp, capture_output=True, text=True)
sys.stdout.write(out.stdout); sys.stderr.write(out.stderr)
