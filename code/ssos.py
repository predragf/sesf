import utils
from ssoshelpers import *
from custom_exceptions import TransitionValueException
from custom_enums import TransitionValueType
from decorators import print_enter_exit_decorator

class TransitionRules:
    @staticmethod
    @print_enter_exit_decorator
    def t_fire(transition, symbolic_state, transition_value):
        symbolic_state, transition_value = utils.deep_copy(symbolic_state, transition_value)
        condition_action = transition.get("ca", "")
        condition = transition.get("c", "")
        rule_name = "t-fire-{0}".format(condition)
        symbolic_state = update_path_condition(symbolic_state, condition)
        symbolic_state = update_path_condition(symbolic_state, transition.get("e", ""))
        symbolic_state = update_derivation_tree(symbolic_state, rule_name)
        symbolic_state = update_symbolic_environment(symbolic_state, condition_action)
        transition_value_actions = transition_value.get("a", []) if transition_value is not None else []
        transition_value_actions.append(transition.get("ta", ""))
        # transition returns only 1 symbolic state and one transition_value
        return symbolic_state, {"type": TransitionValueType.FIRE, "d": transition.get("d", ""), "a": transition_value_actions}

    @staticmethod
    @print_enter_exit_decorator
    def t_no_fire(transition, symbolic_state, transition_value):
        symbolic_state, transition_value = utils.deep_copy(symbolic_state, transition_value)
        condition = transition.get("c", "")
        rule_name = "t-no-fire-{0}".format(condition)
        symbolic_state = update_path_condition(symbolic_state, condition, True)
        symbolic_state = update_path_condition(symbolic_state, transition.get("e", ""))
        symbolic_state = update_derivation_tree(symbolic_state, rule_name)
        # transition returns only 1 symbolic state and one transition_value
        return symbolic_state, {"type": TransitionValueType.NO}

    @staticmethod
    @print_enter_exit_decorator
    def t_no_fire2(transition, symbolic_state, transition_value):
        symbolic_state, transition_value = utils.deep_copy(symbolic_state, transition_value)
        condition = transition.get("c", "")
        rule_name = "t-no-fire-2-{0}".format(condition)
        symbolic_state = update_derivation_tree(symbolic_state, rule_name)
        # transition returns only 1 symbolic state and one transition_value
        return symbolic_state, {"type": TransitionValueType.NO}

class TransitionListRules:

    @staticmethod
    @print_enter_exit_decorator
    def T_fire_J_F(junction, J, symbolic_state, transition_value):
        rule_name = f"T-fire-J-F-{junction}"
        symbolic_state = update_derivation_tree(symbolic_state, rule_name)
        return([tuple((symbolic_state, transition_value))])

    @staticmethod
    @print_enter_exit_decorator
    def T_end(junction, J, symbolic_state, transition_value):
        rule_name = f"T-End-{junction}"
        symbolic_state = update_derivation_tree(symbolic_state, rule_name)
        return([tuple((symbolic_state, transition_value))])

    @staticmethod
    @print_enter_exit_decorator
    def T_fire_J_N(junction, J, symbolic_state, transition_value, events):
        junction, J, symbolic_state, transition_value = utils.deep_copy(junction, J, symbolic_state, transition_value)
        j_list = J.get(junction, [])
        result_tuples = []
        for intermediate_symbolic_state, intermediate_transition_value in TransitionListRules.execute_T_list(j_list, J, symbolic_state, transition_value, events):
            if intermediate_transition_value.get("type", "") == TransitionValueType.FIRE:
                result_tuples.extend(TransitionListRules.T_fire_J_F(junction, J, intermediate_symbolic_state, intermediate_transition_value))
            elif intermediate_transition_value.get("type", "") == TransitionValueType.END:
                result_tuples.extend(TransitionListRules.T_end(junction, J, intermediate_symbolic_state, intermediate_transition_value))
            elif intermediate_transition_value.get("type", "") == TransitionValueType.NO:
                result_tuples.append(tuple((intermediate_symbolic_state, intermediate_transition_value)))
        return result_tuples

    @staticmethod
    @print_enter_exit_decorator
    def execute_T_list(t_list, J, symbolic_state, transition_value, events):
        t_list, symbolic_state, transition_value = utils.deep_copy(t_list, symbolic_state, transition_value)
        J = utils.deep_copy(J)[0] if J is not None else {}
        # t_list returns a set of symbolic states and tvs
        return_tuples = []
        if len(t_list) == 0:
            symbolic_state = update_derivation_tree(symbolic_state, "T-empty")
            return [(symbolic_state, {"type": TransitionValueType.END})]
        head = t_list.pop(0)
        # this is the case that event of the transition does not match
        # the currently active event we never fire the transition
        if head.get("e", "") != "" and head.get("e", "") not in events:
            processed_symbolic_state, processed_transition_value = TransitionRules.t_no_fire2(head, symbolic_state, transition_value)
            return_tuples.extend(TransitionListRules.execute_T_list(t_list, J, processed_symbolic_state, processed_transition_value, events))
            return return_tuples
        symbolic_state_from_transition, tansition_value_from_transition = TransitionRules.t_fire(head, symbolic_state, transition_value)
        # here is a check whether the transition fired to a state or junction
        if tansition_value_from_transition.get("d", "") in J.keys():
            for symbolic_state_from_junction, transition_value_from_junction in TransitionListRules.T_fire_J_N(tansition_value_from_transition.get("d", ""), J, symbolic_state_from_transition, tansition_value_from_transition, events):
                symbolic_state_from_junction, transition_value_from_junction = utils.deep_copy(symbolic_state_from_junction, transition_value_from_junction)
                symbolic_state_from_junction = update_derivation_tree(symbolic_state_from_junction, "T-fire")
                if len(t_list) == 0:
                    return_tuples.append(tuple((symbolic_state_from_junction, transition_value_from_junction)))
                else:
                    if transition_value_from_junction.get("type", "") == TransitionValueType.FIRE:
                        return_tuples.append(tuple((symbolic_state_from_junction, transition_value_from_junction)))
                    else:
                        return_tuples.extend(TransitionListRules.execute_T_list(t_list, J, symbolic_state_from_junction, transition_value_from_junction, events))
        else:
            symbolic_state_from_transition = update_derivation_tree(symbolic_state_from_transition, "T-fire")
            return_tuples.append(tuple((symbolic_state_from_transition, tansition_value_from_transition)))
        symbolic_state_from_T, transition_value_from_T = TransitionRules.t_no_fire(head, symbolic_state, transition_value)
        if len(t_list) > 0:
            symbolic_state_from_T = update_derivation_tree(symbolic_state_from_T, "T-no")
            return_tuples.extend(TransitionListRules.execute_T_list(t_list, J, symbolic_state_from_T, transition_value_from_T, events))
        else:
            symbolic_state_from_T = update_derivation_tree(symbolic_state_from_T, "T-no-Last")
            return_tuples.append(tuple((symbolic_state_from_T, transition_value_from_T)))
        return return_tuples

