# Nonmapped operand provenance

Unit: one unique decoded register per static MMA run in the active kernels. CFG may-reaching definitions describe all possible origins; this is not a dynamic frame frequency, and memory loads do not by themselves prove weight semantics. Symbol names are interned in source-audit.json.

| FB | Mapped run events | Nonmapped run events | Leaf combinations |
|---:|---:|---:|---|
| 0 | 1636 | 844 | global_load: 648; constant_or_special+global_load: 68; global_load+local_FP8_quantization: 128 |
| 1 | 776 | 1052 | global_load: 720; shared_load: 328; constant_or_special+global_load: 4 |
| 2 | 512 | 1244 | shared_load: 656; global_load: 584; constant_or_special+global_load: 4 |
| 3 | 384 | 1188 | shared_load: 712; global_load: 472; constant_or_special+global_load: 4 |
| 4 | 184 | 864 | shared_load: 352; global_load: 512 |
| 5 | 32 | 512 | shared_load: 256; global_load: 240; global_load+local_FP8_quantization: 16 |
| 6 | 0 | 144 | shared_load: 16; global_load: 128 |

## Why the largest decoded pools remain

At the first peak of every active run achieving the FB maximum, the compositions below agree. Counts are simultaneously live decoded pairs, each occupying two b32 temporaries, not total physical kernel registers.

| FB | Global pairs at peak | Shared pairs at peak | Temporary b32 peak | Global pointer root |
|---:|---:|---:|---:|---|
| 1 | 24 | 4 | 56 | param64+16 |
| 2 | 24 | 4 | 56 | param64+16 |
| 3 | 24 | 4 | 56 | param64+16 |
| 4 | 48 | 8 | 112 | param64+16 |
| 5 | 32 | 8 | 80 | param64+24 |

Global bases are traced to actual argument offsets; they are not all relabeled weights without a host-structure proof. Shared producers are also audited: FB01 shared_storage is written from local FP8 quantization; FB02/03 and FB04/05 may include local quantization plus global/async-copy sources. This motivates layout/storage experiments, but does not establish safe same-lane FP16 forwarding across a shared-memory exchange.

Current multidef mode disables the same-basic-block restriction. Rejected pack/phi paths and numerical quantization semantics require proof before widening forwarding. No same-basic-block pure-mov duplicate decode identities were found.

The audit parser recognizes :: qualifiers. The production definition parser was hardened likewise; all 112 entry mappings remained identical, and a full V2.6 rebuild remained byte-identical. See parser-scope-check.json and parser-binary-check.json.
