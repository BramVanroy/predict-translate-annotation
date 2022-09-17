import re
from pathlib import Path

def verify_order_lines(lines):
    idxs = set([int(re.search("segId=\"(\d+)\"", line).group(1))
                       for line in lines if re.search("segId=\"(\d+)\"", line) is not None])
    gold_idxs = set(range(1, max(idxs)+1))

    print("All indices present? (false expected if do_increase)", idxs == gold_idxs)

    if idxs != gold_idxs:
       print(idxs)
       print(gold_idxs)


def main(fin, start_idx, end_idx=None, do_increase=False):
    pfin = Path(fin).resolve()

    # make bakup
    pfin.with_suffix(f"{pfin.suffix}.bak").write_bytes(pfin.read_bytes())

    mod_lines = []
    for line in pfin.read_text(encoding="utf-8").splitlines(keepends=True):
        match = re.search("segId=\"(\d+)\"", line)

        if match:
            matched_idx = int(match.group(1))
            if matched_idx >= start_idx:
                if end_idx is None or end_idx < matched_idx:
                    if do_increase:
                        mod_lines.append(re.sub("segId=\"(\d+)\"", f'segId=\"{str(matched_idx+1)}\"', line))
                    else:
                        mod_lines.append(re.sub("segId=\"(\d+)\"", f'segId=\"{str(matched_idx-1)}\"', line))
                else:
                    mod_lines.append(line)
            else:
                mod_lines.append(line)
        else:
            mod_lines.append(line)

    verify_order_lines(mod_lines)
    pfin.write_text("".join(mod_lines), encoding="utf-8")

if __name__ == '__main__':
    import argparse

    cparser = argparse.ArgumentParser(description=__doc__)

    cparser.add_argument("fin", help="Input file .src or .tgt.")
    cparser.add_argument("start_idx",
                         help="starting from this index, all seg_ids are decreased by one. So for 8 the segId is"
                              " decreased by one for all lines with segId=8 or higher", type=int)
    cparser.add_argument("--end_idx", help="if given, the decrease of segId only happens for indices between start_idx "
                                           " and end_idx", type=int, default=None)
    cparser.add_argument("--do_increase", help="whether to increase instead of decrease the indices",
                         action="store_true")
    cargs = cparser.parse_args()

    main(**vars(cargs))
