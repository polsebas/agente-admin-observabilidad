import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class TimeoutSession(requests.Session):
    def __init__(self, timeout=None):
        self.timeout = timeout
        super().__init__()

    def request(self, method, url, *args, **kwargs):
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout
        return super().request(method, url, *args, **kwargs)

def get_shared_session(
    retries: int = 3,
    backoff_factor: float = 0.5,
    status_forcelist: tuple = (500, 502, 503, 504),
    timeout: int = 10
) -> requests.Session:
    """Configura y devuelve una sesión requests compartida con retries."""
    session = TimeoutSession(timeout=timeout)
    
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Headers default
    session.headers.update({
        "User-Agent": "Agno-Observability-Agent/1.0",
        "Content-Type": "application/json"
    })
    
    return session

# Singleton instance
shared_client = get_shared_session()
