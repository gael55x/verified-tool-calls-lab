# Retry contract check

Target: built-in fixture (durable) with client examples/ticket_client.py:create_ticket

Exit code: 0 (every scenario passed)

| scenario | status | reported success | final completion | effects | reason |
|---|---|---|---|---|---|
| clean | pass | [True] | True | 1 | one effect and a reported success |
| lost_reply | pass | [True] | True | 1 | one effect and a reported success |
| late_commit | pass | [True] | True | 1 | one effect and a reported success |
| concurrent | pass | [True, True] | True | 1 | one effect and a reported success |
| restart | pass | [True, True] | True | 1 | one effect and a reported success |

## clean

- harness events: adapter:create > adapter:enter > invoke:1 > invoke:1:returned:true > settle > observe > adapter:exit
- fault events: server:start > request:received > effect:committed
- action: None for this scenario.

## lost_reply

- harness events: adapter:create > adapter:enter > invoke:1 > invoke:1:returned:true > settle > observe > adapter:exit
- fault events: server:start > request:received > effect:committed > lost_reply:dropped_after_commit > request:received > effect:replayed
- action: None for this scenario.

## late_commit

- harness events: adapter:create > adapter:enter > invoke:1 > invoke:1:returned:true > settle > observe > adapter:exit
- fault events: server:start > request:received > late_commit:held > request:received > effect:committed > late_commit:released > effect:replayed
- action: None for this scenario.

## concurrent

- harness events: adapter:create > adapter:enter > invoke:1-2:together > invoke:1:returned:true > invoke:2:returned:true > settle > observe > adapter:exit
- fault events: server:start > request:received > request:received > effect:committed > concurrent:overlap > effect:replayed
- action: None for this scenario.

## restart

- harness events: adapter:create > adapter:enter > invoke:1 > invoke:1:returned:true > restart > invoke:2 > invoke:2:returned:true > settle > observe > adapter:exit
- fault events: server:start > request:received > effect:committed > restart:new_process > server:start > request:received > effect:replayed
- action: None for this scenario.

A pass means no duplicate or lost effect was observed in these five deterministic scenarios against this target. It is not an exactly-once proof.
