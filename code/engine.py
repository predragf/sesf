import copy
import json
import sys


def currentFuncName(n=0): return sys._getframe(n + 1).f_code.co_name


# global variables definition start
tvEnd = "End"
tvFire = "Fire"
tvNo = "No"
# global variables definition end

# helper functions start


def defaultSS():
    return {"delta": "", "pc": "true", "dtree": ""}


def openAndReadFile(filename):
    f = None
    fileContents = ""
    try:
        f = open(filename, "r")
        fileContents = f.read()

    except Exception as exc:
        print exc

    finally:
        if f is not None and not f.closed:
            f.close()
    return fileContents


def loadProgram(programLocation):
    fileContents = openAndReadFile(programLocation)
    return json.loads(fileContents)


def deepCopy(*arguments):
    returnArguments = []
    for argument in arguments:
        returnArguments.append(copy.deepcopy(argument))
    return tuple(returnArguments)


def getStateDefinitionComposition(stateDefinition):
    composition = stateDefinition.get("Or", {})
    if composition == {}:
        composition = stateDefinition.get("And", {})
    return composition


def getStateDefinitionCompositionType(stateDefinition):
    return "Or" if "Or" in stateDefinition.keys(
    ) else "And" if "And" in stateDefinition.keys() else ""


def getStateDefinitionChildrenPath(stateDefinition):
    composition = getStateDefinitionComposition(stateDefinition)
    return getOrCompositionChildrenPath(composition)


def getOrCompositionChildrenPath(orComposition):
    cPaths = set()
    sdList = orComposition.get("SD", [])
    for sd in sdList:
        sdName = sd.keys()[0]
        cPaths.add(sdName)
        cPaths.update(getStateDefinitionChildrenPath(sd.get(sdName)))
    return cPaths


def getStateDefinitionByPath(composition, sdPath):
    resultStateDefinition = {}
    for sd in composition.get("SD", []):
        if sdPath in sd.keys():
            resultStateDefinition = sd.get(sdPath)
            break
    return resultStateDefinition


def getOrCompositionActiveStatesPaths(orComposition):
    activeStates = []
    activeStatePath = orComposition.get("sa", "")
    if activeStatePath == "":
        return activeStates
    activeStates.append(activeStatePath)
    activeStateDefinition = getStateDefinitionByPath(orComposition,
                                                     activeStatePath)
    activeStates.extend(getStateDefinitionActiveStatesPaths(
        activeStateDefinition))
    return activeStates


def getAndCompositionActiveStatesPaths(andComposition):
    # to be implemented, not needed now
    pass


def getStateDefinitionActiveStatesPaths(stateDefinition):
    activeStates = []
    if stateDefinition is None or stateDefinition == {}:
        return activeStates
    composition = getStateDefinitionComposition(stateDefinition)
    compositionType = getStateDefinitionCompositionType(stateDefinition)
    if compositionType == "Or":
        activeStates.extend(getOrCompositionActiveStatesPaths(composition))
    elif compositionType == "And":
        activeStates.extend(getAndCompositionActiveStatesPaths(composition))
    return activeStates


def getCompositionSubCompositionByPath(_composition, requiredCompositionPath):
    sd = getStateDefinitionByPath(_composition, requiredCompositionPath)
    if sd == {}:
        for _sdWrap in _composition.get("SD", []):
            sdName = _sdWrap.keys()[0]
            _sd = _sdWrap.get(sdName)
            cType = getStateDefinitionCompositionType(_sd)
            cmp = _sd.get(cType, {})
            sd = getCompositionSubCompositionByPath(cmp, requiredCompositionPath)
            if sd != {}:
                break
    cType = getStateDefinitionCompositionType(sd)
    return sd.get(cType, {})


