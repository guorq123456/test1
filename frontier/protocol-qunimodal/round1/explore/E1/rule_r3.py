# Rule for r=3 with no a_i divisible by 3 (proved in proof.txt):
#   P = prod [a_i]_q * [b]_{q^3} is unimodal  iff  b <= 1 + F + 2*floor(S/6),
#   F = sum floor(a_i/3), S = #{i : a_i = 2 mod 3}.
def domain(r, a):
    return r == 3 and all(x % 3 != 0 for x in a)
def predict(r, a, b):
    if any(x % 3 == 0 for x in a):
        return True  # Cor. 4.3 of arXiv:2605.12822 (outside this rule's domain; not part of my proof)
    F = sum(x // 3 for x in a)
    S = sum(1 for x in a if x % 3 == 2)
    return b <= 1 + F + 2 * (S // 6)
