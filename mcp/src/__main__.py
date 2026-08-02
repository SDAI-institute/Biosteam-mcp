"""Package entrypoint: ``python -m src`` runs the FastMCP server.

Imports ``src.app`` as a normal module so the tool modules register on the same
FastMCP instance that ``run()`` serves.
