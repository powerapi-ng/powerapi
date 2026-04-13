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

from pathlib import Path

import pytest

from powerapi.database.json.file_handlers import FileHandlerRegistry, RawFileHandler, GzipFileHandler, LzmaFileHandler


def make_filepath(suffix: str = '.jsonl', stem: str = "pytest-powerapi", root: str = "/tmp") -> Path:
    """
    Helper method to create a file path.
    :param suffix: File suffix
    :param stem: File stem
    :param root: File root directory
    :return: File path
    """
    return Path(root) / f"{stem}{suffix}"


@pytest.mark.parametrize('compression_method', ['none', 'gzip', 'lzma'])
def test_registry_get_compression_method(compression_method):
    """
    Registry should return the handler matching an explicit compression method.
    """
    filepath = make_filepath()
    handler = FileHandlerRegistry.get(compression_method, filepath)

    assert handler.compression_method == compression_method


def test_registry_get_invalid_compression_method() -> None:
    """
    Registry should raise a ValueError for an unsupported compression method.
    """
    filepath = make_filepath()

    with pytest.raises(ValueError, match='Unknown compression method'):
        FileHandlerRegistry.get('invalid', filepath)


@pytest.mark.parametrize('file_extension', ['.jsonl', '.jsonlines', '.ndjson', '.json', ''])
def test_registry_get_none_compression_method_from_file_extension(file_extension):
    """
    Auto-detection should resolve uncompressed JSON file suffixes to the raw file handler.
    """
    filepath = make_filepath(file_extension)
    handler = FileHandlerRegistry.get('auto', filepath)

    assert handler is RawFileHandler
    assert handler.compression_method == 'none'


@pytest.mark.parametrize('file_extension', ['.gz', '.gzip'])
def test_registry_get_gzip_compression_method_from_file_extension(file_extension):
    """
    Auto-detection should resolve gzip-related suffixes to the Gzip file handler.
    """
    filepath = make_filepath(file_extension)
    handler = FileHandlerRegistry.get('auto', filepath)

    assert handler is GzipFileHandler
    assert handler.compression_method == 'gzip'


@pytest.mark.parametrize('file_extension', ['.xz', '.lzma'])
def test_registry_get_lzma_compression_method_from_file_extension(file_extension):
    """
    Auto-detection should resolve lzma-related suffixes to the LZMA file handler.
    """
    filepath = make_filepath(file_extension)
    handler = FileHandlerRegistry.get('auto', filepath)

    assert handler is LzmaFileHandler
    assert handler.compression_method == 'lzma'


def test_registry_get_unknown_compression_method_from_file_extension():
    """
    Auto-detection should raise a ValueError for an unknown file suffix.
    """
    filepath = make_filepath('.invalid')

    with pytest.raises(ValueError, match='Unknown file extension'):
        FileHandlerRegistry.get('auto', filepath)
