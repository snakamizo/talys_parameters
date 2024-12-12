from script.utilities import split_by_number
from script.elem import elemtoz
from config import IAEA_MEDICAL_LIST

f = open(IAEA_MEDICAL_LIST, "r")

for line in f.readlines():
    l = line.split()
    projectile = l[1]
    target = split_by_number(l[0])
    residual = split_by_number(l[3])

    z = elemtoz(target[0])


    if target[1] == "000":
        tmass = "\mathrm{Nat}"
    else:
        tmass = str(int(target[1]))

    rmass = str(int(residual[1]))

    dic = {}
    latex_target = "$^{" + tmass + "}$"+target[0]

    if residual[2]:
        isomeric = "\mathrm" + "{" + residual[2] + "}"
        latex_residual = "$^{" + rmass + isomeric + "}$"+residual[0]
    else:
        latex_residual = "$^{" + rmass + "}$"+residual[0]

    print( f"{z:5} {latex_target:20} {projectile:8} X    {latex_residual:20}")