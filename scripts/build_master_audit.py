#!/usr/bin/env python3
"""Backward-compatible entry point for the dynamic canonical audit builder."""

from sync_catalog_audits import main


if __name__ == "__main__":
    raise SystemExit(main())