def getCompositionSubStateDefinitionByPath(_composition, requiredStateDefinitionPath):
    sd = getStateDefinitionByPath(_composition, requiredStateDefinitionPath)
    if sd == {}:
        for _sdWrap in _composition.get("SD", []):
            _sdName = _sdWrap.keys()[0]
            _sd = _sdWrap.get(_sdName, {})
            _sdCmpType = getStateDefinitionCompositionType(_sd)
            if _sdCmpType != "":
                cmp = _sd.get(_sdCmpType)
                sd = getCompositionSubStateDefinitionByPath(cmp, requiredStateDefinitionPath)
                if sd != {}:
                    break
    return sd


def getStateDefinitionSubCompositionByPath(_stateDefinition, requiredCompositionPath):
    # search in the inner composition of the current state definition
    resultCmp = {}
    cType = getStateDefinitionCompositionType(_stateDefinition)
    if cType != "":
        cmp = _stateDefinition.get(cType)
        resultCmp = getCompositionSubCompositionByPath(cmp, requiredCompositionPath)
    return resultCmp


def getStateDefinitionSubStateDefinitionByPath(_stateDefinition, requiredCompositionPath):
    # search in the innner composition of the current state definition
    resultSd = {}
    cType = getStateDefinitionCompositionType(_stateDefinition)
    if cType != "":
        cmp = _stateDefinition.get(cType)
        resultSd = getCompositionSubStateDefinitionByPath(cmp, requiredCompositionPath)
    return resultSd


def setCompositionStateDefinitionByPath(_component, _stateDefinition, _stateDefinitionPath):
    _component, _stateDefinition = deepCopy(_component, _stateDefinition)
    for _sdWrap in _component.get("SD", []):
        if _sdWrap.keys()[0] == _stateDefinitionPath:
            _sdWrap[_sdWrap.keys()[0]] = _stateDefinition
            break
    return _component


def setStateDefinitionComposition(_sd, _composition):
    _sd, _component = deepCopy(_sd, _composition)
    cType = getStateDefinitionCompositionType(_sd)
    _sd[cType] = _composition
    return _sd


def parseExpressionForAdding(expression=""):
    return "[{0}]".format(expression) if not expression == "" else ""


def getStateDefinitionActionString(stateDefinition, actionName):
    A = stateDefinition.get("A", {})
    action = A.get(actionName, "")
    return parseExpressionForAdding(action)


def getCompositionChildStateDefinitionByPath(composition, statedefinitionpath):
    candidate = None
    result = None
    activatedSDPath = ""
    for sdWrap in composition.get("SD", []):
        sdName = sdWrap.keys()[0]
        if sdName == statedefinitionpath:
            result = sdWrap.get(sdName)
            activatedSDPath = sdName
            break
        if statedefinitionpath.startswith(sdName):
            candidate = sdWrap.get(sdName)
            activatedSDPath = sdName
    if result is None and candidate is not None:
        result = candidate
    return result, activatedSDPath
# helper functions end


# t-rules start
def tFire(transition, ss, tv):
    # for debugging purposes
    print currentFuncName()
    print transition
    print "------"
    # for debugging purposes
    ss, tv = deepCopy(ss, tv)
    ca = parseExpressionForAdding(transition.get("ca", ""))
    c = parseExpressionForAdding(transition.get("c", ""))
    ss["delta"] = "{0}{1}".format(ss.get("delta", ""), ca)
    ss["pc"] = "{1} && {0}".format(c, ss.get("pc", ""))
    ss["dtree"] = "{0}[{1}]".format(ss.get("dtree", ""), "t-fire-{0}".format(c))
    # transition returns only 1 symbolic state and one tv
    return ss, {"type": tvFire, "d": transition.get("d", ""), "a": transition.get("ta", "")}


def tNoFire(transition, ss, tv):
    # for debugging purposes
    print currentFuncName()
    print transition
    print "------"
    # for debugging purposes
    ss, tv = deepCopy(ss, tv)
    c = transition.get("c", "")
    ss["pc"] = "{1} && [neg ({0})]".format(c, ss.get("pc", ""))
    ss["dtree"] = "{0}[{1}]".format(ss.get("dtree", ""), "t-no-fire-{0}".format(c))
    # transition returns only 1 symbolic state and one tv
    return ss, {"type": tvNo}
