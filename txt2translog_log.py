"""Extract text from given source and target texts and use it to generate a Translog log file which can be used
   in the TPR-DB.
   Make sure to back up your data before using this script!"""
from copy import deepcopy
from pathlib import Path
import xml.etree.ElementTree as ET


SPECIAL_CHARS = {
    "<": "&lt;",
    ">": "&gt;",
    "&": "&amp;",
    "'": "&apos;",
    '"': "&quot;",
}


def map_special_chars(char):
    try:
        return SPECIAL_CHARS[char]
    except KeyError:
        return char


def add_char_pos(text):
    """Turn text into CharPos elements. Use a height of 26pt and width of 16pt per character.
    :param text:
    :return:
    """
    cur = 0
    x = 0
    y = 27
    for char in text:
        char = map_special_chars(char)
        yield ET.fromstring(f'<CharPos Cursor="{cur}" Value="{char}" X="{x}" Y="{y}" Width="16" Height="26"/>')
        cur += 1
        x += 16
        if char == "\n":
            x = 0
            y += 27


def indent(elem, level=0):
    """Borrowed from: https://stackoverflow.com/a/33956544/1150683"""
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def process_pair(pfsrc, pftgt, pdout, tree_base):
    root = tree_base.getroot()

    pfout = pdout.joinpath(pfsrc.with_suffix(".xml").name)
    # Set FileName to the correct path (the output path)
    root.find(".//FileName").text = str(pfout)

    src_text = pfsrc.read_text(encoding="utf-8")
    tgt_text = pftgt.read_text(encoding="utf-8")
    root.find(".//SourceText").text = src_text.replace("\n", "\\par\n")
    root.find(".//SourceTextUTF8").text = src_text
    root.find(".//FinalTextUTF8").text = tgt_text

    root.find(".//SourceTextChar").extend(list(add_char_pos(src_text)))
    root.find(".//FinalTextChar").extend(list(add_char_pos(tgt_text)))

    indent(root)
    tree_base.write(pfout, encoding="utf-8")


def group_files(srcfs, tgtfs):
    """Group together the corresponding files, e.g. P01_T01.src of the original and of the manually edited directory"""
    groups = []
    for pf in srcfs:
        try:
            groups.append((pf, next(f for f in tgtfs if f.stem == pf.stem)))
        except StopIteration:
            continue

    return groups


def main(fsrc, ftgt, dout, fbase, src_ext=None, tgt_ext=None):
    psrc = Path(fsrc).resolve()
    ptgt = Path(ftgt).resolve()
    pdout = Path(dout).resolve()
    tree_base = ET.parse(fbase)
    src_ext = "" if not src_ext else src_ext
    tgt_ext = "" if not tgt_ext else tgt_ext

    if psrc.is_dir():
        if not ptgt.is_dir():
            raise ValueError(f"'src' and 'tgt' must both be a file or both be a directory")
        src_files = list(psrc.glob(f"*{src_ext}"))
        tgt_files = list(ptgt.glob(f"*{tgt_ext}"))
        groups = group_files(src_files, tgt_files)

        for pfsrc, pftgt in groups:
            process_pair(pfsrc, pftgt, pdout, deepcopy(tree_base))
    elif psrc.is_file():
        if not ptgt.is_file():
            raise ValueError(f"'src' and 'tgt' must both be a file or both be a directory")

        process_pair(psrc, ptgt, pdout, deepcopy(tree_base))


if __name__ == '__main__':
    import argparse

    cparser = argparse.ArgumentParser(description=__doc__)

    cparser.add_argument("src", help="Input text file or directory to process.")
    cparser.add_argument("tgt", help="Input text file or directory to process.")
    cparser.add_argument("dout", help="Path to output directory.")
    cparser.add_argument("fbase", help="The XML Translog template to use as a base.")
    cparser.add_argument("--src_ext", default="", help="Only files with this extension will be processed.")
    cparser.add_argument("--tgt_ext", default="", help="Only files with this extension will be processed.")

    cargs = cparser.parse_args()

    main(cargs.src,
         cargs.tgt,
         cargs.dout,
         cargs.fbase,
         cargs.src_ext,
         cargs.tgt_ext)
