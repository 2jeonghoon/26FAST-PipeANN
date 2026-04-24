#!/bin/bash
# /mnt/nvme2/DiskANN/scripts/moti_long.sh — SIFT1M 최종본

rm -f /home/sift1m_index/500K_shadow*
rm -f /home/sift1m_index/500K_merge*

# 19회 반복, 각 ckpt에서 한 번 merge 후 재시작
for i in {0..18}
do
    echo "Running with i = $i"
    OMP_PLACES=cores OMP_PROC_BIND=close \
    build/tests/motivation float \
        /home/sift1m/sift1m_base.fbin \
        128 96 1.2 500000 0 \
        /home/sift1m_index/500K \
        /home/sift1m/sift1m_query.fbin \
        /home/sift1m_gnd_diskann/500K_topk \
        10 4 100 $i 30000 \
        20 30 40 50 60 80 100
done
