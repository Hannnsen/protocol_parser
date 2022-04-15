import re
import warnings
from pathlib import Path
from typing import Dict, List, Union

import numpy as np
import pandas as pd

from . import ParserBase


class MarkdownParser(ParserBase):
    __metadata_files: Dict[str, Path]

    def __init__(self, filepath: Union[str, Path], metadata_directory: Union[Path]):
        """Standard constructor for a MarkdownParser object.

        Parameters
        ----------
        filepath : str | Path
            Markdown file, which will get parsed.
        metadata_directory : Path
            Directory, which contains the files with the experiment metadata.
        """
        self.filepath = filepath
        if not self.filepath.is_file():
            warnings.warn('File indicated to be parsed is not existing! Trying to parse it will throw an exception!',
                          RuntimeWarning)

        if not metadata_directory.is_dir() or not metadata_directory.exists():
            raise IsADirectoryError('metadata_directory needs to be an existing directory!')

        self.__metadata_files = {}
        for path_element in metadata_directory.iterdir():
            if path_element.is_file() and path_element.suffix == '.meta':
                path_str = path_element.as_posix()
                file_match = re.findall(r'\.(?P<experiment_name>.+)\..+\.meta', path_str)
                if file_match is not None:
                    experiment_name = file_match[0]
                    self.__metadata_files[experiment_name] = path_element

    @staticmethod
    def __split_compounds(experiment_raw_protocol: pd.DataFrame) -> pd.DataFrame:
        split_protocol_df = pd.DataFrame()

        compound_regex = re.compile(r'(?P<compound>\S+)\s(?P<concentration>\d+[pnum]?\w+)')
        for ix, data in experiment_raw_protocol.iterrows():
            for match in compound_regex.finditer(data['compounds']):
                new_row_index = len(split_protocol_df)
                split_protocol_df.loc[new_row_index, 'start'] = data['start']
                split_protocol_df.loc[new_row_index, 'end'] = data['end']
                split_protocol_df.loc[new_row_index, 'compound'] = match.group('compound')
                split_protocol_df.loc[new_row_index, 'concentration'] = match.group('concentration')

        return split_protocol_df

    @staticmethod
    def __connect_compound_times(experiment_raw_protocol: pd.DataFrame) -> pd.DataFrame:
        result = pd.DataFrame()
        for group, df in experiment_raw_protocol.groupby(by=['compound', 'concentration']):
            for ix, start_time in df['start'].iteritems():
                matching_rows = df[df['end'].isin([start_time])]
                if not matching_rows.empty:
                    idx = matching_rows.index.values[0]
                    df.loc[idx, 'end'] = df.loc[ix, 'end']
                    df.drop(index=ix, inplace=True)
            result = pd.concat([result, df], ignore_index=True)

        return result

    def __correct_fillers(self, experiment_name: str, experiment_raw_protocol: pd.DataFrame) -> pd.DataFrame:
        experiment_metadata: pd.DataFrame

        try:
            if self.__metadata_files is None:
                warnings.warn('No metadata found to parse markdown!', RuntimeWarning)
                return pd.DataFrame(columns=['start', 'end', 'compounds'])
            meta_file = self.__metadata_files[experiment_name]
            experiment_metadata = pd.read_csv(meta_file, index_col=0)
        except KeyError:
            warnings.warn(f'The experiment {experiment_name} has no metadata in the given directory! '
                          f'The experiment will be skipped.', RuntimeWarning)
            return pd.DataFrame(columns=['start', 'end', 'compounds'])

        experiment_metadata = experiment_metadata.mask(~experiment_metadata['Name'].str.contains(r'Series\d+'))
        experiment_metadata.dropna(inplace=True)
        experiment_metadata.reset_index(drop=True, inplace=True)

        i = 0
        seconds_to_add = 0
        time_regex = re.compile(r'(?P<minutes>\d{2}):(?P<seconds>\d{2})')
        for ix, data in experiment_raw_protocol.iterrows():
            start = data['start']
            end = data['end']

            start_match = time_regex.match(start)
            start_minutes = int(start_match.group('minutes'))
            start_seconds = start_minutes * 60 + int(start_match.group('seconds')) + seconds_to_add
            start_minutes = start_seconds // 60

            end_minutes: int
            end_seconds: int
            if end == 'XX:XX':
                series_duration = experiment_metadata.loc[i, 'Duration']
                series_duration = int(pd.Timedelta(series_duration).total_seconds())
                end_seconds = series_duration + seconds_to_add
                end_minutes = end_seconds // 60
                seconds_to_add += series_duration
                i += 1
            else:
                end_match = time_regex.match(end)
                end_minutes = int(end_match.group('minutes'))
                end_seconds = end_minutes * 60 + int(end_match.group('seconds')) + seconds_to_add
                end_minutes = end_seconds // 60

            start = f'{start_minutes:02d}:{start_seconds % 60:02d}'
            end = f'{end_minutes:02d}:{end_seconds % 60:02d}'

            experiment_raw_protocol.loc[ix, 'start'] = start
            experiment_raw_protocol.loc[ix, 'end'] = end

        return experiment_raw_protocol

    @staticmethod
    def __fix_dataframe(protocol_df: pd.DataFrame) -> pd.DataFrame:
        starting_indices = protocol_df[protocol_df['start'].isin(['00:00'])].index
        for idx in starting_indices:
            protocol_df.loc[idx, 'start'] = np.NaN

        ending_value = protocol_df['end'].sort_values().unique()[-1]
        ending_indices = protocol_df[protocol_df['end'].isin([ending_value])].index
        for idx in ending_indices:
            protocol_df.loc[idx, 'end'] = np.NaN

        protocol_df.rename(
            columns={
                'start': 'begin',
                'end': 'end'
            },
            inplace=True)

        return protocol_df

    def parse(self) -> Dict[str, pd.DataFrame]:
        """Function to parse the markdown and metadata to get the protocols.

        Function starts parsing of the given data. Each experiment will be parsed separately.

        Returns
        -------
        Dictionary containing the protocol dataframes for each experiment. The experiment names are the keys of the
        given dictionary.
        """

        experiment_list = self.get_experiment_names()
        experiment_markdown: List[str]

        if len(experiment_list) > 1:
            tmp_markdown = self.filepath.read_text()
            idx = [tmp_markdown.find(experiment) for experiment in reversed(experiment_list)]
            starts = idx[:-1]
            ends = idx[1:]
            experiment_markdown = [tmp_markdown[pos[0]:pos[1]] for pos in zip(starts, ends)]
        elif len(experiment_list) == 1:
            experiment_markdown = [self.filepath.read_text()]
        else:
            raise ImportError

        protocol_line_regex = re.compile(
            r'^\[(?P<start>[\dxX]{1,2}:[\dxX]{1,2})\s?-\s?(?P<end>[\dxX]{1,2}:[\dxX]{1,2})]:\s?(?P<compounds>.*)$',
            re.MULTILINE
        )

        raw_protocols: List[pd.DataFrame] = []
        for experiment in experiment_markdown:
            raw_protocol_df = pd.DataFrame(columns=['start', 'end', 'compounds'])
            for match in protocol_line_regex.finditer(experiment):
                raw_protocol_df.loc[len(raw_protocol_df.index)] = [
                    match.group('start'),
                    match.group('end'),
                    match.group('compounds')
                ]
            raw_protocols.append(raw_protocol_df)

        protocols: Dict[str, pd.DataFrame] = {}
        for name, protocol in zip(experiment_list, raw_protocols):
            protocol = self.__correct_fillers(name, protocol)
            protocol = self.__split_compounds(protocol)
            protocol = self.__connect_compound_times(protocol)
            protocol = self.__fix_dataframe(protocol)
            protocol = protocol.reindex(columns=['compound', 'concentration', 'begin', 'end'])

            protocols[name] = protocol.sort_values(by=['begin', 'compound', 'concentration'],
                                                   na_position='first', ignore_index=True)

        return protocols

    def get_experiment_names(self) -> List[str]:
        """Gets the Names of the experiments based on the markdown.

        This function is intended to return the names of the experiments, which were found in the markdown.
        The experiments need to follow the naming 'ExperimentXXX', where XXX is any number.

        Returns
        -------
        List of strings, where each string represents one experiment name.

        """
        experiment_pattern = re.compile(r'Experiment\d+\w?')
        return experiment_pattern.findall(self.filepath.read_text())
