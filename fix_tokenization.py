"""Fixes src and tgt XML files after manually changing tokenization. Particularly, this script fixes the cur and id
   attributes. After modifying the manually edited files, it will check whether the number of characters (i.e. cursor
   positions) is the same between the new file and the original file.
   Make sure to back up your data before using this script!"""
from html import unescape
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
    char_diff = 0
    for word in tree.findall(".//W"):
        space_len = len(word.get("space")) if "space" in word.attrib else 0
        word.set("cur", str(curr_cursor + space_len))
        word.set("id", str(curr_id))
        # TPR-DB unfortunately does not work with well-formed XML
        # and it does not play nice with encoded characters...
        # We keep track of the length of characters we encoded/modified
        # so that we can use this later to verify the correct length
        diff = len(word.text)
        word.text = unescape(word.text)
        char_diff += diff - len(word.text)

        # sort attributes to make sure that the order is always the same
        # does not matter if we use a real parser, but you never know...
        word.attrib = {k: word.attrib[k] for k in sorted(word.attrib)}

        curr_cursor += space_len + len(word.text)
        curr_id += 1

    tree.write(pfin, encoding="utf-8")

    return char_diff


def verify_cursor(pforig, pfman, char_diff):
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

    # This report includes the character difference after unescaping special characters
    # So the (edited) count is NOT the same as in the finale file, but final_cur+char_diff
    if o_last_cursor != m_last_cursor + char_diff:
        print(f"Number of characters differs for {pforig.name}: {o_last_cursor} (orig), {m_last_cursor + char_diff} (edited).")

    return o_last_cursor == m_last_cursor + char_diff


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

    n_processed = 0
    all_valid = True
    for f_orig, f_man in dir_groups:
        char_diff = process_man_file(f_man)
        valid = verify_cursor(f_orig, f_man, char_diff)
        if not valid:
            all_valid = False
        n_processed += 1

    if not all_valid:
        print("\nSome of your files have errors in them. You should check the files mentioned above and make sure all"
              " needed space-attributes are present and that tokenisation is correct. Particularly, check for missing"
              " space attributes near \'\"-()[]&{}). ")

    print(f"Finished processing {n_processed:,} .src and .tgt file(s).")

if __name__ == '__main__':
    import argparse

    cparser = argparse.ArgumentParser(description=__doc__)

    cparser.add_argument("dir_orig", help="Input directory containing original files.")
    cparser.add_argument("dir_man", help="Input directory containing manually corrected files.")

    cargs = cparser.parse_args()
    main(cargs.dir_orig, cargs.dir_man)
