===============
Protocol_Parser
===============

Protocol_Parser is a python module to parse protocols from metadata, which was created by CTN.
The format is oriented to parse protocols according to module `islets <https://github.com/szarma/Physio_Ca>`_.
Protocol parser provides a base class ``ParserBase``, which is used to define custom parsers.

Currently supported parsers and their formats:

- Markdown (``MarkdownParser``)

MarkdownParser
--------------
The markdown parser requires has the following format requirements::

    Experiment001a:
    [start:time - end:time]: Compound 0mM
    [start:time - XX:XX]: CompoundUntilEndOfSeries 0mM

::
