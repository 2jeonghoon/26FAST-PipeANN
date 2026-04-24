IFT1M Dataset Preparation

This repository contains instructions for setting up and converting the **SIFT1M** dataset, which is used for benchmarking approximate nearest neighbor search algorithms. The SIFT1M dataset includes a base set and a set of query vectors.

## Prerequisites

- Ensure that you have **wget** installed to download the dataset.
- The following tools are required for conversion:
  - `fvecs_to_bin`: A utility to convert `.fvecs` files to `.fbin` binary files.
  - `change_pts`: A tool to manipulate the number of points in a `.fbin` file.

## Setup Instructions

### 1. Set the Environment Variable and Create Directory
First, set the environment variable to store the SIFT1M dataset and create the necessary directory:
```bash
export SIFT1M_DIR=/home/sift1m
mkdir -p ${SIFT1M_DIR}
```
### 2. Download and Extract the Dataset

Download the SIFT1M dataset from the FTP server and extract it to the specified directory:
```bash
wget ftp://ftp.irisa.fr/local/texmex/corpus/sift.tar.gz
tar -xzf ${SIFT1M_DIR}/sift.tar.gz -C ${SIFT1M_DIR}
```

### 3. Convert the Dataset to Binary Format

Use the `fvecs_to_bin` utility to convert the fvecs files (base and query) to binary format (fbin):

```bash
build/tests/utils/fvecs_to_bin ${SIFT1M_DIR}/sift/sift_base.fvecs   ${SIFT1M_DIR}/sift1m_base.fbin
build/tests/utils/fvecs_to_bin ${SIFT1M_DIR}/sift/sift_query.fvecs  ${SIFT1M_DIR}/sift1m_query.fbin
```
### 4. Copy and Modify the Base Binary File

Create a copy of the `sift1m_base.fbin` file and modify the number of points using `change_pts`:
```bash
cp ${SIFT1M_DIR}/sift1m_base.fbin ${SIFT1M_DIR}/sift1m_base_copy.fbin
build/tests/change_pts float ${SIFT1M_DIR}/sift1m_base_copy.fbin 500000
```
### 5. Rename the Modified File

Finally, rename the modified file to 500K.fbin:
```bash
mv ${SIFT1M_DIR}/sift1m_base_copy.fbin500000 ${SIFT1M_DIR}/500K.fbin
```
### File Structure

After following the steps above, the resulting file structure will be:
```
/home/sift1m
│
├── sift
│   ├── sift_base.fvecs
│   └── sift_query.fvecs
│
├── sift1m_base.fbin
├── sift1m_query.fbin
├── sift1m_base_copy.fbin
└── 500K.fbin
```