# t-rules end

# T-rules start
# the T-rules now do not implement the T-rules for junctions. That will
# be in the next release


def executeTList(tList, ss, tv):
    # for debugging purposes
    print currentFuncName()
    print tList
    print "------"
    # for debugging purposes
    wtList, wss, wtv = deepCopy(tList, ss, tv)
    # TList returns a set of symbolic states and tvs
    returnTuples = []
    if len(wtList) == 0:
        return [(wss, {"type": tvEnd})]
    head = wtList.pop(0)
    returnTuples.append(tFire(head, wss, wtv))
    _ssTnf, _tvTnf = tNoFire(head, wss, wtv)
    returnTuples.extend(executeTList(wtList, _ssTnf, _tvTnf))
    return returnTuples

# T-rules end

# sd-rules start


def sd_no(stateDefinition, ss, tv):
    # for debugging purposes
    print currentFuncName()
    print stateDefinition
    print "------"
    # for debugging purposes
    stateDefinition, ss, tv = deepCopy(stateDefinition, ss, tv)
    ss["dtree"] = "{0}[{1}]".format(ss.get("dtree", ""), "sd-no")
    return [(stateDefinition, ss, tv)]


def sd_init(stateDefinition, ss, tv, p):
    # for debugging purposes
    print currentFuncName()
    print stateDefinition
    print "------"
    # for debugging purposes
    p = p if p is not None else ""
    ss, tv, stateDefinition, p = deepCopy(ss, tv, stateDefinition, p)
    returnTuples = []
    action = getStateDefinitionActionString(stateDefinition, "en")
    # update delta and the derrivation tree
    ss["delta"] = "{0}{1}".format(ss["delta"], action)
    # ss["dtree"] = "{0}[{1}]".format(ss.get("dtree", ""), "sd-init")
    # execute the internal composition
    cType = getStateDefinitionCompositionType(stateDefinition)
    _composition = stateDefinition.get(cType, {})
    # here one of the or-inits shall be called
    for _C, _ss, _tv in initialize_or(_composition, stateDefinition.get("J", []), ss, None, p):
        _sd, _C, _ss, _tv = deepCopy(stateDefinition, _C, _ss, _tv)
        _sd[cType] = _C
        _ss["dtree"] = "{0}[{1}]".format(_ss.get("dtree", ""), "sd-init")
        # think about the return tv type
        returnTuples.append(tuple((_sd, _ss, tv)))
    # this is the case if there was no component
    if len(returnTuples) < 1:
        ss["dtree"] = "{0}[{1}]".format(ss.get("dtree", ""), "sd-init")
        returnTuples.append(tuple((stateDefinition, ss, tv)))
    return returnTuples


def sd_exit(stateDefinition, ss, tv):
    # for debugging purposes
    print currentFuncName()
    print stateDefinition
    print "------"
    # for debugging purposes
    returnTuples = []
    stateDefinition, ss, tv = deepCopy(stateDefinition, ss, tv)
    exitAction = getStateDefinitionActionString(stateDefinition, "ex")
    # ss["dtree"] = "{0}[{1}]".format(ss.get("dtree", ""), "sd-exit")
    # this can be only or_exit (update when AND component is developed)
    cType = getStateDefinitionCompositionType(stateDefinition)
    _composition = stateDefinition.get(cType, {})
    for _C, _ssC, _tvC in or_exit(_composition, stateDefinition.get("J", []), ss, tv):
        # _ss has the value from the execution of the internal component
        _sd, _C, _ssC, _tvC = deepCopy(stateDefinition, _C, _ssC, _tvC)
        # update delta with exit action
        _ssC["delta"] = "{0}{1}".format(_ssC["delta"], exitAction)
        _ssC["dtree"] = "{0}[{1}]".format(_ssC.get("dtree", ""), "sd-exit")
        _sd[cType] = _C
        # there should in principle be no tv at the end of this rule
        # however, I am returning the input tv
        returnTuples.append(tuple((_sd, _ssC, tv)))

    # this is the case when there was no component
    if len(returnTuples) < 1:
        ss["delta"] = "{0}{1}".format(ss["delta"], exitAction)
        ss["dtree"] = "{0}[{1}]".format(ss.get("dtree", ""), "sd-exit")
        returnTuples.append(tuple((stateDefinition, ss, tv)))
    return returnTuples


