# pyre-ignore-all-errors
import os
import json
import requests
from datetime import datetime, timezone
from typing import Optional
from .models import ShortLink
from fileshare.interfaces import D1Client

class ShortLinkDBInterface:
    @staticmethod
    def create_short_link(short_link: ShortLink):
        sql = """
            INSERT INTO short_links 
            (id, code, shared_file_id, created_at, expires_at, max_downloads, download_count, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = [
            short_link.id,
            short_link.code,
            short_link.shared_file_id,
            short_link.created_at.isoformat() if isinstance(short_link.created_at, datetime) else short_link.created_at,
            short_link.expires_at.isoformat() if isinstance(short_link.expires_at, datetime) else short_link.expires_at,
            short_link.max_downloads,
            short_link.download_count,
            1 if short_link.is_active else 0
        ]
        D1Client.execute(sql, params)
        return short_link

    @staticmethod
    def get_link_by_code(code: str):
        sql = "SELECT * FROM short_links WHERE code = ?"
        res = D1Client.execute(sql, [code])
        results = res.get("results", [])
        
        if not results:
            return None
            
        row = results[0]
        return ShortLink(
            id=row["id"],
            code=row["code"],
            shared_file_id=row["shared_file_id"],
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")),
            expires_at=datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00")) if row["expires_at"] else None,
            max_downloads=int(row["max_downloads"]),
            download_count=int(row["download_count"]),
            is_active=bool(row["is_active"])
        )

    @staticmethod
    def increment_usage(short_link: ShortLink):
        short_link.download_count += 1
        D1Client.execute(
            "UPDATE short_links SET download_count = ? WHERE id = ?",
            [short_link.download_count, short_link.id]
        )
        return short_link
