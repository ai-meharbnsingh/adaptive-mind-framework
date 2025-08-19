# 03_Demo_Interface/context_validator.py

"""
Context Preservation Validator for Adaptive Mind Framework
Validates context preservation during failovers and provider switches.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import hashlib
import json

# Configure logger
logger = logging.getLogger(__name__)


class ContextElementType(Enum):
    """Types of context elements that can be validated"""
    CONVERSATION_HISTORY = "conversation_history"
    USER_PREFERENCES = "user_preferences"
    SESSION_VARIABLES = "session_variables"
    PROMPT_CONTEXT = "prompt_context"
    RESPONSE_FORMAT = "response_format"
    SAFETY_FILTERS = "safety_filters"
    MODEL_PARAMETERS = "model_parameters"
    BUSINESS_CONTEXT = "business_context"
    TEMPORAL_CONTEXT = "temporal_context"
    SEMANTIC_CONTEXT = "semantic_context"


class ValidationStatus(Enum):
    """Status of context validation"""
    PRESERVED = "preserved"
    PARTIALLY_PRESERVED = "partially_preserved"
    LOST = "lost"
    CORRUPTED = "corrupted"
    ENHANCED = "enhanced"


@dataclass
class ContextElement:
    """Individual context element for validation"""
    element_type: ContextElementType
    content: Any
    checksum: str
    timestamp: datetime
    priority: int  # 1-10, 10 being most critical
    is_required: bool


@dataclass
class ValidationResult:
    """Result of context element validation"""
    element_type: ContextElementType
    status: ValidationStatus
    preservation_score: float
    details: Dict[str, Any]
    recommendations: List[str]


@dataclass
class ContextSnapshot:
    """Complete context snapshot for validation"""
    snapshot_id: str
    timestamp: datetime
    elements: Dict[ContextElementType, ContextElement]
    session_id: str
    provider: str
    operation: str


class ContextValidator:
    """
    Advanced Context Preservation Validator for the Adaptive Mind Framework.

    Provides comprehensive validation of context preservation during:
    - Provider failovers
    - Model switches
    - Error recovery
    - Load balancing
    - Cost optimization switches
    """

    def __init__(self):
        """Initialize context validator"""
        self.logger = logger
        self.validation_history: List[Dict[str, Any]] = []
        self.context_snapshots: Dict[str, ContextSnapshot] = {}

        # Validation thresholds
        self.preservation_thresholds = {
            "excellent": 95.0,
            "good": 85.0,
            "acceptable": 75.0,
            "poor": 60.0
        }

        # Element priorities (1-10 scale)
        self.element_priorities = {
            ContextElementType.CONVERSATION_HISTORY: 10,
            ContextElementType.USER_PREFERENCES: 8,
            ContextElementType.SESSION_VARIABLES: 7,
            ContextElementType.PROMPT_CONTEXT: 9,
            ContextElementType.RESPONSE_FORMAT: 6,
            ContextElementType.SAFETY_FILTERS: 8,
            ContextElementType.MODEL_PARAMETERS: 5,
            ContextElementType.BUSINESS_CONTEXT: 7,
            ContextElementType.TEMPORAL_CONTEXT: 6,
            ContextElementType.SEMANTIC_CONTEXT: 8
        }

        # Required elements (cannot be lost)
        self.required_elements = {
            ContextElementType.CONVERSATION_HISTORY,
            ContextElementType.PROMPT_CONTEXT,
            ContextElementType.SAFETY_FILTERS
        }

    async def create_context_snapshot(self, session_id: str, provider: str,
                                      operation: str, context_data: Dict[str, Any]) -> str:
        """
        Create a context snapshot for validation.

        Args:
            session_id: Session identifier
            provider: Current provider
            operation: Operation being performed
            context_data: Current context data

        Returns:
            Snapshot ID for later validation
        """
        try:
            snapshot_id = str(uuid.uuid4())
            timestamp = datetime.now(timezone.utc)

            # Create context elements from provided data
            elements = {}

            for element_type in ContextElementType:
                element_data = context_data.get(element_type.value, {})

                if element_data or element_type in self.required_elements:
                    # Create checksum for integrity validation
                    content_str = json.dumps(element_data, sort_keys=True, default=str)
                    checksum = hashlib.sha256(content_str.encode()).hexdigest()

                    element = ContextElement(
                        element_type=element_type,
                        content=element_data,
                        checksum=checksum,
                        timestamp=timestamp,
                        priority=self.element_priorities.get(element_type, 5),
                        is_required=element_type in self.required_elements
                    )

                    elements[element_type] = element

            # Create snapshot
            snapshot = ContextSnapshot(
                snapshot_id=snapshot_id,
                timestamp=timestamp,
                elements=elements,
                session_id=session_id,
                provider=provider,
                operation=operation
            )

            self.context_snapshots[snapshot_id] = snapshot

            self.logger.info(f"📸 Context snapshot created: {snapshot_id} ({len(elements)} elements)")
            return snapshot_id

        except Exception as e:
            self.logger.error(f"❌ Failed to create context snapshot: {e}")
            return str(uuid.uuid4())  # Return dummy ID to prevent crashes

    async def validate_context_preservation(self, before_snapshot_id: str,
                                            after_context_data: Dict[str, Any],
                                            operation_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate context preservation between snapshots.

        Args:
            before_snapshot_id: Snapshot ID before operation
            after_context_data: Context data after operation
            operation_details: Details about the operation performed

        Returns:
            Comprehensive validation results
        """
        validation_start_time = datetime.now(timezone.utc)

        try:
            # Get before snapshot
            before_snapshot = self.context_snapshots.get(before_snapshot_id)
            if not before_snapshot:
                return await self._generate_fallback_validation_result(
                    "Snapshot not found", before_snapshot_id)

            # Create after snapshot for comparison
            after_snapshot_id = await self.create_context_snapshot(
                before_snapshot.session_id,
                operation_details.get("target_provider", "unknown") if operation_details else "unknown",
                "post_validation",
                after_context_data
            )

            after_snapshot = self.context_snapshots[after_snapshot_id]

            # Perform element-by-element validation
            validation_results = []
            total_score = 0.0
            weighted_score = 0.0
            total_weight = 0

            for element_type, before_element in before_snapshot.elements.items():
                after_element = after_snapshot.elements.get(element_type)

                result = await self._validate_element(before_element, after_element)
                validation_results.append(result)

                # Calculate weighted scores
                weight = before_element.priority
                total_weight += weight
                weighted_score += result.preservation_score * weight
                total_score += result.preservation_score

            # Calculate overall preservation metrics
            if validation_results:
                average_score = total_score / len(validation_results)
                weighted_average = weighted_score / max(total_weight, 1)
            else:
                average_score = weighted_average = 0.0

            # Determine overall status
            overall_status = self._determine_overall_status(weighted_average, validation_results)

            # Generate preservation analysis
            preservation_analysis = self._analyze_preservation_patterns(validation_results)

            # Calculate business impact
            business_impact = self._calculate_business_impact(validation_results, operation_details)

            # Generate recommendations
            recommendations = self._generate_improvement_recommendations(validation_results)

            # Prepare comprehensive validation report
            validation_report = {
                "validation_id": str(uuid.uuid4()),
                "session_id": before_snapshot.session_id,
                "validation_timestamp": validation_start_time.isoformat(),
                "operation_details": operation_details or {},

                # Overall Results
                "overall_status": overall_status.value,
                "preservation_score": round(weighted_average, 2),
                "average_score": round(average_score, 2),
                "preservation_grade": self._calculate_preservation_grade(weighted_average),

                # Snapshot Information
                "before_snapshot": {
                    "id": before_snapshot_id,
                    "timestamp": before_snapshot.timestamp.isoformat(),
                    "provider": before_snapshot.provider,
                    "element_count": len(before_snapshot.elements)
                },
                "after_snapshot": {
                    "id": after_snapshot_id,
                    "timestamp": after_snapshot.timestamp.isoformat(),
                    "provider": getattr(after_snapshot, 'provider', 'unknown'),
                    "element_count": len(after_snapshot.elements)
                },

                # Detailed Element Results
                "element_validation_results": [
                    {
                        "element_type": result.element_type.value,
                        "status": result.status.value,
                        "preservation_score": result.preservation_score,
                        "priority": self.element_priorities.get(result.element_type, 5),
                        "is_required": result.element_type in self.required_elements,
                        "details": result.details,
                        "recommendations": result.recommendations
                    }
                    for result in validation_results
                ],

                # Analysis and Insights
                "preservation_analysis": preservation_analysis,
                "business_impact": business_impact,
                "improvement_recommendations": recommendations,

                # Performance Metrics
                "validation_metrics": {
                    "total_elements_validated": len(validation_results),
                    "preserved_elements": len(
                        [r for r in validation_results if r.status == ValidationStatus.PRESERVED]),
                    "partially_preserved_elements": len(
                        [r for r in validation_results if r.status == ValidationStatus.PARTIALLY_PRESERVED]),
                    "lost_elements": len([r for r in validation_results if r.status == ValidationStatus.LOST]),
                    "corrupted_elements": len(
                        [r for r in validation_results if r.status == ValidationStatus.CORRUPTED]),
                    "enhanced_elements": len([r for r in validation_results if r.status == ValidationStatus.ENHANCED]),
                    "validation_duration_ms": (datetime.now(
                        timezone.utc) - validation_start_time).total_seconds() * 1000
                }
            }

            # Store validation in history
            self.validation_history.append(validation_report)

            # Keep only last 100 validations for performance
            if len(self.validation_history) > 100:
                self.validation_history = self.validation_history[-100:]

            self.logger.info(f"✅ Context validation completed: {weighted_average:.1f}% preservation")
            return validation_report

        except Exception as e:
            self.logger.error(f"❌ Context validation failed: {e}", exc_info=True)
            return await self._generate_fallback_validation_result(str(e), before_snapshot_id)

    async def _validate_element(self, before_element: ContextElement,
                                after_element: Optional[ContextElement]) -> ValidationResult:
        """Validate individual context element preservation"""
        try:
            if not after_element:
                # Element completely lost
                return ValidationResult(
                    element_type=before_element.element_type,
                    status=ValidationStatus.LOST,
                    preservation_score=0.0,
                    details={
                        "issue": "Element completely missing after operation",
                        "before_checksum": before_element.checksum,
                        "after_checksum": None,
                        "content_size_before": len(str(before_element.content)),
                        "content_size_after": 0
                    },
                    recommendations=[
                        "Implement element preservation safeguards",
                        "Add element backup/restore mechanism",
                        "Review failover context transfer logic"
                    ]
                )

            # Compare checksums for exact preservation
            if before_element.checksum == after_element.checksum:
                return ValidationResult(
                    element_type=before_element.element_type,
                    status=ValidationStatus.PRESERVED,
                    preservation_score=100.0,
                    details={
                        "preservation_type": "exact_match",
                        "checksum_match": True,
                        "content_size_before": len(str(before_element.content)),
                        "content_size_after": len(str(after_element.content)),
                        "size_change": 0
                    },
                    recommendations=[]
                )

            # Perform content-based similarity analysis
            similarity_score = await self._calculate_content_similarity(
                before_element.content, after_element.content)

            # Determine status based on similarity
            if similarity_score >= 95.0:
                status = ValidationStatus.PRESERVED
                recommendations = []
            elif similarity_score >= 75.0:
                status = ValidationStatus.PARTIALLY_PRESERVED
                recommendations = [
                    "Review content transfer mechanism for higher fidelity",
                    "Implement content validation checksums"
                ]
            elif similarity_score >= 50.0:
                status = ValidationStatus.CORRUPTED
                recommendations = [
                    "Critical: Implement robust content preservation",
                    "Add integrity validation during transfers",
                    "Review serialization/deserialization logic"
                ]
            else:
                status = ValidationStatus.LOST
                recommendations = [
                    "Urgent: Complete content preservation failure",
                    "Implement backup/restore mechanisms",
                    "Review entire context transfer pipeline"
                ]

            # Check for content enhancement
            if similarity_score > 100.0:  # Enhanced content
                status = ValidationStatus.ENHANCED
                recommendations = [
                    "Content was enhanced during transfer",
                    "Validate that enhancements are beneficial"
                ]

            return ValidationResult(
                element_type=before_element.element_type,
                status=status,
                preservation_score=min(similarity_score, 100.0),
                details={
                    "preservation_type": "content_analysis",
                    "similarity_score": similarity_score,
                    "checksum_match": False,
                    "before_checksum": before_element.checksum,
                    "after_checksum": after_element.checksum,
                    "content_size_before": len(str(before_element.content)),
                    "content_size_after": len(str(after_element.content)),
                    "size_change": len(str(after_element.content)) - len(str(before_element.content))
                },
                recommendations=recommendations
            )

        except Exception as e:
            self.logger.error(f"Element validation failed for {before_element.element_type}: {e}")
            return ValidationResult(
                element_type=before_element.element_type,
                status=ValidationStatus.CORRUPTED,
                preservation_score=0.0,
                details={"error": str(e)},
                recommendations=["Fix validation logic error"]
            )

    async def _calculate_content_similarity(self, before_content: Any, after_content: Any) -> float:
        """Calculate similarity between content objects"""
        try:
            # Convert to strings for comparison
            before_str = json.dumps(before_content, sort_keys=True, default=str)
            after_str = json.dumps(after_content, sort_keys=True, default=str)

            if before_str == after_str:
                return 100.0

            # Simple character-based similarity (in production would use more sophisticated algorithms)
            if not before_str:
                return 100.0 if not after_str else 0.0

            # Calculate Jaccard similarity on character level
            before_chars = set(before_str)
            after_chars = set(after_str)

            intersection = len(before_chars.intersection(after_chars))
            union = len(before_chars.union(after_chars))

            jaccard_similarity = (intersection / union) * 100 if union > 0 else 100.0

            # Calculate length similarity
            len_before = len(before_str)
            len_after = len(after_str)
            max_len = max(len_before, len_after)
            min_len = min(len_before, len_after)

            length_similarity = (min_len / max_len) * 100 if max_len > 0 else 100.0

            # Weighted average of similarities
            overall_similarity = (jaccard_similarity * 0.7) + (length_similarity * 0.3)

            return round(overall_similarity, 2)

        except Exception as e:
            self.logger.error(f"Content similarity calculation failed: {e}")
            return 50.0  # Default to moderate similarity on error

    def _determine_overall_status(self, weighted_average: float,
                                  results: List[ValidationResult]) -> ValidationStatus:
        """Determine overall validation status"""
        # Check for any lost required elements
        lost_required = any(
            result.status == ValidationStatus.LOST and result.element_type in self.required_elements
            for result in results
        )

        if lost_required:
            return ValidationStatus.LOST

        # Check for corruption in required elements
        corrupted_required = any(
            result.status == ValidationStatus.CORRUPTED and result.element_type in self.required_elements
            for result in results
        )

        if corrupted_required:
            return ValidationStatus.CORRUPTED

        # Determine based on weighted average
        if weighted_average >= self.preservation_thresholds["excellent"]:
            return ValidationStatus.PRESERVED
        elif weighted_average >= self.preservation_thresholds["acceptable"]:
            return ValidationStatus.PARTIALLY_PRESERVED
        else:
            return ValidationStatus.LOST

    def _analyze_preservation_patterns(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Analyze patterns in preservation results"""
        # Group results by status
        status_groups = {}
        for result in results:
            status = result.status.value
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(result)

        # Analyze by priority
        high_priority_issues = [
            result for result in results
            if result.preservation_score < 90 and self.element_priorities.get(result.element_type, 5) >= 8
        ]

        # Identify most problematic elements
        worst_performing = sorted(results, key=lambda x: x.preservation_score)[:3]

        return {
            "status_distribution": {status: len(results) for status, results in status_groups.items()},
            "high_priority_issues_count": len(high_priority_issues),
            "worst_performing_elements": [
                {
                    "element_type": result.element_type.value,
                    "score": result.preservation_score,
                    "status": result.status.value
                }
                for result in worst_performing if result.preservation_score < 100
            ],
            "preservation_trend": self._calculate_preservation_trend(),
            "common_failure_patterns": self._identify_failure_patterns(results)
        }

    def _calculate_business_impact(self, results: List[ValidationResult],
                                   operation_details: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate business impact of context preservation results"""
        # Critical element preservation
        critical_elements_preserved = sum(
            1 for result in results
            if result.element_type in self.required_elements and result.preservation_score >= 90
        )

        total_critical_elements = len([
            result for result in results if result.element_type in self.required_elements
        ])

        # Calculate impact scores
        user_experience_impact = self._calculate_ux_impact(results)
        operational_impact = self._calculate_operational_impact(results)
        compliance_impact = self._calculate_compliance_impact(results)

        # Overall business impact
        if critical_elements_preserved == total_critical_elements and user_experience_impact == "minimal":
            overall_impact = "minimal"
        elif user_experience_impact in ["low", "minimal"] and operational_impact == "low":
            overall_impact = "low"
        elif user_experience_impact == "moderate" or operational_impact == "moderate":
            overall_impact = "moderate"
        else:
            overall_impact = "high"

        return {
            "overall_impact": overall_impact,
            "user_experience_impact": user_experience_impact,
            "operational_impact": operational_impact,
            "compliance_impact": compliance_impact,
            "critical_elements_preserved": f"{critical_elements_preserved}/{total_critical_elements}",
            "business_continuity_score": self._calculate_continuity_score(results),
            "recovery_recommendation": self._get_recovery_recommendation(overall_impact)
        }

    def _generate_improvement_recommendations(self, results: List[ValidationResult]) -> List[Dict[str, Any]]:
        """Generate actionable improvement recommendations"""
        recommendations = []

        # Analyze common issues
        low_score_elements = [r for r in results if r.preservation_score < 75]
        lost_elements = [r for r in results if r.status == ValidationStatus.LOST]
        corrupted_elements = [r for r in results if r.status == ValidationStatus.CORRUPTED]

        # Generate specific recommendations
        if lost_elements:
            recommendations.append({
                "priority": "Critical",
                "category": "Element Loss Prevention",
                "title": "Implement Element Backup/Restore",
                "description": f"{len(lost_elements)} elements were completely lost during operation",
                "action_items": [
                    "Add pre-operation context backup",
                    "Implement element-by-element validation",
                    "Create automatic restore mechanisms"
                ],
                "estimated_effort": "High",
                "business_value": "Critical system reliability"
            })

        if corrupted_elements:
            recommendations.append({
                "priority": "High",
                "category": "Data Integrity",
                "title": "Enhance Content Integrity Validation",
                "description": f"{len(corrupted_elements)} elements were corrupted during transfer",
                "action_items": [
                    "Implement content checksums",
                    "Add serialization validation",
                    "Create integrity monitoring"
                ],
                "estimated_effort": "Medium",
                "business_value": "Data accuracy and reliability"
            })

        if low_score_elements:
            recommendations.append({
                "priority": "Medium",
                "category": "Preservation Optimization",
                "title": "Optimize Context Transfer Mechanisms",
                "description": f"{len(low_score_elements)} elements have preservation scores below 75%",
                "action_items": [
                    "Review transfer algorithms",
                    "Optimize serialization methods",
                    "Implement smart preservation priorities"
                ],
                "estimated_effort": "Medium",
                "business_value": "Improved user experience"
            })

        # Add general improvements if preservation is already good
        if not recommendations:
            recommendations.append({
                "priority": "Low",
                "category": "Continuous Improvement",
                "title": "Enhance Monitoring and Analytics",
                "description": "Context preservation is performing well - focus on monitoring",
                "action_items": [
                    "Add predictive preservation analytics",
                    "Implement real-time monitoring dashboards",
                    "Create automated optimization"
                ],
                "estimated_effort": "Low",
                "business_value": "Proactive optimization"
            })

        return recommendations

    def _calculate_preservation_grade(self, score: float) -> str:
        """Calculate letter grade for preservation score"""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 80:
            return "B"
        elif score >= 75:
            return "C+"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _calculate_preservation_trend(self) -> str:
        """Calculate preservation trend from recent validations"""
        if len(self.validation_history) < 2:
            return "insufficient_data"

        recent_scores = [
            validation.get("preservation_score", 0)
            for validation in self.validation_history[-5:]
        ]

        if len(recent_scores) < 2:
            return "stable"

        # Simple trend calculation
        trend = recent_scores[-1] - recent_scores[0]

        if trend > 5:
            return "improving"
        elif trend < -5:
            return "declining"
        else:
            return "stable"

    def _identify_failure_patterns(self, results: List[ValidationResult]) -> List[str]:
        """Identify common failure patterns"""
        patterns = []

        # Check for systematic issues
        lost_count = len([r for r in results if r.status == ValidationStatus.LOST])
        corrupted_count = len([r for r in results if r.status == ValidationStatus.CORRUPTED])

        if lost_count > len(results) * 0.3:
            patterns.append("high_element_loss_rate")

        if corrupted_count > len(results) * 0.2:
            patterns.append("content_corruption_pattern")

        # Check for specific element type issues
        conversation_issues = any(
            r.element_type == ContextElementType.CONVERSATION_HISTORY and r.preservation_score < 80
            for r in results
        )

        if conversation_issues:
            patterns.append("conversation_preservation_issues")

        return patterns

    def _calculate_ux_impact(self, results: List[ValidationResult]) -> str:
        """Calculate user experience impact"""
        # Check conversation history preservation
        conv_result = next(
            (r for r in results if r.element_type == ContextElementType.CONVERSATION_HISTORY),
            None
        )

        if conv_result and conv_result.preservation_score < 70:
            return "high"
        elif conv_result and conv_result.preservation_score < 90:
            return "moderate"
        else:
            return "minimal"

    def _calculate_operational_impact(self, results: List[ValidationResult]) -> str:
        """Calculate operational impact"""
        required_preserved = sum(
            1 for r in results
            if r.element_type in self.required_elements and r.preservation_score >= 90
        )

        total_required = len([r for r in results if r.element_type in self.required_elements])

        if required_preserved == total_required:
            return "low"
        elif required_preserved >= total_required * 0.8:
            return "moderate"
        else:
            return "high"

    def _calculate_compliance_impact(self, results: List[ValidationResult]) -> str:
        """Calculate compliance impact"""
        # Check safety and security elements
        safety_result = next(
            (r for r in results if r.element_type == ContextElementType.SAFETY_FILTERS),
            None
        )

        if safety_result and safety_result.preservation_score < 95:
            return "high"
        else:
            return "low"

    def _calculate_continuity_score(self, results: List[ValidationResult]) -> float:
        """Calculate business continuity score"""
        if not results:
            return 0.0

        # Weight by element priority
        weighted_sum = sum(
            result.preservation_score * self.element_priorities.get(result.element_type, 5)
            for result in results
        )

        total_weight = sum(
            self.element_priorities.get(result.element_type, 5)
            for result in results
        )

        return round(weighted_sum / max(total_weight, 1), 1)

    def _get_recovery_recommendation(self, impact: str) -> str:
        """Get recovery recommendation based on impact"""
        recommendations = {
            "minimal": "Continue normal operations - monitor for trends",
            "low": "Schedule preventive maintenance during next maintenance window",
            "moderate": "Plan context preservation improvements in next sprint",
            "high": "Immediate action required - implement preservation safeguards"
        }

        return recommendations.get(impact, "Assess and implement appropriate measures")

    async def _generate_fallback_validation_result(self, error: str,
                                                   snapshot_id: str) -> Dict[str, Any]:
        """Generate fallback validation result when validation fails"""
        return {
            "validation_id": str(uuid.uuid4()),
            "session_id": "unknown",
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": "corrupted",
            "preservation_score": 0.0,
            "preservation_grade": "F",
            "error": error,
            "before_snapshot": {"id": snapshot_id, "status": "error"},
            "validation_metrics": {
                "total_elements_validated": 0,
                "validation_error": True
            },
            "business_impact": {
                "overall_impact": "unknown",
                "recovery_recommendation": "Investigate validation system error"
            }
        }

    async def get_validation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent validation history"""
        return self.validation_history[-limit:]

    async def get_preservation_analytics(self) -> Dict[str, Any]:
        """Get preservation analytics and trends"""
        if not self.validation_history:
            return {"status": "insufficient_data"}

        recent_validations = self.validation_history[-20:]

        # Calculate trends
        scores = [v.get("preservation_score", 0) for v in recent_validations]
        avg_score = sum(scores) / len(scores) if scores else 0

        # Status distribution
        statuses = [v.get("overall_status", "unknown") for v in recent_validations]
        status_counts = {}
        for status in statuses:
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "analytics_period": f"Last {len(recent_validations)} validations",
            "average_preservation_score": round(avg_score, 1),
            "preservation_trend": self._calculate_preservation_trend(),
            "status_distribution": status_counts,
            "total_validations": len(self.validation_history),
            "analytics_timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def validate_simple_context(self, before_context: Dict[str, Any],
                                      after_context: Dict[str, Any]) -> Dict[str, Any]:
        """Simple context validation for quick checks"""
        try:
            # Create temporary snapshot
            snapshot_id = await self.create_context_snapshot(
                "temp_session", "temp_provider", "simple_validation", before_context
            )

            # Validate preservation
            result = await self.validate_context_preservation(
                snapshot_id, after_context, {"operation": "simple_validation"}
            )

            return {
                "is_preserved": result["preservation_score"] >= 90.0,
                "preservation_score": result["preservation_score"],
                "preservation_grade": result["preservation_grade"],
                "summary": f"Context preservation: {result['preservation_score']:.1f}%"
            }

        except Exception as e:
            self.logger.error(f"Simple validation failed: {e}")
            return {
                "is_preserved": False,
                "preservation_score": 0.0,
                "preservation_grade": "F",
                "summary": f"Validation error: {str(e)}"
            }