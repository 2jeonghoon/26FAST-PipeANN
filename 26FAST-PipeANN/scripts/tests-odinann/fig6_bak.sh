#!/bin/bash
# fig6-diskann-only.sh — SIFT1M DiskANN 단독 실행

# 이전 임시 파일 정리 (500K 인덱스 기준으로 바꿈)
rm -f /home/sift1m_index/500K_mem*
rm -f /home/sift1m_index/500Ktemp0*
rm -f /home/sift1m_index/500K_shadow*
rm -f /home/sift1m_index/500K_shadow1*
rm -f /home/sift1m_index/500K_merge*

mkdir -p data
CWD=$(pwd)

cd /home/FreshDiskANN-baseline/
scripts/moti_long_bak.sh |& tee $CWD/data/DiskANN-insertonly-sift1m.txt

