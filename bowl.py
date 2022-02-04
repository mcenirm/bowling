import argparse
import inspect
import sys
import textwrap
import typing

import rich


class Alley:
    ...


class Lane:
    ...


def init():
    """TODO Initialize alley"""
    ...


def bowl():
    """TODO Bowl"""
    ...


########## development commands ##########


def dev_init():
    """Prepare for development"""
    # TODO check venv ($VIRTUAL_ENV)
    # TODO check dependencies


def dev_pytest():
    """TODO Run tests"""
    ...


########## argument parsing ##########


def build_arg_parser(
    *,
    prog: str = __name__,
    subcommands: list[typing.Callable] = [
        bowl,
        init,
        dev_init,
        dev_pytest,
    ],
) -> argparse.ArgumentParser:
    def add(parser: argparse.ArgumentParser, tree: dict, /) -> None:
        """Recursively add subcommands to a parser"""
        subparsers = parser.add_subparsers(dest="COMMAND", required=True)
        for name, func_or_subtree in tree.items():
            if isinstance(func_or_subtree, dict):
                subtree = func_or_subtree
                add(subparsers.add_parser(name), subtree)
            else:
                func = func_or_subtree
                desc, params = description_and_parameters_from_function(func)
                p = subparsers.add_parser(name, description=desc)
                for args, kwargs in params:
                    p.add_argument(*args, **kwargs)

    if prog == "__main__":
        prog = sys.argv[0]
    parser = argparse.ArgumentParser(prog=prog)
    add(parser, build_tree(subcommands, lambda f: f.__name__.split("_")))
    return parser


def build_tree(
    items: typing.Iterable,
    getpath: typing.Callable[[typing.Any], list] = lambda o: str(o).split(),
    /,
) -> dict:
    """Build a recursive dictionary"""
    collision_msg = "collision at path {!r}"
    tree = {}
    for item in items:
        path = getpath(item)
        place = tree
        for i, step in enumerate(path[:-1]):
            if step not in place:
                place[step] = {}
            assert isinstance(place[step], dict), collision_msg.format(path[: i + 1])
            place = place[step]
        assert path[-1] not in place, collision_msg.format(path)
        place[path[-1]] = item
    return tree


def test_build_tree():
    import pytest

    assert build_tree(["a", "b 1", "b 2", "c"]) == {
        "a": "a",
        "b": {"1": "b 1", "2": "b 2"},
        "c": "c",
    }
    with pytest.raises(AssertionError):
        build_tree(["a b c"] * 2)
    with pytest.raises(AssertionError):
        build_tree([1, 2, 3], lambda n: ["x"] * n)


def description_and_parameters_from_function(func: typing.Callable) -> tuple[str, list]:
    lines = textwrap.dedent(func.__doc__).splitlines()
    spec = inspect.getfullargspec(func)
    return lines[0], [[_] for _ in spec.args]


def test_description_and_parameters_from_function():
    """TODO test functions with parameters"""
    import pytest

    def function_without_parameters():
        """This function has no parameters"""

    d, p = description_and_parameters_from_function(function_without_parameters)
    assert d == function_without_parameters.__doc__
    assert p == []

    def function_with_parameters_but_no_details(a, b, c):
        """This function has parameters but does not explain them"""
        ...

    d, p = description_and_parameters_from_function(
        function_with_parameters_but_no_details
    )
    assert d == function_with_parameters_but_no_details.__doc__
    assert p == [[_] for _ in "abc"]


def parse_args(args: list[str] = sys.argv[1:]):
    return build_arg_parser().parse_args(args=args)


########## CLI driver ##########


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