def sd_fire(stateDefinition, ss, tv):
    # for debugging purposes
    print currentFuncName()
    print stateDefinition
    print "------"
    # for debugging purposes
    returnTuples = []
    stateDefinition, ss, tv = deepCopy(stateDefinition, ss, tv)
    exAction = getStateDefinitionActionString(stateDefinition, "ex")
    tvAction = parseExpressionForAdding(tv.get("a", ""))
    tv["a"] = ""
    ss["delta"] = "{0}{1}".format(ss["delta"], tvAction)
    # ss["dtree"] = "{0}[{1}]".format(ss.get("dtree", ""), "sd-fire")
    # or-exit shall be called here - update for AND component once developed
    cType = getStateDefinitionCompositionType(stateDefinition)
    _composition = stateDefinition.get(cType, {})
    for _C, _ssC, _tvC in or_exit(_composition, [], ss, tv):
        _sd, _C, _ssC, _tv = deepCopy(stateDefinition, _C, _ssC, tv)
        _ssC["delta"] = "{0}{1}".format(_ssC["delta"], exAction)
        _ssC["dtree"] = "{0}[{1}]".format(_ssC.get("dtree", ""), "sd-fire")
        _sd[cType] = _C
        returnTuples.append((_sd, _ssC, _tv))
    # this is the case when there was no component
    if len(returnTuples) < 1:
        ss["delta"] = "{0}{1}".format(ss["delta"], exAction)
        ss["dtree"] = "{0}[{1}]".format(ss.get("dtree", ""), "sd-fire")
        returnTuples.append(tuple((stateDefinition, ss, tv)))
    return returnTuples


def sd_int_fire(stateDefinition, ss, tv):
    # for debugging purposes
    print currentFuncName()
    print stateDefinition
    print "------"
    # for debugging purposes

    stateDefinition, ss, tv = deepCopy(stateDefinition, ss, tv)
    tvAct = parseExpressionForAdding(tv.get("a", ""))
    sdAction = getStateDefinitionActionString(stateDefinition, "ex")

    ss["delta"] = "{0}{1}{2}".format(ss["delta"], tvAct, sdAction)
    ss["dtree"] = "{0}[{1}]".format(ss.get("dtree", ""), "sd-int-fire")
    tv["a"] = ""

    return [tuple((stateDefinition, ss, tv))]


