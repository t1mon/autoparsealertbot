import os

import structlog

logger = structlog.get_logger(__name__)

from core.config import PROXY_USER, PROXY_PASSWORD, PROXY_IP, PROXY_PORT


def setup_proxy() -> bool:
    """
    Ставит http(s)_proxy в окружение, только если PROXY_IP задан.
    Иначе сбрасывает битые значения — иначе Groq/HTTP ломаются на None:None@None.
    """
    try:
        if not (PROXY_IP and PROXY_PORT):
            for key in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"):
                os.environ.pop(key, None)
            return False

        user = PROXY_USER or ""
        password = PROXY_PASSWORD or ""
        if user or password:
            auth = f"{user}:{password}@"
        else:
            auth = ""
        proxy_url = f"http://{auth}{PROXY_IP}:{PROXY_PORT}"
        os.environ["http_proxy"] = proxy_url
        os.environ["https_proxy"] = proxy_url
        return True
    except Exception as e:
        logger.exception("proxy_setup_error", error=e)
        return False


if __name__ == "__main__":
    setup_proxy()
