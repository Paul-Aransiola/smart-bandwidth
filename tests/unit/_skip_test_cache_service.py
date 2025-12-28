"""
Unit tests for CacheService.
"""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.cache_service import CacheService


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis_client = MagicMock()
    redis_client.ping = AsyncMock()
    redis_client.get = AsyncMock()
    redis_client.set = AsyncMock()
    redis_client.setex = AsyncMock()
    redis_client.delete = AsyncMock()
    redis_client.exists = AsyncMock()
    redis_client.ttl = AsyncMock()
    redis_client.flushdb = AsyncMock()
    redis_client.info = AsyncMock()
    redis_client.scan_iter = MagicMock()
    redis_client.aclose = AsyncMock()
    return redis_client


@pytest.fixture
async def cache_service():
    """Create cache service instance."""
    service = CacheService(redis_url="redis://localhost:6379", enabled=True)
    return service


@pytest.mark.asyncio
class TestCacheServiceConnection:
    """Tests for cache service connection management."""

    async def test_connect_success(self, cache_service, mock_redis):
        """Test successful Redis connection."""

        async def mock_from_url_async(*args, **kwargs):
            return mock_redis

        with patch("src.services.cache_service.redis.from_url", side_effect=mock_from_url_async):
            mock_redis.ping = AsyncMock(return_value=True)

            await cache_service.connect()

            assert cache_service.enabled is True
            assert cache_service._client is mock_redis
            mock_redis.ping.assert_called_once()

    async def test_connect_failure(self, cache_service):
        """Test connection failure handling."""
        with patch("src.services.cache_service.redis.from_url") as mock_from_url:
            mock_from_url.side_effect = Exception("Connection failed")

            await cache_service.connect()

            assert cache_service.enabled is False
            assert cache_service._client is None

    async def test_connect_disabled(self):
        """Test connection when caching is disabled."""
        service = CacheService(redis_url="redis://localhost:6379", enabled=False)

        await service.connect()

        assert service.enabled is False
        assert service._client is None

    async def test_disconnect(self, cache_service, mock_redis):
        """Test disconnecting from Redis."""
        cache_service._client = mock_redis

        await cache_service.disconnect()

        mock_redis.aclose.assert_called_once()


@pytest.mark.asyncio
class TestCacheGetOperations:
    """Tests for cache get operations."""

    async def test_get_success(self, cache_service, mock_redis):
        """Test successful cache get."""
        cache_service._client = mock_redis
        mock_redis.get.return_value = '{"key": "value"}'

        result = await cache_service.get("test_key")

        assert result == {"key": "value"}
        mock_redis.get.assert_called_once_with("test_key")

    async def test_get_miss(self, cache_service, mock_redis):
        """Test cache miss."""
        cache_service._client = mock_redis
        mock_redis.get.return_value = None

        result = await cache_service.get("test_key")

        assert result is None

    async def test_get_disabled(self):
        """Test get when caching is disabled."""
        service = CacheService(redis_url="redis://localhost:6379", enabled=False)

        result = await service.get("test_key")

        assert result is None

    async def test_get_no_client(self, cache_service):
        """Test get when client is not connected."""
        cache_service._client = None

        result = await cache_service.get("test_key")

        assert result is None

    async def test_get_error_handling(self, cache_service, mock_redis):
        """Test error handling during get."""
        cache_service._client = mock_redis
        mock_redis.get.side_effect = Exception("Redis error")

        result = await cache_service.get("test_key")

        assert result is None


@pytest.mark.asyncio
class TestCacheSetOperations:
    """Tests for cache set operations."""

    async def test_set_success(self, cache_service, mock_redis):
        """Test successful cache set."""
        cache_service._client = mock_redis
        mock_redis.set.return_value = True

        result = await cache_service.set("test_key", {"key": "value"})

        assert result is True
        mock_redis.set.assert_called_once()

    async def test_set_with_ttl_seconds(self, cache_service, mock_redis):
        """Test cache set with TTL in seconds."""
        cache_service._client = mock_redis
        mock_redis.setex.return_value = True

        result = await cache_service.set("test_key", {"key": "value"}, ttl=3600)

        assert result is True
        mock_redis.setex.assert_called_once_with("test_key", 3600, '{"key": "value"}')

    async def test_set_with_ttl_timedelta(self, cache_service, mock_redis):
        """Test cache set with TTL as timedelta."""
        cache_service._client = mock_redis
        mock_redis.setex.return_value = True

        result = await cache_service.set("test_key", {"key": "value"}, ttl=timedelta(hours=1))

        assert result is True
        mock_redis.setex.assert_called_once_with("test_key", 3600, '{"key": "value"}')

    async def test_set_disabled(self):
        """Test set when caching is disabled."""
        service = CacheService(redis_url="redis://localhost:6379", enabled=False)

        result = await service.set("test_key", {"key": "value"})

        assert result is False

    async def test_set_no_client(self, cache_service):
        """Test set when client is not connected."""
        cache_service._client = None

        result = await cache_service.set("test_key", {"key": "value"})

        assert result is False

    async def test_set_error_handling(self, cache_service, mock_redis):
        """Test error handling during set."""
        cache_service._client = mock_redis
        mock_redis.set.side_effect = Exception("Redis error")

        result = await cache_service.set("test_key", {"key": "value"})

        assert result is False

    async def test_set_complex_value(self, cache_service, mock_redis):
        """Test setting complex JSON value."""
        cache_service._client = mock_redis
        mock_redis.set.return_value = True

        complex_value = {
            "users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
            "count": 2,
            "metadata": {"cached_at": "2025-11-18"},
        }

        result = await cache_service.set("test_key", complex_value)

        assert result is True


