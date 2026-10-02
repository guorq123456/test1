import time,sys
sys.argv=['x','1','5']
t=time.time()
exec(open('rule_check.py').read().replace('print("ERR"','print(time.time()-t,"ERR"').replace('inst+=1','inst+=1; print(time.time()-t,r,len(a),B,D,flush=True)'))
