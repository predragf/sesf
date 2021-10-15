import json
import sys
import utils
from custom_exceptions import TransitionValueException
from custom_enums import TransitionValueType
from ssoshelpers import *
from ssos import CompositeStateRules

class SESF:

    @staticmethod
    def load_program(program_location):
        try:
            program_file = utils.open_file(program_location)
            program = json.load(program_file)
        except Exception:
            print("Problems opening file. Script will run on empty stateflow program!")
            program = dict()
        finally:
            if program_file is not None and not program_file.closed:
                program_file.close()
        return program

    @staticmethod
    def execute_symbolically_recursive(program, symbolic_state, transition_value=None, explored_executions=None):
        transition_value = transition_value if transition_value is not None else {}
        explored_executions = explored_executions if explored_executions is not None else set()
        symbolic_state_fresh_copy, transition_value_fresh_copy, explored_executions_fresh_copy = utils.deep_copy(symbolic_state, transition_value, explored_executions)
        # get the events. In case no events, we create a list of
        # empty event such that the loop can loop
        events = get_all_events(program)
        # we add the current configuration into the explored executions
        # represented through the hash of the currently active states
        current_program_active_states_string = "".join(get_or_composition_active_states_paths(program))
        # explored_executions.add(current_program_active_states_string)
        transition_relation = []
        # now we execute the composition without events - no events allowed
        # on the initialization edges
        for event in events:
            explored_executions.add("{0}{1}".format(current_program_active_states_string, event))
            orExecutions = CompositeStateRules.execute_composition(program, program.get("J", {}), symbolic_state_fresh_copy, transition_value_fresh_copy, "", [event])
            # return orExecutions, set()
            # this will not execute
            for modified_program, symbolic_state_after_execution, transition_value_after_execution in orExecutions:
                modified_program, symbolic_state_after_execution, transition_value_after_execution = utils.deep_copy(modified_program, symbolic_state_after_execution, transition_value_after_execution)
                modified_program_active_states_string = "".join(get_or_composition_active_states_paths(modified_program))
                transition = {"source": "{0}".format(current_program_active_states_string),
                              "destination": "{0}".format(modified_program_active_states_string),
                              "delta'": symbolic_state_after_execution.get("delta", []),
                              "derivation-tree": symbolic_state_after_execution.get("derivation-tree"),
                              "tv": transition_value_after_execution,
                              "pc": symbolic_state_after_execution.get("pc", {}),
                              "event": event}
                transition_relation.append(transition)
                if "{0}{1}".format(modified_program_active_states_string, event) not in explored_executions:
                    transition_relation_one_step, explored_executions_fresh_copy = SESF.execute_symbolically_recursive(
                        modified_program, symbolic_state, {"type": TransitionValueType.END}, explored_executions)
                    # append new transition
                    transition_relation.extend(transition_relation_one_step)
                    # update the set of explored executions
                    explored_executions.update(explored_executions_fresh_copy)
        return transition_relation, explored_executions

    @staticmethod
    def execute_symbolically(program_location):        
        stateflow_program = SESF.load_program(program_location)
        complete_transition_relation = SESF.execute_symbolically_recursive(stateflow_program.get("Or", {}), generate_default_ss(), None)[0]
        return complete_transition_relation
