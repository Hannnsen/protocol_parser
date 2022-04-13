from abc import ABC, abstractmethod
import pandas as pd
from pathlib import Path
from typing import Dict, Union


class ParserBase(ABC):
    __file_path: Path

    @abstractmethod
    def parse(self) -> Dict[str, pd.DataFrame]:
        pass

    @property
    def filepath(self) -> Path:
        return self.__file_path

    @filepath.setter
    def filepath(self, value: Union[str, Path]):
        self.__file_path = Path(value.replace(' ', '_')) if type(value) == str else value
