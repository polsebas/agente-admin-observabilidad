from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class Alert(BaseModel):
    status: str
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    startsAt: Optional[datetime] = None
    endsAt: Optional[datetime] = None
    generatorURL: Optional[str] = None
    fingerprint: Optional[str] = None

class GroupLabel(BaseModel):
    alertname: Optional[str] = None

class AlertmanagerWebhook(BaseModel):
    receiver: str
    status: str
    alerts: List[Alert]
    groupLabels: Dict[str, str] = Field(default_factory=dict)
    commonLabels: Dict[str, str] = Field(default_factory=dict)
    commonAnnotations: Dict[str, str] = Field(default_factory=dict)
    externalURL: Optional[str] = None
    version: Optional[str] = None
    groupKey: Optional[str] = None
    truncatedAlerts: Optional[int] = 0
