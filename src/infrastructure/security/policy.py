"""Provider-independent deny-by-default identity and endpoint controls."""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address, ip_network
from urllib.parse import urlsplit

_ALLOWED_V4 = tuple(ip_network(net) for net in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))
_ALLOWED_V6 = ip_network("fc00::/7")
_OPERATIONS = frozenset({"evaluation:submit", "evaluation:read", "feedback:create", "rubric:manage", "metrics:read"})


@dataclass(frozen=True)
class Identity:
    user_id: str
    organization_id: str
    permissions: frozenset[str]
    is_authenticated: bool = False
    assigned_resource_ids: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ResourceScope:
    resource_id: str
    owner_id: str
    organization_id: str


def is_allowed(identity: Identity | None, operation: str, resource: ResourceScope | None = None) -> bool:
    if identity is None or not identity.is_authenticated or not identity.user_id or not identity.organization_id:
        return False
    if operation not in _OPERATIONS or operation not in identity.permissions:
        return False
    if operation in ("evaluation:read", "feedback:create"):
        if resource is None or resource.organization_id != identity.organization_id:
            return False
        if operation == "evaluation:read":
            return resource.owner_id == identity.user_id or resource.resource_id in identity.assigned_resource_ids
        return resource.resource_id in identity.assigned_resource_ids
    return resource is None or resource.organization_id == identity.organization_id


def validate_internal_endpoint(url: str, *, environment: str) -> str:
    """Validate a future service endpoint without DNS resolution or external calls."""
    try:
        parts = urlsplit(url)
        host = parts.hostname
        address = ip_address(host or "")
        secure = parts.scheme == "https"
        local_dev = environment == "development" and parts.scheme == "http" and address.is_loopback
        allowed = (address.version == 4 and any(address in n for n in _ALLOWED_V4)) or (address.version == 6 and address in _ALLOWED_V6)
        if (not secure and not local_dev) or (not allowed and not (environment == "development" and address.is_loopback)):
            raise ValueError
        if parts.username or parts.password or parts.fragment or parts.query or not parts.port:
            raise ValueError
        if environment not in ("development", "staging", "production"):
            raise ValueError
        return url
    except (ValueError, TypeError):
        raise ValueError("ENDPOINT_NOT_ALLOWED") from None
