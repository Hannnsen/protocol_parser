from typing import List, Tuple

import pandas as pd

from protocol_parser.cli import main, parse_cli_arguments
import pytest


@pytest.mark.parametrize(
    'markdown, metadata, result_csvs',
    [
        (
            '### Experiment084d:\n'
            '[00:00 - 05:30]: Glucose 6mM\n'
            '[05:30 - XX:XX]: Glucose 8mM\n'
            '[00:00 - 16:30]: Glucose 8mM, cAMP 25uM\n'
            '[16:30 - XX:XX]: Glucose 8mM, Caffeine 10mM',
            [
                ('Experiment084d',
                 ',Name,SizeT,SizeX,SizeY,SizeZ,Nchannels,pxSize,pxUnit,bit depth,Frequency,Start time,End time,'
                 'Duration, line scan\n '
                 '0,Image001,1,1024,1024,1,1,0.250,µm,uint8,,2022-03-23 17:28:16,,,none\n'
                 '1,Series002,32000,256,256,1,1,1.00,µm,uint8,19.7,2022-03-23 17:28:48,2022-03-23 17:55:48.838001251,'
                 '0 days 00:27:00.838001251,none\n '
                 '2,Series003,32000,256,256,1,1,1.00,µm,uint8,19.7,2022-03-23 17:55:50,2022-03-23 18:22:50.853000641,'
                 '0 days 00:27:00.853000641,none\n '
                 '3,Series004,5979,256,256,1,1,1.00,µm,uint8,19.7,2022-03-23 18:22:51,2022-03-23 18:27:53.795000076,'
                 '0 days 00:05:02.795000076,none ')
            ],
            [
                ('Experiment084d',
                 'compound,concentration,begin,end\n'
                 'Glucose,6mM,,05:30\n'
                 'Glucose,8mM,05:30,\n'
                 'cAMP,25uM,27:00,43:30\n'
                 'Caffeine,10mM,43:30,')
            ]
        )
    ]
)
def test_cli_markdown_parser(markdown: str,
                             metadata: List[Tuple[str, str]],
                             result_csvs: List[Tuple[str, str]],
                             tmp_path):
    # prepare temp-file for markdown
    d = tmp_path / 'files_to_parse'
    d.mkdir()
    p = d / 'markdown.md'
    p.write_text(markdown)

    # prepare temp-file for metadata
    for name, meta in metadata:
        m = d / f'.{name}.test.meta'
        m.write_text(meta)

    # prepare temp-file with result CSV data
    for experiment_name, result_csv in result_csvs:
        r = d / f'{experiment_name}.csv'
        r.write_text(result_csv)

    o = tmp_path / 'output'
    o.mkdir()

    args = parse_cli_arguments(['--metadata-dir', f'{d.as_posix()}',
                                '--output-dir', f'{o.as_posix()}',
                                '--parser-type', 'MarkdownParser',
                                f'{p.as_posix()}'])
    main(args)

    for file in o.iterdir():
        if file.suffix == '.csv':
            parsed_protocol = pd.read_csv(file.as_posix())
            parsed_protocol.sort_values(by=['begin', 'compound', 'concentration'], na_position='first',
                                        inplace=True, ignore_index=True)

            experiment_name = file.stem
            assert (d / f'{experiment_name}.csv').is_file()

            sample_protocol = pd.read_csv((d / f'{experiment_name}.csv').as_posix())
            sample_protocol.sort_values(by=['begin', 'compound', 'concentration'], na_position='first',
                                        inplace=True, ignore_index=True)

            pd.testing.assert_frame_equal(parsed_protocol, sample_protocol, check_like=True)


def test_cli_exception_parser(tmp_path):
    args = parse_cli_arguments(['--metadata-dir', f'dir_doesnt_exist',
                                '--output-dir', f'output_will_not_happen',
                                '--parser-type', 'FaultyParser',
                                f'markdown_will_not_be_parsed.md'])
    with pytest.raises(FileNotFoundError):
        main(args)

    meta_dir = tmp_path / 'dir_doesnt_exist'
    meta_dir.mkdir()
    out_dir = tmp_path / 'output_will_not_happen'
    out_dir.mkdir()
    m = tmp_path / 'markdown_will_not_be_parsed.md'
    m.touch()

    args = parse_cli_arguments(['--metadata-dir', f'{meta_dir.as_posix()}',
                                '--output-dir', f'{out_dir.as_posix()}',
                                '--parser-type', 'FaultyParser',
                                f'{m.as_posix()}'])
    with pytest.raises(NotImplementedError):
        main(args)
