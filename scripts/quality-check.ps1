$ErrorActionPreference = "Stop"

uvx ruff check app tests
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

uv run pytest
exit $LASTEXITCODE