class StateDefinitionRules:

    @staticmethod
    @print_enter_exit_decorator
    def sd_no(state_definition, symbolic_state, transition_value, events):
        state_definition, symbolic_state, transition_value = utils.deep_copy(state_definition, symbolic_state, transition_value)
        symbolic_state = update_derivation_tree(symbolic_state, "sd-no")
        return [(state_definition, symbolic_state, transition_value)]

    @staticmethod
    @print_enter_exit_decorator
    def sd_init(state_definition, symbolic_state, transition_value, p, events):
        p = p if p is not None else ""
        symbolic_state, transition_value, state_definition, p = utils.deep_copy(symbolic_state, transition_value, state_definition, p)
        return_tuples = []
        entry_action = get_state_definition_action_string(state_definition, "en")
        # update delta and the derrivation tree
        symbolic_state = update_symbolic_environment(symbolic_state, entry_action)
        # execute the internal composition
        composition_type = get_state_definition_composition_type(state_definition)
        composition = state_definition.get(composition_type, {})
        # here one of the or-inits shall be called
        for composition_initialized, symbolic_state_composition, transition_value_composition in CompositeStateRules.composition_init(composition, state_definition.get("J", {}), symbolic_state, None, p, events):
            state_definition_fresh_copy, composition_initialized, symbolic_state_composition, transition_value_composition = utils.deep_copy(state_definition, composition_initialized, symbolic_state_composition, transition_value_composition)
            state_definition_fresh_copy[composition_type] = composition_initialized
            symbolic_state_composition = update_derivation_tree(symbolic_state_composition, "sd-init")
            return_tuples.append(tuple((state_definition_fresh_copy, symbolic_state_composition, transition_value)))
        # this is the case if there was no component
        if len(return_tuples) < 1:
            symbolic_state = update_derivation_tree(symbolic_state, "sd-init")
            return_tuples.append(tuple((state_definition, symbolic_state, transition_value)))
        return return_tuples

    @staticmethod
    @print_enter_exit_decorator
    def sd_exit(state_definition, symbolic_state, transition_value, events):
        return_tuples = []
        state_definition, symbolic_state, transition_value = utils.deep_copy(state_definition, symbolic_state, transition_value)
        exit_action = get_state_definition_action_string(state_definition, "ex")
        composition_type = get_state_definitioncomposition_type(state_definition)
        composition = state_definition.get(composition_type, {})

        for composition_after_exit, symbolic_state_composition, transition_value_composition in CompositeStateRules.composition_exit(composition, state_definition.get("J", {}), symbolic_state, transition_value, events):
            # _ss has the value from the execution of the internal component
            state_definition_fresh_copy, composition_after_exit, symbolic_state_composition, transition_value_composition = utils.deep_copy(state_definition, composition_after_exit, symbolic_state_composition, transition_value_composition)
            # update delta with exit action
            symbolic_state_composition = update_symbolic_environment(symbolic_state_composition, exit_action)
            symbolic_state_composition = update_derivation_tree(symbolic_state_composition, "sd-exit")
            state_definition_fresh_copy[composition_type] = composition_after_exit
            # in principle, there should be an NO-tv at the end of this rule,
            # however, we are returning the tv which was passed as an input
            return_tuples.append(tuple((state_definition_fresh_copy, symbolic_state_composition, transition_value)))
        # this is the case when there was no component
        if len(return_tuples) < 1:
            symbolic_state = update_symbolic_environment(symbolic_state, exit_action)
            symbolic_state = update_derivation_tree(symbolic_state, "sd-exit")
            return_tuples.append(tuple((state_definition, symbolic_state, transition_value)))
        return return_tuples

    @staticmethod
    @print_enter_exit_decorator
    def sd_fire(state_definition, symbolic_state, transition_value, events):
        return_tuples = []
        state_definition, symbolic_state, transition_value = utils.deep_copy(state_definition, symbolic_state, transition_value)
        exit_action = get_state_definition_action_string(state_definition, "ex")
        transition_value_actions = transition_value.get("a", [])
        transition_value["a"] = []
        symbolic_state = update_symbolic_environment_with_list(symbolic_state, transition_value_actions)
        composition_type = get_state_definition_composition_type(state_definition)
        _composition = state_definition.get(composition_type, {})
        for composition_after_exit, symbolic_state_composition, transition_value_composition in CompositeStateRules.composition_exit(_composition, [], symbolic_state, transition_value, events):
            state_definition_fresh_copy, composition_after_exit, symbolic_state_composition, transition_value_fresh_copy = utils.deep_copy(state_definition, composition_after_exit, symbolic_state_composition, transition_value)
            symbolic_state_composition = update_symbolic_environment(symbolic_state_composition, exit_action)
            symbolic_state_composition = update_derivation_tree(symbolic_state_composition, "sd-fire")
            state_definition_fresh_copy[composition_type] = composition_after_exit
            return_tuples.append((state_definition_fresh_copy, symbolic_state_composition, transition_value_fresh_copy))
        # this is the case when there was no component
        if len(return_tuples) < 1:
            symbolic_state = update_symbolic_environment(ss, exit_action)
            symbolic_state = update_derivation_tree(symbolic_state, "sd-fire")
            return_tuples.append(tuple((state_definition, symbolic_state, transition_value)))
        return return_tuples

    @staticmethod
    @print_enter_exit_decorator
    def sd_int_fire(state_definition, symbolic_state, transition_value, events):
        state_definition, symbolic_state, tv = utils.deep_copy(state_definition, symbolic_state, transition_value)
        transition_value_actions = transition_value.get("a", [])
        transition_value["a"] = []
        state_definition_action = get_state_definition_action_string(state_definition, "ex")

        symbolic_state = update_symbolic_environment_with_list(symbolic_state, transition_value_actions)
        symbolic_state = update_symbolic_environment(symbolic_state, state_definition_action)
        symbolic_state = update_derivation_tree(symbolic_state, "sd-init-fire")

        return [tuple((state_definition, symbolic_state, transition_value))]

    @staticmethod
    @print_enter_exit_decorator
    def execute_state_definition(state_definition, ss, tv, p = "", events=None):
        events = events if events is not None else []
        state_definition_fresh, symbolic_state_fresh, transition_value_fresh = utils.deep_copy(state_definition, ss, tv)
        return_tuples = []
        composition_type = get_state_definition_composition_type(state_definition_fresh)
        durationAction = get_state_definition_action_string(state_definition_fresh, "du")
        for symbolic_state_after_To, transition_value_after_To in TransitionListRules.execute_T_list(state_definition_fresh.get("To", []), state_definition_fresh.get("J", {}), symbolic_state_fresh, transition_value_fresh, events):
            symbolic_state_after_To, transition_value_after_To = utils.deep_copy(symbolic_state_after_To, transition_value_after_To)
            if transition_value_after_To.get("type", "") in [TransitionValueType.END, TransitionValueType.NO]:
                symbolic_state_after_To = update_symbolic_environment(symbolic_state_after_To, durationAction)
                for symbolic_state_after_Ti, transition_value_after_Ti in TransitionListRules.execute_T_list(state_definition_fresh.get("Ti", []), state_definition_fresh.get("J", {}), symbolic_state_after_To, transition_value_after_To, events):
                    state_definition_fresh_second, symbolic_state_after_Ti, transition_value_after_Ti = utils.deep_copy(state_definition_fresh, symbolic_state_after_Ti, transition_value_after_Ti)
                    inner_composition = state_definition_fresh_second.get(composition_type, {})
                    destinationPath = transition_value_after_Ti.get("d", "") if transition_value_after_Ti is not None else ""
                    for inner_composition_after_execution, symbolic_state_after_composition_execution, transition_value_after_composition_execution in CompositeStateRules.execute_composition(inner_composition, {}, symbolic_state_after_Ti, transition_value_after_Ti, destinationPath, events):
                        state_definition_fresh_third, inner_composition_after_execution, symbolic_state_after_composition_execution, transition_value_after_composition_execution = utils.deep_copy(state_definition_fresh_second, inner_composition_after_execution, symbolic_state_after_composition_execution, transition_value_after_composition_execution)
                        state_definition_fresh_third[composition_type] = inner_composition_after_execution
                        if transition_value_after_composition_execution.get("type", "") == TransitionValueType.FIRE:
                            return_tuples.extend(StateDefinitionRules.sd_int_fire(state_definition_fresh_third, symbolic_state_after_composition_execution, transition_value_after_composition_execution, events))
                        # in principle, this should be only NO-tv, but since in
                        # symbolic execution we do not have a no, then we treat it
                        # the same as end (this text concerns the if below)
                        elif transition_value_after_composition_execution.get("type", "") in [TransitionValueType.NO, TransitionValueType.END]:
                            return_tuples.extend(StateDefinitionRules.sd_no(state_definition_fresh_third, symbolic_state_after_composition_execution, transition_value_after_composition_execution, events))
                        elif transition_value_after_composition_execution.get("type", "") == TransitionValueType.END:
                            return_tuples.append(tuple((state_definition_fresh_third, symbolic_state_after_composition_execution, transition_value_after_composition_execution)))
            elif transition_value_after_To.get("type", "") == TransitionValueType.FIRE:
                return_tuples.extend(StateDefinitionRules.sd_fire(state_definition_fresh, symbolic_state_after_To, transition_value_after_To, events))
        return return_tuples

