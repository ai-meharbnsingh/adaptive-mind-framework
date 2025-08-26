# 09_Deployment_Package/security_monitoring.py
"""
Security Monitoring System for Adaptive Mind Framework
Comprehensive enterprise-grade security monitoring and threat detection
"""

import asyncio
import json
import logging
import time
import hashlib
import ipaddress
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from collections import defaultdict, deque
import re

import asyncpg
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.monitor.opentelemetry import configure_azure_monitor
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Configure structured logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Prometheus metrics for security monitoring
SECURITY_EVENTS = Counter(
    "security_events_total", "Total security events", ["event_type", "severity"]
)
THREAT_DETECTION_TIME = Histogram("threat_detection_seconds", "Time to detect threats")
ACTIVE_THREATS = Gauge("active_threats_count", "Number of active threats")
BLOCKED_REQUESTS = Counter(
    "blocked_requests_total", "Total blocked requests", ["reason"]
)
API_KEY_VALIDATION_TIME = Histogram(
    "api_key_validation_seconds", "API key validation time"
)


@dataclass
class SecurityEvent:
    """Security event data structure"""

    id: str
    timestamp: datetime
    event_type: str
    severity: str  # low, medium, high, critical
    source_ip: str
    user_agent: str
    endpoint: str
    description: str
    metadata: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class ThreatIntelligence:
    """Threat intelligence data"""

    ip_address: str
    threat_type: str
    confidence_score: float
    first_seen: datetime
    last_seen: datetime
    indicators: List[str]


