# Chapter 12 — Multi-Core Clusters and Interconnect Heuristic Estimates

[Contents](../../README.md) · [Public evidence summary](../../evidence-matrix.md#chapter-12)

Two messages have to take turns on one link. A third message crosses six links, none of them on that first route. Should the last message make the first two finish later? At public Tusim `7a094ff6c5527eff8e4318de676f0c0221c448b4`, adding it raises the shared-link score from 133 to 158 cycles. Yet we can still deliver the last byte of all three by cycle 133. To explain both numbers, start with what the estimator counts, not what its result is called.

## 12.1 What is being timed?

A cluster is a set of core states plus topology and accounting. `tu_cluster_create` takes the core count, topology and mesh rows explicitly; it takes switching, routing, contention, link width and hop latency from the base configuration or defaults. `tu_core_create_with_id` initializes the global TU, moves its state into the core and clears the global state. Executing assembly on a core swaps that state in and back out. Separate output SRAM regions give messages real endpoints in the functional model. They do not give us a concurrent router or one independently ticking simulator per core. See [core lifecycle](05-state-lifecycle-and-public-apis.md).

Three questions that sound like “communication time” have different answers:

| Question | Producer | What the result means |
|---|---|---|
| Did these bytes reach the destination? | `tu_cluster_send` | For a valid nonempty transfer, a host temporary connects a bulk read and a bulk write of output SRAM. The destination core and cluster are charged an isolated estimate. This is not a timestamp of packet arrival. |
| How expensive is one route? | `tu_cluster_estimate_transfer_cycles` | On a nonempty, nonlocal transfer with `h` hops, latency `L` per hop and `s = ceil(bytes / link width)` serialization cycles: legacy `hL`, cut-through `hL + s`, store-and-forward `h(L + s)`. |
| Where would simultaneous transfers compete? | `tu_cluster_estimate_traffic_cycles` | Walk each deterministic route and accumulate service on **directed** links. Report the largest load, its link, the largest isolated cost, and a score. No data moves; no packet is scheduled. |

## 12.2 Place the messages before interpreting the score

Number the 4×4 mesh in row-major order. XY means traverse columns first, then rows. All three messages are ready at zero; each carries 1,024 bytes. Use cut-through switching, a 16-byte/cycle directed link and five cycles per hop. Each message needs 64 service slots on every link it uses.

| Message | Route | Hops | Isolated cycles |
|---|---|---:|---:|
| A | 0 → 1 | 1 | 69 |
| B | 0 → 1 | 1 | 69 |
| C | 12 → 13 → 14 → 15 → 11 → 7 → 3 | 6 | 94 |

The busiest link, 0 → 1, must supply 128 slots. Each link on C's route supplies only 64. Under these assumptions **94** is a necessary time for the longest isolated transfer, and **128** is a necessary amount of service on one link. Both apply to the same workload. That does not make the six-hop latency a delay *after* the busiest link finishes.

The estimator takes the larger of the isolated maximum and `busiest link service + longest hop latency sum`: here `max(94, 128 + 30) = 158`. With only A and B it returns `max(69, 128 + 5) = 133`. As a control, keeping all three messages but selecting ideal-parallel scoring leaves the isolated maximum at 94 and the busiest-link field at 128, while the score falls to 94. The load is still computed; it is no longer used to form the score.

## 12.3 Construct a schedule, not a second score

Use half-open intervals: `[0,64)` reserves 64 one-cycle slots, and a beat launched in slot `t` may launch on its next link in slot `t+5`. Allow cut-through forwarding, independent directed links and no extra injection, arbitration or ejection delays. We are constructing a possible execution under these assumptions, **not** replaying a packet scheduler inside Tusim.

* Give A slots `[0,64)` on 0 → 1, then B slots `[64,128)`. Their last bytes arrive at 69 and 133 respectively.
* Start C at zero too. Its six links carry the stream in `[0,64)`, `[5,69)`, `[10,74)`, `[15,79)`, `[20,84)` and `[25,89)`. The final hop delivers its last byte at 94. None of its slots uses 0 → 1.

The independent schedule checks every `(source, destination, slot)` for double booking and tracks the last beat through every hop. Its makespan is `max(69, 133, 94) = 133`. **One feasible schedule below 158 disproves 158 as a makespan lower bound.** We need neither an optimal scheduler nor a measured router to disprove that inequality. Conversely, 133 is not a prediction of hardware latency. Use the link identity and its service load to diagnose a placement; use a scheduling or hardware model if completion time is the decision variable. The public exploration note calls the combined quantity a lower bound; its equation is reproducible, that interpretation is not.

**Reading a placement report:** ask which link supplied the maximum, which route supplied the latency, and whether they must be serialized. **Reading a collective result:** ask which layer rejected an access, which layer consumed the error, and what was already allowed to change. In both cases, naming the producer of the number or status prevents a local fact from becoming an unsupported global guarantee.

[Next: Chapter 13 — Weight Streams: Quantization, Structured Sparsity, and Compression](13-weight-streams-quantization-sparsity-compression.md)