def executeSD(stateDefinition, ss, tv, p=""):
    # for debugging purposes
    print currentFuncName()
    print stateDefinition
    print "------"
    # for debugging purposes
    # sd = ((a,a,a), C, Ti, To, J)
    wsd, wss, wtv = deepCopy(stateDefinition, ss, tv)
    returnTuples = []
    cType = getStateDefinitionCompositionType(wsd)

    durationAction = getStateDefinitionActionString(wsd, "du")

    for _ssTo, _tvTo in executeTList(wsd.get("To", []), wss, wtv):
        __ssTo, _tvTo = deepCopy(_ssTo, _tvTo)
        if _tvTo.get("type", "") in [tvEnd, tvNo]:
            _ssTo["delta"] = "{0}{1}".format(_ssTo["delta"], durationAction)
            for _ssTi, _tvTi in executeTList(wsd.get("Ti", []), _ssTo, _tvTo):
                _sd, _ssTi, _tvTi = deepCopy(wsd, _ssTi, _tvTi)
                _c1 = _sd.get(cType, {})
                destinationPath = _tvTi.get("d", "") if _tvTi is not None else ""
                for _c1C, _ssC, _tvC in executeOr(_c1, [], _ssTi, _tvTi, destinationPath):
                    _sSd, _c1C, _ssC, _tvC = deepCopy(_sd, _c1C, _ssC, _tvC)
                    _sSd[cType] = _c1C
                    if _tvC.get("type", "") == tvFire:
                        returnTuples.extend(sd_int_fire(_sSd, _ssC, _tvC))
                    # this sould in principle be only tv no, but since in
                    # symbolic execution we do not have a no, then we treat it
                    # the same as end (this text concerns the if below)
                    elif _tvC.get("type", "") in [tvNo, tvEnd]:
                        returnTuples.extend(sd_no(_sSd, _ssC, _tvC))
                    elif _tvC.get("type", "") == tvEnd:
                        returnTuples.append(tuple((_sSd, _ssC, _tvC)))
        elif _tvTo.get("type", "") == tvFire:
            returnTuples.extend(sd_fire(wsd, _ssTo, _tvTo))
    return returnTuples


def or_ext_fire_out(orComposition, J, ss, tv):
    # for debugging purposes
    print currentFuncName()
    print orComposition
    print "------"
    # for debugging purposes
    resultTuples = []
    wOr, wss, wtv = deepCopy(orComposition, ss, tv)
    fireAction = parseExpressionForAdding(wtv.get("a", ""))
    wtv["a"] = ""
    wss["delta"] = "{0}{1}".format(wss["delta"], fireAction)
    activeStateDefinition, notNeeded = getCompositionChildStateDefinitionByPath(
        orComposition, orComposition.get("sa", ""))
    for _sd, _ssSD, _tvSD in sd_exit(activeStateDefinition, ss, tv):
        _orC, _sd, _ssSD, _tvSD = deepCopy(orComposition, _sd, _ssSD, _tvSD)
        _orC["sa"] = ""
        _orC = setCompositionStateDefinitionByPath(_orC, _sd, orComposition.get("sa", ""))
        _ssSD["dtree"] = "{0}[{1}]".format(
            _ssSD.get("dtree", ""), "or-ext-fire-out-{0}".format(_orC.get("p", "")))
        resultTuples.append(tuple((_orC, _ssSD, tv)))
    return resultTuples


def or_int_fire(orComposition, J, ss, tv):
    # for debugging purposes
    print currentFuncName()
    print orComposition
    print "------"
    # for debugging purposes
    orComposition, ss, tv = deepCopy(orComposition, ss, tv)
    resultTuples = []
    p = tv.get("d", "")

    stateDefinitionForActivation, stateDefinitionForActivationPath = getCompositionChildStateDefinitionByPath(
        orComposition, p)
    for _sd, _ssSD, _tvSD in sd_init(stateDefinitionForActivation, ss, tv, p):
        _orC, _sd, _ssSD, _tvSD = deepCopy(orComposition, _sd, _ssSD, _tvSD)
        _orC["sa"] = stateDefinitionForActivationPath
        _orC = setCompositionStateDefinitionByPath(_orC, _sd, stateDefinitionForActivationPath)
        _ssSD["dtree"] = "{0}[{1}]".format(
            _ssSD.get("dtree", ""), "or-int-fire-{0}".format(_orC.get("p", "")))
        resultTuples.append(tuple((_orC, _ssSD, {"type": tvNo})))
    return resultTuples


def or_fire(orComposition, J, ss, tv):
    # for debugging purposes
    print currentFuncName()
    print orComposition
    print "------"
    # for debugging purposes
    resultTuples = []
    orComposition, J, ss, tv = deepCopy(orComposition, J, ss, tv)
    orComposition["sa"] = ""
    ss["dtree"] = "{0}[{1}]".format(
        ss.get("dtree", ""), "or-fire-{0}".format(orComposition.get("p", "")))
    resultTuples.append(tuple((orComposition, ss, tv)))
    return resultTuples


