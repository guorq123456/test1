# Full residue-level certificate for S2 (see proof_S2_reduction.txt, Theorem R):
#  (TP_rho): every z in [-r, sigma+1] with d_z < tau_{z mod r} has floor((sigma+1-2z)/r) even
#  (E_rho) : ND_rho(K) for every K = sigma+1 (mod 2r) with 2 mu*_inf <= K <= sigma+1-2r
#  (O_rho) : ND_rho(K) for every K = sigma+1+r (mod 2r) with 2 mu*_inf+3r <= K <= sigma+1-2r
# (residue_check.check_rho checks E on the larger range -4r <= K, which contains [2mu*_inf, ...] since mu*_inf >= -r.)
import sys, itertools
sys.path.insert(0, '/tmp/claude-0/qu/explore2/R2E2')
from lib import DS
from limit import tau
from residue_check import check_rho, mustar_inf

def tp_rho(r, rho):
    ds = DS(r, rho); tt = tau(r, rho); sigma = sum(x - 1 for x in rho)
    for z in range(-r, sigma + 2):
        if ds(z) < tt[z % r] and ((sigma + 1 - 2 * z) // r) % 2: return False
    return True

def mu_lower_ok(r, rho):
    # sanity: mu*_inf >= -r (used to justify the lower end of the E range)
    tt = tau(r, rho); m = mustar_inf(r, rho, tt)
    return m is not None and m >= -r

def full_check(r, rho):
    okE, okO, ms = check_rho(r, list(rho))
    return okE and okO and tp_rho(r, list(rho)) and mu_lower_ok(r, list(rho))
