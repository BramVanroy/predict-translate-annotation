"""Extract text from a given text file and use it to generate a Translog project file while
   also preserving the style that was provided through a RTF file.
   Make sure to back up your data before using this script!"""
from copy import deepcopy
from pathlib import  Path
import xml.etree.ElementTree as ET


def process_file(pfin, pdout, tree_base, style):
    """Convert a text file into a Translog XML file by using a base XML template (tree_base),
       and a given string (RTF).
    :param pfin: input file whose contents will be placed on the source side of the XML file
    :param pdout: the output directory to write the resulting XML file to
    :param tree_base: the XML tree (ElementTree) that contains the XML Translog template
    :param style: the RTF text string. It must have "[{CONTENT}]" in it (without quotes).
       That part will be replaced by the actual contents of the input file on the source side.
    """
    tree = tree_base.getroot()

    pfout = pdout.joinpath(pfin.with_suffix(".project").name)
    # Set FileName to the correct path (the output path)
    tree.find("./FileName").text = str(pfout)

    src_text = pfin.read_text(encoding="utf-8")
    tree.find(".//SourceText").text = style.replace("[{CONTENT}]", src_text.replace("\n", "\\par\n"))
    tree.find(".//TargetText").text = style.replace("[{CONTENT}]", r"\par")
    tree.find(".//SourceTextUTF8").text = src_text

    tree_base.write(pfout, encoding="utf-8")


def main(fin, dout, fbase, fstyle, extension, recursive=False):
    """Main entry point to convert a text file, or all files with a given extension in a given directory,
       into a Translog-compatible XML file.
    :param fin: input file or directory
    :param dout: output directory to write the Translog projects to
    :param fbase: path to base XML file
    :param fstyle: path to RTF file. It must have "[{CONTENT}]" in it (without quotes).
           That part will be replaced by the actual contents of the input file on the source side.
    :param extension: only files with this extension will be processed when using a directory in 'fin'
    :param recursive: recursively process files when using a directory in 'fin'
    """
    pin = Path(fin).resolve()
    pdout = Path(dout).resolve()
    style = Path(fstyle).read_text(encoding="utf-8")
    tree_base = ET.parse(fbase)

    if pin.is_dir():
        files = pin.rglob(f"*{extension}") if recursive else pin.glob(f"*{extension}")

        for pfin in files:
            process_file(pfin, pdout, deepcopy(tree_base), style)
    elif pin.is_file():
        process_file(pin, pdout, deepcopy(tree_base), style)
    else:
        raise ValueError(f"Not a valid directory or file: {fin}")


if __name__ == '__main__':
    import argparse

    cparser = argparse.ArgumentParser(description=__doc__)

    cparser.add_argument("inp", help="Input text file or directory to process.")
    cparser.add_argument("dout", help="Path to output directory.")
    cparser.add_argument("fbase", help="The XML Translog template to use as a base.")
    cparser.add_argument("fstyle", help="A file containing the RTF instructions regarding style.")
    cparser.add_argument("-e", "--extension", default=".txt", help="Only files with this extension will be processed.")
    cparser.add_argument("-r", "--recursive", action="store_true",
                         help="If 'inp' is a directory, traverse it recursively.")

    cargs = cparser.parse_args()

    main(cargs.inp,
         cargs.dout,
         cargs.fbase,
         cargs.fstyle,
         cargs.extension,
         cargs.recursive)
