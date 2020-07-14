""" Reset counters such as time and cursors to compensate for manually removing data. We removed the first segment
    of some data, which was necessary (these headlines were not part of the original multiLing text).
    NOTE: it only changes the counters for T04, T05, and T06 because those were faulty in our data.
    Make sure to back up your data before using this script!"""


from pathlib import  Path
import xml.etree.ElementTree as ET


def fix_events(inp_tree, orig_tree):
    # ET is quite basic (it's built-in), and is lacking some convenient methods such as
    # getting the parent. Instead, we make a map of child-parents, and find the parent that way
    parent_map = {c: p for p in inp_tree.iter() for c in p}

    # Find the difference between the original's first key and the edited first key. We use this value
    # to rebase all timings in the edit, so that the first item starts at the same time as the original first item
    key_time_diff = int(inp_tree.find(".//Events/Key").get("Time")) - int(orig_tree.find(".//Events/Key").get("Time"))
    # Get the position of the first key, and use it to rebase keys to 0
    first_inp_key_cursor = int(inp_tree.find(".//Events/Key").get("Cursor"))

    for event in inp_tree.findall(".//Events/*"):
        if event.tag == "System":
            continue

        if "Cursor" in event.attrib:
            changed_cursor_pos = int(event.get("Cursor")) - first_inp_key_cursor

            # If cursor < 0, delete item (means someone tried to edit title but we removed title)
            if changed_cursor_pos < 0:
                parent_map[event].remove(event)
            else:
                event.set("Cursor", str(changed_cursor_pos))

        event.set("Time", str(int(event.get("Time")) - key_time_diff))


def fix_char_pos(inp_tree, xpath):
    # Get the position of the first key, and use it to rebase keys to 0
    first_char_cursor = int(inp_tree.find(xpath).get("Cursor"))

    for char_pos in inp_tree.findall(xpath):
        if "Cursor" in char_pos.attrib:
            char_pos.set("Cursor", str(int(char_pos.get("Cursor")) - first_char_cursor))


def process_file(pinp, porig):
    inp_tree = ET.parse(pinp)
    orig_tree = ET.parse(porig)

    fix_events(inp_tree, orig_tree)
    fix_char_pos(inp_tree, ".//SourceTextChar/CharPos")
    fix_char_pos(inp_tree, ".//FinalTextChar/CharPos")

    inp_tree.write(pinp, encoding="utf-8")


def main(dinp, dorig):
    inp_files = {p.name: p for p in Path(dinp).glob("*.xml")}
    orig_files = {p.name: p for p in Path(dorig).glob("*.xml")}

    for inp_name, pinp in inp_files.items():
        # Only change the affected files (4, 5,6)
        if inp_name.endswith(("T04.xml", "T05.xml", "T06.xml")):
            porig = orig_files[inp_name]
            process_file(pinp, porig)


if __name__ == '__main__':
    import argparse

    cparser = argparse.ArgumentParser(description=__doc__)

    cparser.add_argument("inp", help="Input directory to the manually edited XML.")
    cparser.add_argument("orig", help="Input directory to the original Translog XML files.")

    cargs = cparser.parse_args()

    main(cargs.inp, cargs.orig)