@pytest.mark.asyncio
class TestCacheDeleteOperations:
    """Tests for cache delete operations."""

    async def test_delete_success(self, cache_service, mock_redis):
        """Test successful cache delete."""
        cache_service._client = mock_redis
        mock_redis.delete.return_value = 1

        result = await cache_service.delete("test_key")

        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")

    async def test_delete_key_not_exists(self, cache_service, mock_redis):
        """Test deleting nonexistent key."""
        cache_service._client = mock_redis
        mock_redis.delete.return_value = 0

        result = await cache_service.delete("test_key")

        assert result is False

    async def test_delete_disabled(self):
        """Test delete when caching is disabled."""
        service = CacheService(redis_url="redis://localhost:6379", enabled=False)

        result = await service.delete("test_key")

        assert result is False

    async def test_delete_error_handling(self, cache_service, mock_redis):
        """Test error handling during delete."""
        cache_service._client = mock_redis
        mock_redis.delete.side_effect = Exception("Redis error")

        result = await cache_service.delete("test_key")

        assert result is False


@pytest.mark.asyncio
class TestCachePatternOperations:
    """Tests for pattern-based operations."""

    async def test_delete_pattern_success(self, cache_service, mock_redis):
        """Test deleting keys by pattern."""
        cache_service._client = mock_redis

        async def mock_scan():
            for key in ["device:1", "device:2", "device:3"]:
                yield key

        mock_redis.scan_iter.return_value = mock_scan()
        mock_redis.delete.return_value = 3

        result = await cache_service.delete_pattern("device:*")

        assert result == 3
        mock_redis.scan_iter.assert_called_once_with(match="device:*")

    async def test_delete_pattern_no_matches(self, cache_service, mock_redis):
        """Test deleting pattern with no matches."""
        cache_service._client = mock_redis

        async def mock_scan():
            return
            yield

        mock_redis.scan_iter.return_value = mock_scan()

        result = await cache_service.delete_pattern("nonexistent:*")

        assert result == 0

    async def test_delete_pattern_disabled(self):
        """Test delete pattern when caching is disabled."""
        service = CacheService(redis_url="redis://localhost:6379", enabled=False)

        result = await service.delete_pattern("test:*")

        assert result == 0

    async def test_delete_pattern_error_handling(self, cache_service, mock_redis):
        """Test error handling during pattern delete."""
        cache_service._client = mock_redis
        mock_redis.scan_iter.side_effect = Exception("Redis error")

        result = await cache_service.delete_pattern("test:*")

        assert result == 0


