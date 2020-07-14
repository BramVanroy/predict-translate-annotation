"""Modify Translog XML files by automatically inserting tags for source and target language
   and for the task. So we are automating the steps given here:
   https://sites.google.com/site/centretranslationinnovation/tpr-db/uploading#h.p_GnRMB54i2wUL.

   Make sure to back up your data before using this script!"""


from pathlib import  Path
import xml.etree.ElementTree as ET


def process_file(pfin, src_lang="en", tgt_lang="nl", task="translating"):
    """Insert a Languages element in the given XML file and write output to the same file.
    :param pfin: input file
    :param src_lang: abbreviation of source language (e.g. en)
    :param tgt_lang: abbreviation of target language (e.g. nl)
    :param task: task (e.g. translating)
    """
    tree = ET.parse(pfin)

    if tree.find(".//Languages") is not None:
        print(f"File {pfin} already has a Languages element. Skipping...")
        return

    # ET is quite basic (it's built-in), and is lacking some convenient methods such as
    # getting the parent. Instead, we make a map of child-parents, and find the parent that way
    parent_map = {c: p for p in tree.iter() for c in p}

    lock_windows = tree.find(".//lockWindows")
    try:
        parent = parent_map[lock_windows]
    except KeyError:
        raise KeyError("Your XML does not have a lockWindows element, which is required.")

    languages = ET.Element("Languages", attrib={"source": src_lang, "target": tgt_lang, "task": task})
    # Make sure that we end in newline + right number of spaces. Might be important
    # if the file is parsed with a bad, naive parser
    languages.tail = lock_windows.tail
    # Insert the new element in the parent of lockWindows and after the index of lockWindows
    parent.insert(list(parent).index(lock_windows) + 1, languages)

    tree.write(pfin, encoding="utf-8")


def main(fin, src_lang="en", tgt_lang="nl", task="translating", recursive=False):
    """Main entrypoint for the script which decides which course to take depending on 'fin'.
       If it is a directory, modify all files. If it is a file, only change that one file.
    :param fin: input file or directory
    :param src_lang: abbreviation of source language (e.g. en)
    :param tgt_lang: abbreviation of target language (e.g. nl)
    :param task: task (e.g. translating)
    :param recursive: whether to recursively change all files if 'fin' is a directory
    """
    pin = Path(fin).resolve()

    if pin.is_dir():
        files = pin.rglob("*.xml") if recursive else pin.glob("*.xml")

        for pfin in files:
            process_file(pfin, src_lang, tgt_lang, task)
    elif pin.is_file():
        process_file(pin)
    else:
        raise ValueError(f"Not a valid directory or file: {fin}")


if __name__ == '__main__':
    import argparse

    cparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                      description=__doc__)

    cparser.add_argument("inp", help="Input file or directory to process.")
    cparser.add_argument("-s", "--src_lang", default="en", help="Abbreviation for source language.")
    cparser.add_argument("-t", "--tgt_lang", default="nl", help="Abbreviation for target language.")
    cparser.add_argument("--task", default="translating", help="Task (e.g. copying, translating, postediting).")
    cparser.add_argument("-r", "--recursive", action="store_true",
                         help="If 'inp' is a directory, traverse it recursively.")

    cargs = cparser.parse_args()

    main(cargs.inp,
         cargs.src_lang,
         cargs.tgt_lang,
         cargs.task,
         cargs.recursive)
