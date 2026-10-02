# Retry contract check

Target: built-in fixture (broken) with client examples/ticket_client.py:create_ticket

Exit code: 1 (violation observed)

| scenario | status | reported success | final completion | effects | reason |
|---|---|---|---|---|---|
| clean | pass | [True] | True | 1 | one effect and a reported success |
| lost_reply | violation | [True] | True | 2 | 2 side effects for one operation id |
| late_commit | violation | [True] | True | 2 | 2 side effects for one operation id |
| concurrent | violation | [True, True] | True | 2 | 2 side effects for one operation id |
| restart | violation | [True, True] | True | 2 | 2 side effects for one operation id |

## clean

- harness events: adapter:create > adapter:enter > invoke:1 > invoke:1:returned:true > settle > observe > adapter:exit
- fault events: server:start > request:received > effect:committed
- action: None for this scenario.

## lost_reply

- harness events: adapter:create > adapter:enter > invoke:1 > invoke:1:returned:true > settle > observe > adapter:exit
- fault events: server:start > request:received > effect:committed > lost_reply:dropped_after_commit > request:received > effect:committed
- action: Record the operation id under a UNIQUE constraint in the same transaction as the side effect, and replay the stored result for repeats.

## late_commit

- harness events: adapter:create > adapter:enter > invoke:1 > invoke:1:returned:true > settle > observe > adapter:exit
- fault events: server:start > request:received > late_commit:held > request:received > effect:committed > late_commit:released > effect:committed
- action: Record the operation id under a UNIQUE constraint in the same transaction as the side effect, and replay the stored result for repeats.

## concurrent

- harness events: adapter:create > adapter:enter > invoke:1-2:together > invoke:1:returned:true > invoke:2:returned:true > settle > observe > adapter:exit
- fault events: server:start > request:received > request:received > effect:committed > concurrent:overlap > effect:committed
- action: Record the operation id under a UNIQUE constraint in the same transaction as the side effect, and replay the stored result for repeats.

## restart

- harness events: adapter:create > adapter:enter > invoke:1 > invoke:1:returned:true > restart > invoke:2 > invoke:2:returned:true > settle > observe > adapter:exit
- fault events: server:start > request:received > effect:committed > restart:new_process > server:start > request:received > effect:committed
- action: Record the operation id under a UNIQUE constraint in the same transaction as the side effect, and replay the stored result for repeats.

A pass means no duplicate or lost effect was observed in these five deterministic scenarios against this target. It is not an exactly-once proof.
