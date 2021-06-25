import json
import sys
import re
import copy
import utils

# global variables definition start
tvEnd = "End"
tvFire = "Fire"
tvNo = "No"
# global variables definition end

# helper functions start


def generate_default_ss():
    return {"delta": "", "pc": "true", "dtree": ""}


def load_program(programLocation):
    try:
        _file = utils.open_file(programLocation)
        program = json.load(_file)
        _file.close()
    except Exception:
        print("Problems opening file. Script will run on empty stateflow program!")
        program = dict()
    return program

def get_state_definition_composition(stateDefinition):
    composition = stateDefinition.get("Or", {})
    if composition == {}:
        composition = stateDefinition.get("And", {})
    return composition


def get_state_definition_composition_type(stateDefinition):
    return "Or" if "Or" in stateDefinition.keys(
    ) else "And" if "And" in stateDefinition.keys() else ""


def get_state_definition_children_path(stateDefinition):
    composition = get_state_definition_composition(stateDefinition)
    return get_or_composition_children_path(composition)


def get_or_composition_children_path(orComposition):
    cPaths = set()
    sdList = orComposition.get("SD", [])
    for sd in sdList:
        sdName = sd.keys()[0]
        cPaths.add(sdName)
        cPaths.update(get_state_definition_children_path(sd.get(sdName)))
    return cPaths


def get_state_definition_by_path(composition, sdPath):
    resultStateDefinition = {}
    for sd in composition.get("SD", []):
        if sdPath in sd.keys():
            resultStateDefinition = sd.get(sdPath)
            break
    return resultStateDefinition


def get_or_composition_active_states_paths(orComposition):
    activeStates = []
    activeStatePath = orComposition.get("sa", "")
    if activeStatePath == "":
        return activeStates
    activeStates.append(activeStatePath)
    activeStateDefinition = get_state_definition_by_path(orComposition,
                                                     activeStatePath)
    activeStates.extend(get_state_definition_active_states_paths(
        activeStateDefinition))
    return activeStates


def get_and_composition_active_states_paths(andComposition):
    # to be implemented, not needed now
    pass


def get_state_definition_active_states_paths(stateDefinition):
    activeStates = []
    if stateDefinition is not None and stateDefinition != {}:
        composition = get_state_definition_composition(stateDefinition)
        compositionType = get_state_definition_composition_type(stateDefinition)
        if compositionType == "Or":
            activeStates.extend(get_or_composition_active_states_paths(composition))
        elif compositionType == "And":
            activeStates.extend(get_and_composition_active_states_paths(composition))
    return activeStates


def get_composition_sub_composition_by_path(_composition, requiredCompositionPath):
    sd = get_state_definition_by_path(_composition, requiredCompositionPath)
    if sd == {}:
        for _sdWrap in _composition.get("SD", []):
            sdName = _sdWrap.keys()[0]
            _sd = _sdWrap.get(sdName)
            cType = get_state_definition_composition_type(_sd)
            cmp = _sd.get(cType, {})
            sd = get_composition_sub_composition_by_path(cmp, requiredCompositionPath)
            if sd != {}:
                break
    cType = get_state_definition_composition_type(sd)
    return sd.get(cType, {})


def get_composition_sub_state_definition_by_path(_composition, requiredStateDefinitionPath):
    sd = get_state_definition_by_path(_composition, requiredStateDefinitionPath)
    if sd == {}:
        for _sdWrap in _composition.get("SD", []):
            _sdName = _sdWrap.keys()[0]
            _sd = _sdWrap.get(_sdName, {})
            _sdCmpType = get_state_definition_composition_type(_sd)
            if _sdCmpType != "":
                cmp = _sd.get(_sdCmpType)
                sd = get_composition_sub_state_definition_by_path(cmp, requiredStateDefinitionPath)
                if sd != {}:
                    break
    return sd


def get_state_definition_sub_composition_by_path(_stateDefinition, requiredCompositionPath):
    # search in the inner composition of the current state definition
    resultCmp = {}
    cType = get_state_definition_composition_type(_stateDefinition)
    if cType != "":
        cmp = _stateDefinition.get(cType)
        resultCmp = get_composition_sub_composition_by_path(cmp, requiredCompositionPath)
    return resultCmp


def get_state_definition_sub_state_definition_by_path(_stateDefinition, requiredCompositionPath):
    # search in the innner composition of the current state definition
    resultSd = {}
    cType = get_state_definition_composition_type(_stateDefinition)
    if cType != "":
        cmp = _stateDefinition.get(cType)
        resultSd = get_composition_sub_state_definition_by_path(cmp, requiredCompositionPath)
    return resultSd


