import argparse
from pathlib import Path
from typing import Iterable, Optional

from . import __author__, __version__, MarkdownParser, ParserBase


def parse_cli_arguments(content_to_parse: Optional[Iterable]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog='protocol_parser',
                                     description=f"CLI of the protocol_parser module for the islets module. "
                                                 f"Version: {__version__}\nWritten by {__author__}")
    parser.add_argument('--metadata-dir',
                        dest='metadata_dir',
                        help='Directory containing the metadata for the parser.')
    parser.add_argument('--output-dir',
                        dest='output_dir',
                        help='Directory, where the parsed files get written to.')
    parser.add_argument('--parser-type',
                        dest='parser_type',
                        default='MarkdownParser',
                        help='Type of the parser, which shall be used. (default: MarkdownParser)')
    parser.add_argument('input_file',
                        help='Path of the input file being used.')
    args = parser.parse_args() if content_to_parse is None else parser.parse_args(content_to_parse)
    return args


def main(args: Optional[argparse.Namespace]):
    parser: ParserBase

    args = parse_cli_arguments(args) if args is None else args
    meta_dir = Path(args.metadata_dir)
    output_dir = Path(args.output_dir)
    input_file = Path(args.input_file)
    if not meta_dir.is_dir() or not output_dir.is_dir() or not input_file.is_file():
        raise FileNotFoundError('Input parameter could not be located on the system!')

    if args.parser_type == 'MarkdownParser':
        parser = MarkdownParser(input_file, meta_dir)
    else:
        raise NotImplementedError(f'The parser "{args.parser_type}" is currently not implemented.')

    parsed_content = parser.parse()
    for experiment_name, protocol_df in parsed_content.items():
        protocol_df.to_csv((output_dir / f'{experiment_name}.csv').as_posix(), index=False)
