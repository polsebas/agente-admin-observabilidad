from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from agno.db.sqlite import AsyncSqliteDb
from agno.os import AgentOS

from agent.storage import alert_storage
from api.alerts_api import router as alerts_router
from api.quick_commands_api import router as quick_commands_router
from agent.agents.watchdog_agent import watchdog_agent
from agent.agents.triage_agent import triage_agent
from agent.agents.report_agent import report_agent
from agent.agents.query_agent import query_agent
from agent.agents.observability_team import observability_team

# Cargar variables desde .env si existe (para OPENAI_API_KEY, etc.)
load_dotenv()

# Base de datos para AgentOS y alert storage
db = AsyncSqliteDb(db_file="./agno.db")

# Instancia AgentOS con los agentes individuales
agent_os = AgentOS(
    id="observability-os",
    name="Observability Agent OS",
    description="Sistema de análisis de alertas con Grafana MCP y comandos rápidos",
    agents=[watchdog_agent, triage_agent, report_agent, query_agent],
    teams=[observability_team],
)

# FastAPI app provista por AgentOS
app: FastAPI = agent_os.get_app()

# Habilitar CORS abierto (ajustar en prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Webhooks y APIs custom
app.include_router(alerts_router, prefix="/api")
app.include_router(quick_commands_router, prefix="/api")


@app.on_event("startup")
async def startup_event() -> None:
    alert_storage.init_db()


if __name__ == "__main__":
    # Usar serve de AgentOS (equivale a uvicorn main:app)
    agent_os.serve(app="main:app", host="0.0.0.0", port=7777)


