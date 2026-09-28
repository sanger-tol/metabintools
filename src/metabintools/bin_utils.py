from pathlib import Path


def get_extension(file: Path) -> str:
    if file.suffix == ".gz":
        return "".join(file.suffixes[-2:])
    return file.suffix


def get_basename(file: Path | str) -> str:
    if isinstance(file, str):
        file = Path(file)

    if file.suffix == ".gz":
        return file.name.rsplit(".", 2)[0]
    else:
        return file.name.rsplit(".", 1)[0]


def find_binsfiles(directory: Path) -> list[Path]:
    return [
        p
        for p in directory.glob("*")
        if get_extension(p)
        in {".fa", ".fna", ".fasta", ".fa.gz", ".fna.gz", ".fasta.gz"}
    ]