class SecurityMonitor:
    """
    Comprehensive security monitoring system for production deployment
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.running = False

        # Security event storage
        self.security_events: deque = deque(maxlen=10000)
        self.active_threats: Dict[str, ThreatIntelligence] = {}

        # Rate limiting tracking
        self.request_counts: defaultdict = defaultdict(lambda: deque(maxlen=1000))
        self.blocked_ips: Set[str] = set()

        # API key validation tracking
        self.failed_validations: defaultdict = defaultdict(int)
        self.suspicious_keys: Set[str] = set()

        # Threat detection patterns
        self.threat_patterns = self._load_threat_patterns()

        # Azure clients
        self.credential = DefaultAzureCredential()
        self.key_vault_client = None
        self.db_pool = None

        # Initialize Azure monitoring if enabled
        if config.get("azure", {}).get("application_insights", {}).get("enabled"):
            configure_azure_monitor()

    def _load_threat_patterns(self) -> Dict[str, List[str]]:
        """Load threat detection patterns"""
        return {
            "sql_injection": [
                r"('|(\\'))+.*(or|and).+(('|(\\'))+|\w+\\()",
                r"(union.*select|select.*from|insert.*into|delete.*from)",
                r"(drop\s+table|create\s+table|alter\s+table)",
            ],
            "xss_attack": [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"eval\s*\(",
                r"document\.(cookie|write)",
            ],
            "command_injection": [
                r"(;|\||&&|\$\(|\`).*(ls|cat|rm|wget|curl|nc|bash|sh)",
                r"(exec|system|passthru|shell_exec)\s*\(",
                r"\$\{[^}]*\}",
            ],
            "path_traversal": [
                r"\.\./",
                r"\.\.\\",
                r"%2e%2e%2f",
                r"%2e%2e\\",
                r"file://",
                r"..%2f",
            ],
            "suspicious_user_agents": [
                r"(sqlmap|nikto|nmap|masscan|zap|burp)",
                r"(bot|crawler|spider).*?(scan|hack|exploit)",
                r"^.{0,10}$",  # Very short user agents
                r"^[a-zA-Z]{50,}$",  # Very long random strings
            ],
        }

    async def initialize(self):
        """Initialize security monitoring system"""
        try:
            # Initialize Azure Key Vault client
            if self.config.get("azure", {}).get("key_vault", {}).get("enabled"):
                vault_url = self.config["azure"]["key_vault"]["vault_url"]
                self.key_vault_client = SecretClient(
                    vault_url=vault_url, credential=self.credential
                )
                logger.info("Azure Key Vault client initialized")

            # Initialize database connection pool
            if self.config.get("shared", {}).get("database"):
                db_url = await self._get_secret("DATABASE-URL")
                if db_url:
                    self.db_pool = await asyncpg.create_pool(
                        db_url, min_size=2, max_size=10, command_timeout=60
                    )
                    logger.info("Database connection pool initialized")

            # Start Prometheus metrics server
            start_http_server(9091)
            logger.info("Prometheus metrics server started on port 9091")

            logger.info("Security monitoring system initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize security monitoring: {e}")
            raise

    async def _get_secret(self, secret_name: str) -> Optional[str]:
        """Retrieve secret from Azure Key Vault"""
        if not self.key_vault_client:
            return None

        try:
            secret = await asyncio.to_thread(
                self.key_vault_client.get_secret, secret_name
            )
            return secret.value
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            return None

    async def start_monitoring(self):
        """Start the security monitoring system"""
        if self.running:
            logger.warning("Security monitoring is already running")
            return

        self.running = True
        logger.info("Starting security monitoring system")

        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._monitor_threats()),
            asyncio.create_task(self._monitor_rate_limits()),
            asyncio.create_task(self._monitor_api_keys()),
            asyncio.create_task(self._cleanup_old_events()),
            asyncio.create_task(self._generate_reports()),
        ]

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Security monitoring error: {e}")
        finally:
            self.running = False

    async def stop_monitoring(self):
        """Stop the security monitoring system"""
        logger.info("Stopping security monitoring system")
        self.running = False

        if self.db_pool:
            await self.db_pool.close()

    async def analyze_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze incoming request for security threats

        Args:
            request_data: Dictionary containing request information

        Returns:
            Analysis result with threat assessment
        """
        start_time = time.time()

        try:
            analysis_result = {
                "timestamp": datetime.now(timezone.utc),
                "request_id": request_data.get("id", "unknown"),
                "threats_detected": [],
                "risk_score": 0.0,
                "action_required": "allow",
                "details": {},
            }

            # Extract request components
            ip_address = request_data.get("source_ip", "")
            user_agent = request_data.get("user_agent", "")
            endpoint = request_data.get("endpoint", "")
            payload = request_data.get("payload", "")

            # Check IP reputation
            ip_threat = await self._check_ip_reputation(ip_address)
            if ip_threat:
                analysis_result["threats_detected"].append("malicious_ip")
                analysis_result["risk_score"] += 0.8
                analysis_result["details"]["ip_threat"] = ip_threat

            # Check for injection attacks
            injection_threat = self._detect_injection_attacks(payload + endpoint)
            if injection_threat:
                analysis_result["threats_detected"].append("injection_attack")
                analysis_result["risk_score"] += 0.9
                analysis_result["details"]["injection_type"] = injection_threat

            # Analyze user agent
            ua_threat = self._analyze_user_agent(user_agent)
            if ua_threat:
                analysis_result["threats_detected"].append("suspicious_user_agent")
                analysis_result["risk_score"] += 0.5
                analysis_result["details"]["user_agent_threat"] = ua_threat

            # Check rate limiting
            rate_limit_exceeded = await self._check_rate_limits(ip_address)
            if rate_limit_exceeded:
                analysis_result["threats_detected"].append("rate_limit_exceeded")
                analysis_result["risk_score"] += 0.6
                analysis_result["details"]["rate_limit"] = rate_limit_exceeded

            # Determine action based on risk score
            if analysis_result["risk_score"] >= 0.8:
                analysis_result["action_required"] = "block"
            elif analysis_result["risk_score"] >= 0.5:
                analysis_result["action_required"] = "monitor"

            # Log security event if threats detected
            if analysis_result["threats_detected"]:
                await self._log_security_event(
                    event_type="threat_detected",
                    severity=self._calculate_severity(analysis_result["risk_score"]),
                    source_ip=ip_address,
                    user_agent=user_agent,
                    endpoint=endpoint,
                    description=f"Threats detected: {', '.join(analysis_result['threats_detected'])}",
                    metadata=analysis_result["details"],
                )

            # Update Prometheus metrics
            THREAT_DETECTION_TIME.observe(time.time() - start_time)
            for threat in analysis_result["threats_detected"]:
                SECURITY_EVENTS.labels(
                    event_type=threat,
                    severity=self._calculate_severity(analysis_result["risk_score"]),
                ).inc()

            return analysis_result

        except Exception as e:
            logger.error(f"Request analysis failed: {e}")
            return {
                "timestamp": datetime.now(timezone.utc),
                "error": str(e),
                "action_required": "allow",  # Fail open for availability
            }

    async def validate_api_key(
        self, api_key: str, provider: str, source_ip: str
    ) -> Dict[str, Any]:
        """
        Validate API key and detect suspicious patterns

        Args:
            api_key: The API key to validate
            provider: The AI provider (openai, anthropic, google)
            source_ip: Source IP address

        Returns:
            Validation result
        """
        start_time = time.time()

        try:
            validation_result = {
                "valid": False,
                "provider": provider,
                "threats_detected": [],
                "risk_score": 0.0,
                "action_required": "deny",
            }

            # Hash the API key for security
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]

            # Check key format
            format_valid = self._validate_key_format(api_key, provider)
            if not format_valid:
                validation_result["threats_detected"].append("invalid_format")
                validation_result["risk_score"] += 0.3

                # Track failed validations
                self.failed_validations[source_ip] += 1
                if self.failed_validations[source_ip] > 5:
                    validation_result["threats_detected"].append("repeated_failures")
                    validation_result["risk_score"] += 0.7

            # Check for suspicious key patterns
            if self._is_suspicious_key(api_key):
                validation_result["threats_detected"].append("suspicious_pattern")
                validation_result["risk_score"] += 0.8
                self.suspicious_keys.add(key_hash)

            # Check if key is in suspicious list
            if key_hash in self.suspicious_keys:
                validation_result["threats_detected"].append("known_suspicious")
                validation_result["risk_score"] += 0.9

            # For demo mode, always allow with mock validation
            if (
                self.config.get("deployment_modes", {})
                .get("hosted_demo", {})
                .get("security", {})
                .get("api_key_validation")
                == "mock"
            ):
                validation_result["valid"] = True
                validation_result["action_required"] = "allow"
                validation_result["risk_score"] = 0.0

            # For evaluation mode, perform strict validation
            elif (
                self.config.get("deployment_modes", {})
                .get("buyer_evaluation", {})
                .get("security", {})
                .get("api_key_validation")
                == "strict"
            ):
                if format_valid and validation_result["risk_score"] < 0.5:
                    validation_result["valid"] = True
                    validation_result["action_required"] = "allow"

            # Log validation events
            if validation_result["threats_detected"]:
                await self._log_security_event(
                    event_type="api_key_validation_failed",
                    severity=self._calculate_severity(validation_result["risk_score"]),
                    source_ip=source_ip,
                    user_agent="",
                    endpoint="/api/validate-key",
                    description=f"API key validation failed: {', '.join(validation_result['threats_detected'])}",
                    metadata={"provider": provider, "key_hash": key_hash},
                )

            # Update metrics
            API_KEY_VALIDATION_TIME.observe(time.time() - start_time)

            return validation_result

        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return {"valid": False, "error": str(e), "action_required": "deny"}

    def _validate_key_format(self, api_key: str, provider: str) -> bool:
        """Validate API key format for specific provider"""
        if provider == "openai":
            return api_key.startswith("sk-") and len(api_key) >= 20
        elif provider == "anthropic":
            return api_key.startswith("sk-ant-") and len(api_key) >= 20
        elif provider == "google":
            return api_key.startswith("AIza") and len(api_key) >= 20
        elif provider == "azure_openai":
            return len(api_key) >= 20  # Azure keys have different format
        else:
            return len(api_key) >= 10  # Generic validation

    def _is_suspicious_key(self, api_key: str) -> bool:
        """Check if API key shows suspicious patterns"""
        suspicious_patterns = [
            r"^[a-z]+$",  # All lowercase
            r"^[A-Z]+$",  # All uppercase
            r"^[0-9]+$",  # All numbers
            r"^(.)\1{10,}",  # Repeated characters
            r"(test|demo|fake|invalid|placeholder)",  # Test patterns
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, api_key, re.IGNORECASE):
                return True

        return False

    async def _check_ip_reputation(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Check IP reputation against threat intelligence"""
        try:
            # Validate IP address format
            ipaddress.ip_address(ip_address)

            # Check against known threat IPs
            if ip_address in self.active_threats:
                threat = self.active_threats[ip_address]
                return {
                    "threat_type": threat.threat_type,
                    "confidence": threat.confidence_score,
                    "last_seen": threat.last_seen.isoformat(),
                }

            # Check against common threat patterns
            if self._is_private_ip(ip_address):
                return None  # Private IPs are generally safe

            # Additional reputation checks could be added here
            # (e.g., external threat intelligence APIs)

            return None

        except ValueError:
            # Invalid IP address format
            return {"threat_type": "invalid_ip", "confidence": 0.9}

    def _is_private_ip(self, ip_address: str) -> bool:
        """Check if IP address is private"""
        try:
            ip = ipaddress.ip_address(ip_address)
            return ip.is_private
        except ValueError:
            return False

    def _detect_injection_attacks(self, payload: str) -> Optional[str]:
        """Detect various injection attack patterns"""
        for attack_type, patterns in self.threat_patterns.items():
            if attack_type in [
                "sql_injection",
                "xss_attack",
                "command_injection",
                "path_traversal",
            ]:
                for pattern in patterns:
                    if re.search(pattern, payload, re.IGNORECASE):
                        return attack_type
        return None

    def _analyze_user_agent(self, user_agent: str) -> Optional[str]:
        """Analyze user agent for suspicious patterns"""
        if not user_agent:
            return "empty_user_agent"

        for pattern in self.threat_patterns["suspicious_user_agents"]:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return "suspicious_pattern"

        return None

    async def _check_rate_limits(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Check if IP address exceeds rate limits"""
        current_time = time.time()
        window_size = 300  # 5 minutes

        # Add current request timestamp
        self.request_counts[ip_address].append(current_time)

        # Remove old timestamps outside the window
        while (
            self.request_counts[ip_address]
            and self.request_counts[ip_address][0] < current_time - window_size
        ):
            self.request_counts[ip_address].popleft()

        # Check rate limit
        request_count = len(self.request_counts[ip_address])
        rate_limit = (
            self.config.get("shared", {})
            .get("rate_limiting", {})
            .get("requests_per_minute", 100)
        )

        if request_count > rate_limit:
            self.blocked_ips.add(ip_address)
            BLOCKED_REQUESTS.labels(reason="rate_limit_exceeded").inc()
            return {
                "requests_in_window": request_count,
                "limit": rate_limit,
                "window_seconds": window_size,
            }

        return None

    def _calculate_severity(self, risk_score: float) -> str:
        """Calculate severity level based on risk score"""
        if risk_score >= 0.8:
            return "critical"
        elif risk_score >= 0.6:
            return "high"
        elif risk_score >= 0.3:
            return "medium"
        else:
            return "low"

    async def _log_security_event(
        self,
        event_type: str,
        severity: str,
        source_ip: str,
        user_agent: str,
        endpoint: str,
        description: str,
        metadata: Dict[str, Any],
    ):
        """Log security event"""
        event = SecurityEvent(
            id=hashlib.sha256(
                f"{time.time()}{source_ip}{event_type}".encode()
            ).hexdigest()[:16],
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            severity=severity,
            source_ip=source_ip,
            user_agent=user_agent,
            endpoint=endpoint,
            description=description,
            metadata=metadata,
        )

        self.security_events.append(event)

        # Store in database if available
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO security_events 
                        (id, timestamp, event_type, severity, source_ip, user_agent, 
                         endpoint, description, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                        event.id,
                        event.timestamp,
                        event.event_type,
                        event.severity,
                        event.source_ip,
                        event.user_agent,
                        event.endpoint,
                        event.description,
                        json.dumps(event.metadata),
                    )
            except Exception as e:
                logger.error(f"Failed to store security event in database: {e}")

        # Log to application logger
        logger.warning(f"Security event: {event.event_type} - {event.description}")

        # Update metrics
        SECURITY_EVENTS.labels(event_type=event_type, severity=severity).inc()

    async def _monitor_threats(self):
        """Background task to monitor for ongoing threats"""
        while self.running:
            try:
                # Update active threat count
                ACTIVE_THREATS.set(len(self.active_threats))

                # Analyze recent events for patterns
                await self._analyze_threat_patterns()

                # Check for coordinated attacks
                await self._detect_coordinated_attacks()

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Threat monitoring error: {e}")
                await asyncio.sleep(60)

    async def _monitor_rate_limits(self):
        """Background task to monitor rate limiting"""
        while self.running:
            try:
                current_time = time.time()

                # Clean up old rate limit data
                for ip in list(self.request_counts.keys()):
                    while (
                        self.request_counts[ip]
                        and self.request_counts[ip][0] < current_time - 3600
                    ):  # 1 hour
                        self.request_counts[ip].popleft()

                    # Remove empty entries
                    if not self.request_counts[ip]:
                        del self.request_counts[ip]

                # Clean up blocked IPs after cooldown period
                blocked_ips_to_remove = []
                for ip in self.blocked_ips:
                    if (
                        not self.request_counts.get(ip)
                        or len(self.request_counts[ip]) == 0
                    ):
                        blocked_ips_to_remove.append(ip)

                for ip in blocked_ips_to_remove:
                    self.blocked_ips.discard(ip)

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Rate limit monitoring error: {e}")
                await asyncio.sleep(60)

    async def _monitor_api_keys(self):
        """Background task to monitor API key usage patterns"""
        while self.running:
            try:
                time.time()

                # Reset failed validation counters after cooldown
                for ip in list(self.failed_validations.keys()):
                    if self.failed_validations[ip] > 0:
                        # Decay failed validation count over time
                        self.failed_validations[ip] = max(
                            0, self.failed_validations[ip] - 1
                        )

                        if self.failed_validations[ip] == 0:
                            del self.failed_validations[ip]

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"API key monitoring error: {e}")
                await asyncio.sleep(60)

    async def _cleanup_old_events(self):
        """Background task to clean up old security events"""
        while self.running:
            try:
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

                # Clean up in-memory events
                while (
                    self.security_events
                    and self.security_events[0].timestamp < cutoff_time
                ):
                    self.security_events.popleft()

                # Clean up database events if configured
                if self.db_pool:
                    try:
                        async with self.db_pool.acquire() as conn:
                            retention_days = (
                                self.config.get("data_management", {})
                                .get("retention", {})
                                .get("audit_logs", "7y")
                            )
                            if retention_days.endswith("d"):
                                days = int(retention_days[:-1])
                                cutoff = datetime.now(timezone.utc) - timedelta(
                                    days=days
                                )

                                deleted_count = await conn.fetchval(
                                    """
                                    DELETE FROM security_events 
                                    WHERE timestamp < $1
                                    RETURNING COUNT(*)
                                """,
                                    cutoff,
                                )

                                if deleted_count > 0:
                                    logger.info(
                                        f"Cleaned up {deleted_count} old security events"
                                    )
                    except Exception as e:
                        logger.error(f"Database cleanup error: {e}")

                await asyncio.sleep(3600)  # Check every hour

            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(3600)

    async def _generate_reports(self):
        """Background task to generate security reports"""
        while self.running:
            try:
                await self._generate_hourly_report()
                await asyncio.sleep(3600)  # Generate every hour

            except Exception as e:
                logger.error(f"Report generation error: {e}")
                await asyncio.sleep(3600)

    async def _analyze_threat_patterns(self):
        """Analyze recent events for threat patterns"""
        try:
            recent_events = [
                event
                for event in self.security_events
                if event.timestamp > datetime.now(timezone.utc) - timedelta(minutes=15)
            ]

            if not recent_events:
                return

            # Group events by source IP
            ip_events = defaultdict(list)
            for event in recent_events:
                ip_events[event.source_ip].append(event)

            # Look for IPs with multiple high-severity events
            for ip, events in ip_events.items():
                high_severity_count = sum(
                    1 for e in events if e.severity in ["high", "critical"]
                )

                if high_severity_count >= 3:
                    # Mark as active threat
                    self.active_threats[ip] = ThreatIntelligence(
                        ip_address=ip,
                        threat_type="coordinated_attack",
                        confidence_score=0.8,
                        first_seen=min(e.timestamp for e in events),
                        last_seen=max(e.timestamp for e in events),
                        indicators=[e.event_type for e in events],
                    )

                    await self._log_security_event(
                        event_type="threat_pattern_detected",
                        severity="critical",
                        source_ip=ip,
                        user_agent="",
                        endpoint="",
                        description=f"Coordinated attack detected from {ip}",
                        metadata={
                            "event_count": len(events),
                            "high_severity_count": high_severity_count,
                        },
                    )

        except Exception as e:
            logger.error(f"Threat pattern analysis error: {e}")

    async def _detect_coordinated_attacks(self):
        """Detect coordinated attacks across multiple IPs"""
        try:
            recent_events = [
                event
                for event in self.security_events
                if event.timestamp > datetime.now(timezone.utc) - timedelta(minutes=30)
            ]

            if len(recent_events) < 10:  # Need sufficient events for analysis
                return

            # Group by event type and time window
            time_windows = defaultdict(lambda: defaultdict(set))

            for event in recent_events:
                window = event.timestamp.replace(
                    minute=event.timestamp.minute // 10 * 10, second=0, microsecond=0
                )
                time_windows[window][event.event_type].add(event.source_ip)

            # Look for coordinated patterns
            for window, event_types in time_windows.items():
                for event_type, ips in event_types.items():
                    if len(ips) >= 5:  # 5+ different IPs with same event type
                        await self._log_security_event(
                            event_type="coordinated_attack_detected",
                            severity="critical",
                            source_ip=",".join(list(ips)[:5]),
                            user_agent="",
                            endpoint="",
                            description=f"Coordinated {event_type} attack detected",
                            metadata={
                                "ip_count": len(ips),
                                "time_window": window.isoformat(),
                            },
                        )

        except Exception as e:
            logger.error(f"Coordinated attack detection error: {e}")

    async def _generate_hourly_report(self):
        """Generate hourly security report"""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=1)

            # Get events from the last hour
            hourly_events = [
                event
                for event in self.security_events
                if start_time <= event.timestamp <= end_time
            ]

            if not hourly_events:
                return

            # Generate report
            report = {
                "timestamp": end_time.isoformat(),
                "period": f"{start_time.isoformat()} to {end_time.isoformat()}",
                "summary": {
                    "total_events": len(hourly_events),
                    "unique_ips": len(set(e.source_ip for e in hourly_events)),
                    "severity_breakdown": defaultdict(int),
                    "event_type_breakdown": defaultdict(int),
                    "top_source_ips": [],
                    "active_threats": len(self.active_threats),
                    "blocked_ips": len(self.blocked_ips),
                },
                "details": {
                    "critical_events": [],
                    "new_threats": [],
                    "recommendations": [],
                },
            }

            # Calculate summary statistics
            for event in hourly_events:
                report["summary"]["severity_breakdown"][event.severity] += 1
                report["summary"]["event_type_breakdown"][event.event_type] += 1

            # Get top source IPs
            ip_counts = defaultdict(int)
            for event in hourly_events:
                ip_counts[event.source_ip] += 1

            report["summary"]["top_source_ips"] = [
                {"ip": ip, "event_count": count}
                for ip, count in sorted(
                    ip_counts.items(), key=lambda x: x[1], reverse=True
                )[:5]
            ]

            # Get critical events
            critical_events = [e for e in hourly_events if e.severity == "critical"]
            report["details"]["critical_events"] = [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "type": e.event_type,
                    "source_ip": e.source_ip,
                    "description": e.description,
                }
                for e in critical_events[:10]  # Top 10 critical events
            ]

            # Generate recommendations
            if report["summary"]["severity_breakdown"]["critical"] > 5:
                report["details"]["recommendations"].append(
                    "High number of critical events detected. Consider implementing stricter security measures."
                )

            if len(self.blocked_ips) > 20:
                report["details"]["recommendations"].append(
                    "Large number of blocked IPs. Review rate limiting configuration."
                )

            # Log report
            logger.info(f"Hourly security report: {json.dumps(report, indent=2)}")

            # Store report in database if available
            if self.db_pool:
                try:
                    async with self.db_pool.acquire() as conn:
                        await conn.execute(
                            """
                            INSERT INTO security_reports (timestamp, report_data)
                            VALUES ($1, $2)
                        """,
                            end_time,
                            json.dumps(report),
                        )
                except Exception as e:
                    logger.error(f"Failed to store security report: {e}")

        except Exception as e:
            logger.error(f"Report generation error: {e}")

    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status"""
        current_time = datetime.now(timezone.utc)
        recent_events = [
            event
            for event in self.security_events
            if event.timestamp > current_time - timedelta(minutes=30)
        ]

        return {
            "timestamp": current_time.isoformat(),
            "status": "operational" if len(recent_events) < 10 else "elevated",
            "recent_events_count": len(recent_events),
            "active_threats_count": len(self.active_threats),
            "blocked_ips_count": len(self.blocked_ips),
            "monitoring_status": "running" if self.running else "stopped",
            "last_report_time": current_time.replace(
                minute=0, second=0, microsecond=0
            ).isoformat(),
        }


async def main():
    """Main function for standalone security monitoring"""
    import yaml

    # Load configuration
    try:
        with open("09_Deployment_Package/dual_mode_config.yml", "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("Configuration file not found")
        return

    # Initialize security monitor
    monitor = SecurityMonitor(config)

    try:
        await monitor.initialize()
        logger.info("Security monitoring system started")

        # Start monitoring
        await monitor.start_monitoring()

    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Security monitoring failed: {e}")
    finally:
        await monitor.stop_monitoring()
        logger.info("Security monitoring system stopped")


if __name__ == "__main__":
    asyncio.run(main())
