# CloudFlow
CloudFlow is a framework to identify security-sensitive data flows in serverless applications. The research paper [CloudFlow: Identifying Security-sensitive Data Flows in Serverless Applications](https://www.usenix.org/conference/usenixsecurity25/presentation/raffa), which was presented at _USENIX Security 2025_, provides details about its implementation and evaluation.

As detailed in this [Zenodo record](https://doi.org/10.5281/zenodo.15609299), CloudFlow was also assessed as part of the _USENIX Security 2025_ Artifact Evaluation process, and the results are available on the [conference website](https://secartifacts.github.io/usenixsec2025/results). This artifact evaluation [appendix](https://secartifacts.github.io/usenixsec2025/appendix-files/sec25cycle2ae-final181.pdf), in particular, details how to reproduce the results of our study. The assessed versions of CloudFlow and [CloudBench](https://github.com/giusepperaffa/cloudbench), the microbenchmark suite used for the evaluation of our framework, are also available on their repositories as detailed below:
- CloudFlow - Tag [v0.0.1](https://github.com/giusepperaffa/cloudflow/tags)
- CloudBench - Tag [v0.0.1](https://github.com/giusepperaffa/cloudbench/tags)

The artifact evaluation appendix is also available on the research paper [webpage](https://www.usenix.org/system/files/usenixsecurity25-appendix-raffa.pdf). A summary of the paper can be found in the following video.

[![CloudFlow: Identifying Security-sensitive Data Flows in Serverless Applications](https://img.youtube.com/vi/Jd3kmfkk2dQ/0.jpg)](https://www.youtube.com/watch?v=Jd3kmfkk2dQ)

# CloudBench
[CloudBench](https://github.com/giusepperaffa/cloudbench) is the microbenchmark suite used for the evaluation of CloudFlow. CloudBench can be reused and extended to test future static analysis tools for serverless environments. While the instructions provided in the above-mentioned [appendix](https://secartifacts.github.io/usenixsec2025/appendix-files/sec25cycle2ae-final181.pdf) explain how to use both CloudFlow and CloudBench, it is worth highlighting that our microbenchmark suite relies on a [configuration file](https://github.com/giusepperaffa/cloudbench/blob/main/cloudbench_config.yml). The latter needs to be edited by considering the specifics of the tool under test.   

# Environment Installation
CloudFlow and CloudBench are included in a ready-to-use Virtual Machine (VM) available on [Zenodo](https://doi.org/10.5281/zenodo.15609299). However, it is also possible to install the environment in a Ubuntu 20.04 VM by following the instructions available in this [repository](https://github.com/giusepperaffa/cloudflow-environment-installation).

# PhD Thesis
The work presented at _USENIX Security 2025_ is part of the PhD thesis _Static Analysis of Serverless Applications for Security_. The thesis, which contains further information on CloudFlow and CloudBench, is available on the [Royal Holloway University of London College Repository](https://pure.royalholloway.ac.uk/en/publications/static-analysis-of-serverless-applications-for-security/), and it can be downloaded from [here](https://pure.royalholloway.ac.uk/ws/portalfiles/portal/70099343/2025raffagphd.pdf). A summary of this research is also available in this [presentation](https://github.com/giusepperaffa/serverless-security-microbenchmarks/blob/main/docs/PhD_Viva_Presentation.pdf).
