import argparse
import dataclasses
import inspect
import os
import pathlib
import sys
import textwrap
import typing
import venv

# TODO maybe remove rich import?
try:
    import rich
except ImportError:
    rich = type("", (), {})()
    rich.print = print


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


# region development commands


def dev_init():
    """Prepare for development"""
    if not is_in_venv():
        # TODO maybe check if venv exists, but is not activated?
        venv_path = pathlib.Path(__file__).parent / "venv"
        hr = "-" * 40
        print(hr, file=sys.stderr)
        venv.create(venv_path, with_pip=True, upgrade_deps=True)
        print(hr, file=sys.stderr)
        lines = [
            "Created a new virtual environment at: {path}",
            "",
            *textwrap.wrap(
                "Activate the virtual environment using the appropriate"
                " command for your shell, then try again:"
            ),
            "",
        ]
        if os.name == "posix":
            lines.extend(
                [
                    "  bash/zsh         |  source {path}/bin/activate",
                    "  fish             |  source {path}/bin/activate.fish",
                    "  csh/tcsh         |  source {path}/bin/activate.csh",
                    "  PowerShell Core  |  {path}/bin/Activate.ps1",
                ]
            )
        elif os.name == "nt":
            lines.extend(
                [
                    r"  cmd.exe     |  {path}\Scripts\activate.bat",
                    r"  PowerShell  |  {path}\Scripts\Activate.ps1",
                ]
            )
        msg = "\n".join(lines).format(path=str(venv_path))
        print(msg, file=sys.stderr)
        print(hr, file=sys.stderr)
    # TODO check dependencies
    raise NotImplementedError()


def dev_pytest():
    """TODO Run tests"""
    ...


# endregion


# region development support


def is_in_venv(environ=os.environ) -> bool:
    venv_location = environ.get("VIRTUAL_ENV", None)
    if not venv_location:
        return False
    return (pathlib.Path(venv_location) / "pyvenv.cfg").exists()


def test_is_in_venv(tmp_path: pathlib.Path):
    def is_in_venv_with_environ(environ: dict) -> bool:
        return is_in_venv(environ=environ)

    assert not is_in_venv_with_environ({})
    tmp_venv_path = tmp_path / "venv"
    if tmp_venv_path.exists():
        import shutil

        shutil.rmtree(tmp_venv_path)
    tmp_environ = dict(VIRTUAL_ENV=str(tmp_venv_path))
    assert not is_in_venv_with_environ(tmp_environ)
    venv.create(tmp_venv_path)
    assert is_in_venv_with_environ(tmp_environ)


# endregion


# region argument parsing


@dataclasses.dataclass
class ArgumentParserAddArgumentArguments:
    # Either a name or a list of option strings, e.g. foo or -f, --foo.
    name_or_flags: list[str] = dataclasses.field(default_factory=list)

    # The basic type of action to be taken when this argument is encountered at the command line.
    # action: typing.Union[str, typing.Type[argparse.Action]]

    # The number of command-line arguments that should be consumed.
    # nargs: typing.Union[int, str]

    # A constant value required by some action and nargs selections.
    # const: typing.Any

    # The value produced if the argument is absent from the command line and if it is absent from the namespace object.
    # default: typing.Any

    # The type to which the command-line argument should be converted.
    # type: typing.Union[typing.Callable[[str], argparse._T @ add_argument], argparse.FileType]

    # A container of the allowable values for the argument.
    # choices: typing.Union[typing.Iterable[argparse._T @ add_argument], None]

    # Whether or not the command-line option may be omitted (optionals only).
    # required: bool

    # A brief description of what the argument does.
    # help: typing.Union[str, None]

    # A name for the argument in usage messages.
    # metavar: typing.Union[str, tuple[str, ...], None]

    # The name of the attribute to be added to the object returned by parse_args().
    # dest: typing.Union[str, None]

    # ...
    # version: str

    kwargs: dict = dataclasses.field(default_factory=dict)


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
        subparsers = parser.add_subparsers(
            title="subcommands",
            dest="COMMAND",
            required=True,
        )
        for name, func_or_subtree in tree.items():
            if isinstance(func_or_subtree, dict):
                subtree = func_or_subtree
                add(subparsers.add_parser(name), subtree)
            else:
                func = func_or_subtree
                desc, params = description_and_parameters_from_function(func)
                p = subparsers.add_parser(name, description=desc)
                p.set_defaults(func=func)
                for param in params:
                    p.add_argument(*param.name_or_flags, **param.kwargs)

    if prog == "__main__":
        prog = sys.argv[0]
    parser = argparse.ArgumentParser(prog=prog)
    add(parser, build_tree(subcommands, lambda f: f.__name__.split("_")))
    return parser


