"""Fixes src and tgt XML files after manually changing tokenization. Particularly, this script fixes the cur and id
   attributes. After modifying the manually edited files, it will check whether the number of characters (i.e. cursor
   positions) is the same between the new file and the original file.
   Make sure to back up your data before using this script!"""
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET


def _parse(fin):
    """Parse an XML file. Improves the error message by saying which file throws an error."""
    try:
        tree = ET.parse(fin)
    except ET.ParseError as e:
        raise ET.ParseError(f"Error parsing {fin}: {str(e)}")

    return tree


def process_man_file(pfin):
    """Updates the id and cur attributes of given files to ensure that they are sequential, and write output to the
       same file.
    :param pfin: input file
    """
    tree = _parse(pfin)

    curr_cursor = 0
    curr_id = 1
    idx_map = defaultdict(list)
    for word in tree.findall(".//W"):
        idx_map[int(word.get("id"))].append(curr_id)
        space_len = len(word.get("space")) if "space" in word.attrib else 0
        word.set("cur", str(curr_cursor + space_len))
        word.set("id", str(curr_id))

        curr_cursor += space_len + len(word.text)
        curr_id += 1

    tree.write(pfin, encoding="utf-8")


def verify_cursor(pforig, pfman):
    """Verify that the number of characters (i.e. the final cursor position) is identical between the manually
       modified file and the original file.
    :param pforig: path to the original file
    :param pfman: path to the manually edited file
    :return: whether or not the files have the same number of characters/cursor positions
    """
    tree_o = _parse(pforig)
    tree_m = _parse(pfman)

    o_last_word = tree_o.findall(".//W")[-1]
    m_last_word = tree_m.findall(".//W")[-1]

    o_last_cursor = int(o_last_word.get("cur")) + len(o_last_word.text)
    m_last_cursor = int(m_last_word.get("cur")) + len(m_last_word.text)

    if o_last_cursor != m_last_cursor:
        print(f"Number of characters differs for {pforig.name}: {o_last_cursor} (orig), {m_last_cursor} (edited)."
              " You should check your file and make sure all needed space-attributes are present and that tokenisation"
              " is correct. Particularly, check for missing space attributes near \'\"-()[]&{}). ")

    return o_last_cursor == m_last_cursor


def group_files(origfs, manfs):
    """Group together the corresponding files, e.g. P01_T01.src of the original and of the manually edited directory"""
    groups = []
    for pf in origfs:
        try:
            groups.append((pf, next(f for f in manfs if str(f).endswith(pf.name))))
        except StopIteration:
            pass

    return groups


def main(dir_orig, dir_man):
    """Main entrypoint for the script. First group files together based on their names, then modify the manually edited
       files to fix the id and cur attributes, and finally verify the number of characters."""
    dir_orig = Path(dir_orig).resolve()
    orig_files = list(dir_orig.glob("*.src")) + list(dir_orig.glob("*.tgt"))

    dir_man = Path(dir_man).resolve()
    man_files = list(dir_man.glob("*.src")) + list(dir_man.glob("*.tgt"))

    # Groups identical filenames together, e.g. P01_T01.src of the original and of the manually edited
    dir_groups = group_files(orig_files, man_files)

    for f_orig, f_man in dir_groups:
        process_man_file(f_man)
        verify_cursor(f_orig, f_man)


if __name__ == '__main__':
    import argparse

    cparser = argparse.ArgumentParser(description=__doc__)

    cparser.add_argument("dir_orig", help="Input directory containing original files.")
    cparser.add_argument("dir_man", help="Input directory containing manually corrected files.")

    cargs = cparser.parse_args()
    main(cargs.dir_orig, cargs.dir_man)
