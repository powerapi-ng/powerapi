# Copyright (c) 2026, Inria
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from abc import ABC, abstractmethod
from io import TextIOWrapper
from pathlib import Path
from typing import Literal, TextIO, ClassVar


_OPEN_MODES = Literal['r', 'w']

class FileHandler(ABC):
    """
    Base class for JSON file opening strategies.
    """
    compression_method: str = ''
    supported_suffixes: tuple[str, ...] = ()

    @classmethod
    @abstractmethod
    def open(cls, filepath: Path, mode: _OPEN_MODES) -> TextIO:
        """
        Open a file as a UTF-8 text stream using the handler strategy.
        :param filepath: Path to the file to open
        :param mode: Text mode used to open the file
        :return: Open text stream
        """
        ...


class RawFileHandler(FileHandler):
    """
    File handler for uncompressed JSON files.
    """
    compression_method = 'none'
    supported_suffixes = ('.jsonl', '.jsonlines', '.ndjson', '.json', '')

    @classmethod
    def open(cls, filepath: Path, mode: _OPEN_MODES) -> TextIO:
        return open(filepath, mode, encoding='utf-8')


class GzipFileHandler(FileHandler):
    """
    File handler for gzip-compressed JSON files.
    """
    compression_method = 'gzip'
    supported_suffixes = ('.gz', '.gzip')

    @classmethod
    def open(cls, filepath: Path, mode: _OPEN_MODES) -> TextIO:
        from gzip import GzipFile
        gzip_file = GzipFile(filepath, mode)
        text_handler = TextIOWrapper(gzip_file, encoding='utf-8')
        return text_handler


class LzmaFileHandler(FileHandler):
    """"
    File handler for lzma-compressed JSON files.
    """
    compression_method = 'lzma'
    supported_suffixes = ('.xz', '.lzma')

    @classmethod
    def open(cls, filepath: Path, mode: _OPEN_MODES) -> TextIO:
        from lzma import LZMAFile
        lzma_file = LZMAFile(filepath, mode)
        text_handler = TextIOWrapper(lzma_file, encoding='utf-8')
        return text_handler


class FileHandlerRegistry:
    """
    Registry of JSON file handlers.
    """
    _file_handlers: ClassVar[list[type[FileHandler]]] = []

    @classmethod
    def register(cls, handler: type[FileHandler]) -> None:
        """
        Register a file handler in lookup order.
        :param handler: Handler class to register
        """
        cls._file_handlers.append(handler)

    @classmethod
    def _get_from_compression_method(cls, compression_method: str) -> type[FileHandler]:
        """
        Retrieve a handler from its compression method name.
        :param compression_method: Name of the compression method to resolve
        :return: File handler matching the requested compression method
        :raises ValueError: If the compression method is not recognized
        """
        for handler in cls._file_handlers:
            if handler.compression_method == compression_method:
                return handler

        raise ValueError(f'Unknown compression method: {compression_method}')

    @classmethod
    def _get_from_file_extension(cls, filepath: Path) -> type[FileHandler]:
        """
        Infer a handler from the suffix of the given filepath.
        :param filepath: Path to the file
        :return: Handler matching the filepath suffix
        :raises ValueError: If the file extension is not recognized
        """
        suffix = filepath.suffix.casefold()
        for handler in cls._file_handlers:
            if suffix in handler.supported_suffixes:
                return handler

        raise ValueError(f'Unknown file extension for: {filepath}')

    @classmethod
    def get(cls, compression_method: str, filepath: Path) -> type[FileHandler]:
        """
        Resolve the file handler for a JSON file.

        When the ``compression_method`` parameter is ``auto``, the handler is inferred from the filepath suffix.
        Otherwise, the compression method is resolved explicitly.

        :param compression_method: Compression method name or ``auto``
        :param filepath: Path to the file associated with the handler lookup
        :return: Matching file handler
        :raises ValueError: If no handler matches the requested method or file suffix
        """
        method = compression_method.casefold()
        if method == 'auto':
            handler = cls._get_from_file_extension(filepath)
        else:
            handler = cls._get_from_compression_method(method)

        return handler


FileHandlerRegistry.register(RawFileHandler)
FileHandlerRegistry.register(GzipFileHandler)
FileHandlerRegistry.register(LzmaFileHandler)
