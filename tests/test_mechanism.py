import ast
from dataclasses import replace
from pathlib import Path
import unittest

from vtc.model import (AMBIGUOUS, FAILURE, SUCCESS, Action, Environment, Fault,
                       TASKS, duplicate_count, fixture, full_predicate, main_tape,
                       paper_predicate, stress_tape)
from vtc.wrappers import (MODES, engineering, engineering_key, paper_key, paper_literal,
                          run_wrapper)


def case(mode, pattern, task='activate_customer', supported=True):
    action = fixture(task, 42)
    env = Environment(stress_tape(pattern), supported)
    reported = run_wrapper(mode, env.port(), action)
    at_return = env.truth_snapshot(action)
    env.settle()
    return reported, at_return, env.truth_snapshot(action), env, action


class MechanismTests(unittest.TestCase):
    def test_review_probe_final_false_has_no_unverifiable_retry(self):
        for task in TASKS:
            for polls, first in ((3, Fault('none', AMBIGUOUS, unknown_until=3)),
                                 (1, Fault('none', AMBIGUOUS))):
                with self.subTest(task=task, polls=polls):
                    action=fixture(task,42); env=Environment([first,Fault()],True)
                    reported=engineering(env.port(),action,polls=polls)
                    self.assertFalse(reported)
                    self.assertEqual((env.calls,env.reads),(1,polls))
                    self.assertEqual(env.truth_snapshot(action),{})
                    self.assertTrue(any(e['kind']=='retry_withheld' for e in env.trace))

    def test_penultimate_false_reserves_post_retry_verification(self):
        for task in TASKS:
            action=fixture(task,42)
            env=Environment([Fault('none',AMBIGUOUS,unknown_until=2),Fault()],True)
            reported=engineering(env.port(),action,polls=3)
            self.assertTrue(reported and full_predicate(action,env.truth_snapshot(action)))
            self.assertEqual((env.calls,env.reads),(2,3))
            dispatch=[i for i,e in enumerate(env.trace) if e['kind']=='dispatch']
            self.assertTrue(any(e['kind']=='verification' and e['outcome']=='TRUE'
                                for e in env.trace[dispatch[-1]+1:]))

    def test_invalid_engineering_budget_rejected_before_dispatch(self):
        for budget in ({'polls':0},{'polls':-1},{'retries':-1}):
            env=Environment([Fault()],True); action=fixture('record_invoice',42)
            with self.assertRaises(ValueError): engineering(env.port(),action,**budget)
            self.assertEqual((env.calls,env.reads,env.writes),(0,0,0))

    def test_clean_all_methods_and_tasks(self):
        for task in TASKS:
            for mode in MODES:
                for supported in (False, True):
                    with self.subTest(task=task, mode=mode, supported=supported):
                        reported, _, final, env, action = case(mode, 'clean', task, supported)
                        self.assertTrue(reported and full_predicate(action, final))
                        self.assertEqual(env.calls, 1)

    def test_literal_false_success_without_effect(self):
        reported, _, final, env, _ = case('paper_literal', 'false_success')
        self.assertTrue(reported)
        self.assertEqual(final, {})
        self.assertEqual(env.reads, 0)

    def test_literal_partial_success_is_false_completion(self):
        for task in TASKS:
            reported, _, final, _, action = case('paper_literal', 'partial_success', task)
            self.assertTrue(reported and paper_predicate(action, final))
            self.assertFalse(full_predicate(action, final))

    def test_incomplete_paper_predicate_accepts_partial_ambiguous(self):
        for task in TASKS:
            reported, _, final, env, action = case('paper_literal', 'partial_ambiguous', task)
            self.assertTrue(reported)
            self.assertFalse(full_predicate(action, final))
            self.assertEqual(env.calls, 1)

    def test_literal_last_retry_response_not_inspected(self):
        reported, _, final, env, action = case('paper_literal', 'no_effect_timeout')
        self.assertFalse(reported)
        self.assertTrue(full_predicate(action, final))
        self.assertEqual(env.calls, 2)
        self.assertEqual(sum(e['kind']=='response_inspected' for e in env.trace), 1)

    def test_n_is_iteration_not_retry_budget(self):
        reported, _, final, env, action = case('paper_literal', 'delayed_unknown')
        self.assertFalse(reported)
        self.assertTrue(full_predicate(action, final))
        self.assertEqual((env.calls, env.reads), (1,1))

    def test_definitive_failure_shortcircuits_verification(self):
        for mode in ('paper_literal','engineering','verify_only'):
            reported, _, final, env, _ = case(mode, 'definitive_conflict')
            self.assertFalse(reported)
            self.assertEqual((env.calls,env.reads), (1,0))
            self.assertEqual(final,{})

    def test_baseline_sensitivity_counts_committed_duplicates(self):
        for task in TASKS:
            reported, _, final, env, action = case('retry_only','commit_timeout',task,False)
            self.assertTrue(reported)
            self.assertEqual(duplicate_count(action,final),1)
            self.assertEqual(env.writes,6)

    def test_verified_commit_timeout_does_not_retry(self):
        for mode in ('paper_literal','verify_only','engineering'):
            reported, _, final, env, action = case(mode,'commit_timeout',supported=False)
            self.assertTrue(reported and full_predicate(action,final))
            self.assertEqual(env.calls,1)

    def test_delayed_commit_is_pending_key_reservation(self):
        for task in TASKS:
            _, _, final, env, action = case('paper_literal','delayed_commit',task,True)
            self.assertEqual(env.calls,2)
            self.assertEqual(duplicate_count(action,final),0)
            self.assertTrue(any(e['kind']=='dedupe_pending' for e in env.trace))

    def test_unsupported_late_commit_defeats_return_time_verification(self):
        for task in TASKS:
            reported, at_return, final, _, action = case('engineering','delayed_commit',task,False)
            self.assertTrue(reported and full_predicate(action,at_return))
            self.assertEqual(duplicate_count(action,final),1)
            self.assertFalse(full_predicate(action,final))

    def test_engineering_checks_success_and_final_retry(self):
        for task in TASKS:
            for pattern in ('false_success','no_effect_timeout','partial_success'):
                reported, _, final, env, action = case('engineering',pattern,task,True)
                self.assertTrue(reported and full_predicate(action,final))
                self.assertEqual(env.calls,2)
                self.assertEqual(sum(e['kind']=='response_inspected' for e in env.trace),2)

    def test_partial_invoice_repair_needs_stage_receipts(self):
        for supported in (False,True):
            reported, _, final, _, action = case('engineering','partial_success','record_invoice',supported)
            self.assertEqual(reported,supported)
            self.assertEqual(duplicate_count(action,final),0 if supported else 1)

    def test_unknown_polling_is_bounded_without_blind_retry(self):
        reported, _, final, env, _ = case('engineering','unknown_forever')
        self.assertFalse(reported)
        self.assertEqual(final,{})
        self.assertEqual((env.calls,env.reads,env.tick),(1,3,8))

    def test_effect_after_budget_causes_false_failure(self):
        reported, at_return, final, env, action = case('engineering','commit_after_budget')
        self.assertFalse(reported or full_predicate(action,at_return))
        self.assertTrue(full_predicate(action,final))
        self.assertEqual(env.reads,3)

    def test_reads_are_copies_and_do_not_commit(self):
        action=fixture('activate_customer',42); env=Environment([Fault()],True)
        env.execute(action); before=env.writes
        view=env.port().read(action);view['customer']['status']='CORRUPTED'
        self.assertEqual(env.writes,before)
        self.assertEqual(env.truth_snapshot(action)['customer']['status'],'ACTIVE')

    def test_wrapper_capability_surface_has_no_truth_api(self):
        port=Environment([Fault()],True).port()
        self.assertFalse(hasattr(port,'truth_snapshot'))
        tree=ast.parse(Path('vtc/wrappers.py').read_text())
        attrs={n.attr for n in ast.walk(tree) if isinstance(n,ast.Attribute)}
        self.assertFalse({'truth_snapshot','_truth','settle','trace'} & attrs)

    def test_stable_key_across_retry(self):
        _, _, _, env, _=case('paper_literal','no_effect_timeout')
        keys=[e['key'] for e in env.trace if e['kind']=='dispatch']
        self.assertEqual(keys[0],keys[1])

    def test_timestamp_bucket_drift_on_restart_duplicates(self):
        a=fixture('record_invoice',42); env=Environment([Fault(),Fault()],True)
        env.execute(a,paper_key(a))
        restarted=replace(a,timestamp_bucket=1)
        env.execute(restarted,paper_key(restarted))
        self.assertEqual(duplicate_count(a,env.truth_snapshot(a)),1)
        self.assertEqual(engineering_key(a),engineering_key(restarted))

    def test_payload_key_collision_between_explicit_operations(self):
        a=fixture('record_invoice',42); b=replace(a,operation_id='explicit-second-request')
        self.assertEqual(paper_key(a),paper_key(b))
        self.assertNotEqual(engineering_key(a),engineering_key(b))
        env=Environment([Fault(),Fault()],True)
        env.execute(a,paper_key(a));env.execute(b,paper_key(b))
        self.assertFalse(full_predicate(b,env.truth_snapshot(b)))
        # Domain identity here deliberately allows two explicit operations with
        # identical arguments. Real invoice APIs must define their own identity.

    def test_different_legitimate_invoices_same_customer_not_deduped(self):
        a=fixture('record_invoice',42)
        b=replace(a,payload=dict(a.payload,invoice_id='synthetic-second-invoice'),
                  operation_id='second-invoice')
        env=Environment([Fault(),Fault()],True)
        env.execute(a,paper_key(a));env.execute(b,paper_key(b))
        self.assertTrue(full_predicate(a,env.truth_snapshot(a)))
        self.assertTrue(full_predicate(b,env.truth_snapshot(b)))

    def test_paired_tape_determinism_and_attempt_index(self):
        for seed in range(42,67):
            self.assertEqual(main_tape(seed,'high'),main_tape(seed,'high'))
            self.assertEqual(len(main_tape(seed,'high')[0]),2)

    def test_unexpected_call_overrun_is_harness_error(self):
        env=Environment([Fault()],True);action=fixture('record_invoice',42)
        env.execute(action)
        with self.assertRaises(RuntimeError): env.execute(action)


if __name__=='__main__': unittest.main()
