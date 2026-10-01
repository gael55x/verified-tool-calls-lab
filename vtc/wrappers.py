"""Algorithm 1 literal control flow and explicitly separated adaptations."""
from .model import (AMBIGUOUS, FAILURE, FALSE, SUCCESS, TRUE, UNKNOWN,
                    digest, full_predicate, paper_predicate)

MODES = ("retry_only", "verify_only", "paper_literal", "engineering")


def paper_key(action):
    # Section 4.5. Captured timestamp bucket stays fixed across this call's retries.
    return digest([action.agent_id, action.task, action.payload, action.timestamp_bucket])


def engineering_key(action):
    # Labeled change: durable caller logical operation ID, no time-based expiry.
    return digest([action.agent_id, action.task, action.payload, action.operation_id])


def verify(port, action, complete=False):
    view = port.read(action)
    outcome = UNKNOWN if view is None else (
        TRUE if (full_predicate if complete else paper_predicate)(action, view) else FALSE)
    port.note("verification", predicate="full" if complete else "paper", outcome=outcome)
    return outcome


def paper_literal(port, action, n=1):
    """PDF Algorithm 1, p7. N counts iterations, not just execute retries."""
    key = paper_key(action)
    port.execute(action, key)
    for i in range(1, n + 1):
        response = port.response()
        if response == SUCCESS:
            return True
        if response == FAILURE:
            return False
        if response == AMBIGUOUS:
            port.wait(i)
            result = verify(port, action)
            if result == TRUE:
                return True
            elif result == UNKNOWN:
                continue
            elif result == FALSE:
                port.execute(action, key)
    return False


def retry_only(port, action):
    port.execute(action)
    if port.response() == SUCCESS:
        return True
    port.execute(action)
    return port.response() == SUCCESS


def verify_only(port, action):
    port.execute(action)
    response = port.response()
    if response == SUCCESS:
        return True
    if response == FAILURE:
        return False
    port.wait(1)
    return verify(port, action) == TRUE


def engineering(port, action, retries=1, polls=3):
    """Engineering v2: reserve verification capacity before executing a retry.

    A true read can still precede an outstanding non-idempotent commit. This
    algorithm cannot undo duplicates or turn an inconclusive read into proof.
    """
    if polls < 1 or retries < 0:
        raise ValueError("engineering requires positive polls and nonnegative retries")
    key = engineering_key(action)
    port.execute(action, key)
    used_retries = 0
    response = port.response()
    wait_before_read = response == AMBIGUOUS
    for poll in range(polls):
        if response == FAILURE:
            return False
        if wait_before_read:
            port.wait(1)
        result = verify(port, action, complete=True)
        if result == TRUE:
            return True
        if result == FALSE and used_retries < retries and poll + 1 < polls:
            port.execute(action, key)
            used_retries += 1
            response = port.response()  # deliberately absent in literal mode
            wait_before_read = response == AMBIGUOUS
        else:
            if result == FALSE and used_retries < retries:
                port.note("retry_withheld", reason="no_post_retry_verification_capacity")
            wait_before_read = True
    return False


FUNCTIONS = dict(retry_only=retry_only, verify_only=verify_only,
                 paper_literal=paper_literal, engineering=engineering)


def run_wrapper(mode, port, action):
    result = FUNCTIONS[mode](port, action)
    port.note("wrapper_return", mode=mode, success=result)
    return result