def or_init_no_state(orComposition, J, ss, tv):
    # for debugging purposes
    print currentFuncName()
    print orComposition
    print "------"
    # for debugging purposes
    orComposition, ss, tv = deepCopy(orComposition, ss, tv)
    # only thing that we do is that we are adding the rule in the dtree
    ss["dtree"] = "{0}[{1}]".format(
        ss.get("dtree", ""), "or-init-no-state-{0}".format(orComposition.get("p", "")))
    return [tuple((orComposition, ss, tv))]


def or_init_empty_path(orComposition, J, ss, tv):
    # for debugging purposes
    print currentFuncName()
    print orComposition
    print "------"
    # for debugging purposes
    resultTuples = []
    orComposition, ss, tv = deepCopy(orComposition, ss, tv)
    for _ssT, _tvT in executeTList(orComposition.get("T", []), ss, tv):
        if _tvT.get("type", "") == tvFire:
            fireAction = "[{0}]".format(_tvT.get("a", "")) if _tvT.get("a", "") != "" else ""
            # we will use the a, so it will be reset
            _tvT["a"] = ""
            # the assumption is that you will always initialize the direct child
            stateDefinitionForActivationPath = _tvT.get("d", "")
            stateDefinitionForActivation = getCompositionSubStateDefinitionByPath(
                orComposition, stateDefinitionForActivationPath)
            for _sd, _ssSD, _tvSD in sd_init(stateDefinitionForActivation, _ssT, None, ""):
                _orC, _sd, _ssSD, _tvSD = deepCopy(orComposition, _sd, _ssSD, _tvSD)
                _orC["sa"] = stateDefinitionForActivationPath
                _orC = setCompositionStateDefinitionByPath(
                    _orC, _sd, stateDefinitionForActivationPath)
                _ssSD["delta"] = "{0}{1}".format(_ssSD["delta"], fireAction)
                _ssSD["dtree"] = "{0}[{1}]".format(
                    _ssSD.get("dtree", ""), "or-init-empty-path-{0}".format(_orC.get("p", "")))
                resultTuples.append(tuple((_orC, _ssSD, tv)))

    return resultTuples


def or_init(orComposition, J, ss, tv, p):
    # for debugging purposes
    print currentFuncName()
    print orComposition
    print "------"
    # for debugging purposes
    resultTuples = []
    p = p if p is not None else ""
    orComposition, J, ss, tv = deepCopy(orComposition, J, ss, tv)
    stateDefinitionForInitializing, stateDefinitionForInitializingPath = getCompositionChildStateDefinitionByPath(
        orComposition, p)
    # if this the state that needed to be activated with the propagating p,
    # then set p=""
    if stateDefinitionForInitializingPath == p:
        p = ""
    for _sd, _ssSD, _tvSD in sd_init(stateDefinitionForInitializing, ss, tv, p):
        _orC, _sd, _ssSD, _tvSD = deepCopy(orComposition, _sd, _ssSD, _tvSD)
        _orC["sa"] = stateDefinitionForInitializingPath
        _orC = setCompositionStateDefinitionByPath(_orC, _sd, stateDefinitionForInitializingPath)
        _ssSD["dtree"] = "{0}[{1}]".format(
            _ssSD.get("dtree", ""), "or-init-{0}".format(_orC.get("p", "")))
        resultTuples.append(tuple((_orC, _ssSD, tv)))
    return resultTuples


