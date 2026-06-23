# T-041 tests

No direct test cases. Verified transitively when T-042 ORM models (which inherit TimestampMixin) round-trip through PG via testcontainers fixtures — `created_at` reads back with `tzinfo` populated.

See [sprints/S2/design/test_cases.md](../../design/test_cases.md) for the broader S2 test catalog.
