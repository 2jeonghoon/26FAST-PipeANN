#!/usr/bin/env python3

import argparse
import struct
from pathlib import Path


def read_truth_ids(path: Path):
    with path.open("rb") as f:
        npts = struct.unpack("i", f.read(4))[0]
        dim = struct.unpack("i", f.read(4))[0]
        ids = struct.unpack(f"{npts * dim}I", f.read(npts * dim * 4))
    return npts, dim, ids


def write_ids_only_truth(path: Path, rows, topk: int):
    with path.open("wb") as f:
        f.write(struct.pack("i", len(rows)))
        f.write(struct.pack("i", topk))
        for row in rows:
            f.write(struct.pack(f"{topk}I", *row))


def main():
    parser = argparse.ArgumentParser(
        description="Regenerate gt_<inserted>.bin files from a large truthset."
    )
    parser.add_argument("--truth", required=True, type=Path, help="Path to top-k truthset file.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory to write gt_*.bin into.")
    parser.add_argument("--base-count", required=True, type=int, help="Initial active point count.")
    parser.add_argument("--step", required=True, type=int, help="Inserted points per checkpoint.")
    parser.add_argument("--max-inserted", required=True, type=int, help="Maximum inserted points to cover.")
    parser.add_argument("--topk", default=10, type=int, help="Top-k to keep per query.")
    parser.add_argument(
        "--lower-bound",
        default=0,
        type=int,
        help="Minimum allowed id for an active point. Default keeps prefix [0, base+inserted).",
    )
    args = parser.parse_args()

    nqueries, dim, ids = read_truth_ids(args.truth)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for inserted in range(0, args.max_inserted + 1, args.step):
        upper = args.base_count + inserted
        rows = []
        for q in range(nqueries):
            row = ids[q * dim : (q + 1) * dim]
            filtered = [idx for idx in row if args.lower_bound <= idx < upper][: args.topk]
            if len(filtered) < args.topk:
                raise RuntimeError(
                    f"Query {q} has only {len(filtered)} ids in range "
                    f"[{args.lower_bound}, {upper}); need {args.topk}."
                )
            rows.append(filtered)

        out_path = args.output_dir / f"gt_{inserted}.bin"
        write_ids_only_truth(out_path, rows, args.topk)
        print(f"Wrote {out_path} with active upper bound {upper}")


if __name__ == "__main__":
    main()
