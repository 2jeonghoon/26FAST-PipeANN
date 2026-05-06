# 26FAST-PipeANN Artifact Workspace

This git repository is a workspace for the OdinANN/PipeANN artifact and the
FreshDiskANN baseline used by the local Figure 6 workflow.

The verified workflow in this checkout is limited to preparing the SIFT1M 500K
insert-only setup and running:

```bash
cd 26FAST-PipeANN
bash scripts/tests-odinann/fig6.sh
```

Other experiment scripts and larger-dataset workflows are included for
reference, but they have not been verified as part of this README.

## Repository Layout

```text
.
|-- 26FAST-PipeANN/          # OdinANN/PipeANN source tree
|-- FreshDiskANN-baseline/   # FreshDiskANN baseline source tree
`-- sift1m/                  # SIFT1M dataset preparation notes
```

Most commands below are run from `26FAST-PipeANN/`, because that directory
contains the build system and the `build/tests/` binaries.

## Verified Scope

Only the following script execution is documented as verified:

```bash
cd 26FAST-PipeANN
bash scripts/tests-odinann/fig6.sh
```

The script currently changes directory to:

```text
/home/jhlee/FreshDiskANN-baseline/
```

If the FreshDiskANN baseline you want to use is in another location, update the
path in `26FAST-PipeANN/scripts/tests-odinann/fig6.sh` before running it.

## Dependencies

Install the required packages on Ubuntu:

```bash
sudo apt install make cmake g++ libaio-dev libgoogle-perftools-dev \
  clang-format libboost-all-dev libmkl-full-dev libjemalloc-dev
```

The workflow assumes Linux with NVMe SSD storage. The paths below are an
nvmevirt-based example used in this local setup:

```text
/mnt/nvmevirt/sift1m/
/mnt/nvmevirt/sift1m_index/
/mnt/nvmevirt/sift1m_gnd_diskann/
```

## Build OdinANN/PipeANN

Build `liburing` first:

```bash
cd 26FAST-PipeANN/third_party/liburing
./configure
make -j
cd ../../..
```

Then build OdinANN/PipeANN:

```bash
cd 26FAST-PipeANN
bash ./build.sh
```

If `build/` already exists and `build.sh` stops at `mkdir build`, rebuild
manually:

```bash
cd 26FAST-PipeANN/build
cmake ..
make -j
```

The binaries used below are created under:

```text
26FAST-PipeANN/build/tests/
```

## Prepare SIFT1M Files

This example stores SIFT1M under `/mnt/nvmevirt`. Skip this section if these
files already exist:

```text
/mnt/nvmevirt/sift1m/sift1m_base.fbin
/mnt/nvmevirt/sift1m/sift1m_query.fbin
/mnt/nvmevirt/sift1m/500K.fbin
```

Download and extract SIFT1M:

```bash
export SIFT1M_DIR=/mnt/nvmevirt/sift1m
mkdir -p ${SIFT1M_DIR}
wget ftp://ftp.irisa.fr/local/texmex/corpus/sift.tar.gz -O ${SIFT1M_DIR}/sift.tar.gz
tar -xzf ${SIFT1M_DIR}/sift.tar.gz -C ${SIFT1M_DIR}
```

Convert the base and query vectors to the `.fbin` format:

```bash
cd 26FAST-PipeANN

build/tests/utils/fvecs_to_bin \
  ${SIFT1M_DIR}/sift/sift_base.fvecs \
  ${SIFT1M_DIR}/sift1m_base.fbin

build/tests/utils/fvecs_to_bin \
  ${SIFT1M_DIR}/sift/sift_query.fvecs \
  ${SIFT1M_DIR}/sift1m_query.fbin