def set_composition_state_definition_by_path(_component, _stateDefinition, _stateDefinitionPath):
    _component, _stateDefinition = utils.deep_copy(_component, _stateDefinition)
    for _sdWrap in _component.get("SD", []):
        if _sdWrap.keys()[0] == _stateDefinitionPath:
            _sdWrap[_sdWrap.keys()[0]] = _stateDefinition
            break
    return _component


def set_state_definition_composition(_sd, _composition):
    _sd, _component = utils.deep_copy(_sd, _composition)
    cType = get_state_definition_composition_type(_sd)
    _sd[cType] = _composition
    return _sd


def parse_expression_for_adding(expression=""):
    return "[{0}]".format(expression) if expression != "" else ""


def get_state_definition_action_string(stateDefinition, actionName):
    A = stateDefinition.get("A", {})
    action = A.get(actionName, "")
    return parse_expression_for_adding(action)


def get_composition_child_state_definition_by_path(composition, statedefinitionpath):
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


def get_number_of_assignments(expression=""):
    assignmentExpression = r"\[(.*?)\]"  # r'\[.+\]'
    allMatches = re.findall(assignmentExpression, expression)
    return len(allMatches)


def get_all_events(orComposition):
    events = set()
    # add empty event by default
    events.add("")
    for sdName in get_or_composition_children_path(orComposition):
        sd = get_composition_sub_state_definition_by_path(orComposition, sdName)
        IOJtransitions = sd.get("To", []) + sd.get("Ti", [])
        jList = sd.get("J", {})
        for junction in jList.keys():
            IOJtransitions = IOJtransitions + jList.get(junction, [])
        for transition in IOJtransitions:
            event = transition.get("e", "")
            if event != "":
                events.add(event)
    return list(events)

    # helper functions end


# T-rules start

def T_fire_J_F(junction, J, ss, tv):
    # for debugging purposes
    print utils.currentFuncName()
    print junction
    print "------"
    # for debugging purposes

    ss["dtree"] = "{0}[{1}]".format(ss.get("dtree", ""), "T-fire-J-F-{0}".format(junction))
    return([tuple((ss, tv))])


def T_end(junction, J, ss, tv):
    # for debugging purposes
    print utils.currentFuncName()
    print junction
    print "------"
    # for debugging purposes

    ss["dtree"] = "{0}[{1}]".format(ss.get("dtree", ""), "T-End-{0}".format(junction))
    return([tuple((ss, tv))])


def T_fire_J_N(junction, J, ss, tv, events):
    # for debugging purposes
    print utils.currentFuncName()
    print junction
    print "------"
    # for debugging purposes
    junction, J, ss, tv = utils.deep_copy(junction, J, ss, tv)
    jList = J.get(junction, [])
    resultTuples = []
    for _tss, _ttv in execute_T_list(jList, J, ss, tv, events):
        if _ttv.get("type", "") == tvFire:
            resultTuples.extend(T_fire_J_F(junction, J, _tss, _ttv))
        elif _ttv.get("type", "") == tvEnd:
            resultTuples.extend(T_end(junction, J, _tss, _ttv))
        elif _ttv.get("type", "") == tvNo:
            resultTuples.append(tuple((_tss, _ttv)))
    return resultTuples

# T-rules end


# t-rules start

def t_fire(transition, ss, tv):
    # for debugging purposes
    print utils.currentFuncName()
    print transition
    print "------"
    # for debugging purposes
    ss, tv = utils.deep_copy(ss, tv)
    ca = parse_expression_for_adding(transition.get("ca", ""))
    c = parse_expression_for_adding(transition.get("c", ""))
    event = parse_expression_for_adding(transition.get("e", ""))
    if c not in ["[True]", ""]:
        ss["pc"] = "{0} && {1}_{2}".format(ss.get("pc", ""), c, get_number_of_assignments(ss["delta"]))
    if event != "":
        ss["pc"] = "{0} && {1}".format(ss.get("pc", ""), event)
    ss["dtree"] = "{0}[{1}]".format(ss.get("dtree", ""), "t-fire-{0}".format(c))
    ss["delta"] = "{0}{1}".format(ss.get("delta", ""), ca)
    fireAction = "{0};{{0}}".format(
        tv.get("a")) if tv is not None and tv.get("a", "") != "" else "{0}"
    # transition returns only 1 symbolic state and one tv
    return ss, {"type": tvFire, "d": transition.get("d", ""), "a": fireAction.format(transition.get("ta", ""))}


