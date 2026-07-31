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

import csv
from pathlib import Path
from unittest.mock import Mock

import pytest

from powerapi.database.csv.fileio_handlers import (
    MultiCsvFileReader,
    MultiCsvFileWriter,
    SingleCsvFileReader,
    SingleCsvFileWriter,
)

FIELDNAMES = ['timestamp', 'sensor', 'target', 'value']


def make_row(timestamp: int, sensor: str = 'sensor', target: str = 'target', value: str = '1'):
    """
    Create one flat CSV row.
    :param timestamp: Row timestamp
    :param sensor: Row sensor
    :param target: Row target
    :param value: Row value
    :return: CSV row
    """
    return {
        'timestamp': str(timestamp),
        'sensor': sensor,
        'target': target,
        'value': value,
    }


def write_csv(
    filepath: Path,
    rows: list[dict[str, str]],
    fieldnames: list[str] | None = None,
    write_header: bool = True,
) -> None:
    """
    Write rows to a CSV test file.
    :param filepath: Path to the test file
    :param rows: Rows to write
    :param fieldnames: Optional column names
    :param write_header: Whether to write the CSV header
    """
    selected_fieldnames = fieldnames or (list(rows[0]) if rows else FIELDNAMES)
    with filepath.open('w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=selected_fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


@pytest.fixture
def csv_row_groups():
    """
    Return fixed CSV row groups for reader tests.
    """
    return [
        [
            make_row(100, sensor='sensor-a', target='target-a', value='one'),
            make_row(100, sensor='sensor-a', target='target-a', value='two'),
        ],
        [make_row(100, sensor='sensor-a', target='target-b', value='three')],
        [make_row(100, sensor='sensor-b', target='target-a', value='four')],
        [make_row(101, sensor='sensor-a', target='target-a', value='five')],
    ]


@pytest.fixture
def multi_csv_row_groups():
    """
    Return fixed row groups for multi-file reader tests.
    """
    return {
        'first.csv': [
            [make_row(100, value='first-100')],
            [make_row(102, value='first-102')],
        ],
        'second.csv': [
            [make_row(100, value='second-100')],
            [make_row(101, value='second-101')],
            [make_row(102, value='second-102')],
        ],
    }


@pytest.fixture
def csv_file_factory(tmp_path):
    """
    Return a factory creating temporary CSV files.
    """
    def create_csv_file(
        rows: list[dict[str, str]],
        *,
        filename: str,
        fieldnames: list[str] | None = None,
        write_header: bool = True,
    ) -> Path:
        filepath = tmp_path / filename
        write_csv(filepath, rows, fieldnames, write_header)
        return filepath

    return create_csv_file


@pytest.fixture
def csv_group_file_factory(csv_file_factory):
    """
    Return a factory creating temporary CSV files from row groups.
    """
    def create_csv_group_file(row_groups: list[list[dict[str, str]]], *, filename: str) -> Path:
        rows = [
            row
            for group_rows in row_groups
            for row in group_rows
        ]
        return csv_file_factory(rows, filename=filename)

    return create_csv_group_file


@pytest.fixture
def multi_csv_file_factory(csv_group_file_factory):
    """
    Return a factory creating multiple temporary CSV files.
    """
    def create_csv_files(row_groups_by_filename: dict[str, list[list[dict[str, str]]]]) -> list[Path]:
        return [
            csv_group_file_factory(row_groups, filename=filename)
            for filename, row_groups in row_groups_by_filename.items()
        ]

    return create_csv_files


@pytest.fixture(params=[True, False], ids=['with-header', 'without-header'])
def empty_csv_file(request, csv_file_factory):
    """
    Return an empty CSV file with or without a header.
    """
    return csv_file_factory([], filename='empty.csv', write_header=request.param)


class TestSingleCsvFileReader:
    """
    Test class for SingleCsvFileReader.
    """

    @pytest.mark.parametrize(
        ('filename', 'expected_group_name'),
        [
            ('rapl.csv', 'rapl'),
            ('MSR.csv', 'MSR'),
            ('core.cpu0.csv', 'core.cpu0'),
        ],
        ids=('lowercase', 'uppercase', 'multipart'),
    )
    def test_group_name_is_input_file_stem(self, csv_file_factory, filename, expected_group_name):
        """
        Reader should derive its group name from the input file stem.
        """
        filepath = csv_file_factory([], filename=filename)
        reader = SingleCsvFileReader(filepath)

        assert reader.group_name == expected_group_name

    def test_open_nonexistent_file_raises_file_not_found_error(self, tmp_path):
        """
        Reader should propagate FileNotFoundError when the input file does not exist.
        """
        reader = SingleCsvFileReader(tmp_path / 'missing.csv')

        with pytest.raises(FileNotFoundError):
            reader.open()

    def test_read_empty_file_returns_no_rows(self, empty_csv_file):
        """
        Reader should expose no cursor or rows for empty and header-only files.
        """
        reader = SingleCsvFileReader(empty_csv_file)

        reader.open()

        assert reader.cursor() is None
        assert reader.next_rows() == []
        reader.close()

    def test_open_preserves_first_row_group(self, csv_row_groups, csv_group_file_factory):
        """
        Reader should return the first logical group after opening a file.
        """
        filepath = csv_group_file_factory(csv_row_groups[:2], filename='first-groups.csv')
        reader = SingleCsvFileReader(filepath)

        reader.open()

        assert reader.next_rows() == csv_row_groups[0]
        assert reader.next_rows() == csv_row_groups[1]
        reader.close()

    def test_next_rows_groups_rows_by_cursor(self, csv_row_groups, csv_group_file_factory):
        """
        Reader should create a new group when timestamp, sensor, or target changes.
        """
        filepath = csv_group_file_factory(csv_row_groups, filename='cursor-groups.csv')
        reader = SingleCsvFileReader(filepath)

        reader.open()
        actual_batches = [reader.next_rows() for _ in csv_row_groups]

        assert actual_batches == csv_row_groups
        assert reader.cursor() is None
        reader.close()

    def test_cursor_filter_mismatch_does_not_consume_rows(self, csv_row_groups, csv_file_factory, csv_group_file_factory):
        """
        Reader should not consume its pending group when the expected cursor differs.
        """
        filepath = csv_group_file_factory(csv_row_groups[:2], filename='expected.csv')
        reader = SingleCsvFileReader(filepath)
        reader.open()
        expected_cursor = reader.cursor()

        other_filepath = csv_file_factory([make_row(1)], filename='other.csv')
        other_reader = SingleCsvFileReader(other_filepath)
        other_reader.open()
        mismatched_cursor = other_reader.cursor()

        assert expected_cursor is not None
        assert mismatched_cursor is not None
        assert mismatched_cursor != expected_cursor
        assert reader.next_rows(mismatched_cursor) == []
        assert reader.cursor() == expected_cursor
        assert reader.next_rows(expected_cursor) == csv_row_groups[0]
        other_reader.close()
        reader.close()

    def test_next_rows_rejects_invalid_timestamp(self, csv_file_factory):
        """
        Reader should reject an invalid timestamp encountered after opening the file.
        """
        invalid_row = make_row(101)
        invalid_row['timestamp'] = 'invalid'
        filepath = csv_file_factory([make_row(100), invalid_row], filename='invalid-later-timestamp.csv')
        reader = SingleCsvFileReader(filepath)
        reader.open()

        with pytest.raises(ValueError, match='invalid literal'):
            reader.next_rows()

        reader.close()

    def test_next_rows_rejects_decreasing_timestamp(self, csv_file_factory):
        """
        Reader should reject timestamps that move backward.
        """
        filepath = csv_file_factory([make_row(100), make_row(99)], filename='decreasing-timestamp.csv')
        reader = SingleCsvFileReader(filepath)
        reader.open()

        with pytest.raises(ValueError, match='Timestamp regression'):
            reader.next_rows()

        reader.close()

    def test_repeated_reads_after_end_of_file_return_no_rows(self, csv_file_factory):
        """
        Reader should return no rows and expose no cursor after reaching end of file.
        """
        expected_rows = [make_row(100)]
        filepath = csv_file_factory(expected_rows, filename='end-of-file.csv')
        reader = SingleCsvFileReader(filepath)
        reader.open()

        assert reader.next_rows() == expected_rows
        assert reader.cursor() is None
        assert reader.next_rows() == []
        assert reader.next_rows() == []
        reader.close()

    @pytest.mark.parametrize(
        ('column', 'special_value'),
        [
            ('sensor', 'pytest, caractères "spéciaux"'),
            ('target', '/system.slice/system-serial\\x2dgetty.slice/serial-getty@ttyS0.service'),
            ('value', '6.022e+23'),
        ],
        ids=('utf8-sensor', 'escaped-target-path', 'scientific-notation'),
    )
    def test_reader_preserves_special_field_values(self, csv_file_factory, column, special_value):
        """
        Reader should preserve representative sensor, target, and value formats.
        """
        expected_row = make_row(100)
        expected_row[column] = special_value
        filepath = csv_file_factory([expected_row], filename=f'{column}.csv')
        reader = SingleCsvFileReader(filepath)

        reader.open()

        assert reader.next_rows() == [expected_row]
        reader.close()

    @pytest.mark.parametrize(
        'timestamp',
        ['invalid', '1.5', ''],
        ids=['text', 'float', 'empty'],
    )
    def test_open_rejects_invalid_timestamp(self, csv_file_factory, timestamp):
        """
        Reader should reject timestamps that cannot be converted to integers.
        """
        row = make_row(100)
        row['timestamp'] = timestamp
        filepath = csv_file_factory([row], filename='invalid-timestamp.csv')
        reader = SingleCsvFileReader(filepath)

        with pytest.raises(ValueError, match='invalid literal'):
            reader.open()

    @pytest.mark.parametrize(
        'missing_column',
        ['timestamp', 'sensor', 'target'],
    )
    def test_open_rejects_missing_cursor_column(self, csv_file_factory, missing_column):
        """
        Reader should reject rows missing a required cursor column.
        """
        row = make_row(100)
        del row[missing_column]
        filepath = csv_file_factory([row], filename=f'missing-{missing_column}.csv', fieldnames=list(row))
        reader = SingleCsvFileReader(filepath)

        with pytest.raises(KeyError, match=missing_column):
            reader.open()

    def test_open_parse_failure_closes_reader(self, csv_file_factory):
        """
        Reader should close and clear its state when initial cursor parsing fails.
        """
        row = make_row(100)
        row['timestamp'] = 'invalid'
        filepath = csv_file_factory([row], filename='malformed.csv')
        reader = SingleCsvFileReader(filepath)
        close_reader = Mock(wraps=reader.close)

        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(reader, 'close', close_reader)

            with pytest.raises(ValueError, match='invalid literal'):
                reader.open()

        close_reader.assert_called_once_with()
        assert reader._file is None

    def test_close_releases_file_and_clears_state(self, csv_row_groups, csv_file_factory):
        """
        Reader should close its file and clear all parsing state.
        """
        filepath = csv_file_factory(csv_row_groups[0], filename='close.csv')
        reader = SingleCsvFileReader(filepath)
        reader.open()
        file = reader._file

        reader.close()

        assert file.closed
        assert reader._file is None
        assert reader._reader is None
        assert reader.cursor() is None
        assert reader._last_row_buffer is None

    def test_close_suppresses_file_closing_failure_and_clears_state(self):
        """
        Reader should suppress file-closing errors and clear its state.
        """
        reader = SingleCsvFileReader(Path('/unused/input.csv'))
        file = Mock()
        file.close.side_effect = OSError('pytest close failed')
        reader._file = file
        reader._reader = Mock()
        reader._row_cursor = Mock()
        reader._last_row_buffer = make_row(101)

        reader.close()

        file.close.assert_called_once_with()
        assert reader._file is None
        assert reader._reader is None
        assert reader.cursor() is None
        assert reader._last_row_buffer is None

    def test_close_is_idempotent(self):
        """
        Reader close should not close the same file more than once.
        """
        reader = SingleCsvFileReader(Path('/unused/input.csv'))
        file = Mock()
        reader._file = file

        reader.close()
        reader.close()

        file.close.assert_called_once_with()


class TestMultiCsvFileReader:
    """
    Test class for MultiCsvFileReader.
    """

    def test_next_rows_returns_no_rows_when_no_files_are_configured(self):
        """
        Reader should return no rows when no input files are configured.
        """
        reader = MultiCsvFileReader([])

        reader.open()

        assert reader.next_rows() == {}
        reader.close()

    def test_next_rows_merges_matching_groups_across_files(self, multi_csv_row_groups, multi_csv_file_factory):
        """
        Reader should merge matching and sparse file groups in cursor order.
        """
        filepaths = iter(multi_csv_file_factory(multi_csv_row_groups))
        reader = MultiCsvFileReader(filepaths)

        reader.open()

        assert reader.next_rows() == {
            'first': multi_csv_row_groups['first.csv'][0],
            'second': multi_csv_row_groups['second.csv'][0],
        }
        assert reader.next_rows() == {
            'second': multi_csv_row_groups['second.csv'][1],
        }
        assert reader.next_rows() == {
            'first': multi_csv_row_groups['first.csv'][1],
            'second': multi_csv_row_groups['second.csv'][2],
        }
        assert reader.next_rows() == {}
        reader.close()

    def test_next_rows_orders_by_timestamp_sensor_and_target(self, multi_csv_file_factory):
        """
        Reader should order file groups by timestamp, sensor, and target.
        """
        row_groups_by_filename = {
            'target-b.csv': [[make_row(100, sensor='sensor-a', target='target-b')]],
            'target-a.csv': [[make_row(100, sensor='sensor-a', target='target-a')]],
            'sensor-b.csv': [[make_row(100, sensor='sensor-b', target='target-a')]],
            'later.csv': [[make_row(101, sensor='sensor-a', target='target-a')]],
        }
        filepaths = multi_csv_file_factory(row_groups_by_filename)
        reader = MultiCsvFileReader(filepaths)

        reader.open()

        assert reader.next_rows() == {'target-a': row_groups_by_filename['target-a.csv'][0]}
        assert reader.next_rows() == {'target-b': row_groups_by_filename['target-b.csv'][0]}
        assert reader.next_rows() == {'sensor-b': row_groups_by_filename['sensor-b.csv'][0]}
        assert reader.next_rows() == {'later': row_groups_by_filename['later.csv'][0]}
        reader.close()

    def test_exhausted_file_does_not_block_remaining_files(self, multi_csv_file_factory):
        """
        Reader should continue after one input file reaches end of file.
        """
        row_groups_by_filename = {
            'short.csv': [[make_row(100, value='short-100')]],
            'long.csv': [[make_row(100, value='long-100')], [make_row(101, value='long-101')]],
        }
        filepaths = multi_csv_file_factory(row_groups_by_filename)
        reader = MultiCsvFileReader(filepaths)

        reader.open()

        assert reader.next_rows() == {
            'short': row_groups_by_filename['short.csv'][0],
            'long': row_groups_by_filename['long.csv'][0],
        }
        assert reader.next_rows() == {'long': row_groups_by_filename['long.csv'][1]}
        reader.close()

    def test_open_failure_closes_all_pending_readers(self):
        """
        Reader should roll back all pending readers when one file fails to open.
        """
        opened_reader = Mock(spec=SingleCsvFileReader)
        failing_reader = Mock(spec=SingleCsvFileReader)
        failing_reader.open.side_effect = OSError('pytest open failed')
        file_reader_factory = Mock(side_effect=[opened_reader, failing_reader])
        reader = MultiCsvFileReader([Path('/unused/opened.csv'), Path('/unused/failing.csv')])

        with pytest.MonkeyPatch.context() as patch:
            patch.setattr('powerapi.database.csv.fileio_handlers.SingleCsvFileReader', file_reader_factory)

            with pytest.raises(OSError, match='pytest open failed'):
                reader.open()

        opened_reader.close.assert_called_once_with()
        failing_reader.close.assert_called_once_with()

    def test_close_closes_all_readers(self):
        """
        Reader close should close every input reader.
        """
        first_reader = Mock(spec=SingleCsvFileReader)
        second_reader = Mock(spec=SingleCsvFileReader)
        file_reader_factory = Mock(side_effect=[first_reader, second_reader])
        reader = MultiCsvFileReader([Path('/unused/first.csv'), Path('/unused/second.csv')])

        with pytest.MonkeyPatch.context() as patch:
            patch.setattr('powerapi.database.csv.fileio_handlers.SingleCsvFileReader', file_reader_factory)
            reader.open()

        reader.close()

        first_reader.close.assert_called_once_with()
        second_reader.close.assert_called_once_with()


class TestSingleCsvFileWriter:
    """
    Test class for SingleCsvFileWriter.
    """

    def test_open_writes_header_in_fieldname_order(self, tmp_path):
        """
        Writer should create a file with its configured fieldnames in order.
        """
        filepath = tmp_path / 'header.csv'
        fieldnames = ['sensor', 'value', 'timestamp', 'target']
        writer = SingleCsvFileWriter(filepath, fieldnames)

        writer.open()
        writer.close()

        with filepath.open(encoding='utf-8', newline='') as file:
            assert list(csv.reader(file)) == [fieldnames]

    @pytest.mark.parametrize(
        ('column', 'special_value'),
        [
            ('sensor', 'pytest, caractères "spéciaux"'),
            ('target', '/system.slice/system-serial\\x2dgetty.slice/serial-getty@ttyS0.service'),
            ('value', '6.022e+23'),
        ],
        ids=('utf8-sensor', 'escaped-target-path', 'scientific-notation'),
    )
    def test_write_rows_preserves_special_field_values(self, tmp_path, column, special_value):
        """
        Writer should preserve representative sensor, target, and value formats.
        """
        expected_row = make_row(100)
        expected_row[column] = special_value
        filepath = tmp_path / f'{column}.csv'
        writer = SingleCsvFileWriter(filepath, FIELDNAMES)

        writer.open()
        writer.write_rows([expected_row])
        writer.close()

        with filepath.open(encoding='utf-8', newline='') as file:
            assert list(csv.DictReader(file)) == [expected_row]

    def test_write_rows_preserves_order_across_multiple_calls(self, tmp_path):
        """
        Writer should append rows in write call order.
        """
        filepath = tmp_path / 'rows.csv'
        first_rows = [make_row(100, value='first')]
        second_rows = [make_row(101, value='second')]
        writer = SingleCsvFileWriter(filepath, FIELDNAMES)

        writer.open()
        writer.write_rows(first_rows)
        writer.write_rows(second_rows)
        writer.close()

        with filepath.open(encoding='utf-8', newline='') as file:
            assert list(csv.DictReader(file)) == first_rows + second_rows

    def test_close_releases_file_and_clears_state(self, tmp_path):
        """
        Writer should close its file and clear all writing state.
        """
        writer = SingleCsvFileWriter(tmp_path / 'close.csv', FIELDNAMES)
        writer.open()
        file = writer._file

        writer.close()

        assert file.closed
        assert writer._file is None
        assert writer._writer is None

    def test_close_suppresses_file_closing_failure_and_clears_state(self):
        """
        Writer should suppress file-closing errors and clear its state.
        """
        writer = SingleCsvFileWriter(Path('/unused/output.csv'), FIELDNAMES)
        file = Mock()
        file.close.side_effect = OSError('pytest close failed')
        writer._file = file
        writer._writer = Mock()

        writer.close()

        file.close.assert_called_once_with()
        assert writer._file is None
        assert writer._writer is None

    def test_close_is_idempotent(self):
        """
        Writer close should not close the same file more than once.
        """
        writer = SingleCsvFileWriter(Path('/unused/output.csv'), FIELDNAMES)
        file = Mock()
        writer._file = file

        writer.close()
        writer.close()

        file.close.assert_called_once_with()


class TestMultiCsvFileWriter:
    """
    Test class for MultiCsvFileWriter.
    """

    def test_write_rows_creates_file_for_each_group(self, tmp_path):
        """
        Writer should create a separate CSV file for each group.
        """
        rows_by_group = {'first': [make_row(100, value='first')], 'second': [make_row(101, value='second')]}
        writer = MultiCsvFileWriter(tmp_path)
        writer.open()

        writer.write_rows(rows_by_group)
        writer.close()

        assert {filepath.name for filepath in tmp_path.iterdir()} == {'first.csv', 'second.csv'}
        for group_name, expected_rows in rows_by_group.items():
            with (tmp_path / f'{group_name}.csv').open(encoding='utf-8', newline='') as file:
                reader = csv.DictReader(file)

                assert reader.fieldnames == list(expected_rows[0])
                assert list(reader) == expected_rows

    def test_write_rows_appends_to_existing_group_file(self, tmp_path):
        """
        Writer should append rows to an existing group file.
        """
        first_rows = [make_row(100, value='first')]
        second_rows = [make_row(101, value='second')]
        writer = MultiCsvFileWriter(tmp_path)
        writer.open()

        writer.write_rows({'pytest': first_rows})
        writer.write_rows({'pytest': second_rows})
        writer.close()

        with (tmp_path / 'pytest.csv').open(encoding='utf-8', newline='') as file:
            assert list(csv.DictReader(file)) == first_rows + second_rows

    def test_write_rows_skips_empty_groups(self, tmp_path):
        """
        Writer should skip empty groups and continue writing populated groups.
        """
        expected_rows = [make_row(100)]
        writer = MultiCsvFileWriter(tmp_path)
        writer.open()

        writer.write_rows({'empty': [], 'populated': expected_rows})
        writer.close()

        assert not (tmp_path / 'empty.csv').exists()
        assert (tmp_path / 'populated.csv').exists()

    def test_close_closes_all_file_writers(self):
        """
        Writer close should close every group file writer.
        """
        first_writer = Mock(spec=SingleCsvFileWriter)
        second_writer = Mock(spec=SingleCsvFileWriter)
        file_writer_factory = Mock(side_effect=[first_writer, second_writer])
        writer = MultiCsvFileWriter(Path('/unused'))
        writer.open()

        with pytest.MonkeyPatch.context() as patch:
            patch.setattr('powerapi.database.csv.fileio_handlers.SingleCsvFileWriter', file_writer_factory)
            writer.write_rows({'first': [make_row(100)], 'second': [make_row(101)]})

        writer.close()

        first_writer.close.assert_called_once_with()
        second_writer.close.assert_called_once_with()
