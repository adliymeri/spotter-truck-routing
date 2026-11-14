import httpx

from planner.domain.entities import LatLng
from planner.ports import ProviderError


class MapboxGeocoder:
    def __init__(
        self,
        token: str,
        base_url: str,
        timeout_seconds: float,
        countries: str,
        client: httpx.Client | None = None,
    ):
        if not token:
            raise ValueError("Mapbox token is missing")
        self._token = token
        self._base_url = base_url
        self._countries = countries
        self._client = client or httpx.Client(timeout=timeout_seconds)

    def search(self, query: str, limit: int = 5) -> list[tuple[str, LatLng]]:
        params: dict[str, str | int] = {
            "q": query,
            "access_token": self._token,
            "limit": limit,
            "autocomplete": "true",
        }
        if self._countries:
            params["country"] = self._countries

        try:
            response = self._client.get(self._base_url, params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(f"Mapbox geocoding failed with status {exc.response.status_code}") from None
        except httpx.HTTPError as exc:
            raise ProviderError(f"Mapbox geocoding failed: {type(exc).__name__}") from None

        results: list[tuple[str, LatLng]] = []
        for feature in response.json().get("features", []):
            props = feature.get("properties", {})
            label = props.get("full_address") or props.get("name")
            lng, lat = feature["geometry"]["coordinates"][:2]
            if label:
                results.append((label, LatLng(lat, lng)))
        return results