def t_no_fire(transition, ss, tv):
    # for debugging purposes
    print utils.currentFuncName()
    print transition
    print "------"
    # for debugging purposes
    ss, tv = utils.deep_copy(ss, tv)
    c = transition.get("c", "") if transition.get("c", "") != "" else "True"
    # if there is an event, the c should be empty string (the event acts like a guard)
    c = parse_expression_for_adding(c)
    if c != "":
        ss["pc"] = "{0} && [neg ({1})]".format(ss.get("pc", ""), c)
    if c not in ["[True]", ""]:
        ss["pc"] = "{0}_{1}".format(ss["pc"], get_number_of_assignments(ss["delta"]))
    ss["dtree"] = "{0}[{1}]".format(ss.get("dtree", ""), "t-no-fire-{0}".format(c))
    # transition returns only 1 symbolic state and one tv
    return ss, {"type": tvNo}


def t_no_fire2(transition, ss, tv):
    # for debugging purposes
    print utils.currentFuncName()
    print transition
    print "------"
    # for debugging purposes
    ss, tv = utils.deep_copy(ss, tv)
    c = transition.get("c", "")
    ss["dtree"] = "{0}[{1}]".format(ss.get("dtree", ""), "t-no-fire-2-{0}".format(c))
    # transition returns only 1 symbolic state and one tv
    return ss, {"type": tvNo}


def execute_T_list(tList, J, ss, tv, events):
    # for debugging purposes
    print utils.currentFuncName()
    print events
    print tList
    print "------"
    # for debugging purposes
    wtList, wss, wtv = utils.deep_copy(tList, ss, tv)
    J = utils.deep_copy(J)[0] if J is not None else {}
    # TList returns a set of symbolic states and tvs
    returnTuples = []
    if len(wtList) == 0:
        wss["dtree"] = "{0}[{1}]".format(wss.get("dtree", ""), "T-empty")
        return [(wss, {"type": tvEnd})]
    head = wtList.pop(0)
    # this is the case that event of the transition does not match
    # the currently active event we never fire the transition
    if head.get("e", "") != "" and head.get("e", "") not in events:
        _ssNo2, _tvNo2 = t_no_fire2(head, wss, wtv)
        returnTuples.extend(execute_T_list(wtList, J, _ssNo2, _tvNo2, events))
        return returnTuples
    _sstFire, _tvtFire = t_fire(head, wss, wtv)
    # here is a check whether the transition fired to a state or junction
    if _tvtFire.get("d", "") in J.keys():
        for _ssj, _tvj in T_fire_J_N(_tvtFire.get("d", ""), J, _sstFire, _tvtFire, events):
            _ssj, _tvj = utils.deep_copy(_ssj, _tvj)
            _ssj["dtree"] = "{0}[{1}]".format(_ssj.get("dtree", ""), "T-fire")
            if len(wtList) == 0:
                returnTuples.append(tuple((_ssj, _tvj)))
            else:
                if _tvj.get("type", "") == tvFire:
                    returnTuples.append(tuple((_ssj, _tvj)))
                else:
                    returnTuples.extend(execute_T_list(wtList, J, _ssj, _tvj, events))
    else:
        _sstFire["dtree"] = "{0}[{1}]".format(_sstFire.get("dtree", ""), "T-fire")
        returnTuples.append(tuple((_sstFire, _tvtFire)))
    _ssTnf, _tvTnf = t_no_fire(head, wss, wtv)
    if len(wtList) > 0:
        _ssTnf["dtree"] = "{0}[{1}]".format(_ssTnf.get("dtree", ""), "T-no")
        returnTuples.extend(execute_T_list(wtList, J, _ssTnf, _tvTnf, events))
    else:
        _ssTnf["dtree"] = "{0}[{1}]".format(_ssTnf.get("dtree", ""), "T-no-Last")
        returnTuples.append(tuple((_ssTnf, _tvTnf)))
    return returnTuples

# T-rules end

# sd-rules start

def sd_no(stateDefinition, ss, tv, events):
    # for debugging purposes
    print utils.currentFuncName()
    print events
    print stateDefinition
    print "------"
    # for debugging purposes
    stateDefinition, ss, tv = utils.deep_copy(stateDefinition, ss, tv)
    ss["dtree"] = "{0}[{1}]".format(ss.get("dtree", ""), "sd-no")
    return [(stateDefinition, ss, tv)]