class OrCompositionRules:

    @staticmethod
    @print_enter_exit_decorator
    def or_ext_fire_out(or_composition, J, symbolic_state, transition_value, events):
        result_tuples = []
        or_composition_fresh_copy, symbolic_state_fresh_copy, transition_value_fresh_copy = utils.deep_copy(or_composition, symbolic_state, transition_value)
        transition_value_actions = transition_value_fresh_copy.get("a", [])
        transition_value_fresh_copy["a"] = []
        symbolic_state_fresh_copy = update_symbolic_environment_with_list(symbolic_state_fresh_copy, transition_value_actions)
        active_state_definition, not_needed = get_composition_child_state_definition_by_path(
            or_composition, or_composition.get("sa", ""))
        for active_state_definition_after_exit, symbolic_state_after_exit, transition_value_after_exit in StateDefinitionRules.sd_exit(active_state_definition, symbolic_state, transition_value, events):
            or_composition_fresh_copy, active_state_definition_after_exit, symbolic_state_after_exit, transition_value_after_exit = utils.deep_copy(or_composition, active_state_definition_after_exit, symbolic_state_after_exit, transition_value_after_exit)
            or_composition_fresh_copy["sa"] = ""
            or_composition_fresh_copy = set_composition_state_definition_by_path(or_composition_fresh_copy, active_state_definition_after_exit, or_composition.get("sa", ""))
            rule_name = "or-ext-fire-out-{0}".format(or_composition_fresh_copy.get("p", ""))
            symbolic_state_after_exit = update_derivation_tree(symbolic_state_after_exit, rule_name)
            result_tuples.append(tuple((or_composition_fresh_copy, symbolic_state_after_exit, transition_value)))
        return result_tuples

    @staticmethod
    @print_enter_exit_decorator
    def or_int_fire(or_composition, J, symbolic_state, transition_value, events):
        or_composition, symbolic_state, transition_value = utils.deep_copy(or_composition, symbolic_state, transition_value)
        result_tuples = []
        p = transition_value.get("d", "")

        state_definition_for_activation, state_definition_for_activation_path = get_composition_child_state_definition_by_path(
            or_composition, p)
        for active_state_definition_after_init, state_definition_after_init, transition_value_after_init in StateDefinitionRules.sd_init(state_definition_for_activation, symbolic_state, transition_value, p, events):
            or_composition_fresh_copy, active_state_definition_after_init, state_definition_after_init, transition_value_after_init = utils.deep_copy(or_composition, active_state_definition_after_init, state_definition_after_init, transition_value_after_init)
            or_composition_fresh_copy["sa"] = state_definition_for_activation_path
            or_composition_fresh_copy = set_composition_state_definition_by_path(or_composition_fresh_copy, active_state_definition_after_init, state_definition_for_activation_path)
            rule_name = "or-int-fire-{0}".format(or_composition_fresh_copy.get("p", ""))
            state_definition_after_init = update_derivation_tree(state_definition_after_init, rule_name)
            result_tuples.append(tuple((or_composition_fresh_copy, state_definition_after_init, {"type": TransitionValueType.NO})))
        return result_tuples

    @staticmethod
    @print_enter_exit_decorator
    def or_fire(or_composition, J, symbolic_state, transition_value, events):
        result_tuples = []
        or_composition, J, symbolic_state, transition_value = utils.deep_copy(or_composition, J, symbolic_state, transition_value)
        or_composition["sa"] = ""
        rule_name = "or-fire-{0}".format(or_composition.get("p", ""))
        symbolic_state = update_derivation_tree(symbolic_state, rule_name)
        result_tuples.append(tuple((or_composition, symbolic_state, transition_value)))
        return result_tuples

    @staticmethod
    @print_enter_exit_decorator
    def or_init_no_state(or_composition, J, symbolic_state, transition_value, events):
        or_composition, symbolic_state, transition_value = utils.deep_copy(or_composition, symbolic_state, transition_value)
        # only thing that we do is that we are adding the rule in the dtree
        rule_name = "or-init-no-state-{0}".format(or_composition.get("p", ""))
        symbolic_state = update_derivation_tree(symbolic_state, rule_name)
        return [tuple((or_composition, symbolic_state, transition_value))]

    @staticmethod
    @print_enter_exit_decorator
    def or_init_empty_path(or_composition, J, symbolic_state,  transition_value, events):
        result_tuples = []
        or_composition, symbolic_state,  transition_value = utils.deep_copy(or_composition, symbolic_state,  transition_value)
        for symbolic_state_after_T, transition_value_after_T in TransitionListRules.execute_T_list(or_composition.get("T", []), J, symbolic_state,  transition_value, events):
            if transition_value_after_T.get("type", "") == TransitionValueType.FIRE:
                transition_value_actions = transition_value_after_T.get("a", [])
                # we will use the a, so it will be reset
                transition_value_after_T["a"] = []
                # the assumption is that we always initialize the direct child
                state_definition_for_activation_path = transition_value_after_T.get("d", "")
                state_definition_for_activation = get_composition_sub_state_definition_by_path(
                    or_composition, state_definition_for_activation_path)
                for state_definition_after_init, symbolic_state_after_init, transition_value_after_init in StateDefinitionRules.sd_init(state_definition_for_activation, symbolic_state_after_T, None, "", events):
                    or_composition_fresh_copy, state_definition_after_init, symbolic_state_after_init, transition_value_after_init = utils.deep_copy(or_composition, state_definition_after_init, symbolic_state_after_init, transition_value_after_init)
                    or_composition_fresh_copy["sa"] = state_definition_for_activation_path
                    or_composition_fresh_copy = set_composition_state_definition_by_path(
                        or_composition_fresh_copy, state_definition_after_init, state_definition_for_activation_path)
                    symbolic_state_after_init = update_symbolic_environment_with_list(symbolic_state_after_init, transition_value_actions)
                    rule_name = "or-init-empty-path-{0}".format(or_composition_fresh_copy.get("p", ""))
                    symbolic_state_after_init = update_derivation_tree(symbolic_state_after_init, rule_name)
                    result_tuples.append(tuple((or_composition_fresh_copy, symbolic_state_after_init,  transition_value)))
        return result_tuples

    @staticmethod
    @print_enter_exit_decorator
    def or_init(or_composition, J, symbolic_state, transition_value, p, events):
        result_tuples = []
        p = p if p is not None else ""
        or_composition, J, symbolic_state, transition_value = utils.deep_copy(or_composition, J, symbolic_state, transition_value)
        state_definition_for_initialization, state_definition_for_initialization_path = get_composition_child_state_definition_by_path(
            or_composition, p)
        # if this the state that needed to be activated with the propagating p,
        # then set p = ""
        if state_definition_for_initialization_path == p:
            p = ""
        for state_definition_after_init, symbolic_state_after_init, transition_value_after_init in StateDefinitionRules.sd_init(state_definition_for_initialization, symbolic_state, transition_value, p, events):
            or_composition_fresh_copy, state_definition_after_init, symbolic_state_after_init, transition_value_after_init = utils.deep_copy(or_composition, state_definition_after_init, symbolic_state_after_init, transition_value_after_init)
            or_composition_fresh_copy["sa"] = state_definition_for_initialization_path
            or_composition_fresh_copy = set_composition_state_definition_by_path(or_composition_fresh_copy, state_definition_after_init, state_definition_for_initialization_path)
            rule_name = "or-init-{0}".format(or_composition_fresh_copy.get("p", ""))
            symbolic_state_after_init = update_derivation_tree(symbolic_state_after_init, rule_name)
            result_tuples.append(tuple((or_composition_fresh_copy, symbolic_state_after_init, transition_value)))
        return result_tuples

    @staticmethod
    @print_enter_exit_decorator
    def or_exit(or_composition, J, symbolic_state, transition_value, events):
        result_tuples = []
        or_composition, J, symbolic_state, transition_value = utils.deep_copy(or_composition, J, symbolic_state, transition_value)
        active_state_definition_path = or_composition.get("sa", "")
        if(active_state_definition_path == ""):
            result_tuples.append(tuple((or_composition, symbolic_state, {"type": TransitionValueType.END})))
            return result_tuples
        active_state_definition = get_composition_sub_state_definition_by_path(
            or_composition, active_state_definition_path)
        for state_definition_after_exit, symbolic_state_after_exit, transition_value_after_exit in StateDefinitionRules.sd_exit(active_state_definition, symbolic_state, transition_value, events):
            or_composition_fresh_copy, state_definition_after_exit, symbolic_state_after_exit, transition_value_after_exit = utils.deep_copy(or_composition, state_definition_after_exit, symbolic_state_after_exit, transition_value_after_exit)
            or_composition_fresh_copy["sa"] = ""
            or_composition_fresh_copy = set_composition_state_definition_by_path(or_composition_fresh_copy, state_definition_after_exit, active_state_definition_path)
            rule_name = "or-exit-{0}".format(or_composition_fresh_copy.get("p", ""))
            symbolic_state_after_exit = update_derivation_tree(symbolic_state_after_exit, rule_name)
            result_tuples.append(tuple((or_composition_fresh_copy, symbolic_state_after_exit, transition_value_after_exit)))
        return result_tuples

    @staticmethod
    @print_enter_exit_decorator
    def or_no(or_composition, J, symbolic_state, transition_value, events):
        return_tuples = []
        or_composition, symbolic_state, transition_value = utils.deep_copy(or_composition, symbolic_state, transition_value)
        rule_name = "or-no-{0}".format(or_composition.get("p", ""))
        symbolic_state = update_derivation_tree(symbolic_state, rule_name)
        return_tuples.append(tuple((or_composition, symbolic_state, transition_value)))
        return return_tuples

    @staticmethod
    @print_enter_exit_decorator
    def initialize_or(or_composition, J, symbolic_state, transition_value, p, events):
        result_tuples = []
        or_composition, J, symbolic_state, transition_value, p = utils.deep_copy(or_composition, J, symbolic_state, transition_value, p)
        # if the C element is empty
        if or_composition is None or or_composition == {}:
            return [tuple((or_composition, symbolic_state, transition_value))]
        if p != "":
            result_tuples.extend(OrCompositionRules.or_init(or_composition, J, symbolic_state, transition_value, p, events))
        else:
            if (len(or_composition.get("SD", [])) > 0):
                result_tuples.extend(OrCompositionRules.or_init_empty_path(or_composition, J, symbolic_state, transition_value, events))
            else:
                result_tuples.extend(OrCompositionRules.or_init_no_state(or_composition, J, symbolic_state, transition_value, events))
        return result_tuples

    @staticmethod
    @print_enter_exit_decorator
    def execute_or(or_composition, J={},symbolic_state=generate_default_ss(), transition_value=None, p = "", events=None):
        # or = (sa, p, T, SD)
        # if the composition object is empty, do not process.
        if or_composition is not None and or_composition == {}:
            return [tuple((or_composition,symbolic_state, transition_value))]
        # prepare data for execution
        events = events if events is not None else []
        result_tuples = []
        or_composition, J,symbolic_state, transition_value = utils.deep_copy(or_composition, J,symbolic_state, transition_value)
        active_state_definition_path = or_composition.get("sa", "")
        # prepare data for execution end

        # if there is no active state, then it must be one of the initializations
        if active_state_definition_path == "":
            result_tuples.extend(OrCompositionRules.initialize_or(or_composition, J,symbolic_state, transition_value, p, events))
        else:
            # just to make sure that transition_value is not None, so it does not raise
            # an exception, although in principle it should never happen
            if transition_value is None:
                raise TransitionValueException('The transition value is missing.')
            transition_value = transition_value if transition_value is not None else {}
            if transition_value.get("type", "") == TransitionValueType.FIRE:
                destinationPath = transition_value.get("d", "")
                if destinationPath not in get_or_composition_children_path(or_composition):
                    result_tuples.extend(OrCompositionRules.or_ext_fire_out(or_composition, J,symbolic_state, transition_value, events))
                else:
                    raise Exception('Error', 'ID missmatch. The component not found where expected.')
                    # this basically means do nothing
                    return [tuple((or_composition,symbolic_state, transition_value))]

            # here we should treat or-no, or-int-fire, or-fire
            elif transition_value.get("type", "") in [TransitionValueType.END, TransitionValueType.NO]:
                # we fetch the active_state_definition from the list
                active_state_definition, active_state_definition_path = get_composition_child_state_definition_by_path(
                    or_composition, active_state_definition_path)
                # now we need to execute the state_definition
                for active_state_definition_after_execution, symbolic_state_after_execution, transition_value_after_execution in StateDefinitionRules.execute_state_definition(active_state_definition,symbolic_state, transition_value, "", events):
                    or_composition_fresh_copy, active_state_definition_after_execution, symbolic_state_after_execution, transition_value_after_execution = utils.deep_copy(or_composition, active_state_definition_after_execution, symbolic_state_after_execution, transition_value_after_execution)
                    or_composition_fresh_copy = set_composition_state_definition_by_path(or_composition_fresh_copy, active_state_definition_after_execution, active_state_definition_path)
                    # here again should be [TransitionValueType.NO, TransitionValueType.END] because there is no TransitionValueType.NO
                    # if transition_value_after_execution.get("type", "") == TransitionValueType.NO:
                    if transition_value_after_execution.get("type", "") in [TransitionValueType.NO, TransitionValueType.END]:
                        result_tuples.extend(OrCompositionRules.or_no(or_composition_fresh_copy, J, symbolic_state_after_execution, transition_value_after_execution, events))
                    elif transition_value_after_execution.get("type", "") == TransitionValueType.FIRE:
                        # the other assumption would be that transition_value_after_execution.get("d", "") is not a prefix of
                        # the current component
                        if transition_value_after_execution.get("d", "") in get_or_composition_children_path(or_composition):
                            result_tuples.extend(OrCompositionRules.or_int_fire(or_composition_fresh_copy, J, symbolic_state_after_execution, transition_value_after_execution, events))
                        else:
                            result_tuples.extend(OrCompositionRules.or_fire(or_composition_fresh_copy, J, symbolic_state_after_execution, transition_value_after_execution, events))
            else:
                raise TransitionValueException("The transition value does not match the expected value.")
        return result_tuples