```

Create the first-500K base file:

```bash
cp ${SIFT1M_DIR}/sift1m_base.fbin ${SIFT1M_DIR}/sift1m_base_copy.fbin
build/tests/change_pts float ${SIFT1M_DIR}/sift1m_base_copy.fbin 500000
mv ${SIFT1M_DIR}/sift1m_base_copy.fbin500000 ${SIFT1M_DIR}/500K.fbin
```

## Prepare the SIFT1M 500K Figure 6 Inputs

Run this section from `26FAST-PipeANN/` after building the binaries:

```bash
cd 26FAST-PipeANN
mkdir -p /mnt/nvmevirt/sift1m_index
mkdir -p /mnt/nvmevirt/sift1m_gnd_diskann
```

0. Compute top-1000 ground truth over the full SIFT1M base set.

```bash
build/tests/utils/compute_groundtruth float \
  /mnt/nvmevirt/sift1m/sift1m_base.fbin \
  /mnt/nvmevirt/sift1m/sift1m_query.fbin \
  1000 \
  /mnt/nvmevirt/sift1m/sift1m_truth1000.bin
```

1. Generate per-step top-k ground-truth files for the 500K insert-only workload.

```bash
build/tests/gt_update \
  /mnt/nvmevirt/sift1m/sift1m_truth1000.bin \
  1000000 \
  500000 \
  10 \
  /mnt/nvmevirt/sift1m_gnd_diskann/500K_topk \
  1
```

2. Build the 500K on-disk index.

```bash
build/tests/build_disk_index float \
  /mnt/nvmevirt/sift1m/500K.fbin \
  /mnt/nvmevirt/sift1m_index/500K \
  96 128 0.05 64 20 l2 0
```

3. Generate identity tags for the 500K index.

```bash
build/tests/gen_tags float \
  /mnt/nvmevirt/sift1m/500K.fbin \
  /mnt/nvmevirt/sift1m_index/500K \
  false
```

The important generated files are:

```text
/mnt/nvmevirt/sift1m/sift1m_truth1000.bin
/mnt/nvmevirt/sift1m_gnd_diskann/500K_topk/gt_*.bin
/mnt/nvmevirt/sift1m_index/500K_disk.index
/mnt/nvmevirt/sift1m_index/500K_disk.index.tags
/mnt/nvmevirt/sift1m_index/500K_pq_compressed.bin
/mnt/nvmevirt/sift1m_index/500K_pq_pivots.bin
```

## Run Figure 6

Run the default verified script:

```bash
cd 26FAST-PipeANN
bash scripts/tests-odinann/fig6.sh
```

The default output is:

```text
26FAST-PipeANN/data/DiskANN-insertonly-sift1m.txt
```

Optional variants supported by the script are:

```bash
cd 26FAST-PipeANN
bash scripts/tests-odinann/fig6.sh ionice
bash scripts/tests-odinann/fig6.sh affinity
```

Their outputs are:

```text
26FAST-PipeANN/data/DiskANN-insertonly-sift1m_ionice.txt
26FAST-PipeANN/data/DiskANN-insertonly-sift1m_affinity.txt
```

## Command Reference

Compute exact ground truth:

```bash
build/tests/utils/compute_groundtruth \
  <float|int8|uint8> <base.bin> <query.bin> <top_k> <output_truth.bin>
```

Generate update ground-truth slices:

```bash
build/tests/gt_update \
  <truth.bin> <total_points> <batch_points> <target_topk> <output_dir> <insert_only>
```

Build an on-disk index:

```bash
build/tests/build_disk_index \
  <float|int8|uint8> <data.bin> <index_prefix> <R> <L> <B> <M> <T> <l2|cosine> <single_file_index>
```

Generate identity tags:

```bash
build/tests/gen_tags \
  <float|int8|uint8> <base_data.bin> <index_prefix> <sector_aligned>
```

Parameter notes:

- `R`: maximum number of out-neighbors in the graph.
- `L`: candidate pool size during index construction.
- `B`: PQ-compressed vector budget.
- `M`: memory budget for index construction.
- `T`: number of build threads.
- `insert_only`: use `1` for insert-only workloads and `0` for insert-delete workloads.

## Related Documentation

For the original OdinANN/PipeANN README, see:

```text
26FAST-PipeANN/README.md
```

For SIFT1M conversion notes, see:

```text
sift1m/README.md
```
