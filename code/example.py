from sesf import SESF
import sys
from custom_enums import *

def main():
    if len(sys.argv) < 2 or sys.argv[1] == "":
        print("please call this script with a stateflow program location")
        return

    program_location = sys.argv[1]    
    rezult = SESF.execute_symbolically(program_location)
    final = []
    unfeasible = []
    duplicates = []
    for itm in rezult:
        if itm not in final:
            if "[neg ([True])]" not in itm.get("pc", ""):
                final.append(itm)
            else:
                unfeasible.append(itm)
        else:
            duplicates.append(itm)

    print(f'all {len(rezult)}')
    print(f"final {len(final)}")
    print(f"unfeasible {len(unfeasible)}")
    print(f"duplicates {len(duplicates)}")
    for itm in rezult:
        print(f"{itm}\n")

main()