class AndCompositionRules:

    @staticmethod
    @print_enter_exit_decorator
    def and_rule(and_composition, J, symbolic_state, transition_value, events):
        and_composition_fresh_copy, symbolic_state_fresh_copy, transition_value_fresh_copy = deep_copy(and_composition, symbolic_state, transition_value)
        # the first state definition is executed with the symbolic_state, and transition_value which are passed as
        # an input to the and_rule

        # startig point of execution is the initial AND composition, and the symbolic state and the trasition value that were passed as arguments.
        execution_points = [tuple(and_composition_fresh_copy, symbolic_state_fresh_copy, transition_value_fresh_copy)]
        for state_definition_wrapper in and_composition.get("SD", []):
            state_definitionName = state_definition_wrapper.keys()[0]
            state_definition = state_definition_wrapper[state_definitionName]
            temporary_point_of_execution = []
            # this are execution points generated after executing each of the state definitions
            for intermediateExecutionPoint in AndCompositionRules.execute_state_definition_within_and_composition(state_definition, execution_points, "", events):
                and_composition_after_execution, state_definition_after_execution, symbolic_state_after_execution, transition_value_after_execution = deep_copy(and_composition_fresh_copy, intermediateExecutionPoint[0], intermediateExecutionPoint[1], intermediateExecutionPoint[2])
                and_composition_after_execution[state_definitionName] = state_definition_after_execution
                temporary_point_of_execution.append(tuple(and_composition_after_execution, symbolic_state_after_execution, transition_value_fresh_copy))
            # here we assign newly generated temporary execution points to the global execution points
            execution_points = temporary_point_of_execution
        # after all of the inner states have been processed, the resulting execution_points is returned as the overall result from this function
        return execution_points

    @staticmethod
    @print_enter_exit_decorator
    def and_init(and_composition, J, symbolic_state, tv, p = "", events=None):
        events = events if events is not None else []
        and_composition_fresh_copy, symbolic_state_fresh_copy, transition_value_fresh_copy, _p = utils.deep_copy(and_composition, symbolic_state, tv, p)
        for stae_definition_wrapper in and_composition.get("SD", []):
            state_definition_name = stae_definition_wrapper.keys()[0]
            state_definition = stae_definition_wrapper[state_definition_name]
            # this loop should execute only once
            for state_definition_after_init, symbolic_state_fresh_copy, transition_value_fresh_copy in StateDefinitionRules.sd_init(state_definition, symbolic_state_fresh_copy, transition_value_fresh_copy, p, events):
                and_composition_fresh_copy = set_composition_state_definition_by_path(and_composition_fresh_copy, state_definition_after_init, state_definition_name)
        and_composition_fresh_copy["b"] = "True"
        return[tuple((and_composition_fresh_copy, symbolic_state_fresh_copy, transition_value_fresh_copy))]

    @staticmethod
    @print_enter_exit_decorator
    def and_exit(and_composition, J, symbolic_state, transition_value, events):
        and_composition_fresh_copy, symblic_state_fresh_copy, transition_value_fresh_copy = utils.deep_copy(and_composition, symbolic_state, transition_value)
        for state_definition_wrapper in and_composition.get("SD", []):
            sd_name = state_definition_wrapper.keys()[0]
            state_definitino_after_exit = state_definition_wrapper[sd_name]
            # this loop should execute only once
            for state_definitino_after_exit, symblic_state_fresh_copy, transition_value_fresh_copy in StateDefinitionRules.sd_exit(state_definitino_after_exit, symblic_state_fresh_copy, transition_value_fresh_copy, "", events):
                and_composition_fresh_copy = set_composition_state_definition_by_path(and_composition_fresh_copy, state_definitino_after_exit, sd_name)
        and_composition_fresh_copy["b"] = "False"
        return[tuple((and_composition_fresh_copy, symblic_state_fresh_copy, transition_value_fresh_copy))]

    @staticmethod
    @print_enter_exit_decorator
    def execute_and(and_composition, J={}, symbolic_state=generate_default_ss(), transition_value=None, p = "", events=None):
        events = events if events is not None else []
        if and_composition.get("b", "") == "True":
            return AndCompositionRules.and_rule(and_composition, J, symbolic_state, transition_value, events)
        else:
            return AndCompositionRules.and_init(and_composition, J, symbolic_state, transition_value, events)


    @staticmethod
    @print_enter_exit_decorator
    def execute_state_definition_within_and_composition(state_definition, starting_point_of_execution, path, events):
        result = []
        for point_of_execution in starting_point_of_execution:
            for state_definition_after_execute, symbolic_state_after_execute, transition_value_after_execute in StateDefinitionRules.execute_state_definition(state_definition, point_of_execution[1], point_of_execution[2], path, events):
                state_definition_after_execute_fresh_copy, symbolic_state_after_execute_fresh_copy, transition_value_after_execute_fresh_copy = deep_copy(state_definition_after_execute, symbolic_state_after_execute, transition_value_after_execute)
                result.append(tuple(state_definition_after_execute_fresh_copy, symbolic_state_after_execute_fresh_copy, transition_value_after_execute_fresh_copy))
        return result

