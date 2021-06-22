from sesf import *
import sys

def main():
    if len(sys.argv) < 2 or sys.argv[1] == "":
        print("please call this script with a stateflow program location")
        return

    _program = load_program(sys.argv[1])
    programComposition = _program.get("Or", {})

    rezult = execute_symbolically(_program)
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

    print "all {0}".format(len(rezult))
    print "final {0}".format(len(final))
    print "unfeasible {0}".format(len(unfeasible))
    print "duplicates {0}".format(len(duplicates))
    for itm in []:
        print itm
        print "\n"
    print "++++++++++++++++++++++"


main()