def sd_init(stateDefinition, ss, tv, p, events):
    # for debugging purposes
    print utils.currentFuncName()
    print events
    print stateDefinition
    print "------"
    # for debugging purposes
    p = p if p is not None else ""
    ss, tv, stateDefinition, p = utils.deep_copy(ss, tv, stateDefinition, p)
    returnTuples = []
    action = get_state_definition_action_string(stateDefinition, "en")
    # update delta and the derrivation tree
    ss["delta"] = "{0}{1}".format(ss["delta"], action)
    # execute the internal composition
    cType = get_state_definition_composition_type(stateDefinition)
    _composition = stateDefinition.get(cType, {})
    # here one of the or-inits shall be called
    for _C, _ss, _tv in composition_init(_composition, stateDefinition.get("J", {}), ss, None, p, events):
        _sd, _C, _ss, _tv = utils.deep_copy(stateDefinition, _C, _ss, _tv)
        _sd[cType] = _C
        _ss["dtree"] = "{0}[{1}]".format(_ss.get("dtree", ""), "sd-init")
        returnTuples.append(tuple((_sd, _ss, tv)))
    # this is the case if there was no component
    if len(returnTuples) < 1:
        ss["dtree"] = "{0}[{1}]".format(ss.get("dtree", ""), "sd-init")
        returnTuples.append(tuple((stateDefinition, ss, tv)))
    return returnTuples


def sd_exit(stateDefinition, ss, tv, events):
    # for debugging purposes
    print utils.currentFuncName()
    print events
    print stateDefinition
    print "------"
    # for debugging purposes
    returnTuples = []
    stateDefinition, ss, tv = utils.deep_copy(stateDefinition, ss, tv)
    exitAction = get_state_definition_action_string(stateDefinition, "ex")
    cType = get_state_definition_composition_type(stateDefinition)
    _composition = stateDefinition.get(cType, {})

    for _C, _ssC, _tvC in composition_exit(_composition, stateDefinition.get("J", {}), ss, tv, events):
        # _ss has the value from the execution of the internal component
        _sd, _C, _ssC, _tvC = utils.deep_copy(stateDefinition, _C, _ssC, _tvC)
        # update delta with exit action
        _ssC["delta"] = "{0}{1}".format(_ssC["delta"], exitAction)
        _ssC["dtree"] = "{0}[{1}]".format(_ssC.get("dtree", ""), "sd-exit")
        _sd[cType] = _C
        # in principle, there should be an NO-tv at the end of this rule,
        # however, we are returning the tv which was passed as an input
        returnTuples.append(tuple((_sd, _ssC, tv)))
    # this is the case when there was no component
    if len(returnTuples) < 1:
        ss["delta"] = "{0}{1}".format(ss["delta"], exitAction)
        ss["dtree"] = "{0}[{1}]".format(ss.get("dtree", ""), "sd-exit")
        returnTuples.append(tuple((stateDefinition, ss, tv)))
    return returnTuples


def sd_fire(stateDefinition, ss, tv, events):
    # for debugging purposes
    print utils.currentFuncName()
    print events
    print stateDefinition
    print "------"
    # for debugging purposes
    returnTuples = []
    stateDefinition, ss, tv = utils.deep_copy(stateDefinition, ss, tv)
    exAction = get_state_definition_action_string(stateDefinition, "ex")
    tvAction = parse_expression_for_adding(tv.get("a", ""))
    tv["a"] = ""
    ss["delta"] = "{0}{1}".format(ss["delta"], tvAction)
    cType = get_state_definition_composition_type(stateDefinition)
    _composition = stateDefinition.get(cType, {})
    for _C, _ssC, _tvC in composition_exit(_composition, [], ss, tv, events):
        _sd, _C, _ssC, _tv = utils.deep_copy(stateDefinition, _C, _ssC, tv)
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


def sd_int_fire(stateDefinition, ss, tv, events):
    # for debugging purposes
    print utils.currentFuncName()
    print events
    print stateDefinition
    print "------"
    # for debugging purposes

    stateDefinition, ss, tv = utils.deep_copy(stateDefinition, ss, tv)
    tvAct = parse_expression_for_adding(tv.get("a", ""))
    sdAction = get_state_definition_action_string(stateDefinition, "ex")

    ss["delta"] = "{0}{1}{2}".format(ss["delta"], tvAct, sdAction)
    ss["dtree"] = "{0}[{1}]".format(ss.get("dtree", ""), "sd-int-fire")
    tv["a"] = ""

    return [tuple((stateDefinition, ss, tv))]

# sd-rules end

