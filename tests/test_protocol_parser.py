import pandas as pd

import protocol_parser
import pytest


#################################
# BEGIN TESTS - MARKDOWN PARSER #
#################################


@pytest.mark.parametrize(
    'markdown, metadata, result_csv',
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

            'compound,concentration,begin,end\n'
            'Glucose,6mM,,05:30\n'
            'Glucose,8mM,05:30,\n'
            'cAMP,25uM,27:00,43:30\n'
            'Caffeine,10mM,43:30,'
        )
    ]
)
def test_markdown_parser(markdown, metadata, result_csv, tmp_path):
    parser: protocol_parser.ParserBase

    # prepare temp-file for markdown
    d = tmp_path / 'parser_files'
    d.mkdir()
    p = d / 'markdown.md'
    p.write_text(markdown)

    # prepare temp-file for metadata
    for name, meta in metadata:
        m = d / f'.{name}.test.meta'
        m.write_text(meta)

    # prepare temp-file with result CSV data
    r = d / 'protocol.csv'
    r.write_text(result_csv)

    parser = protocol_parser.MarkdownParser(p, d)
    csv_df = pd.read_csv(r)
    parsed_protocols = parser.parse()
    assert pd.DataFrame.equals(csv_df, parsed_protocols)


@pytest.mark.parametrize(
    'markdown, name_list',
    [
        (
                '### Experiment086a:\n'
                '[00:00 - 20:00]: Glucose 4mM\n'
                '[20:00 - XX:XX]: Glucose 8mM\n'
                '### Experiment086b:\n'
                '[00:00 - 20:30]: Glucose 4mM\n'
                '[20:30 - XX:XX]: Glucose 8mM\n'
                '[00:00 - 12:00]: Glucose 8mM\n'
                '[12:00 - XX:XX]: Glucose 8mM, Epinephrine 5nM\n'
                '[00:00 - 05300]: Glucose 8mM, Epinephrine 5nM\n'
                '[03:00 - XX:XX]: Glucose 8mM\n'
                '### Experiment086c:\n'
                '[00:00 - 10:00]: Glucose 4mM\n'
                '[10:00 - XX:XX]: Glucose 8mM\n'
                '[00:00 - 05:00]: Glucose 8mM\n'
                '[05:00 - XX:XX]: Glucose 4mM\n'
                '### Experiment086d:\n'
                '[00:00 - XX:XX]: Glucose 4mM\n'
                '[00:00 - XX:XX]: Glucose 8mM',
                ['Experiment086a', 'Experiment086b', 'Experiment086c', 'Experiment086d']
        ),
        (
                '### Experiment084d:\n'
                '[00:00 - 05:30]: Glucose 6mM\n'
                '[05:30 - XX:XX]: Glucose 8mM\n'
                '[00:00 - 16:30]: Glucose 8mM, cAMP 25uM\n'
                '[16:30 - XX:XX]: Glucose 8mM, Caffeine 10mM',
                ['Experiment084d']
        ),
        (
                '',
                []
        )
    ]
)
def test_markdown_parser_experiment_names(markdown, name_list, tmp_path):
    # prepare temp-file for markdown
    d = tmp_path / 'parser_files'
    d.mkdir()
    p = d / 'markdown.md'
    p.write_text(markdown)

    parser = protocol_parser.MarkdownParser(p, d)
    assert parser.get_experiment_names() == name_list

###############################
# END TESTS - MARKDOWN PARSER #
###############################
