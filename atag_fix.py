"""Fixes atag XML files after manually changing tokenization. Particularly, this script fixes the `id` of words
   to match the modifed ids that the words received after running the fix_tokenization.py script.
   *Never run this script on the same data twice. That will throw errors!* Only want to run it over a few files
    that you edited? Copy those files to a separate directory, and use that directory for this script.
   Make sure to back up your data before using this script!"""
from copy import deepcopy
from pathlib import Path
from typing import Dict
import xml.etree.ElementTree as ET


class AtagFixer:
    def __init__(self, fsorig: Dict, fsman: Dict):
        # {P01_T01: {"src": "/home/.../P01_T01.src", "tgt": "/home/.../P01_T01.tgt", "atag": "/home/.../P01_T01.atag"}
        self.fsorig = fsorig
        self.fsman = fsman

        # {P01_T01: {"1": {"src": ET.tree with W's, "tgt": ET.tree with W's}, "2": ...}
        self.sents_orig = self.extract_sents(self.fsorig)
        self.sents_man = self.extract_sents(self.fsman)
        self.sent_aligns = self.get_sent_align(self.fsman)

    @staticmethod
    def get_sent_align(files):
        """For each identifier (e.g. P01_T01), get the sentence alignments as a dictionary mapping from
           source segment index to the target.

        :param files: dictionary that looks like {identifier: {src: ..., tgt: ..., atag: ...}
        :return: dictionary of identifiers with a mapping from src to tgt indices
        """
        alignments = {}
        for identifier, files_d in files.items():
            pfin = files_d["atag"]
            tree = ET.parse(pfin)
            salign = tree.findall(".//salign")
            alignments[identifier] = {el.get("src"): el.get("tgt") for el in salign}

        return alignments

    def extract_sents(self, files):
        """Extract the sentences as XML trees."""
        res = {}
        for identifier, type_d in files.items():
            # {src: idx: sent}
            src_sents = self._extract_sents(type_d["src"])
            tgt_sents = self._extract_sents(type_d["tgt"])

            # convert {src: idx: sent} and {tgt: idx: sent} to {idx: src: sent, tgt: sent}
            res[identifier] = {}
            for seg_id, sent in src_sents.items():
                res[identifier][seg_id] = {"src": sent}

            for seg_id, sent in tgt_sents.items():
                if seg_id in res[identifier]:
                    res[identifier][seg_id]["tgt"] = sent
                else:
                    res[identifier][seg_id] = {"tgt": sent}

        return res

    @staticmethod
    def _extract_sents(pfin):
        """Extract sentence as XML tree of W elements"""
        tree = ET.parse(pfin)
        sents = {}
        for word in tree.findall(".//W"):
            seg_id = word.get("segId")
            if seg_id not in sents:
                sents[seg_id] = ET.fromstring("<tree/>")

            sents[seg_id].append(word)

        return sents

    def elements_equal(self, e1, e2):
        """Check whether two XML trees at least have the same node with the same text values.
           So, re-tokenized trees will not be seen as equal."""
        # Modified from https://stackoverflow.com/a/24349916/1150683
        if e1.text != e2.text:
            return False
        if len(e1) != len(e2):
            return False
        return all(self.elements_equal(c1, c2) for c1, c2 in zip(e1, e2))

    def fix_atag_alignments(self):
        """Main entry point to fix the atag files."""
        n_processed = 0
        all_valid = True
        has_error = False
        segment_not_found = False
        for identifier, sents_d in self.sents_orig.items():
            if identifier not in self.sents_man:
                print(f"File {identifier} not found in manual correction. Skipping...")
                continue

            valid_src_segs = []
            for src_seg_id, direction_d in sents_d.items():
                try:
                    src_orig_tree = direction_d["src"]
                except KeyError:
                    segment_not_found = True
                    print(f"WARNING 2: No segment {src_seg_id} found for {identifier} in the original .src file."
                          f" Skipping this segment and its alignment.")
                    continue

                src_man_tree = self.sents_man[identifier][src_seg_id]["src"]

                tgt_seg_id = self.sent_aligns[identifier][src_seg_id]

                try:
                    tgt_orig_tree = self.sents_orig[identifier][tgt_seg_id]["tgt"]
                except KeyError:
                    segment_not_found = True
                    print(f"WARNING 2: No segment {tgt_seg_id} found for {identifier} in the original .tgt file."
                          f" Skipping this segment and its alignment...")
                    continue

                tgt_man_tree = self.sents_man[identifier][tgt_seg_id]["tgt"]

                if self.elements_equal(src_orig_tree, src_man_tree) and \
                        self.elements_equal(tgt_orig_tree, tgt_man_tree):
                    valid_src_segs.append(src_seg_id)
                else:
                    print(f"WARNING 1: NOT identical for {identifier}, aligned pair {src_seg_id}-{tgt_seg_id}.")
                    all_valid = False

            if valid_src_segs:
                error = self.update_atag(identifier, valid_src_segs)
                if error:
                    has_error = True
                n_processed += 1

        if has_error:
            print(f"\nThe 'possible errors' that occurred likely happen because you ran this script twice on the same"
                  f" data. Once an atag file has been fixed, trying to fix it again will lead to errors. In most cases"
                  f" you can ignore those warnings. In the future, though, it is best to only run the script only once"
                  f" over the same files. Only want to run it over a few files that you edited? Copy those files to a"
                  f" separate directory, and use that directory for this script.")

        if not all_valid:
            print(f"\nAfter uploading files to TPR-DB/YAWAT, the 'WARNING 1' sentence pairs above will need to be"
                  f" re-aligned. If they are also part of a 'possible errors' warning, there are underlying issues"
                  f" and they were not processed.")

        if segment_not_found:
            print(f"\nSome segments were expected but not found (WARNING 2). That is not an issue when you expect that"
                  f" some segments are not translated.")

        print(f"Finished processing {n_processed:,} .atag file(s).")

    @classmethod
    def from_dirs(cls, dir_orig, dir_man):
        """Create class from given input directories."""
        # {P01_T01: {"src": "/home/.../P01_T01.src", "tgt": "/home/.../P01_T01.tgt", "atag": "/home/.../P01_T01.atag"}
        pdorig = Path(dir_orig).resolve()
        pdman = Path(dir_man).resolve()

        def group_files(pdin):
            grouped_fs = {}
            for pfin in pdin.glob("*.src"):
                grouped_fs[pfin.stem] = {"src": pfin,
                                         "tgt": pfin.with_suffix(".tgt"),
                                         "atag": pfin.with_suffix(".atag")}

            # Listify so we can delete the keys when necessary
            for fname in list(grouped_fs.keys()):
                for p in grouped_fs[fname].values():
                    if not p.exists():
                        print(f"Warning: file {p} not found. NOT processing files of {p.parent.joinpath(p.stem)}")
                        del grouped_fs[fname]

            return grouped_fs

        origfs = group_files(pdorig)
        manfs = group_files(pdman)

        return cls(origfs, manfs)

    def orig_man_mapping(self, identifier, seg_id, direction):
        """Create a mapping between the IDs of a given word in the original file
           to the manually edited value."""
        orig_tree = self.sents_orig[identifier][seg_id][direction]
        man_tree = self.sents_man[identifier][seg_id][direction]

        mapping = {}
        for orig_el, man_el in zip(orig_tree, man_tree):
            mapping[orig_el.get("id")] = man_el.get("id")

        return mapping

    def update_atag(self, identifier, valid_segs):
        """Update the atag files based on the previously created mappings.
           Copy, change and append sentence subtrees to a new tree (valid_tree),
           if a sentence is not able to be saved, do not add it to the new tree."""
        pfin = self.fsman[identifier]["atag"]
        tree = ET.parse(pfin)
        tree_root = tree.getroot()

        # Copy tree and remove all align elements
        valid_tree = deepcopy(tree)
        valid_tree_root = valid_tree.getroot()
        for align in valid_tree.findall(".//align"):
            valid_tree_root.remove(align)

        align_keys = tree.findall(".//alignFile")
        a_keyfiles = {Path(el.get("href")).suffix.replace(".", ""): el.get("key") for el in align_keys}

        has_error = False
        # For a given segment pair, find the mappings of their tokens
        for src_seg_id in valid_segs:
            tgt_seg_id = self.sent_aligns[identifier][src_seg_id]
            idx_maps = {"src": self.orig_man_mapping(identifier, src_seg_id, "src"),
                        "tgt": self.orig_man_mapping(identifier, tgt_seg_id, "tgt")}

            # Iterate over the source tokens so that we can map them
            for orig_src_token_idx, man_src_token_idx in idx_maps["src"].items():
                src_xml_id = f"{a_keyfiles['src']}{orig_src_token_idx}"

                for el in tree.findall(f".//align[@out='{src_xml_id}']"):
                    try:
                        el.set("out", f"{a_keyfiles['src']}{man_src_token_idx}")
                        prev_out = el.get("in")[1:]
                        el.set("in", f"{a_keyfiles['tgt']}{idx_maps['tgt'][prev_out]}")
                    except KeyError:
                        has_error = True

                    if has_error:
                        print(f"POSSIBLE ERROR: an error occurred for {identifier}. Skipping file...")
                        return has_error

                    valid_tree_root.append(el)
                    # need to remove from original tree to prevent recursion problems
                    # if we change index of a node, it will be found by the query for that new index
                    tree_root.remove(el)

        # sort align nodes. No functional difference, but easier to have a look at files
        # by setting default to a0 or b0, the salign nodes will not be affected and stay at the top
        valid_tree_root[:] = sorted(valid_tree_root, key=lambda node: (int(node.get("in", "b0")[1:]),
                                                                       int(node.get("out", "a0")[1:])))

        valid_tree.write(pfin)

        return has_error


if __name__ == '__main__':
    import argparse

    cparser = argparse.ArgumentParser(description=__doc__)

    cparser.add_argument("dir_orig",
                         help="Input directory containing original files. Must include .src, .tgt., and .atag files.")
    cparser.add_argument("dir_man",
                         help="Input directory containing manually corrected files. Must include .src, .tgt.,"
                              " and .atag files.")

    cargs = cparser.parse_args()

    fixer = AtagFixer.from_dirs(cargs.dir_orig, cargs.dir_man)
    fixer.fix_atag_alignments()