def execute_sd(stateDefinition, ss, tv, p="", events=[]):
    # for debugging purposes
    print utils.currentFuncName()
    print events
    print stateDefinition
    print "------"
    # for debugging purposes
    wsd, wss, wtv = utils.deep_copy(stateDefinition, ss, tv)
    returnTuples = []
    cType = get_state_definition_composition_type(wsd)

    durationAction = get_state_definition_action_string(wsd, "du")

    for _ssTo, _tvTo in execute_T_list(wsd.get("To", []), wsd.get("J", {}), wss, wtv, events):
        _ssTo, _tvTo = utils.deep_copy(_ssTo, _tvTo)
        if _tvTo.get("type", "") in [tvEnd, tvNo]:
            _ssTo["delta"] = "{0}{1}".format(_ssTo["delta"], durationAction)
            for _ssTi, _tvTi in execute_T_list(wsd.get("Ti", []), wsd.get("J", {}), _ssTo, _tvTo, events):
                _sd, _ssTi, _tvTi = utils.deep_copy(wsd, _ssTi, _tvTi)
                _c1 = _sd.get(cType, {})
                destinationPath = _tvTi.get("d", "") if _tvTi is not None else ""
                for _c1C, _ssC, _tvC in execute_composition(_c1, {}, _ssTi, _tvTi, destinationPath, events):
                    _sSd, _c1C, _ssC, _tvC = utils.deep_copy(_sd, _c1C, _ssC, _tvC)
                    _sSd[cType] = _c1C
                    if _tvC.get("type", "") == tvFire:
                        returnTuples.extend(sd_int_fire(_sSd, _ssC, _tvC, events))
                    # in principle, this should be only NO-tv, but since in
                    # symbolic execution we do not have a no, then we treat it
                    # the same as end (this text concerns the if below)
                    elif _tvC.get("type", "") in [tvNo, tvEnd]:
                        returnTuples.extend(sd_no(_sSd, _ssC, _tvC, events))
                    elif _tvC.get("type", "") == tvEnd:
                        returnTuples.append(tuple((_sSd, _ssC, _tvC)))
        elif _tvTo.get("type", "") == tvFire:
            returnTuples.extend(sd_fire(wsd, _ssTo, _tvTo, events))
    return returnTuples

# or-rules start

def or_ext_fire_out(orComposition, J, ss, tv, events):
    # for debugging purposes
    print utils.currentFuncName()
    print events
    print orComposition
    print "------"
    # for debugging purposes
    resultTuples = []
    wOr, wss, wtv = utils.deep_copy(orComposition, ss, tv)
    fireAction = parse_expression_for_adding(wtv.get("a", ""))
    wtv["a"] = ""
    wss["delta"] = "{0}{1}".format(wss["delta"], fireAction)
    activeStateDefinition, notNeeded = get_composition_child_state_definition_by_path(
        orComposition, orComposition.get("sa", ""))
    for _sd, _ssSD, _tvSD in sd_exit(activeStateDefinition, ss, tv, events):
        _orC, _sd, _ssSD, _tvSD = utils.deep_copy(orComposition, _sd, _ssSD, _tvSD)
        _orC["sa"] = ""
        _orC = set_composition_state_definition_by_path(_orC, _sd, orComposition.get("sa", ""))
        _ssSD["dtree"] = "{0}[{1}]".format(
            _ssSD.get("dtree", ""), "or-ext-fire-out-{0}".format(_orC.get("p", "")))
        resultTuples.append(tuple((_orC, _ssSD, tv)))
    return resultTuples


def or_int_fire(orComposition, J, ss, tv, events):
    # for debugging purposes
    print utils.currentFuncName()
    print events
    print orComposition
    print "------"
    # for debugging purposes
    orComposition, ss, tv = utils.deep_copy(orComposition, ss, tv)
    resultTuples = []
    p = tv.get("d", "")

    stateDefinitionForActivation, stateDefinitionForActivationPath = get_composition_child_state_definition_by_path(
        orComposition, p)
    for _sd, _ssSD, _tvSD in sd_init(stateDefinitionForActivation, ss, tv, p, events):
        _orC, _sd, _ssSD, _tvSD = utils.deep_copy(orComposition, _sd, _ssSD, _tvSD)
        _orC["sa"] = stateDefinitionForActivationPath
        _orC = set_composition_state_definition_by_path(_orC, _sd, stateDefinitionForActivationPath)
        _ssSD["dtree"] = "{0}[{1}]".format(
            _ssSD.get("dtree", ""), "or-int-fire-{0}".format(_orC.get("p", "")))
        resultTuples.append(tuple((_orC, _ssSD, {"type": tvNo})))
    return resultTuples


def or_fire(orComposition, J, ss, tv, events):
    # for debugging purposes
    print utils.currentFuncName()
    print events
    print orComposition
    print "------"
    # for debugging purposes
    resultTuples = []
    orComposition, J, ss, tv = utils.deep_copy(orComposition, J, ss, tv)
    orComposition["sa"] = ""
    ss["dtree"] = "{0}[{1}]".format(
        ss.get("dtree", ""), "or-fire-{0}".format(orComposition.get("p", "")))
    resultTuples.append(tuple((orComposition, ss, tv)))
    return resultTuples


