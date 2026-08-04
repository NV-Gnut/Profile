"""CodeTrace Desktop - lightweight source code security analyzer."""

from .engine import Analyzer
from .models import Finding, Rule, TraceStep

__all__ = ["Analyzer", "Finding", "Rule", "TraceStep"]
__version__ = "1.0.0"
