"""OpenTelemetry configuration for bridge design system."""

import os
import base64
from typing import Optional

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from openinference.instrumentation.smolagents import SmolagentsInstrumentor

from ..config.logging_config import get_logger
from ..config.settings import settings

logger = get_logger(__name__)


class OpenTelemetryConfig:
    """Manages OpenTelemetry configuration for the bridge design system."""
    
    def __init__(self, backend: Optional[str] = None):
        """
        Initialize OpenTelemetry configuration.
        
        Args:
            backend: One of "none", "console", "langfuse", "phoenix", "hybrid"
                    If None, uses settings.otel_backend
        """
        self.backend = backend or settings.otel_backend
        self.trace_provider = TracerProvider()
        self._configured = False
        self._instrumentor = None
        
    def configure_langfuse(self) -> bool:
        """Configure Langfuse as OpenTelemetry backend."""
        public_key = settings.langfuse_public_key
        secret_key = settings.langfuse_secret_key
        
        if not public_key or not secret_key:
            logger.warning("⚠️ Langfuse keys not found in settings")
            return False
            
        try:
            auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
            
            # Set up OTLP endpoint for Langfuse
            if "us.cloud.langfuse.com" in settings.langfuse_host:
                endpoint = "https://us.cloud.langfuse.com/api/public/otel"
            else:
                endpoint = "https://cloud.langfuse.com/api/public/otel"
                
            os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = endpoint
            os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {auth}"
            
            exporter = OTLPSpanExporter()
            self.trace_provider.add_span_processor(SimpleSpanProcessor(exporter))
            logger.info("✅ Configured Langfuse OpenTelemetry backend")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to configure Langfuse: {e}")
            return False
        
    def configure_phoenix(self, lcars_exporter=None) -> bool:
        """Configure Arize Phoenix as OpenTelemetry backend with optional LCARS integration."""
        try:
            # Import required OTLP exporter
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            
            phoenix_url = f"{settings.phoenix_host}:{settings.phoenix_port}"
            
            # Configure OTLP gRPC exporter for Phoenix
            phoenix_exporter = OTLPSpanExporter(
                endpoint="http://localhost:4317",
                insecure=True  # For local development
            )
            
            self.trace_provider.add_span_processor(SimpleSpanProcessor(phoenix_exporter))
            logger.info(f"✅ Configured Phoenix OpenTelemetry backend at {phoenix_url}")
            
            # Add LCARS exporter if provided for combined monitoring
            if lcars_exporter:
                self.trace_provider.add_span_processor(SimpleSpanProcessor(lcars_exporter))
                logger.info("✅ Added LCARS exporter to Phoenix configuration")
            
            return True
            
        except ImportError:
            logger.warning("⚠️ Phoenix not installed. Install with: uv sync --extra telemetry")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to configure Phoenix: {e}")
            return False
        
    def configure_console(self) -> bool:
        """Configure console output for debugging."""
        try:
            exporter = ConsoleSpanExporter()
            self.trace_provider.add_span_processor(SimpleSpanProcessor(exporter))
            logger.info("✅ Configured Console OpenTelemetry backend")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to configure console backend: {e}")
            return False
        
    def configure_hybrid(self, lcars_exporter=None) -> bool:
        """Configure hybrid mode with LCARS integration."""
        try:
            # Add console for debugging
            if settings.debug:
                self.configure_console()
            
            # Add Langfuse if keys available
            if settings.langfuse_public_key and settings.langfuse_secret_key:
                self.configure_langfuse()
            
            # Add custom LCARS exporter if provided
            if lcars_exporter:
                self.trace_provider.add_span_processor(SimpleSpanProcessor(lcars_exporter))
                logger.info("✅ Added LCARS exporter to hybrid configuration")
                
            logger.info("✅ Configured Hybrid OpenTelemetry backend")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to configure hybrid backend: {e}")
            return False
        
    def instrument(self, lcars_exporter=None) -> bool:
        """Instrument smolagents with OpenTelemetry.
        
        Args:
            lcars_exporter: Optional LCARS span exporter for hybrid mode
            
        Returns:
            True if instrumentation successful, False otherwise
        """
        if not settings.otel_enabled:
            logger.info("📊 OpenTelemetry disabled in settings")
            return False
            
        if self._configured:
            logger.warning("⚠️ OpenTelemetry already instrumented")
            return True
            
        try:
            # Configure backend
            success = False
            if self.backend == "langfuse":
                success = self.configure_langfuse()
            elif self.backend == "phoenix":
                success = self.configure_phoenix(lcars_exporter)  # Pass LCARS exporter to Phoenix
            elif self.backend == "console":
                success = self.configure_console()
            elif self.backend == "hybrid":
                success = self.configure_hybrid(lcars_exporter)
            elif self.backend == "none":
                logger.info("📊 OpenTelemetry backend set to 'none' - skipping instrumentation")
                return False
            else:
                logger.error(f"❌ Unknown OpenTelemetry backend: {self.backend}")
                return False
                
            if not success:
                logger.error("❌ Failed to configure OpenTelemetry backend")
                return False
                
            # Instrument smolagents
            self._instrumentor = SmolagentsInstrumentor()
            self._instrumentor.instrument(tracer_provider=self.trace_provider)
            self._configured = True
            
            logger.info(f"🚀 OpenTelemetry instrumentation active with {self.backend} backend")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to instrument OpenTelemetry: {e}")
            return False
    
    def shutdown(self) -> None:
        """Shutdown OpenTelemetry instrumentation."""
        try:
            if self._instrumentor:
                self._instrumentor.uninstrument()
                logger.info("🔌 OpenTelemetry instrumentation shutdown")
            
            # Shutdown trace provider
            if hasattr(self.trace_provider, 'shutdown'):
                self.trace_provider.shutdown()
                
            self._configured = False
            
        except Exception as e:
            logger.warning(f"⚠️ Error shutting down OpenTelemetry: {e}")
    
    @property
    def is_configured(self) -> bool:
        """Check if OpenTelemetry is configured."""
        return self._configured


# Global instance for easy access
_global_otel_config: Optional[OpenTelemetryConfig] = None


def get_otel_config() -> OpenTelemetryConfig:
    """Get or create global OpenTelemetry configuration."""
    global _global_otel_config
    if _global_otel_config is None:
        _global_otel_config = OpenTelemetryConfig()
    return _global_otel_config


def instrument_smolagents(backend: Optional[str] = None, lcars_exporter=None) -> bool:
    """
    Convenience function to instrument smolagents with OpenTelemetry.
    
    Args:
        backend: OpenTelemetry backend to use
        lcars_exporter: Optional LCARS span exporter for hybrid mode
        
    Returns:
        True if instrumentation successful, False otherwise
    """
    config = get_otel_config()
    if backend:
        config.backend = backend
    return config.instrument(lcars_exporter)


def shutdown_otel() -> None:
    """Shutdown global OpenTelemetry configuration."""
    global _global_otel_config
    if _global_otel_config:
        _global_otel_config.shutdown()
        _global_otel_config = None