def or_init_no_state(orComposition, J, ss, tv, events):
    # for debugging purposes
    print utils.currentFuncName()
    print events
    print orComposition
    print "------"
    # for debugging purposes
    orComposition, ss, tv = utils.deep_copy(orComposition, ss, tv)
    # only thing that we do is that we are adding the rule in the dtree
    ss["dtree"] = "{0}[{1}]".format(
        ss.get("dtree", ""), "or-init-no-state-{0}".format(orComposition.get("p", "")))
    return [tuple((orComposition, ss, tv))]


def or_init_empty_path(orComposition, J, ss, tv, events):
    # for debugging purposes
    print utils.currentFuncName()
    print events
    print orComposition
    print "------"
    # for debugging purposes
    resultTuples = []
    orComposition, ss, tv = utils.deep_copy(orComposition, ss, tv)
    for _ssT, _tvT in execute_T_list(orComposition.get("T", []), J, ss, tv, events):
        if _tvT.get("type", "") == tvFire:
            fireAction = "[{0}]".format(_tvT.get("a", "")) if _tvT.get("a", "") != "" else ""
            # we will use the a, so it will be reset
            _tvT["a"] = ""
            # the assumption is that we always initialize the direct child
            stateDefinitionForActivationPath = _tvT.get("d", "")
            stateDefinitionForActivation = get_composition_sub_state_definition_by_path(
                orComposition, stateDefinitionForActivationPath)
            for _sd, _ssSD, _tvSD in sd_init(stateDefinitionForActivation, _ssT, None, "", events):
                _orC, _sd, _ssSD, _tvSD = utils.deep_copy(orComposition, _sd, _ssSD, _tvSD)
                _orC["sa"] = stateDefinitionForActivationPath
                _orC = set_composition_state_definition_by_path(
                    _orC, _sd, stateDefinitionForActivationPath)
                _ssSD["delta"] = "{0}{1}".format(_ssSD["delta"], fireAction)
                _ssSD["dtree"] = "{0}[{1}]".format(
                    _ssSD.get("dtree", ""), "or-init-empty-path-{0}".format(_orC.get("p", "")))
                resultTuples.append(tuple((_orC, _ssSD, tv)))
    return resultTuples


def or_init(orComposition, J, ss, tv, p, events):
    # for debugging purposes
    print utils.currentFuncName()
    print events
    print orComposition
    print "------"
    # for debugging purposes
    resultTuples = []
    p = p if p is not None else ""
    orComposition, J, ss, tv = utils.deep_copy(orComposition, J, ss, tv)
    stateDefinitionForInitializing, stateDefinitionForInitializingPath = get_composition_child_state_definition_by_path(
        orComposition, p)
    # if this the state that needed to be activated with the propagating p,
    # then set p=""
    if stateDefinitionForInitializingPath == p:
        p = ""
    for _sd, _ssSD, _tvSD in sd_init(stateDefinitionForInitializing, ss, tv, p, events):
        _orC, _sd, _ssSD, _tvSD = utils.deep_copy(orComposition, _sd, _ssSD, _tvSD)
        _orC["sa"] = stateDefinitionForInitializingPath
        _orC = set_composition_state_definition_by_path(_orC, _sd, stateDefinitionForInitializingPath)
        _ssSD["dtree"] = "{0}[{1}]".format(
            _ssSD.get("dtree", ""), "or-init-{0}".format(_orC.get("p", "")))
        resultTuples.append(tuple((_orC, _ssSD, tv)))
    return resultTuples


def or_exit(orComposition, J, ss, tv, events):
    # for debugging purposes
    print utils.currentFuncName()
    print events
    print orComposition
    print "------"
    # for debugging purposes
    resultTuples = []
    orComposition, J, ss, tv = utils.deep_copy(orComposition, J, ss, tv)
    activeStateDefinitionPath = orComposition.get("sa", "")
    if(activeStateDefinitionPath == ""):
        resultTuples.append(tuple((orComposition, ss, {"type": tvEnd})))
        return resultTuples
    activeStateDefinition = get_composition_sub_state_definition_by_path(
        orComposition, activeStateDefinitionPath)
    for _sd, _ssSD, _tvSD in sd_exit(activeStateDefinition, ss, tv, events):
        _orC, _sd, _ssSD, _tvSD = utils.deep_copy(orComposition, _sd, _ssSD, _tvSD)
        _orC["sa"] = ""
        _orC = set_composition_state_definition_by_path(_orC, _sd, activeStateDefinitionPath)
        _ssSD["dtree"] = "{0}[{1}]".format(
            _ssSD.get("dtree", ""), "or-exit-{0}".format({_orC.get("p", "")}))
        resultTuples.append(tuple((_orC, _ssSD, _tvSD)))
    return resultTuples


