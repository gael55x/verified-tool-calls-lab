# Related tools and why this extension exists

Checked 2 October 2026 against public project documentation. This is a bounded comparison, not proof of novelty or an exhaustive market survey. We have not benchmarked or audited these projects.

| Project | Documented overlap | When to investigate it |
| --- | --- | --- |
| [idempotency-tester](https://github.com/hhw12409/idempotency-tester) | Concurrent duplicate delivery, database-state verification, custom adapters, JSON/Markdown reports and CI failures | You need an existing multi-protocol runner for HTTP, Kafka, SQS or RabbitMQ |
| [latch](https://github.com/sangaraju1988/latch) | Agent idempotency middleware, timeout/circuit-breaker primitives and chaos utilities | You need application middleware rather than an independent contract test |
| [verified-tool](https://github.com/yadukpb/verified-tool) | Verified/failed/unknown postcondition checks for tool calls | You want a postcondition-verification integration |
| [reprise](https://github.com/freyesperales/dev-experiment-038) | Offline modeling of repeated effects under nested retries and key changes | You want to explore a modeled execution before integration |
| [Toxiproxy](https://github.com/Shopify/toxiproxy) | Real connection faults including delays and timeouts | You need general network fault injection against an existing service |

This lab's practical extension focuses on a small Python contract suite and an inspectable HTTP/SQLite reference application. It connects a client callable, exercises explicitly controlled failure schedules, inspects committed effects after pending work settles, and demonstrates the difference between an unsafe write and a durable database constraint. Its test-only fault hooks are deliberately narrower than a network proxy.

The contribution is the usable reference, explicit failure boundaries and retained evidence. The underlying retry, idempotency and fault-testing ideas are established. We do not claim to be first, unique, universally safer, or a replacement for the projects above. No third-party implementation was copied or vendored.
