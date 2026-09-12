"""Run the API with uvicorn: python -m evidence_dossier.api [store path] [gold directory].

The store path defaults to dossier.db in the working directory. Without a gold
directory, GET /evaluation answers 404. uvicorn is a dev dependency, so the
module reports a missing install instead of failing on import.
"""

import sys


def main(argv: list[str]) -> int:
    try:
        import uvicorn
    except ImportError:
        print("uvicorn is not installed; install the dev extras to run the API", file=sys.stderr)
        return 1
    from evidence_dossier.api import create_app

    store_path = argv[1] if len(argv) > 1 else "dossier.db"
    gold_dir = argv[2] if len(argv) > 2 else None
    uvicorn.run(create_app(store_path, gold_dir=gold_dir), host="127.0.0.1", port=8000)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
