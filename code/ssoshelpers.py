import utils
from custom_exceptions import *
from custom_enums import *

# helper functions start
def generate_default_ss():
        return {"delta": [], "pc": {}, "derivation-tree": []}

def get_state_definition_composition(state_definition):
    composition = state_definition.get("Or", {})
    if composition == {}:
        composition = state_definition.get("And", {})
    return composition

def get_state_definition_composition_type(state_definition):
    return "Or" if "Or" in state_definition.keys(
    ) else "And" if "And" in state_definition.keys() else ""

def get_state_definition_children_path(state_definition):
    composition = get_state_definition_composition(state_definition)
    return get_or_composition_children_path(composition)

def get_or_composition_children_path(or_composition):
    c_paths = set()
    sd_list = or_composition.get("SD", [])
    for sd in sd_list:
        sd_name = list(sd.keys())[0]
        c_paths.add(sd_name)
        c_paths.update(get_state_definition_children_path(sd.get(sd_name)))
    return c_paths

def get_state_definition_by_path(composition, sd_path):
    result_state_definition = {}
    for sd in composition.get("SD", []):
        if sd_path in sd.keys():
            result_state_definition = sd.get(sd_path)
            break
    return result_state_definition

def get_or_composition_active_states_paths(or_composition):
    active_states = []
    active_state_path = or_composition.get("sa", "")
    if active_state_path == "":
        return active_states
    active_states.append(active_state_path)
    active_state_definition = get_state_definition_by_path(or_composition,
                                                     active_state_path)
    active_states.extend(get_state_definition_active_states_paths(
        active_state_definition))
    return active_states

def get_and_composition_active_states_paths(and_composition):
    active_states = []
    for sd_wrap in and_composition.get("SD", []):
        sd_name = sd_wrap.keys()[0]
        active_states.append(sd_name)
        active_state_definition = get_state_definition_by_path(and_composition, sd_name)
        active_states.extend(get_state_definition_active_states_paths(active_state_definition))
    return active_states

def get_state_definition_active_states_paths(state_definition):
    active_states = []
    if state_definition is not None and state_definition != {}:
        composition = get_state_definition_composition(state_definition)
        composition_type = get_state_definition_composition_type(state_definition)
        if composition_type == "Or":
            active_states.extend(get_or_composition_active_states_paths(composition))
        elif composition_type == "And":
            active_states.extend(get_and_composition_active_states_paths(composition))
    return active_states

def get_composition_sub_composition_by_path(composition, required_composition_path):
    state_definition = get_state_definition_by_path(composition, required_composition_path)
    if state_definition == {}:
        for child_state_definition_wrapper in composition.get("SD", []):
            sd_name = child_state_definition_wrapper.keys()[0]
            child_state_definition = child_state_definition_wrapper.get(sd_name)
            child_component_type = get_state_definition_composition_type(child_state_definition)
            child_component = _sd.get(child_component_type, {})
            sd = get_composition_sub_composition_by_path(child_component, required_composition_path)
            if state_definition != {}:
                break
    component_type = get_state_definition_composition_type(state_definition)
    return sd.get(component_type, {})

def get_composition_sub_state_definition_by_path(composition, required_state_definition_path):
    state_definition = get_state_definition_by_path(composition, required_state_definition_path)
    if state_definition == {}:
        for child_state_definition_wrapper in composition.get("SD", []):
            child_state_definition_wrapper_keys_list = list(child_state_definition_wrapper.keys())
            child_state_definition_name = child_state_definition_wrapper_keys_list[0]
            child_state_definition =child_state_definition_wrapper.get(child_state_definition_name, {})
            child_state_definition_composition_type = get_state_definition_composition_type(child_state_definition)
            if child_state_definition_composition_type != "":
                composition = child_state_definition.get(child_state_definition_composition_type)
                state_definition = get_composition_sub_state_definition_by_path(composition, required_state_definition_path)
                if state_definition != {}:
                    break
    return state_definition

def get_state_definition_sub_composition_by_path(state_definition, required_composition_path):
    # search in the inner composition of the current state definition
    result_component = {}
    composition_type = get_state_definition_composition_type(state_definition)
    if composition_type != "":
        composition = _state_definition.get(composition_type)
        result_component = get_composition_sub_composition_by_path(composition, required_composition_path)
    return result_component

