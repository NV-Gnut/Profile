import string

SMILES_KEY = "HOH.HOH.CCO.c1ccc(O)cc1.CCNC"

MOLECULE_DB = [
    # 17 phần tử đầu tiên
    "C", "CC", "CCC", "O", "CO", "CCO", "N", "CN", "CCN", "S", "CS", "CCS",
    "F", "CF", "CCF", "Cl", "CCl",
    # 111 phần tử tiếp theo
    "CCCl", "Br", "CBr", "HOH", "OO", "OCO", "c1ccccc1", "Cc1ccccc1",
    "OCc1ccccc1", "Nc1ccccc1", "Sc1ccccc1", "c1ccc(C)cc1", "c1ccc(O)cc1",
    "c1ccc(N)cc1", "c1ccc(S)cc1", "c1ccc(F)cc1", "CC(C)C", "CC(C)O",
    "CC(C)N", "CC(C)S", "CC(C)F", "CCCC", "CCCCO", "CCCCN", "CCCCS",
    "CCCCF", "C1CC1", "C1CCO1", "C1CCN1", "C1CCS1", "C1CCF1",
    "C=C", "C=CO", "C=CN", "C=CS", "C=CF",
    "C#C", "C#CO", "C#CN", "C#CS", "C#CF",
    "c1ccncc1", "c1ccnc(C)c1", "c1ccnc(O)c1", "c1ccnc(N)c1", "c1ccnc(S)c1",
    "CC=C", "CCC=C", "CCCC=C", "CCCCC=C", "CCCCCC=C", "c1cccnc1",
    "c1ccc(C=C)cc1", "c1ccc(C#C)cc1", "c1ccc(CC)cc1", "c1ccc(CCC)cc1",
    "COC", "CCOC", "CCCOC", "CCCCOC", "CCCCCOC", "CNC", "CCNC", "CCCNC",
    "CCCCNC", "CCCCCNC", "CSC", "CCSC", "CCCSC", "CCCCSC", "CCCCCSC",
    "CFC", "CCFC", "CCCFC", "CCCCFC", "CCCCCFC", "ClCCl", "BrCBr", "ICl",
    "ClF", "BrF", "c1ccc2ccccc2c1", "c1ccc2cc(C)ccc2c1",
    "c1ccc2cc(O)ccc2c1", "c1ccc2cc(N)ccc2c1", "c1ccc2cc(S)ccc2c1",
    "CC(C)(C)C", "CC(C)(C)O", "CC(C)(C)N", "CC(C)(C)S", "CC(C)(C)F",
    "C1CCC1", "C1CCCO1", "C1CCCN1", "C1CCCS1", "C1CCCF1", "C1CCCC1",
    "C1CCCCO1", "C1CCCCN1", "C1CCCCS1", "C1CCCCF1", "C1CCCCC1",
    "C1CCCCCO1", "C1CCCCCN1", "C1CCCCCS1", "C1CCCCCF1",
    "c1ccc(C(C)C)cc1", "c1ccc(C(C)O)cc1", "c1ccc(C(C)N)cc1",
    "CC(=O)C", "CC(=O)O", "I"
]

dest = (
    "CCCC.CCCC.CC(C)F.C.HOH.c1ccc(S)cc1.CCOC.C1CCCC1.CC(C)S.Cc1ccccc1.CC(=O)C."
    "c1ccc(S)cc1.C1CCCC1.c1ccc(S)cc1.BrCBr.CC(C)S.C1CCCCCS1.C1CCCO1.c1ccc(S)cc1."
    "C=CF.c1ccc(C#C)cc1.CC(C)(C)N.C1CCCC1.CCOC.c1ccc(C#C)cc1.c1ccc(CC)cc1."
    "c1ccc(S)cc1.BrF.OCc1ccccc1.c1ccc(S)cc1.C=CF.c1ccc(C#C)cc1.HOH.Cc1ccccc1."
    "c1ccc(S)cc1.CCCCS.c1ccc(C#C)cc1.CC(C)S.C1CCO1.HOH.Cc1ccccc1.c1ccc(CC)cc1."
    "CF.Nc1ccccc1.c1ccc(S)cc1.CC(C)S.BrCBr.CCCCS.CF.Nc1ccccc1.N.c1ccc(CC)cc1."
    "HOH.CC(C)(C)N.BrCBr.OO"
)

def hash_molecular ( a1: str) -> int:
    i=0
    v2=0
    for i in a1:
        v2=31*v2+ord(i)
    return v2 & 0x7fffffff

def create_permutation(a1: str):
    perm = list(range(128))
    v4 = hash_molecular(a1)
    for j in range(127, 0, -1):
        v4 = (16807 * v4) % 0x7FFFFFFF
        k = v4 % (j + 1)
        perm[j], perm[k] = perm[k], perm[j]
    return perm

def brute_force(dest:str , MOLECULE_DB:str ):
    perm=create_permutation(SMILES_KEY)
    tokens=dest.split(".")
    revmap={}
    for i in range(128):
        revmap[MOLECULE_DB[i]]=perm[i]
    flag= []
    for j in tokens:
        if j not in revmap:
            flag.append("?")
        else:
            val=revmap[j]
            flag.append(chr(val))
    return "".join(flag)

flag=brute_force(dest,MOLECULE_DB)
print(flag)
