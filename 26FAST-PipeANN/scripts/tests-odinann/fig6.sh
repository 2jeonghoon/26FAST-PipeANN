#!/bin/bash
# fig6-diskann-only.sh — SIFT1M DiskANN 단독 실행

# 이전 임시 파일 정리 (500K 인덱스 기준으로 바꿈)
rm -f /mnt/nvmevirt/sift1m_index/500K_mem*
rm -f /mnt/nvmevirt/sift1m_index/500Ktemp0*
rm -f /mnt/nvmevirt/sift1m_index/500K_shadow*
rm -f /mnt/nvmevirt/sift1m_index/500K_shadow1*
rm -f /mnt/nvmevirt/sift1m_index/500K_merge*

mkdir -p data
CWD=$(pwd)

EXE="motivation"
OUT_FILE="DiskANN-insertonly-sift1m.txt"
if [ "$1" == "ionice" ]; then
    EXE="motivation_ionice"
    OUT_FILE="DiskANN-insertonly-sift1m_ionice.txt"
elif [ "$1" == "affinity" ]; then
    EXE="motivation_affinity"
    OUT_FILE="DiskANN-insertonly-sift1m_affinity.txt"
fi

cd /home/jhlee/FreshDiskANN-baseline/
scripts/moti_long.sh $EXE |& tee $CWD/data/$OUT_FILE
