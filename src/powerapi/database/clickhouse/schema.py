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
from typing import ClassVar

from powerapi.report import PowerReport, Report


class TableSchema(ABC):
    """
    Base declaration of a ClickHouse table schema.
    Subclasses define the target table name and implement the create table query builder method.
    """
    table_name: ClassVar[str]

    @classmethod
    @abstractmethod
    def build_create_table_query(cls) -> str: ...


class PowerReportTableSchema(TableSchema):
    """
    ClickHouse table schema used to persist PowerReport instances.
    """
    table_name = 'powerrep'

    @classmethod
    def build_create_table_query(cls) -> str:
        """
        Build ClickHouse create table query for the table schema used to persist PowerReport instances.
        :return: ClickHouse create table query string
        """
        return f"""
        CREATE TABLE IF NOT EXISTS `{cls.table_name}`
        (
            `timestamp` DateTime64(6, 'UTC') CODEC(DoubleDelta, LZ4),
            `sensor` LowCardinality(String),
            `target` String,
            `power` Float64 CODEC(Gorilla, LZ4),
            `metadata` Map(LowCardinality(String), String)
        )
        ENGINE = MergeTree
        ORDER BY (target, sensor, timestamp)
        """


class TableSchemaRegistry:
    """
    Associate report types with their ClickHouse table schemas.
    """
    schemas: ClassVar[dict[type[Report], type[TableSchema]]] = {
        PowerReport: PowerReportTableSchema,
    }

    @classmethod
    def get(cls, report_type: type[Report]) -> type[TableSchema]:
        """
        Return the ClickHouse table schema registered for a report type.
        :param report_type: Report type whose table schema is requested.
        :return: Registered table schema class.
        :raise ValueError: If no table schema is registered for the report type.
        """
        try:
            return cls.schemas[report_type]
        except KeyError as exn:
            raise ValueError(f'Unknown report type: {report_type.__name__}') from exn
