# Verified Foundation References

This is the working primary-source bibliography for the opening chapters. Metadata was checked against DOI resolution, Crossref records, arXiv, or official publication/project pages. “Safe use” is a conservative paraphrase, not a quotation.

## [KUN82] Systolic architecture

H. T. Kung, “Why Systolic Architectures?,” *Computer*, vol. 15, no. 1, pp. 37–46, 1982. DOI: [10.1109/MC.1982.1653825](https://doi.org/10.1109/MC.1982.1653825).

**Safe use:** Regular arrays with local communication can pipeline data movement and computation to expose concurrency and reuse. This paper does not supply a universal cycle equation for modern GEMM accelerators.

## [WAT09] Roofline model

Samuel Williams, Andrew Waterman, and David Patterson, “Roofline: An Insightful Visual Performance Model for Floating-Point Programs and Multicore Architectures,” *Communications of the ACM*, vol. 52, no. 4, 2009. DOI: [10.1145/1498765.1498785](https://doi.org/10.1145/1498765.1498785). Associated LBNL report: [10.2172/1407078](https://doi.org/10.2172/1407078).

**Safe use:** Attainable performance is bounded by compute peak and memory bandwidth multiplied by operational intensity. The byte boundary must be stated. Roofline is an upper-bound reasoning tool, not a latency simulator.

## [JOU17] Production TPU analysis

Norman P. Jouppi et al., “In-Datacenter Performance Analysis of a Tensor Processing Unit,” *Proceedings of the 44th ACM/IEEE International Symposium on Computer Architecture (ISCA)*, 2017. DOI: [10.1145/3079856.3080246](https://doi.org/10.1145/3079856.3080246). Open manuscript: [arXiv:1704.04760v1](https://arxiv.org/abs/1704.04760v1).

**Safe use:** The evaluated TPU combines matrix hardware, software-managed on-chip storage, and deterministic host-controlled execution. The silicon results show that memory organization, workload mix, latency requirements, and software affect achieved performance. Its measurements do not transfer numerically to Tusim.

## [CHE16] Eyeriss

Yu-Hsin Chen, Joel Emer, and Vivienne Sze, “Eyeriss: A Spatial Architecture for Energy-Efficient Dataflow for Convolutional Neural Networks,” *Proceedings of the 43rd ACM/IEEE International Symposium on Computer Architecture (ISCA)*, 2016. DOI: [10.1109/ISCA.2016.40](https://doi.org/10.1109/ISCA.2016.40).

**Safe use:** The row-stationary dataflow is designed to exploit convolutional reuse across weights, activations, and partial sums while reducing expensive data movement through hierarchical storage. It is not universally optimal for all shapes or topologies.

## [BAN02] Scratchpad memory

Rajeshwari Banakar, Stefan Steinke, Bo-Sik Lee, M. Balakrishnan, and Peter Marwedel, “Scratchpad Memory: A Design Alternative for Cache On-Chip Memory in Embedded Systems,” *10th International Symposium on Hardware/Software Codesign (CODES)*, 2002. DOI: [10.1109/CODES.2002.1003604](https://doi.org/10.1109/CODES.2002.1003604).

**Safe use:** Software-managed scratchpads trade hardware-managed placement for predictable access and explicit compiler/programmer responsibility. The architectural distinction is relevant; the paper’s old-node quantitative results should not be transferred to modern accelerators.

## [SHA14] Aladdin

Yakun Sophia Shao, Brandon Reagen, Gu-Yeon Wei, and David Brooks, “Aladdin: A Pre-RTL, Power-Performance Accelerator Simulator Enabling Large Design Space Exploration of Customized Architectures,” *Proceedings of the 41st ACM/IEEE International Symposium on Computer Architecture (ISCA)*, 2014. DOI: [10.1109/ISCA.2014.6853196](https://doi.org/10.1109/ISCA.2014.6853196).

**Safe use:** Pre-RTL dependence/resource models can evaluate broad accelerator design spaces earlier than complete RTL. Aladdin’s reported validation does not transfer automatically to Tusim.

## [SAM18] SCALE-Sim

Ananda Samajdar, Yuhao Zhu, Paul Whatmough, Matthew Mattina, and Tushar Krishna, “SCALE-Sim: Systolic CNN Accelerator Simulator,” arXiv preprint, 2018. [arXiv:1811.02883v2](https://arxiv.org/abs/1811.02883v2); DOI for arXiv record: [10.48550/arXiv.1811.02883](https://doi.org/10.48550/arXiv.1811.02883). Official project: <https://github.com/ARM-software/SCALE-Sim>.

**Safe use:** SCALE-Sim is a configurable systolic accelerator simulator used to study array dimensions, dataflow, bandwidth, mapping, cycles, and traffic. Its “cycle accurate” description is bounded by its modeled abstraction and does not prove equivalence to arbitrary RTL.

## [PAR19] Timeloop

Angshuman Parashar, Priyanka Raina, Yakun Sophia Shao, Yu-Hsin Chen, Victor A. Ying, Anurag Mukkara, Rangharajan Venkatesan, Brucek Khailany, Stephen W. Keckler, and Joel Emer, “Timeloop: A Systematic Approach to DNN Accelerator Evaluation,” *IEEE International Symposium on Performance Analysis of Systems and Software (ISPASS)*, 2019. DOI: [10.1109/ISPASS.2019.00042](https://doi.org/10.1109/ISPASS.2019.00042). Official project: <https://github.com/NVlabs/timeloop>.

**Safe use:** Separating workload shape, architecture description, mapping, and constraints enables systematic mapping search and model-based estimates of performance and data movement. A Timeloop result is not inherently RTL- or silicon-equivalent.

## [KWO19] MAESTRO

Hyoukjun Kwon, Prasanth Chatarasi, Michael Pellauer, Angshuman Parashar, Vivek Sarkar, and Tushar Krishna, “Understanding Reuse, Performance, and Hardware Cost of DNN Dataflow,” *52nd IEEE/ACM International Symposium on Microarchitecture (MICRO)*, 2019. DOI: [10.1145/3352460.3358252](https://doi.org/10.1145/3352460.3358252). Extended manuscript: [arXiv:1805.02566](https://arxiv.org/abs/1805.02566).

**Safe use:** Data-centric mapping directives can describe spatial and temporal mappings; an analytical model can infer reuse, communication, occupancy, execution time, and resource requirements. It does not automatically model arbitrary queueing or backpressure.

## [WU19] Accelergy

Yannan Nellie Wu, Joel S. Emer, and Vivienne Sze, “Accelergy: An Architecture-Level Energy Estimation Methodology for Accelerator Designs,” *IEEE/ACM International Conference on Computer-Aided Design (ICCAD)*, 2019. DOI: [10.1109/ICCAD45719.2019.8942149](https://doi.org/10.1109/ICCAD45719.2019.8942149). Official project: <https://github.com/Accelergy-Project/accelergy>.

**Safe use:** Architecture-level energy estimation can combine action counts with plug-in energy values. Results inherit uncertainty from counts, primitive models, technology, voltage, and characterization; they are not post-layout measurements.

## [GEN21] Gemmini

Hasan Genc et al., “Gemmini: Enabling Systematic Deep-Learning Architecture Evaluation via Full-Stack Integration,” *58th ACM/IEEE Design Automation Conference (DAC)*, 2021. DOI: [10.1109/DAC18074.2021.9586216](https://doi.org/10.1109/DAC18074.2021.9586216). Preprint: [arXiv:1911.09925](https://arxiv.org/abs/1911.09925). Official project: <https://github.com/ucb-bar/gemmini>.

**Safe use:** SoC contention, operating-system behavior, compiler/runtime choices, and programming overhead can materially change application-level accelerator performance. Preserve which Gemmini evidence comes from models, RTL/full-system evaluation, or fabricated instances.

## [CHE18] TVM

Tianqi Chen et al., “TVM: An Automated End-to-End Optimizing Compiler for Deep Learning,” *13th USENIX Symposium on Operating Systems Design and Implementation (OSDI)*, 2018. Official publication page: <https://www.usenix.org/conference/osdi18/presentation/chen>.

**Safe use:** End-to-end deep-learning compilation combines graph transformations, operator scheduling, target-specific code generation, and schedule search. The official USENIX page is preferred; the sometimes-listed `10.5555/...` identifier should not be presented as a reliably resolvable DOI.

## [SMI84] Decoupled access/execute

James E. Smith, “Decoupled Access/Execute Computer Architectures,” *ACM Transactions on Computer Systems*, vol. 2, no. 4, 1984. DOI: [10.1145/357401.357403](https://doi.org/10.1145/357401.357403).

**Safe use:** Queue-connected access and execute streams provide a foundational example of latency tolerance through decoupling. The paper supports questions about queue capacity, synchronization, and loss of decoupling; it does not define modern DMA descriptors, scratchpad protocols, or guaranteed tensor-accelerator speedup.

## [RISCV26] RISC-V Unprivileged ISA

RISC-V International, *The RISC-V Instruction Set Manual, Volume I: Unprivileged Architecture*, ratified snapshot `20260120`, RV32I version 2.1. Official versioned index: <https://docs.riscv.org/reference/isa/v20260120/unpriv/unpriv-index.html>. RV32I chapter: <https://docs.riscv.org/reference/isa/v20260120/unpriv/rv32.html>.

**Safe use:** A normative ISA can define exact instruction fields and scoped predecessor/successor fence effects. This is a vocabulary and comparison source only; it does not establish Tusim encoding, decoding, queue state, visibility, or fence behavior.

## [SS95] Superscalar lifecycle vocabulary

James E. Smith and Gurindar S. Sohi, “The Microarchitecture of Superscalar Processors,” *Proceedings of the IEEE*, vol. 83, no. 12, pp. 1609–1624, 1995. DOI: [10.1109/5.476078](https://doi.org/10.1109/5.476078).

**Safe use:** Decode, dispatch/issue, execution, completion, and ordered architectural update are distinct concepts. The paper does not imply that Tusim has a hardware pipeline, reorder buffer, precise exceptions, speculation, or a retirement stage.

## [TOM67] Dependency-driven scheduling

Robert M. Tomasulo, “An Efficient Algorithm for Exploiting Multiple Arithmetic Units,” *IBM Journal of Research and Development*, vol. 11, no. 1, pp. 25–33, 1967. DOI: [10.1147/rd.111.0025](https://doi.org/10.1147/rd.111.0025).

**Safe use:** Tags, operand readiness, and reservation structures illustrate that admission, dependency satisfaction, issue, and result production are separate events. This does not establish that Tusim implements Tomasulo scheduling, out-of-order execution, or precise retirement.

## [OCL311] OpenCL command-queue contract

Khronos OpenCL Working Group, *The OpenCL Specification*, version 3.1.1. Official unified specification: <https://registry.khronos.org/OpenCL/specs/unified/html/OpenCL_API.html>.

**Safe use:** The normative API distinguishes queued, submitted, running, and complete states; event prerequisites and command-queue barriers have explicit contracts. OpenCL semantics do not transfer to Tusim and cannot fill gaps in Tusim's dependency, barrier, completion, signal, or reclamation behavior.

## [DT01] On-chip interconnection networks

William J. Dally and Brian Towles, “Route Packets, Not Wires: On-Chip Interconnection Networks,” *Proceedings of the 38th Design Automation Conference*, pp. 684–689, 2001. DOI: [10.1109/DAC.2001.935594](https://doi.org/10.1109/DAC.2001.935594).

**Safe use:** Replacing ad hoc global wiring with structured packet networks exposes topology, routing, flow-control, and resource-allocation decisions. The paper motivates those design obligations; it does not establish that Tusim implements packets, routers, queues, arbitration, backpressure, or physical link costs.

## [DS87] Deadlock-free routing

William J. Dally and Charles L. Seitz, “Deadlock-Free Message Routing in Multiprocessor Interconnection Networks,” *IEEE Transactions on Computers*, vol. C-36, no. 5, pp. 547–553, 1987. DOI: [10.1109/TC.1987.1676939](https://doi.org/10.1109/TC.1987.1676939).

**Safe use:** Routing choices and channel dependencies are part of a network correctness contract. Deterministic shortest paths alone do not prove deadlock freedom for a finite-buffer implementation; Tusim's route-load lower bound has no such implementation to validate.

## [PY09] Bandwidth-optimal all-reduce

Pitch Patarasuk and Xin Yuan, “Bandwidth Optimal All-reduce Algorithms for Clusters of Workstations,” *Journal of Parallel and Distributed Computing*, vol. 69, no. 2, pp. 117–124, 2009. DOI: [10.1016/j.jpdc.2008.09.002](https://doi.org/10.1016/j.jpdc.2008.09.002).

**Safe use:** Collective performance depends on the communication algorithm, topology assumptions, and cost model; reduce-scatter/allgather constructions provide a contrast to host-side gather/sum/writeback. The paper does not validate Tusim's functional all-reduce or supply transferable cycle counts.

## Bibliographic cautions

- Check arXiv identifiers by title; plausible numeric IDs can refer to unrelated fields.
- Cite the exact manuscript version actually read when a claim depends on versioned text.
- The late-1970s Kung–Leiserson systolic-array precursor has inconsistent bibliographic forms; use Kung’s verified 1982 article unless an archival scan is checked.
- SCALE-Sim’s original paper is an authoritative project preprint, not an archival peer-reviewed venue.
- Project documentation supports current syntax/capabilities; foundational claims should prefer the archival paper.
- Search snippets, generated summaries, and secondary surveys are discovery aids rather than primary evidence.
