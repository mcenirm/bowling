import argparse
import sys
import typing

import rich


class Alley:
    ...


class Lane:
    ...


def devinit():
    """Prepare for development"""
    ...


def init():
    """TODO Initialize alley"""
    ...


def bowl():
    """TODO Bowl"""
    ...


def build_arg_parser(
    *,
    prog: str = __name__,
    subcommands: list[typing.Callable] = [
        bowl,
        init,
        devinit,
    ],
) -> argparse.ArgumentParser:
    if prog == "__main__":
        prog = sys.argv[0]
    p = argparse.ArgumentParser(prog=prog)
    subparsers = p.add_subparsers(dest="COMMAND", required=True)
    for f in subcommands:
        subparsers.add_parser(f.__name__, description=f.__doc__)
        # TODO add_argument using function signature
    return p


def parse_args(args: list[str] = sys.argv[1:]):
    return build_arg_parser().parse_args(args=args)


def run_args(args):
    rich.print(args)
    func = globals().get(args.COMMAND, None)
    rich.print(func)
    # TODO call function using proper arguments


def main():
    args = parse_args()
    run_args(args)


if __name__ == "__main__":
    main()
