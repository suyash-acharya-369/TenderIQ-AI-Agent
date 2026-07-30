import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RateLimitManager:
    def __init__(self, db_session=None):
        self.db = db_session
        self.domain_delays: Dict[str, float] = {}

    def enforce_rate_limit(self, domain: str, default_delay: float = 2.0):
        """Wait for the specified delay before allowing the next request to the domain."""
        delay = self.domain_delays.get(domain, default_delay)
        logger.debug(f"RateLimitManager: Waiting {delay}s for domain {domain}")
        time.sleep(delay)

    def handle_429(self, domain: str, response_headers: Dict[str, Any]):
        """Handle 429 Too Many Requests by parsing Retry-After and applying exponential backoff."""
        retry_after = response_headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            delay = float(retry_after)
        else:
            # Exponential backoff base
            current_delay = self.domain_delays.get(domain, 2.0)
            delay = current_delay * 2
            
        logger.warning(f"RateLimitManager: Received 429 from {domain}. Backing off for {delay}s.")
        self.domain_delays[domain] = delay
        time.sleep(delay)

    def reset_domain(self, domain: str, default_delay: float = 2.0):
        """Reset the rate limit delay for a domain after successful requests."""
        self.domain_delays[domain] = default_delay

    def report_ip_block(self, domain: str):
        """Handle IP blocking by notifying the system or rotating proxies if configured."""
        logger.error(f"RateLimitManager: IP Block detected for domain {domain}! Proxy rotation required.")
        # In an enterprise system, this would trigger an event on the event bus to switch proxies.
