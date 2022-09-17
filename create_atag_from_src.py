import re
from pathlib import Path


def get_max_idx(lines):
    idxs = set([int(re.search("segId=\"(\d+)\"", line).group(1))
                       for line in lines if re.search("segId=\"(\d+)\"", line) is not None])
    return max(idxs)


def main(srcdir, outdir=None, ext=".src"):
    pfdir = Path(srcdir).resolve()
    pfout = Path(outdir) if outdir is not None else pfdir

    pfout.mkdir(exist_ok=True, parents=True)

    for pfin in pfdir.glob(f"*{ext}"):
        stem = pfin.stem
        lines = pfin.read_text(encoding="utf-8").splitlines()
        max_idx = get_max_idx(lines)
        s = f"""<DTAGalign sent_alignment="yawat" >
    <alignFile key="a" href="{stem}.src" sign="_input"/>
    <alignFile key="b" href="{stem}.tgt" sign="_input"/>
"""
        for i in range(1, max_idx+1):
            s += f'    <salign src="{i}" tgt="{i}"/>\n'

        s += "</DTAGalign>\n"
        (pfout / pfin.with_suffix(".atag").name).write_text(s, encoding="utf-8")


if __name__ == '__main__':
    import argparse

    cparser = argparse.ArgumentParser(description=__doc__)

    cparser.add_argument("srcdir", help="Input directory containing src files.")
    cparser.add_argument("--outdir", help="Output directory to write the atag files to. Uses input directory if not given.",
                         default=None)
    cparser.add_argument("--ext", help="Extension to use, e.g. src or tgt. These files will be used to get the max idx",
                         default=".src")

    cargs = cparser.parse_args()
    main(cargs.srcdir, cargs.outdir, cargs.ext)
