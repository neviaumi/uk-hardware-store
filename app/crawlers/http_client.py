from browserforge.headers import HeaderGenerator
from curl_cffi.requests import AsyncSession, BrowserTypeLiteral

_header_generator = HeaderGenerator()


def create_client(impersonate: BrowserTypeLiteral | None = None) -> AsyncSession:
    headers = _header_generator.generate()
    return AsyncSession(impersonate=impersonate, headers=headers)