def get_state_definition_sub_state_definition_by_path(state_definition, required_composition_path):
    # search in the innner composition of the current state definition
    result_state_definition = {}
    composition_type = get_state_definition_composition_type(state_definition)
    if composition_type != "":
        composition = _state_definition.get(composition_type)
        result_state_definition = get_composition_sub_state_definition_by_path(composition, required_composition_path)
    return result_state_definition

def set_composition_state_definition_by_path(component, state_definition, state_definition_path):
    component, state_definition = utils.deep_copy(component, state_definition)
    for child_state_definition_wrapper in component.get("SD", []):
        child_state_definition_wrapper_keys_list = list(child_state_definition_wrapper.keys())
        if child_state_definition_wrapper_keys_list[0] == state_definition_path:
            child_state_definition_wrapper[child_state_definition_wrapper_keys_list[0]] = state_definition
            break
    return component

def set_state_definitioncomposition(state_definition, composition):
    state_definition, _component = utils.deep_copy(state_definition, composition)
    composition_type = get_state_definitioncomposition_type(state_definition)
    state_definition[composition_type] = composition
    return state_definition

def get_state_definition_action_string(state_definition, action_name):
    A = state_definition.get("A", {})
    return A.get(action_name, "")

def get_composition_child_state_definition_by_path(composition, state_definition_path):
    candidate = None
    result = None
    activated_state_definition_path = ""
    for child_state_definition_wrapper in composition.get("SD", []):
        child_state_definition_wrapper_keys_list = list(child_state_definition_wrapper.keys())
        child_state_definition_name = child_state_definition_wrapper_keys_list[0]
        if child_state_definition_name == state_definition_path:
            result = child_state_definition_wrapper.get(child_state_definition_name)
            activated_state_definition_path = child_state_definition_name
            break
        if state_definition_path.startswith(child_state_definition_name):
            candidate = child_state_definition_wrapper.get(child_state_definition_name)
            activated_state_definition_path = child_state_definition_name
    if result is None and candidate is not None:
        result = candidate
    return result, activated_state_definition_path

def get_all_events(or_composition):
    events = set()
    # add empty event by default
    events.add("")
    for child_state_definition_name in get_or_composition_children_path(or_composition):
        child_state_definition = get_composition_sub_state_definition_by_path(or_composition, child_state_definition_name)
        io_junction_transitions = child_state_definition.get("To", []) + child_state_definition.get("Ti", [])
        junction_list = child_state_definition.get("J", {})
        for junction in junction_list.keys():
            io_junction_transitions = io_junction_transitions + junction_list.get(junction, [])
        for transition in io_junction_transitions:
            event = transition.get("e", "")
            if event != "":
                events.add(event)
    return list(events)

def update_derivation_tree(symbolic_state, rule_name):
    derivation_tree = symbolic_state.get("derivation-tree", [])
    derivation_tree.append(rule_name)
    symbolic_state["derivation-tree"] = derivation_tree
    return symbolic_state

def update_symbolic_environment(symbolic_state, expression):
    if expression is not None and expression != "":
        symbolic_environment = symbolic_state.get("delta", [])
        symbolic_environment.append(expression)
        symbolic_state["delta"] = symbolic_environment
    return symbolic_state

def update_symbolic_environment_with_list(symbolic_state, list_of_expressions):
    if list_of_expressions is None:
        list_of_expressions = []
    for expression in list_of_expressions:
        symbolic_state = update_symbolic_environment(symbolic_state, expression)
    return symbolic_state

def update_path_condition_at_position(symbolic_state, path_condition_addition, position):
    current_path_condition = symbolic_state.get("pc", {})
    current_path_condition_at_position = current_path_condition.get(position, [])
    current_path_condition_at_position.append(path_condition_addition)
    current_path_condition[position] = current_path_condition_at_position
    symbolic_state["pc"] = current_path_condition
    return symbolic_state

def update_path_condition(symbolic_state, path_condition_addition, negated=False):
    if path_condition_addition is not None and path_condition_addition != "":
        symbolic_environment = symbolic_state.get("delta", [])
        number_of_environment_updates = len(symbolic_environment)
        if number_of_environment_updates == 0:
            number_of_environment_updates = 1
        symbolic_state = update_path_condition_at_position(symbolic_state, path_condition_addition, number_of_environment_updates)
        if negated:
            symbolic_state = update_path_condition_at_position(symbolic_state, path_condition_addition, -number_of_environment_updates)
    return symbolic_state

def update_transition_value_action(transition_value, action):
    transition_value_actions = transition_value.get("a", [])
    transition_value_actions.append(action)
    transition_value["a"] = transition_value_actions
    return transition_value
# helper functions end
