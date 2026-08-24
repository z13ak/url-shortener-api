"""A small URL shortener REST API built with FastAPI + SQLite."""

from __future__ import annotations

import random
import re
import string

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl, field_validator

import database

app = FastAPI(
    title="URL Shortener API",
    description="Shorten links, track click counts, redirect on lookup.",
    version="1.0.0",
)

CODE_ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 6
CUSTOM_CODE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,30}$")


def get_db():
    return database.get_shared_connection()


class ShortenRequest(BaseModel):
    url: HttpUrl
    custom_code: str | None = None

    @field_validator("custom_code")
    @classmethod
    def validate_custom_code(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not CUSTOM_CODE_PATTERN.match(value):
            raise ValueError(
                "custom_code must be 3-30 characters: letters, digits, hyphens, underscores"
            )
        return value


class ShortenResponse(BaseModel):
    code: str
    short_url: str
    original_url: str


class StatsResponse(BaseModel):
    code: str
    original_url: str
    clicks: int
    created_at: str


def generate_code(conn) -> str:
    for _ in range(10):
        code = "".join(random.choices(CODE_ALPHABET, k=CODE_LENGTH))
        if not database.code_exists(conn, code):
            return code
    raise HTTPException(status_code=500, detail="Could not generate a unique code, try again.")


@app.post("/shorten", response_model=ShortenResponse)
def shorten(payload: ShortenRequest, conn=Depends(get_db)) -> ShortenResponse:
    original_url = str(payload.url)

    if payload.custom_code:
        code = payload.custom_code
        if not database.create_link(conn, code, original_url):
            raise HTTPException(status_code=409, detail=f"Code '{code}' is already taken.")
    else:
        code = generate_code(conn)
        database.create_link(conn, code, original_url)

    return ShortenResponse(code=code, short_url=f"/{code}", original_url=original_url)


@app.get("/stats/{code}", response_model=StatsResponse)
def stats(code: str, conn=Depends(get_db)) -> StatsResponse:
    row = database.get_link(conn, code)
    if row is None:
        raise HTTPException(status_code=404, detail="No link found for that code.")
    return StatsResponse(
        code=row["code"],
        original_url=row["original_url"],
        clicks=row["clicks"],
        created_at=row["created_at"],
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/{code}")
def redirect(code: str, conn=Depends(get_db)):
    row = database.get_link(conn, code)
    if row is None:
        raise HTTPException(status_code=404, detail="No link found for that code.")
    database.increment_clicks(conn, code)
    return RedirectResponse(url=row["original_url"], status_code=307)