def or_exit(orComposition, J, ss, tv):
    # for debugging purposes
    print currentFuncName()
    print orComposition
    print "------"
    # for debugging purposes
    resultTuples = []
    orComposition, J, ss, tv = deepCopy(orComposition, J, ss, tv)
    activeStateDefinitionPath = orComposition.get("sa", "")
    if(activeStateDefinitionPath == ""):
        resultTuples.append(tuple((orComposition, ss, {"type": tvEnd})))
        return resultTuples
    activeStateDefinition = getCompositionSubStateDefinitionByPath(
        orComposition, activeStateDefinitionPath)

    for _sd, _ssSD, _tvSD in sd_exit(activeStateDefinition, ss, tv):
        _orC, _sd, _ssSD, _tvSD = deepCopy(orComposition, _sd, _ssSD, _tvSD)
        _orC["sa"] = ""
        _orC = setCompositionStateDefinitionByPath(_orC, _sd, activeStateDefinitionPath)
        _ssSD["dtree"] = "{0}[{1}]".format(
            _ssSD.get("dtree", ""), "or-exit-{0}".format({_orC.get("p", "")}))
        resultTuples.append(tuple((_orC, _ssSD, _tvSD)))
    return resultTuples


def or_no(orComposition, J, ss, tv):
    # for debugging purposes
    print currentFuncName()
    print orComposition
    print "------"
    # for debugging purposes
    returnTuples = []
    orComposition, ss, tv = deepCopy(orComposition, ss, tv)
    ss["dtree"] = "{0}[{1}]".format(
        ss.get("dtree", ""), "or-no-{0}".format(orComposition.get("p", "")))
    returnTuples.append(tuple((orComposition, ss, tv)))
    return returnTuples


def initialize_or(orComposition, J, ss, tv, p):
    resultTuples = []
    orComposition, J, ss, tv, p = deepCopy(orComposition, J, ss, tv, p)
    # if the C element is empty
    if orComposition is None or orComposition == {}:
        return [tuple((orComposition, ss, tv))]
    if p != "":
        resultTuples.extend(or_init(orComposition, J, ss, tv, p))
    else:
        if (len(orComposition.get("SD", [])) > 0):
            resultTuples.extend(or_init_empty_path(orComposition, J, ss, tv))
        else:
            resultTuples.extend(or_init_no_state(orComposition, J, ss, tv))
    return resultTuples


def executeOr(orComposition, J={}, ss=defaultSS(), tv=None, p=""):
    # here is the object of the composition, without the or
    print currentFuncName()
    print orComposition
    print "------"
    # or = (sa, p, T, SD)
    # if the composition object is empty, do not process.
    if orComposition is not None and orComposition == {}:
        return [tuple((orComposition, ss, tv))]
    # prepare data for execution
    resultTuples = []
    orComposition, J, ss, tv = deepCopy(orComposition, J, ss, tv)
    activeStateDefinitionPath = orComposition.get("sa", "")
    # prepare data for execution end

    # if there is no active state, then it must be one of the initializations
    if activeStateDefinitionPath == "":
        resultTuples.extend(initialize_or(orComposition, J, ss, tv, p))
    else:
        # just to make sure that tv is not None, so it does not raise
        # an exception, although in principle it should never happen
        if tv is None:
            raise Exception('Error', 'I should not have happened 3')
        tv = tv if tv is not None else {}
        if tv.get("type", "") == tvFire:
            destinationPath = tv.get("d", "")
            if destinationPath not in getOrCompositionChildrenPath(orComposition):
                resultTuples.extend(or_ext_fire_out(orComposition, J, ss, tv))
            else:
                raise Exception('Error', 'I should not have happened 2')
                # this basically means do nothing
                return [tuple((orComposition, ss, tv))]

        # here we should treat or-no, or-int-fire, or-fire
        elif tv.get("type", "") in [tvEnd, tvNo]:
            # we fetch the activestatedefinition from the list
            activeStateDefinition, activeStateDefinitionPath = getCompositionChildStateDefinitionByPath(
                orComposition, activeStateDefinitionPath)
            # now we need to execute the statedefinition
            for _sd, _ssSD, _tvSD in executeSD(activeStateDefinition, ss, tv):
                _orC, _sd, _ssSD, _tvSD = deepCopy(orComposition, _sd, _ssSD, _tvSD)
                _orC = setCompositionStateDefinitionByPath(_orC, _sd, activeStateDefinitionPath)
                # here again should be [tvNo, tvEnd] because there is no tvNo
                # if _tvSD.get("type", "") == tvNo:
                if _tvSD.get("type", "") in [tvNo, tvEnd]:
                    resultTuples.extend(or_no(_orC, J, _ssSD, _tvSD))
                elif _tvSD.get("type", "") == tvFire:
                    # the other assumption would be that _tvSD.get("d", "") is not a prefix of
                    # the current component
                    if _tvSD.get("d", "") in getOrCompositionChildrenPath(orComposition):
                        resultTuples.extend(or_int_fire(_orC, J, _ssSD, _tvSD))
                    else:
                        resultTuples.extend(or_fire(_orC, J, _ssSD, _tvSD))
        else:
            raise Exception('Error', 'I should not have happened')
    return resultTuples


