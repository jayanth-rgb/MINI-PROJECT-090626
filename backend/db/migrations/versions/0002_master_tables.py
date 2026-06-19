"""master tables

Revision ID: 0002_master_tables
Revises:
Create Date: 2026-06-18
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_master_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tbl_supplier_master",
        sa.Column("supplier_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("supplier_name", sa.Text(), nullable=False),
        sa.Column("place", sa.Text(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_supplier_master_is_active",
        "tbl_supplier_master",
        ["is_active"],
    )

    op.create_table(
        "tbl_staff_master",
        sa.Column("staff_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("staff_name", sa.Text(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_staff_master_is_active",
        "tbl_staff_master",
        ["is_active"],
    )

    op.create_table(
        "tbl_dealer_master",
        sa.Column("dealer_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("dealer_name", sa.Text(), nullable=False),
        sa.Column("place", sa.Text(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_dealer_master_is_active",
        "tbl_dealer_master",
        ["is_active"],
    )

    op.create_table(
        "tbl_grade_master",
        sa.Column("grade_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("grade_code", sa.Text(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.UniqueConstraint("grade_code", name="uq_grade_master_grade_code"),
    )
    op.create_index(
        "ix_grade_master_is_active",
        "tbl_grade_master",
        ["is_active"],
    )

    op.create_table(
        "tbl_trading_design_master",
        sa.Column("design_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("size", sa.Text(), nullable=False),
        sa.Column("design_name", sa.Text(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_trading_design_master_is_active",
        "tbl_trading_design_master",
        ["is_active"],
    )

    op.create_table(
        "tbl_design_grade_map",
        sa.Column("map_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("design_id", sa.BigInteger(), nullable=False),
        sa.Column("grade_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.ForeignKeyConstraint(
            ["design_id"],
            ["tbl_trading_design_master.design_id"],
            name="fk_design_grade_map_design_id",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["grade_id"],
            ["tbl_grade_master.grade_id"],
            name="fk_design_grade_map_grade_id",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "design_id",
            "grade_id",
            name="uq_design_grade_map_design_grade",
        ),
    )
    op.create_index(
        "ix_design_grade_map_design_id",
        "tbl_design_grade_map",
        ["design_id"],
    )
    op.create_index(
        "ix_design_grade_map_is_active",
        "tbl_design_grade_map",
        ["is_active"],
    )


def downgrade() -> None:
    op.drop_index("ix_design_grade_map_is_active", table_name="tbl_design_grade_map")
    op.drop_index("ix_design_grade_map_design_id", table_name="tbl_design_grade_map")
    op.drop_table("tbl_design_grade_map")

    op.drop_index("ix_trading_design_master_is_active", table_name="tbl_trading_design_master")
    op.drop_table("tbl_trading_design_master")

    op.drop_index("ix_grade_master_is_active", table_name="tbl_grade_master")
    op.drop_table("tbl_grade_master")

    op.drop_index("ix_dealer_master_is_active", table_name="tbl_dealer_master")
    op.drop_table("tbl_dealer_master")

    op.drop_index("ix_staff_master_is_active", table_name="tbl_staff_master")
    op.drop_table("tbl_staff_master")

    op.drop_index("ix_supplier_master_is_active", table_name="tbl_supplier_master")
    op.drop_table("tbl_supplier_master")
