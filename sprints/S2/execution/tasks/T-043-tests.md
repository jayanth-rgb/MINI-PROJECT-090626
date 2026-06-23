# T-043 tests

No direct TCs. Repository methods are exercised by:
- Domain TCs TC-079..TC-087 (T-045 `domain.stock` calls these repos)
- Service TCs TC-047..TC-078 (services use `create_with_lines`)

Concurrency test **TC-087** explicitly verifies the `for_update=True` lock behavior.
