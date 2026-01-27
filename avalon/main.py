from __future__ import annotations

import uvicorn

from .config import SETTINGS


def main() -> None:
    uvicorn.run(
        "avalon.api:app",
        host=SETTINGS.host,
        port=SETTINGS.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
