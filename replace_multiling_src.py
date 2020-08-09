"""Replaces all occurrences of a given *T*.src file with a pre-existing corresponding T*.src file.
   E.g. if datap contains P01_T01.src and replp contains T01.src, then the contents of P01_T01.src will
   be replaced by those of T01.src. Useful for multiLing, where pre-existing .src files are available.

   Make sure to back up your data before using this script!"""

from pathlib import Path


def main(datap, replp):
    """Main entrypoint to replace .src files in 'datap' by corresponding .src. files in 'replp'.
    :param datap: input directory whose .src files will be replaced with corresponding files from 'replp'
    :param replp: input directory whose .src files will be used to replace those in 'datap'
    """
    repl_files = {p.name: p for p in Path(replp).glob("*.src")}
    data_files = {p.name: p for p in Path(datap).glob("*.src")}

    for fname, pfin in data_files.items():
        # Find corresponding file: the file that fname ends with, e.g.
        # fname: P01_T01.src; frepl: T01.src
        prepl = next(pfrepl for frepl, pfrepl in repl_files.items() if fname.endswith(frepl))

        # remove existing file
        pfin.unlink()
        # read bytes of the replacement file and write it to the original's path
        pfin.write_bytes(prepl.read_bytes())


if __name__ == '__main__':
    import argparse

    cparser = argparse.ArgumentParser(description=__doc__)

    cparser.add_argument("datap",
                         help="Input directory whose .src files will be replaced with corresponding"
                              " files from 'replp'.")
    cparser.add_argument("replp", help="Input directory whose .src files will be used to replace those in 'datap'.")

    cargs = cparser.parse_args()

    main(cargs.datap, cargs.replp)
