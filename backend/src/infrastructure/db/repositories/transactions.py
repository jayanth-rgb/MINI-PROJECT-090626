from datetime import date

from sqlalchemy import select

from src.infrastructure.db.models.transactions import (
    AdjustmentHeaderModel,
    AdjustmentLineModel,
    InwardHeaderModel,
    InwardLineModel,
    SalesHeaderModel,
    SalesLineModel,
    StockLedgerModel,
)
from src.infrastructure.db.repositories.base import BaseRepository


class InwardHeaderRepository(BaseRepository[InwardHeaderModel]):
    def create_with_lines(
        self, header_payload: dict, line_payloads: list[dict]
    ) -> InwardHeaderModel:
        header = InwardHeaderModel(**header_payload)
        self.session.add(header)
        self.session.flush()  # assigns header.header_id
        for lp in line_payloads:
            self.session.add(InwardLineModel(header_id=header.header_id, **lp))
        self.session.flush()
        return header


class SalesHeaderRepository(BaseRepository[SalesHeaderModel]):
    def create_with_lines(
        self, header_payload: dict, line_payloads: list[dict]
    ) -> SalesHeaderModel:
        header = SalesHeaderModel(**header_payload)
        self.session.add(header)
        self.session.flush()
        for lp in line_payloads:
            self.session.add(SalesLineModel(header_id=header.header_id, **lp))
        self.session.flush()
        return header


class AdjustmentHeaderRepository(BaseRepository[AdjustmentHeaderModel]):
    def create_with_lines(
        self, header_payload: dict, line_payloads: list[dict]
    ) -> AdjustmentHeaderModel:
        header = AdjustmentHeaderModel(**header_payload)
        self.session.add(header)
        self.session.flush()
        for lp in line_payloads:
            self.session.add(AdjustmentLineModel(header_id=header.header_id, **lp))
        self.session.flush()
        return header


class StockLedgerRepository(BaseRepository[StockLedgerModel]):
    def latest_for_design_grade(
        self, design_id: int, grade_id: int, for_update: bool = False
    ) -> StockLedgerModel | None:
        stmt = (
            select(StockLedgerModel)
            .where(
                StockLedgerModel.design_id == design_id,
                StockLedgerModel.grade_id == grade_id,
            )
            .order_by(
                StockLedgerModel.txn_date.desc(),
                StockLedgerModel.ledger_id.desc(),
            )
            .limit(1)
        )
        # DS-002: lock acquisition point for write-path serialization.
        if for_update:
            stmt = stmt.with_for_update()
        return self.session.execute(stmt).scalar_one_or_none()

    def latest_as_of(
        self, design_id: int, grade_id: int, as_of_date: date
    ) -> StockLedgerModel | None:
        stmt = (
            select(StockLedgerModel)
            .where(
                StockLedgerModel.design_id == design_id,
                StockLedgerModel.grade_id == grade_id,
                StockLedgerModel.txn_date <= as_of_date,
            )
            .order_by(
                StockLedgerModel.txn_date.desc(),
                StockLedgerModel.ledger_id.desc(),
            )
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def rows_after(
        self, design_id: int, grade_id: int, after_date_inclusive: date
    ) -> list[StockLedgerModel]:
        stmt = (
            select(StockLedgerModel)
            .where(
                StockLedgerModel.design_id == design_id,
                StockLedgerModel.grade_id == grade_id,
                StockLedgerModel.txn_date >= after_date_inclusive,
            )
            .order_by(
                StockLedgerModel.txn_date.asc(),
                StockLedgerModel.ledger_id.asc(),
            )
        )
        return list(self.session.execute(stmt).scalars())

    def insert(self, data: dict) -> StockLedgerModel:
        row = StockLedgerModel(**data)
        self.session.add(row)
        self.session.flush()
        return row