@pytest.mark.asyncio
class TestCacheUtilityOperations:
    """Tests for utility operations."""

    async def test_exists_true(self, cache_service, mock_redis):
        """Test checking if key exists."""
        cache_service._client = mock_redis
        mock_redis.exists.return_value = 1

        result = await cache_service.exists("test_key")

        assert result is True

    async def test_exists_false(self, cache_service, mock_redis):
        """Test checking nonexistent key."""
        cache_service._client = mock_redis
        mock_redis.exists.return_value = 0

        result = await cache_service.exists("test_key")

        assert result is False

    async def test_exists_disabled(self):
        """Test exists when caching is disabled."""
        service = CacheService(redis_url="redis://localhost:6379", enabled=False)

        result = await service.exists("test_key")

        assert result is False

    async def test_get_ttl_success(self, cache_service, mock_redis):
        """Test getting TTL for key."""
        cache_service._client = mock_redis
        mock_redis.ttl.return_value = 3600

        result = await cache_service.get_ttl("test_key")

        assert result == 3600

    async def test_get_ttl_no_expiry(self, cache_service, mock_redis):
        """Test getting TTL for key without expiry."""
        cache_service._client = mock_redis
        mock_redis.ttl.return_value = -1

        result = await cache_service.get_ttl("test_key")

        assert result == -1

    async def test_get_ttl_key_not_exists(self, cache_service, mock_redis):
        """Test getting TTL for nonexistent key."""
        cache_service._client = mock_redis
        mock_redis.ttl.return_value = -2

        result = await cache_service.get_ttl("test_key")

        assert result == -2

    async def test_get_ttl_disabled(self):
        """Test get TTL when caching is disabled."""
        service = CacheService(redis_url="redis://localhost:6379", enabled=False)

        result = await service.get_ttl("test_key")

        assert result == -2

    async def test_clear_all_success(self, cache_service, mock_redis):
        """Test clearing all cache."""
        cache_service._client = mock_redis
        mock_redis.flushdb.return_value = True

        result = await cache_service.clear_all()

        assert result is True
        mock_redis.flushdb.assert_called_once()

    async def test_clear_all_disabled(self):
        """Test clear all when caching is disabled."""
        service = CacheService(redis_url="redis://localhost:6379", enabled=False)

        result = await service.clear_all()

        assert result is False

    async def test_clear_all_error_handling(self, cache_service, mock_redis):
        """Test error handling during clear all."""
        cache_service._client = mock_redis
        mock_redis.flushdb.side_effect = Exception("Redis error")

        result = await cache_service.clear_all()

        assert result is False


@pytest.mark.asyncio
class TestCacheStatistics:
    """Tests for cache statistics."""

    async def test_get_stats_success(self, cache_service, mock_redis):
        """Test getting cache statistics."""
        cache_service._client = mock_redis
        mock_redis.info.side_effect = [
            {"keyspace_hits": 1000, "keyspace_misses": 100},
            {"db0": {"keys": 50}},
        ]

        result = await cache_service.get_stats()

        assert result["enabled"] is True
        assert result["total_keys"] == 50
        assert result["hits"] == 1000
        assert result["misses"] == 100
        assert result["hit_rate"] == 90.91

    async def test_get_stats_disabled(self):
        """Test getting stats when caching is disabled."""
        service = CacheService(redis_url="redis://localhost:6379", enabled=False)

        result = await service.get_stats()

        assert result == {"enabled": False}

    async def test_get_stats_error_handling(self, cache_service, mock_redis):
        """Test error handling during stats retrieval."""
        cache_service._client = mock_redis
        mock_redis.info.side_effect = Exception("Redis error")

        result = await cache_service.get_stats()

        assert result["enabled"] is True
        assert "error" in result

    async def test_calculate_hit_rate_no_requests(self, cache_service):
        """Test hit rate calculation with no requests."""
        hit_rate = cache_service._calculate_hit_rate(0, 0)

        assert hit_rate == 0.0

    async def test_calculate_hit_rate_100_percent(self, cache_service):
        """Test hit rate calculation with 100% hits."""
        hit_rate = cache_service._calculate_hit_rate(100, 0)

        assert hit_rate == 100.0

    async def test_calculate_hit_rate_mixed(self, cache_service):
        """Test hit rate calculation with mixed hits and misses."""
        hit_rate = cache_service._calculate_hit_rate(750, 250)

        assert hit_rate == 75.0


@pytest.mark.asyncio
class TestCacheServiceInitialization:
    """Tests for cache service initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        service = CacheService()

        assert service.redis_url == "redis://localhost:6379"
        assert service.enabled is True
        assert service._client is None

    def test_init_with_custom_url(self):
        """Test initialization with custom Redis URL."""
        service = CacheService(redis_url="redis://custom:6380")

        assert service.redis_url == "redis://custom:6380"
        assert service.enabled is True

    def test_init_disabled(self):
        """Test initialization with caching disabled."""
        service = CacheService(enabled=False)

        assert service.enabled is False


@pytest.mark.asyncio
class TestCacheSingletonFunctions:
    """Tests for singleton cache service functions."""

    def test_init_cache_service(self):
        """Test initializing global cache service."""
        from src.services.cache_service import init_cache_service

        service = init_cache_service("redis://localhost:6379", enabled=True)

        assert service is not None
        assert service.redis_url == "redis://localhost:6379"
        assert service.enabled is True

    def test_get_cache_service_not_initialized(self):
        """Test getting cache service when not initialized."""
        from src.services import cache_service

        # Reset the global instance
        cache_service._cache_service = None

        from src.services.cache_service import get_cache_service

        with pytest.raises(RuntimeError, match="Cache service not initialized"):
            get_cache_service()

    def test_get_cache_service_after_init(self):
        """Test getting cache service after initialization."""
        from src.services.cache_service import get_cache_service, init_cache_service

        service = init_cache_service("redis://localhost:6379", enabled=True)
        retrieved_service = get_cache_service()

        assert retrieved_service is service
