# Glossary

The same word can name different events in different parts of Tusim. These definitions give the meaning used in the worked examples; the [evidence matrix](evidence-matrix.md) locates their records.

| Term | Meaning in this book |
|---|---|
| Active selection | The implementation chosen when an operation runs. The requested JSON value can remain OS after a direct setter changes the active callback to RS. |
| Bank, word, grant | A scratchpad bank has a budget for servicing words. A grant permits a word access under the selected metering policy. Four unaligned payload bytes can cross two words; the byte copy does not get larger. |
| Binding and arbitration | Binding places a descriptor on a channel. Arbitration chooses among eligible work. Changing placement and changing the cost of a selection scan are different experiments. |
| CModel | An executable model written in C. Its functions can compute values, modify state and evaluate timing equations. Calling a function does not imply that it simulates each hardware signal. |
| Context vs core | A context is the state the context manager saves or restores. A core selection switches a core’s model state into use. Alternating cores tests state selection, not simultaneous execution or complete context retention. |
| Dataflow (WS, OS, RS) | Weight-, output- and row-stationary name alternative mappings. In Tusim the selected plug-in has an arithmetic path and a cycle rule. Its name is not a count of weights, outputs or rows moved. |
| Descriptor; DMA | Direct memory access (DMA) moves data under a descriptor that specifies a transfer. Construction describes work; submission admits it. Neither event alone proves which bytes arrived. |
| DRR | Deficit round robin. A scheduler tracks credit; a candidate may need further rounds before it can be selected. The cost of a failed round is distinct from payload service. |
| Fidelity; calibration | Fidelity describes which aspects of a system the model represents. Calibration compares a model quantity with an external reference under stated conditions and reports error. Repeatability is not calibration. |
| FP16, FP32; raw word | Binary16 and binary32 floating-point representations. Comparing stored bit patterns can expose differences hidden by decimal printing. The half×one experiment observes FP32 results, not FP16 narrowing. |
| KV tile | A partition of the keys and values in attention. Different partitions of the same row must contribute to its normalization; the final output cannot simply be the last tile’s local result. |
| MAC; MMA | A multiply–accumulate is one multiplication and one addition. A matrix multiply–accumulate performs many MACs. When reporting operations per second, state whether each MAC counts as two operations. |
| Model cycles, service cycles, ticks | A model cycle is a unit belonging to a named accounting rule. Service cycles charge an operation; ticks advance a specified model clock. A caller can issue requests without advancing by every cycle charged. |
| Occupied vs requested bytes | Requested bytes are useful payload; occupied bytes include transfer granularity such as partial bursts. Divide either by the same named interval to compare useful and interface rates. |
| Operational intensity; roof | Operations per byte crossing a chosen memory boundary. Multiply by the assumed bandwidth and compare with the compute peak; the smaller roof limits the ideal rate under those assumptions. |
| Oracle; negative control | An oracle gives an expected result independently of the claim under test. A negative control deliberately supplies a wrong route, expected bit or other mismatch to show the check can reject it. |
| PE; tile extent | A processing element is an arithmetic lane in the modeled array. A tile extent is the number of valid rows, columns or reduction elements in a visit; an edge need not fill the array. |
| Retirement; makespan | Retirement here is the descriptor engine’s accounting for a completed slot. A makespan is the interval from a stated start to the last required finish under the stated resource rules. A sum of service charges need not equal it. |
| Sentinel | A distinctive initial value used to tell whether bytes changed. Double-buffer probes inspect sentinels at the swap; a later correct final image cannot establish earlier readiness. |
| SRAM regions W/A/O | Separately identified scratchpad storage for weights, activations and outputs. A capacity or a copied byte count says nothing on its own about bank stalls or physical area. |
| Standalone vs integrated | A standalone helper can run directly in a focused test. An integrated claim must identify the caller and show that the workload under discussion actually reaches the helper. |