def executeAnd(andComposition, ss, tv):
    # and = (b, SD)
    return []


def executeComposition(composition, J={}, ss=defaultSS(), tv={}, p=""):
    # this function is needed because we have two types of compositions
    # for debugging purposes
    print currentFuncName()
    print composition
    print "------"
    # for debugging purposes
    composition, J, ss, tv = deepCopy(composition, J, ss, tv)
    compositionType = "" if len(composition.keys()) < 1 else composition.keys()[0]
    # lets say that end should denote end of derrivation
    resultTuples = [(composition, ss,
                     {"type": tvEnd})] if compositionType == "" else []

    if compositionType == "Or":
        resultTuples = executeOr(composition.get(compositionType), J, ss, tv, p)
    elif compositionType == "And":
        resultTuples = executeAnd(composition.get(compositionType), ss, tv)
    return resultTuples


def executeSymbolicallyRecursive(program, ss, tv={}, exploredExecutions=set()):
    _ss, _tv, _exploredExecutions = deepCopy(ss, tv, exploredExecutions)
    print currentFuncName()
    print program
    print "------"
    # we add the current configuration into the explored executions
    # represented through the hash of the currently active states
    currentProgramActiveStatesString = "".join(getOrCompositionActiveStatesPaths(program))
    exploredExecutions.add(currentProgramActiveStatesString)
    transitionRelation = []

    # now we execute the composition
    orExecutions = executeOr(program, program.get("J", []), _ss, _tv, "")
    # return orExecutions, set()
    # this will not execute
    for _newProgram, _ssOr, _tvOr in orExecutions:
        _newProgram, _ssOr, _tvOr = deepCopy(_newProgram, _ssOr, _tvOr)
        _newProgramActiveStatesString = "".join(getOrCompositionActiveStatesPaths(_newProgram))
        transition = {"source": "{0}".format(currentProgramActiveStatesString),
                      "destination": "{0}".format(_newProgramActiveStatesString),
                      "delta'": "{0}(delta)".format(_ssOr.get("delta")),
                      "dtree": _ssOr.get("dtree"),
                      "tv": _tvOr,
                      "pc": _ssOr.get("pc")}
        transitionRelation.append(transition)
        if _newProgramActiveStatesString not in exploredExecutions:
            _tr, _exploredExecutions = executeSymbolicallyRecursive(
                _newProgram, ss, {"type": tvEnd}, exploredExecutions)
            # append new transition
            transitionRelation.extend(_tr)
            # update the set of explored executions
            exploredExecutions.update(_exploredExecutions)
    return transitionRelation, exploredExecutions


def executeSymbolically(program):
    # a program is always a sd for or-composition
    # return only the transition relation
    ss = {"delta": "", "pc": "true", "dtree": ""}
    # get the or composition from the program
    # the program is ALWAYS an Or-composition
    programComposition = program.get("Or", {})
    # return only the transitionRelation

    return executeSymbolicallyRecursive(programComposition, ss, None)[0]


def main():
    _program = loadProgram("./models/program.json")
    result = executeSymbolically(_program)
    print "results start from here\n"
    for itm in result:
        print itm
        print "\n"


main()
