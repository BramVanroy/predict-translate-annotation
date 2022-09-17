"""Extract source and target texts from TMX files. Results will be saved in separate files for
 the source and target text. Requires the "lxml" and "translate-toolkit" to be installed."""
from pathlib import Path
from translate.storage.tmx import tmxfile


def process(pfin, pdout, src_lang, tgt_lang):
    pfout_src = pdout / pfin.with_suffix(f".{src_lang}").name
    pfout_tgt = pdout / pfin.with_suffix(f".{tgt_lang}").name
    with pfin.open("rb") as fhin, pfout_src.open("w", encoding="utf-8") as fhsrc, \
            pfout_tgt.open("w", encoding="utf-8") as fhtgt:
        tmx_file = tmxfile(fhin, src_lang, tgt_lang)
        for node in tmx_file.unit_iter():
            fhsrc.write(f"{node.source}\n")
            fhtgt.write(f"{node.target}\n")


def main(inp, dout, src_lang, tgt_lang):
    pin = Path(inp).resolve()
    pdout = Path(dout).resolve()

    if pin.is_file():
        process(pin, pdout, src_lang, tgt_lang)
    elif pin.is_dir():
        for pfin in pin.glob("*.tmx"):
            process(pfin, pdout, src_lang, tgt_lang)


if __name__ == "__main__":
    import argparse

    cparser = argparse.ArgumentParser(description=__doc__)

    cparser.add_argument("input", help="Input text file or directory to process. If a directory, all TMX files in it"
                                       " will be processed.")
    cparser.add_argument("dout", help="Path to output directory.")
    cparser.add_argument("--src_lang", default="", help="Source language code to use for extraction.")
    cparser.add_argument("--tgt_lang", default="", help="Target language code to use for extraction")

    cargs = cparser.parse_args()

    main(cargs.input,
         cargs.dout,
         cargs.src_lang,
         cargs.tgt_lang)