def or_no(orComposition, J, ss, tv, events):
    # for debugging purposes
    print utils.currentFuncName()
    print events
    print orComposition
    print "------"
    # for debugging purposes
    returnTuples = []
    orComposition, ss, tv = utils.deep_copy(orComposition, ss, tv)
    ss["dtree"] = "{0}[{1}]".format(
        ss.get("dtree", ""), "or-no-{0}".format(orComposition.get("p", "")))
    returnTuples.append(tuple((orComposition, ss, tv)))
    return returnTuples


def initialize_or(orComposition, J, ss, tv, p, events):
    resultTuples = []
    orComposition, J, ss, tv, p = utils.deep_copy(orComposition, J, ss, tv, p)
    # if the C element is empty
    if orComposition is None or orComposition == {}:
        return [tuple((orComposition, ss, tv))]
    if p != "":
        resultTuples.extend(or_init(orComposition, J, ss, tv, p, events))
    else:
        if (len(orComposition.get("SD", [])) > 0):
            resultTuples.extend(or_init_empty_path(orComposition, J, ss, tv, events))
        else:
            resultTuples.extend(or_init_no_state(orComposition, J, ss, tv, events))
    return resultTuples

# or-rules end


def execute_or(orComposition, J={}, ss=generate_default_ss(), tv=None, p="", events=[]):
    # here is the object of the composition, without the or
    print utils.currentFuncName()
    print events
    print orComposition
    print "------"
    # or = (sa, p, T, SD)
    # if the composition object is empty, do not process.
    if orComposition is not None and orComposition == {}:
        return [tuple((orComposition, ss, tv))]
    # prepare data for execution
    resultTuples = []
    orComposition, J, ss, tv = utils.deep_copy(orComposition, J, ss, tv)
    activeStateDefinitionPath = orComposition.get("sa", "")
    # prepare data for execution end

    # if there is no active state, then it must be one of the initializations
    if activeStateDefinitionPath == "":
        resultTuples.extend(composition_init(orComposition, J, ss, tv, p, events))
    else:
        # just to make sure that tv is not None, so it does not raise
        # an exception, although in principle it should never happen
        if tv is None:
            raise Exception('Error', 'I should not have happened 3')
        tv = tv if tv is not None else {}
        if tv.get("type", "") == tvFire:
            destinationPath = tv.get("d", "")
            if destinationPath not in get_or_composition_children_path(orComposition):
                resultTuples.extend(or_ext_fire_out(orComposition, J, ss, tv, events))
            else:
                raise Exception('Error', 'I should not have happened 2')
                # this basically means do nothing
                return [tuple((orComposition, ss, tv))]

        # here we should treat or-no, or-int-fire, or-fire
        elif tv.get("type", "") in [tvEnd, tvNo]:
            # we fetch the activestatedefinition from the list
            activeStateDefinition, activeStateDefinitionPath = get_composition_child_state_definition_by_path(
                orComposition, activeStateDefinitionPath)
            # now we need to execute the statedefinition
            for _sd, _ssSD, _tvSD in execute_sd(activeStateDefinition, ss, tv, "", events):
                _orC, _sd, _ssSD, _tvSD = utils.deep_copy(orComposition, _sd, _ssSD, _tvSD)
                _orC = set_composition_state_definition_by_path(_orC, _sd, activeStateDefinitionPath)
                # here again should be [tvNo, tvEnd] because there is no tvNo
                # if _tvSD.get("type", "") == tvNo:
                if _tvSD.get("type", "") in [tvNo, tvEnd]:
                    resultTuples.extend(or_no(_orC, J, _ssSD, _tvSD, events))
                elif _tvSD.get("type", "") == tvFire:
                    # the other assumption would be that _tvSD.get("d", "") is not a prefix of
                    # the current component
                    if _tvSD.get("d", "") in get_or_composition_children_path(orComposition):
                        resultTuples.extend(or_int_fire(_orC, J, _ssSD, _tvSD, events))
                    else:
                        resultTuples.extend(or_fire(_orC, J, _ssSD, _tvSD, events))
        else:
            raise Exception('Error', 'I should not have happened')
    return resultTuples

# and-rules start

def and_rule(andComposition, J, ss, tv, events):
    _andC, _ss, _tv = utils.deep_copy(andComposition, ss, tv)
    for sdWrap in andComposition.get("SD", []):
        pass


