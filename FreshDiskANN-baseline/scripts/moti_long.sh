#!/bin/bash

# 이전 임시 파일 정리
rm -f /mnt/nvmevirt/sift1m_index/500K_shadow*
rm -f /mnt/nvmevirt/sift1m_index/500K_merge*
rm -f /mnt/nvmevirt/sift1m_index/500Ktemp*
rm -f /mnt/nvmevirt/sift1m_index/500K_mem*

# 19회 반복 (i=0..18), merge 후 재시작
EXE_NAME=${1:-motivation}
echo "Using executable: $EXE_NAME"

for i in {0..18}
do
    echo "Running with i = $i"
    OMP_PLACES=cores OMP_PROC_BIND=close \
    build/tests/$EXE_NAME float \
        /mnt/nvmevirt/sift1m/sift1m_base.fbin \
        128 96 1.2 500000 0 \
        /mnt/nvmevirt/sift1m_index/500K \
        /mnt/nvmevirt/sift1m/sift1m_query.fbin \
        /mnt/nvmevirt/sift1m_gnd_diskann/500K_topk \
        10 4 100 $i 30000 \
        20 30 40 50 60 80 100
done