def test_build_arg_parser():
    def one():
        ...

    def two_a(a: str, b: int, c: list = []) -> None:
        """help for two a

        a: x
        b: y
        c: z"""

    def two_b():
        ...

    p = build_arg_parser(subcommands=[one, two_a, two_b])
    assert "{one,two}" in p.format_usage()
    assert p.parse_args(["one"]) == argparse.Namespace(COMMAND="one", func=one)
    assert p.parse_args("two a 1 2 3".split()) == argparse.Namespace(
        COMMAND="a", a="1", b="2", c="3", func=two_a
    )


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


def description_and_parameters_from_function(
    func: typing.Callable,
) -> tuple[str, list[ArgumentParserAddArgumentArguments]]:
    func_desc = ""
    param_descs = {}
    if func.__doc__:
        lines = textwrap.dedent(func.__doc__).splitlines()
        func_desc = lines[0]
        for line in lines:
            pd = parameter_name_and_description_from_docstring_line(line)
            if pd:
                pname, pdesc = pd
                param_descs[pname] = pdesc
    spec = inspect.getfullargspec(func)
    params = []
    for pname in spec.args:
        param = ArgumentParserAddArgumentArguments(name_or_flags=[pname])
        if pname in param_descs:
            param.kwargs["help"] = param_descs.pop(pname)
        params.append(param)
    return func_desc, params


def test_description_and_parameters_from_function():
    import pytest

    def function_without_parameters():
        """This function has no parameters"""

    d, p = description_and_parameters_from_function(function_without_parameters)
    assert d == function_without_parameters.__doc__
    assert p == []

    def function_with_parameters_but_no_details(a, b, c):
        """This function has parameters but does not explain them"""

    d, p = description_and_parameters_from_function(
        function_with_parameters_but_no_details
    )
    assert d == function_with_parameters_but_no_details.__doc__
    assert p == [ArgumentParserAddArgumentArguments(name_or_flags=[_]) for _ in "abc"]

    def function_with_parameters_with_details(a, b, c):
        """This function has parameters with details in docstring

        a: help message for a
        b: help message for b
        c: help message for c"""

    d, p = description_and_parameters_from_function(
        function_with_parameters_with_details
    )
    assert d == "This function has parameters with details in docstring"
    assert p == [
        ArgumentParserAddArgumentArguments(
            name_or_flags=[_],
            kwargs=dict(
                help=f"help message for {_}",
            ),
        )
        for _ in "abc"
    ]


def parameter_name_and_description_from_docstring_line(
    line: str,
) -> typing.Optional[tuple[str, str]]:
    parts = line.split(":", maxsplit=1)
    if len(parts) == 2:
        left, right = tuple([_.strip() for _ in parts])
        if left.isidentifier():
            return left, right
    return None


def test_parameter_name_and_description_from_docstring_line():
    import pytest

    for line in ["", "no marker"]:
        assert parameter_name_and_description_from_docstring_line(line) is None
    for left in ["example"]:
        for right in ["a description"]:
            line = f"{left}: {right}"
            assert parameter_name_and_description_from_docstring_line(line) == (
                left.strip(),
                right.strip(),
            )


def parse_args(args: list[str] = sys.argv[1:]):
    return build_arg_parser().parse_args(args=args)


# endregion


# region CLI driver


def run_args(args):
    kwargs = dict(vars(args))
    del kwargs["COMMAND"]
    del kwargs["func"]
    args.func(**kwargs)


def test_run_args():
    def make_f(results: list) -> typing.Callable:
        def f(a, *args, **kwargs):
            results.extend((a, args, kwargs))

        return f

    results = []
    f = make_f(results)
    run_args(argparse.Namespace(COMMAND="f", func=f, a="1", b="2"))
    assert results == ["1", (), {"b": "2"}]


def main():
    args = parse_args()
    run_args(args)


if __name__ == "__main__":
    main()


# endregion