def and_init(andComposition, J, ss, tv, p="", events=[]):
    _andC, _ss, _tv, _p = utils.deep_copy(andComposition, ss, tv, p)
    for sdWrap in andComposition.get("SD", []):
        sdName = sdWrap.keys()[0]
        sd = sdWrap[sdName]
        # this loop should execute only once
        for _sd, _ss, _tv in sd_init(sd, _ss, _tv, p, events):
            _andC = set_composition_state_definition_by_path(_andC, _sd, sdName)
    _andC["b"] = "True"
    return[tuple((_andC, _ss, _tv))]


def and_exit(andComposition, J, ss, tv, events):
    _andC, _ss, _tv = utils.deep_copy(andComposition, ss, tv)
    for sdWrap in andComposition.get("SD", []):
        sdName = sdWrap.keys()[0]
        _sd = sdWrap[sdName]
        # this loop should execute only once
        for _sd, _ss, _tv in sd_exit(_sd, _ss, _tv, "", events):
            _andC = set_composition_state_definition_by_path(_andC, _sd, sdName)
    _andC["b"] = "False"
    return[tuple((_andC, _ss, _tv))]


def execute_and(andComposition, J={}, ss=generate_default_ss(), tv=None, p="", events=[]):
    if andComposition.get("b", "") == "True":
        return and_rule(andComposition, J, ss, tv, events)
    else:
        return and_init(andComposition, J, ss, tv, events)


def composition_exit(composition, J, ss, tv, events):
    # this means that and_exit is called only for valid And composition. In
    # case of a valid OR composition or an empty OR composition {}, then or_exit
    # is called
    if len(composition.keys()) == 2:
        return and_exit(composition, J, ss, tv, events)
    else:
        return or_exit(composition, J, ss, tv, events)


def composition_init(composition, J, ss, tv, p, events):
    # this means that and_init is called only for valid And composition. In
    # case of a valid OR composition or empty composition {}, then initalize_or
    # is called
    if len(composition.keys()) == 2:
        return and_init(composition, J, ss, tv, events)
    else:
        return initialize_or(composition, J, ss, tv, p, events)

# and-rules end


def execute_composition(composition, J={}, ss=generate_default_ss(), tv=None, p="", events=[]):
    # this means that executeAnd is called only for valid And composition. In
    # case of a valid OR composition or empty composition {}, then executeOr
    # is called
    if len(composition.keys()) == 2:
        return execute_and(composition, J, ss, tv, events)
    else:
        return execute_or(composition, J, ss, tv, p, events)


def execute_symbolically_recursive(program, ss, tv={}, exploredExecutions=set()):
    _ss, _tv, _exploredExecutions = utils.deep_copy(ss, tv, exploredExecutions)
    print utils.currentFuncName()
    print program
    print "------"
    # get the events. In case no events, we create a list of
    # empty event such that the loop can loop
    events = get_all_events(program)
    # we add the current configuration into the explored executions
    # represented through the hash of the currently active states
    currentProgramActiveStatesString = "".join(get_or_composition_active_states_paths(program))
    # exploredExecutions.add(currentProgramActiveStatesString)
    transitionRelation = []
    # now we execute the composition without events - no events allowed
    # on the initialization edges
    for event in events:
        exploredExecutions.add("{0}{1}".format(currentProgramActiveStatesString, event))
        orExecutions = execute_composition(program, program.get("J", {}), _ss, _tv, "", [event])
        # return orExecutions, set()
        # this will not execute
        for _newProgram, _ssOr, _tvOr in orExecutions:
            _newProgram, _ssOr, _tvOr = utils.deep_copy(_newProgram, _ssOr, _tvOr)
            _newProgramActiveStatesString = "".join(get_or_composition_active_states_paths(_newProgram))
            transition = {"source": "{0}".format(currentProgramActiveStatesString),
                          "destination": "{0}".format(_newProgramActiveStatesString),
                          "delta'": "{0}(delta)".format(_ssOr.get("delta")),
                          "dtree": _ssOr.get("dtree"),
                          "tv": _tvOr,
                          "pc": _ssOr.get("pc"),
                          "event": event}
            transitionRelation.append(transition)
            if "{0}{1}".format(_newProgramActiveStatesString, event) not in exploredExecutions:
                _tr, _exploredExecutions = execute_symbolically_recursive(
                    _newProgram, ss, {"type": tvEnd}, exploredExecutions)
                # append new transition
                transitionRelation.extend(_tr)
                # update the set of explored executions
                exploredExecutions.update(_exploredExecutions)
    return transitionRelation, exploredExecutions


def execute_symbolically(program):
    # at the top level, a Stateflow program is ALWAYS an Or-composition

    # return only the transitionRelation, which is the first component
    # of the return tuple of the recursive function
    return execute_symbolically_recursive(program.get("Or", {}), generate_default_ss(), None)[0]
