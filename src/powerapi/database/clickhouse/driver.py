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

from collections.abc import Iterable

import clickhouse_connect
from clickhouse_connect.driver.exceptions import ClickHouseError

from powerapi.database.clickhouse.codecs import ReportEncoders
from powerapi.database.clickhouse.schema import TableSchemaRegistry
from powerapi.database.driver import WritableDatabase, WritableDatabaseFactory
from powerapi.database.exceptions import ConnectionFailed, WriteFailed
from powerapi.report import Report


class ClickHouseOutput(WritableDatabase):
    """
    ClickHouse output database driver.
    Allow to persist reports to a ClickHouse database.
    """

    def __init__(self, report_type: type[Report], host: str, port: int, username: str, password: str, database_name: str):
        """
        :param report_type: Type of the report handled by this database
        :param host: ClickHouse server host
        :param port: ClickHouse server port (8123 for HTTP, 8443 for HTTPS)
        :param username: Username to use for authentication
        :param password: Password to use for authentication
        :param database_name: Name of the database where the reports will be stored
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database_name = database_name

        self._report_encoder = ReportEncoders.get(report_type)
        self._table_schema = TableSchemaRegistry.get(report_type)
        self._client = None
        self._insert_context = None

    @staticmethod
    def supported_write_types() -> Iterable[type[Report]]:
        """
        Return the report types that can be persisted to the ClickHouse database.
        :return: Iterable of report types
        """
        return ReportEncoders.supported_types()

    def _create_table(self) -> None:
        """
        Create the table where the reports will be stored.
        """
        self._client.command(self._table_schema.build_create_table_query())

    def _create_insert_context(self) -> None:
        """
        Create the insert context used to persist reports to the table.
        The context is bound to the configured table and report schema and is reused sequentially across report batches.
        """
        self._insert_context = self._client.create_insert_context(table=self._table_schema.table_name)

    def connect(self) -> None:
        """
        Connect to the ClickHouse server.
        :raise ConnectionFailed: If the connection to the ClickHouse server fails.
        """
        try:
            self._client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database=self.database_name,
                client_name='PowerAPI',
            )
            self._create_table()
            self._create_insert_context()
        except (ClickHouseError, OSError, ValueError) as exn:
            raise ConnectionFailed(f'Failed to connect to the ClickHouse server: {exn}') from exn

    def disconnect(self) -> None:
        """
        Disconnect from the ClickHouse server.
        """
        try:
            self._client.close()
        except (ClickHouseError, OSError):
            # Errors can happen when closing the client, but nothing can be done in this case.
            pass

    def write(self, reports: Iterable[Report]) -> None:
        """
        Write reports to the ClickHouse database.
        :param reports: Iterable of reports
        :raise WriteFailed: If the write operation fails
        """
        try:
            encoded_reports = [self._report_encoder.encode(report) for report in reports]
            self._client.insert(data=encoded_reports, context=self._insert_context)
        except (ClickHouseError, OSError, TypeError, ValueError) as exn:
            raise WriteFailed(f'Failed to write reports to the ClickHouse database: {exn}') from exn


class ClickHouseOutputFactory(WritableDatabaseFactory):
    """
    ClickHouse output database driver factory.
    """

    def __init__(self, report_type: type[Report], host: str, port: int, username: str, password: str, database_name: str):
        """
        :param report_type: Type of the report handled by this database
        :param host: ClickHouse server host
        :param port: ClickHouse server port
        :param username: Username to use for authentication
        :param password: Password to use for authentication
        :param database_name: Database where the reports will be stored
        """
        if report_type not in ReportEncoders.supported_types():
            raise ValueError(f'Unsupported report type: {report_type.__name__}')

        self.report_type = report_type
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database_name = database_name

    def create(self) -> WritableDatabase:
        """
        Create a ClickHouse output database driver.
        :return: Initialized ClickHouse output database driver
        """
        return ClickHouseOutput(self.report_type, self.host, self.port, self.username, self.password, self.database_name)
