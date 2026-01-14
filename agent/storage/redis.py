from redis import Redis
from agent.config import AdminAgentConfig

_config = AdminAgentConfig()

# Redis Synchoronous (simplest for slash commands if generic, but usually async is better for FastAPI)
# However, Redis-py has sync client by default.
# slash_commands.py functions seem to be referenced via QuickCommands API?
# QuickCommands API calls `run_slash_command` which might be async.

# Let's provide both or standard Sync for now if acceptable, or Sync for simplicity in tools.
# But `agent/slash_commands.py` calls are used in `api/quick_commands_api.py`.
# Let's use standard Redis client.

redis_client = Redis.from_url(_config.redis_url, decode_responses=True)

def get_redis():
    return redis_client