class CompositeStateRules:

    @staticmethod
    @print_enter_exit_decorator
    def composition_exit(composition, J, symbolic_state, transition_value, events):
        # this means that and_exit is called only for valid And composition. In
        # case of a valid OR composition or an empty OR composition {}, then or_exit
        # is called
        if len(composition.keys()) == 2:
            return AndCompositionRules.and_exit(composition, J, symbolic_state, transition_value, events)
        else:
            return OrCompositionRules.or_exit(composition, J, symbolic_state, transition_value, events)

    @staticmethod
    @print_enter_exit_decorator
    def composition_init(composition, J, symbolic_state, transition_value, p, events):
        # this means that and_init is called only for valid And composition. In
        # case of a valid OR composition or empty composition {}, then initalize_or
        # is called
        if len(composition.keys()) == 2:
            return AndCompositionRules.and_init(composition, J, symbolic_state, transition_value, events)
        else:
            return OrCompositionRules.initialize_or(composition, J, symbolic_state, transition_value, p, events)

    @staticmethod
    @print_enter_exit_decorator
    def execute_composition(composition, J={}, symbolic_state=generate_default_ss(), transition_value=None, p = "", events=None):
        # this means that executeAnd is called only for valid And composition. In
        # case of a valid OR composition or empty composition {}, then executeOr
        # is called
        events = events if events is not None else []
        if len(composition.keys()) == 2:
            return AndCompositionRules.execute_and(composition, J, symbolic_state, transition_value, events)
        else:
            return OrCompositionRules.execute_or(composition, J, symbolic_state, transition_value, p, events)

    @staticmethod
    @print_enter_exit_decorator
    def execute_state_definition_within_and_composition(state_definition, starting_point_of_execution, path, events):
        result = []
        for point_of_execution in starting_point_of_execution:
            for state_definition_after_execute, symbolic_state_after_execute, transition_value_after_execute in StateDefinitionRules.execute_state_definition(state_definition, point_of_execution[1], point_of_execution[2], path, events):
                state_definition_after_execute_fresh_copy, symbolic_state_after_execute_fresh_copy, transition_value_after_execute_fresh_copy = deep_copy(state_definition_after_execute, symbolic_state_after_execute, transition_value_after_execute)
                result.append(tuple(state_definition_after_execute_fresh_copy, symbolic_state_after_execute_fresh_copy, transition_value_after_execute_fresh_copy))
        return result
