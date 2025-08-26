# 07_Sales_Materials/cost_analysis.py
# Professional Cost Analysis Engine for Adaptive Mind Framework - Session 9
# Comprehensive cost modeling and analysis for enterprise sales

import pandas as pd
from datetime import datetime
from typing import Dict, Any
import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CostInputs:
    """Input parameters for cost analysis"""

    monthly_requests: int
    current_api_cost: float
    current_failure_rate: float  # Percentage
    downtime_cost_hour: float
    team_size: int
    avg_salary: float
    maintenance_time_percent: float
    industry: str
    analysis_years: int = 5
    discount_rate: float = 0.08


@dataclass
class CostResults:
    """Results of cost analysis"""

    current_annual_cost: float
    adaptive_mind_annual_cost: float
    annual_savings: float
    roi_percentage: float
    payback_months: float
    npv_5_years: float
    total_5_year_savings: float
    risk_adjusted_savings: float


class AdaptiveMindCostAnalyzer:
    """
    Professional cost analysis engine for Adaptive Mind Framework
    Provides comprehensive financial modeling for enterprise decision making
    """

    def __init__(self):
        self.industry_benchmarks = {
            "customer_service": {
                "api_cost_multiplier": 1.0,
                "failure_cost_multiplier": 1.2,
                "maintenance_complexity": 1.0,
                "reliability_requirement": 0.95,
                "performance_criticality": 0.8,
            },
            "fraud_detection": {
                "api_cost_multiplier": 1.8,
                "failure_cost_multiplier": 3.4,
                "maintenance_complexity": 1.5,
                "reliability_requirement": 0.99,
                "performance_criticality": 0.95,
            },
            "e_commerce": {
                "api_cost_multiplier": 0.7,
                "failure_cost_multiplier": 1.8,
                "maintenance_complexity": 1.2,
                "reliability_requirement": 0.98,
                "performance_criticality": 0.9,
            },
            "content_generation": {
                "api_cost_multiplier": 1.4,
                "failure_cost_multiplier": 0.8,
                "maintenance_complexity": 0.8,
                "reliability_requirement": 0.92,
                "performance_criticality": 0.7,
            },
            "data_analytics": {
                "api_cost_multiplier": 2.2,
                "failure_cost_multiplier": 2.0,
                "maintenance_complexity": 1.8,
                "reliability_requirement": 0.96,
                "performance_criticality": 0.85,
            },
        }

        self.adaptive_mind_performance = {
            "failure_rate": 0.008,  # 0.8%
            "performance_multiplier": 12.5,
            "maintenance_reduction": 0.75,  # 75% reduction
            "setup_time_weeks": 3,
            "reliability_score": 0.99,
            "cost_optimization": 0.15,  # 15% API cost reduction
        }

        self.competitor_benchmarks = {
            "langchain": {
                "failure_rate": 0.18,
                "maintenance_overhead": 1.0,
                "setup_complexity": 8.5,
                "licensing_cost": 35000,
                "support_cost": 42000,
            },
            "semantic_kernel": {
                "failure_rate": 0.22,
                "maintenance_overhead": 1.2,
                "setup_complexity": 9.2,
                "licensing_cost": 48000,
                "support_cost": 45000,
            },
            "azure_ai": {
                "failure_rate": 0.15,
                "maintenance_overhead": 0.9,
                "setup_complexity": 7.8,
                "licensing_cost": 42000,
                "support_cost": 38000,
            },
        }

        logger.info("✅ Adaptive Mind Cost Analyzer initialized")

    def analyze_costs(self, inputs: CostInputs) -> CostResults:
        """
        Perform comprehensive cost analysis
        """
        logger.info(f"🔍 Analyzing costs for {inputs.industry} industry scenario")

        # Calculate current state costs
        current_costs = self._calculate_current_costs(inputs)

        # Calculate Adaptive Mind costs
        adaptive_costs = self._calculate_adaptive_mind_costs(inputs)

        # Calculate financial metrics
        results = self._calculate_financial_metrics(
            current_costs, adaptive_costs, inputs
        )

        logger.info(
            f"✅ Cost analysis complete - Annual savings: ${results.annual_savings:,.0f}"
        )
        return results

    def _calculate_current_costs(self, inputs: CostInputs) -> Dict[str, float]:
        """Calculate current infrastructure costs"""

        # Get industry-specific multipliers
        industry_data = self.industry_benchmarks.get(
            inputs.industry, self.industry_benchmarks["customer_service"]
        )

        # API usage costs
        monthly_api_cost = inputs.monthly_requests * inputs.current_api_cost
        annual_api_cost = monthly_api_cost * 12

        # Failure and downtime costs
        failure_rate = inputs.current_failure_rate / 100
        monthly_failures = inputs.monthly_requests * failure_rate
        # Assume average failure causes 0.5 hour downtime
        monthly_downtime_hours = monthly_failures * 0.5 / 1000
        monthly_downtime_cost = monthly_downtime_hours * inputs.downtime_cost_hour
        annual_downtime_cost = monthly_downtime_cost * 12

        # Apply industry multiplier for failure impact
        annual_downtime_cost *= industry_data["failure_cost_multiplier"]

        # Maintenance costs
        annual_maintenance_cost = (
            inputs.team_size * inputs.avg_salary * inputs.maintenance_time_percent / 100
        )

        # Apply industry complexity multiplier
        annual_maintenance_cost *= industry_data["maintenance_complexity"]

        # Infrastructure and support costs
        base_infrastructure_cost = max(50000, inputs.monthly_requests * 0.001 * 12)
        annual_infrastructure_cost = base_infrastructure_cost

        # Support and licensing (current solution)
        annual_support_cost = max(25000, inputs.team_size * 5000)
        annual_licensing_cost = max(40000, inputs.monthly_requests * 0.002 * 12)

        total_annual_cost = (
            annual_api_cost
            + annual_downtime_cost
            + annual_maintenance_cost
            + annual_infrastructure_cost
            + annual_support_cost
            + annual_licensing_cost
        )

        return {
            "api_cost": annual_api_cost,
            "downtime_cost": annual_downtime_cost,
            "maintenance_cost": annual_maintenance_cost,
            "infrastructure_cost": annual_infrastructure_cost,
            "support_cost": annual_support_cost,
            "licensing_cost": annual_licensing_cost,
            "total": total_annual_cost,
        }

    def _calculate_adaptive_mind_costs(self, inputs: CostInputs) -> Dict[str, float]:
        """Calculate Adaptive Mind infrastructure costs"""

        # API costs with optimization
        optimized_api_cost = inputs.current_api_cost * (
            1 - self.adaptive_mind_performance["cost_optimization"]
        )
        annual_api_cost = inputs.monthly_requests * optimized_api_cost * 12

        # Dramatically reduced downtime costs
        adaptive_failure_rate = self.adaptive_mind_performance["failure_rate"]
        monthly_failures = inputs.monthly_requests * adaptive_failure_rate
        monthly_downtime_hours = monthly_failures * 0.1 / 1000  # Much faster recovery
        monthly_downtime_cost = monthly_downtime_hours * inputs.downtime_cost_hour
        annual_downtime_cost = monthly_downtime_cost * 12

        # Reduced maintenance costs
        maintenance_reduction = self.adaptive_mind_performance["maintenance_reduction"]
        annual_maintenance_cost = (
            inputs.team_size
            * inputs.avg_salary
            * inputs.maintenance_time_percent
            / 100
            * (1 - maintenance_reduction)
        )

        # Simplified infrastructure
        annual_infrastructure_cost = max(30000, inputs.monthly_requests * 0.0006 * 12)

        # Adaptive Mind licensing
        base_license = max(45000, inputs.monthly_requests * 0.0015 * 12)
        # Volume discounts for larger deployments
        if inputs.monthly_requests > 500000:
            base_license *= 0.8
        elif inputs.monthly_requests > 200000:
            base_license *= 0.9

        annual_licensing_cost = base_license

        # Reduced support costs (self-managing system)
        annual_support_cost = max(12000, inputs.team_size * 2000)

        total_annual_cost = (
            annual_api_cost
            + annual_downtime_cost
            + annual_maintenance_cost
            + annual_infrastructure_cost
            + annual_support_cost
            + annual_licensing_cost
        )

        return {
            "api_cost": annual_api_cost,
            "downtime_cost": annual_downtime_cost,
            "maintenance_cost": annual_maintenance_cost,
            "infrastructure_cost": annual_infrastructure_cost,
            "support_cost": annual_support_cost,
            "licensing_cost": annual_licensing_cost,
            "total": total_annual_cost,
        }

    def _calculate_financial_metrics(
        self,
        current_costs: Dict[str, float],
        adaptive_costs: Dict[str, float],
        inputs: CostInputs,
    ) -> CostResults:
        """Calculate comprehensive financial metrics"""

        annual_savings = current_costs["total"] - adaptive_costs["total"]

        # ROI calculation
        investment = adaptive_costs["total"]  # First year cost as investment
        roi_percentage = (annual_savings / investment) * 100 if investment > 0 else 0

        # Payback period
        payback_months = (
            (investment / (annual_savings / 12)) if annual_savings > 0 else float("inf")
        )

        # NPV calculation
        npv_5_years = self._calculate_npv(
            annual_savings, inputs.analysis_years, inputs.discount_rate
        )

        # Total 5-year savings
        total_5_year_savings = annual_savings * inputs.analysis_years

        # Risk-adjusted savings (conservative estimate)
        risk_adjustment = 0.85  # 15% risk adjustment
        risk_adjusted_savings = annual_savings * risk_adjustment

        return CostResults(
            current_annual_cost=current_costs["total"],
            adaptive_mind_annual_cost=adaptive_costs["total"],
            annual_savings=annual_savings,
            roi_percentage=roi_percentage,
            payback_months=payback_months,
            npv_5_years=npv_5_years,
            total_5_year_savings=total_5_year_savings,
            risk_adjusted_savings=risk_adjusted_savings,
        )

    def _calculate_npv(
        self, annual_cash_flow: float, years: int, discount_rate: float
    ) -> float:
        """Calculate Net Present Value"""
        npv = 0
        for year in range(1, years + 1):
            npv += annual_cash_flow / (1 + discount_rate) ** year
        return npv

    def compare_with_competitors(
        self, inputs: CostInputs
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare costs with major competitors
        """
        logger.info("🔍 Comparing with competitor solutions")

        comparisons = {}

        for competitor, benchmark in self.competitor_benchmarks.items():
            # Calculate competitor costs
            competitor_costs = self._calculate_competitor_costs(inputs, benchmark)
            adaptive_costs = self._calculate_adaptive_mind_costs(inputs)

            savings = competitor_costs["total"] - adaptive_costs["total"]
            roi = (
                (savings / adaptive_costs["total"]) * 100
                if adaptive_costs["total"] > 0
                else 0
            )

            comparisons[competitor] = {
                "competitor_annual_cost": competitor_costs["total"],
                "adaptive_mind_annual_cost": adaptive_costs["total"],
                "annual_savings": savings,
                "roi_percentage": roi,
                "payback_months": (
                    (adaptive_costs["total"] / (savings / 12))
                    if savings > 0
                    else float("inf")
                ),
                "reliability_advantage": (
                    (1 - self.adaptive_mind_performance["failure_rate"])
                    - (1 - benchmark["failure_rate"])
                )
                * 100,
                "maintenance_reduction": (
                    1
                    - (1 - self.adaptive_mind_performance["maintenance_reduction"])
                    / benchmark["maintenance_overhead"]
                )
                * 100,
            }

        return comparisons

    def _calculate_competitor_costs(
        self, inputs: CostInputs, benchmark: Dict
    ) -> Dict[str, float]:
        """Calculate costs for competitor solution"""

        # API costs (similar to current)
        annual_api_cost = inputs.monthly_requests * inputs.current_api_cost * 12

        # Higher failure costs
        failure_rate = benchmark["failure_rate"]
        monthly_failures = inputs.monthly_requests * failure_rate
        monthly_downtime_hours = monthly_failures * 0.8 / 1000  # Slower recovery
        annual_downtime_cost = monthly_downtime_hours * inputs.downtime_cost_hour * 12

        # Higher maintenance costs
        maintenance_overhead = benchmark["maintenance_overhead"]
        annual_maintenance_cost = (
            inputs.team_size
            * inputs.avg_salary
            * inputs.maintenance_time_percent
            / 100
            * maintenance_overhead
        )

        # Infrastructure costs
        annual_infrastructure_cost = max(60000, inputs.monthly_requests * 0.0012 * 12)

        # Competitor licensing and support
        annual_licensing_cost = benchmark["licensing_cost"]
        annual_support_cost = benchmark["support_cost"]

        total_annual_cost = (
            annual_api_cost
            + annual_downtime_cost
            + annual_maintenance_cost
            + annual_infrastructure_cost
            + annual_support_cost
            + annual_licensing_cost
        )

        return {
            "api_cost": annual_api_cost,
            "downtime_cost": annual_downtime_cost,
            "maintenance_cost": annual_maintenance_cost,
            "infrastructure_cost": annual_infrastructure_cost,
            "support_cost": annual_support_cost,
            "licensing_cost": annual_licensing_cost,
            "total": total_annual_cost,
        }

    def generate_scenario_analysis(
        self, base_inputs: CostInputs
    ) -> Dict[str, CostResults]:
        """
        Generate multiple scenario analyses (Conservative, Expected, Optimistic)
        """
        logger.info("📊 Generating scenario analysis")

        scenarios = {}

        # Conservative scenario (75% of expected benefits)
        conservative_inputs = CostInputs(
            monthly_requests=base_inputs.monthly_requests,
            current_api_cost=base_inputs.current_api_cost,
            current_failure_rate=base_inputs.current_failure_rate
            * 0.8,  # Less current problems
            downtime_cost_hour=base_inputs.downtime_cost_hour
            * 0.8,  # Lower downtime cost
            team_size=base_inputs.team_size,
            avg_salary=base_inputs.avg_salary,
            maintenance_time_percent=base_inputs.maintenance_time_percent * 0.8,
            industry=base_inputs.industry,
        )
        scenarios["conservative"] = self.analyze_costs(conservative_inputs)

        # Expected scenario (base case)
        scenarios["expected"] = self.analyze_costs(base_inputs)

        # Optimistic scenario (125% of expected benefits)
        optimistic_inputs = CostInputs(
            monthly_requests=base_inputs.monthly_requests * 1.2,  # Growth in usage
            current_api_cost=base_inputs.current_api_cost,
            current_failure_rate=base_inputs.current_failure_rate
            * 1.2,  # More current problems
            downtime_cost_hour=base_inputs.downtime_cost_hour
            * 1.2,  # Higher downtime cost
            team_size=base_inputs.team_size,
            avg_salary=base_inputs.avg_salary,
            maintenance_time_percent=base_inputs.maintenance_time_percent * 1.2,
            industry=base_inputs.industry,
        )
        scenarios["optimistic"] = self.analyze_costs(optimistic_inputs)

        return scenarios

    def calculate_total_cost_of_ownership(
        self, inputs: CostInputs, years: int = 5
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive Total Cost of Ownership analysis
        """
        logger.info(f"💰 Calculating {years}-year Total Cost of Ownership")

        # Year-by-year analysis
        tco_analysis = {
            "years": list(range(1, years + 1)),
            "current_solution": [],
            "adaptive_mind": [],
            "annual_savings": [],
            "cumulative_savings": [],
        }

        cumulative_savings = 0

        for year in range(1, years + 1):
            # Account for inflation and growth
            inflation_factor = 1.03 ** (year - 1)  # 3% annual inflation
            growth_factor = 1.1 ** (year - 1)  # 10% annual growth in usage

            # Adjust inputs for year
            adjusted_inputs = CostInputs(
                monthly_requests=int(inputs.monthly_requests * growth_factor),
                current_api_cost=inputs.current_api_cost * inflation_factor,
                current_failure_rate=inputs.current_failure_rate,
                downtime_cost_hour=inputs.downtime_cost_hour * inflation_factor,
                team_size=inputs.team_size
                + (year - 1) // 2,  # Team grows every 2 years
                avg_salary=inputs.avg_salary * inflation_factor,
                maintenance_time_percent=inputs.maintenance_time_percent,
                industry=inputs.industry,
            )

            # Calculate costs for this year
            current_costs = self._calculate_current_costs(adjusted_inputs)
            adaptive_costs = self._calculate_adaptive_mind_costs(adjusted_inputs)

            annual_savings = current_costs["total"] - adaptive_costs["total"]
            cumulative_savings += annual_savings

            tco_analysis["current_solution"].append(current_costs["total"])
            tco_analysis["adaptive_mind"].append(adaptive_costs["total"])
            tco_analysis["annual_savings"].append(annual_savings)
            tco_analysis["cumulative_savings"].append(cumulative_savings)

        # Summary metrics
        total_current_cost = sum(tco_analysis["current_solution"])
        total_adaptive_cost = sum(tco_analysis["adaptive_mind"])
        total_savings = total_current_cost - total_adaptive_cost

        tco_summary = {
            "analysis_period_years": years,
            "total_current_solution_cost": total_current_cost,
            "total_adaptive_mind_cost": total_adaptive_cost,
            "total_savings": total_savings,
            "average_annual_savings": total_savings / years,
            "total_roi_percentage": (total_savings / total_adaptive_cost) * 100,
            "break_even_month": self._calculate_break_even_point(tco_analysis),
            "detailed_analysis": tco_analysis,
        }

        return tco_summary

    def _calculate_break_even_point(self, tco_analysis: Dict) -> float:
        """Calculate when cumulative savings break even with investment"""
        for month, cumulative in enumerate(tco_analysis["cumulative_savings"]):
            if cumulative > 0:
                return month + 1
        return float("inf")

    def generate_executive_summary(
        self, inputs: CostInputs, results: CostResults
    ) -> Dict[str, Any]:
        """
        Generate executive summary for C-level presentation
        """
        logger.info("📋 Generating executive summary")

        # Key financial metrics
        key_metrics = {
            "annual_savings": results.annual_savings,
            "roi_percentage": results.roi_percentage,
            "payback_months": results.payback_months,
            "five_year_npv": results.npv_5_years,
            "risk_adjusted_savings": results.risk_adjusted_savings,
        }

        # Business impact assessment
        business_impact = {
            "revenue_protection": min(
                inputs.downtime_cost_hour * 24 * 30 * 12, results.annual_savings * 0.4
            ),
            "operational_efficiency": results.annual_savings * 0.3,
            "risk_mitigation": results.annual_savings * 0.2,
            "innovation_enablement": results.annual_savings * 0.1,
        }

        # Strategic value assessment
        strategic_value = {
            "competitive_positioning": "Technology Leadership",
            "market_differentiation": "First-mover Advantage",
            "scalability_potential": "Unlimited",
            "innovation_capacity": "Enhanced",
            "risk_profile": "Significantly Reduced",
        }

        # Investment recommendation
        if results.roi_percentage > 200 and results.payback_months < 12:
            recommendation = "IMMEDIATE IMPLEMENTATION RECOMMENDED"
            priority = "CRITICAL"
        elif results.roi_percentage > 100 and results.payback_months < 18:
            recommendation = "HIGH PRIORITY IMPLEMENTATION"
            priority = "HIGH"
        else:
            recommendation = "CONSIDER IMPLEMENTATION"
            priority = "MEDIUM"

        executive_summary = {
            "recommendation": recommendation,
            "priority": priority,
            "key_metrics": key_metrics,
            "business_impact": business_impact,
            "strategic_value": strategic_value,
            "critical_success_factors": [
                "Executive sponsorship and commitment",
                "Dedicated implementation team",
                "Clear success metrics and monitoring",
                "Phased rollout approach",
                "Continuous optimization focus",
            ],
            "next_steps": [
                "Approve business case and budget",
                "Establish implementation team",
                "Begin pilot program planning",
                "Define success metrics and KPIs",
                "Schedule executive briefings",
            ],
        }

        return executive_summary

    def export_analysis_report(
        self, inputs: CostInputs, output_dir: str = "07_Sales_Materials"
    ) -> str:
        """
        Export comprehensive analysis report
        """
        logger.info("📄 Exporting comprehensive analysis report")

        # Perform all analyses
        base_results = self.analyze_costs(inputs)
        competitor_comparison = self.compare_with_competitors(inputs)
        scenario_analysis = self.generate_scenario_analysis(inputs)
        tco_analysis = self.calculate_total_cost_of_ownership(inputs)
        executive_summary = self.generate_executive_summary(inputs, base_results)

        # Compile comprehensive report
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "analysis_type": "Adaptive Mind Framework Cost Analysis",
                "industry": inputs.industry,
                "analysis_parameters": asdict(inputs),
            },
            "executive_summary": executive_summary,
            "base_case_analysis": asdict(base_results),
            "competitor_comparison": competitor_comparison,
            "scenario_analysis": {k: asdict(v) for k, v in scenario_analysis.items()},
            "total_cost_of_ownership": tco_analysis,
            "recommendations": {
                "implementation_approach": "Phased rollout starting with critical workflows",
                "risk_mitigation": "Pilot program with success criteria",
                "success_metrics": [
                    "System reliability improvement",
                    "Cost reduction achievement",
                    "Team productivity gains",
                    "Customer satisfaction improvement",
                ],
                "timeline": "2-4 weeks for full implementation",
            },
        }

        # Save to file
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        report_file = (
            output_path
            / f"cost_analysis_report_{inputs.industry}_{datetime.now().strftime('%Y%m%d')}.json"
        )

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"✅ Analysis report exported: {report_file}")
        return str(report_file)


# Utility functions for easy usage
def quick_roi_analysis(
    monthly_requests: int, current_api_cost: float, industry: str = "customer_service"
) -> CostResults:
    """
    Quick ROI analysis with default parameters
    """
    inputs = CostInputs(
        monthly_requests=monthly_requests,
        current_api_cost=current_api_cost,
        current_failure_rate=10.0,  # Default 10%
        downtime_cost_hour=25000,  # Default $25K/hour
        team_size=6,  # Default team size
        avg_salary=85000,  # Default salary
        maintenance_time_percent=25,  # Default 25%
        industry=industry,
    )

    analyzer = AdaptiveMindCostAnalyzer()
    return analyzer.analyze_costs(inputs)


def generate_cost_comparison_table(
    monthly_requests: int, current_api_cost: float, industry: str = "customer_service"
) -> pd.DataFrame:
    """
    Generate cost comparison table for presentations
    """
    analyzer = AdaptiveMindCostAnalyzer()

    inputs = CostInputs(
        monthly_requests=monthly_requests,
        current_api_cost=current_api_cost,
        current_failure_rate=12.0,
        downtime_cost_hour=25000,
        team_size=6,
        avg_salary=85000,
        maintenance_time_percent=25,
        industry=industry,
    )

    # Get current and Adaptive Mind costs
    current_costs = analyzer._calculate_current_costs(inputs)
    adaptive_costs = analyzer._calculate_adaptive_mind_costs(inputs)

    # Get competitor comparisons
    competitor_comparisons = analyzer.compare_with_competitors(inputs)

    # Build comparison table
    comparison_data = {
        "Solution": ["Current Solution", "Adaptive Mind"],
        "Annual Cost": [current_costs["total"], adaptive_costs["total"]],
        "Annual Savings": [0, current_costs["total"] - adaptive_costs["total"]],
        "ROI %": [
            0,
            (
                (current_costs["total"] - adaptive_costs["total"])
                / adaptive_costs["total"]
            )
            * 100,
        ],
        "Reliability Score": [75, 99],
        "Failure Rate %": [12.0, 0.8],
    }

    # Add competitor data
    for competitor, data in competitor_comparisons.items():
        comparison_data["Solution"].append(competitor.title())
        comparison_data["Annual Cost"].append(data["competitor_annual_cost"])
        comparison_data["Annual Savings"].append(data["annual_savings"])
        comparison_data["ROI %"].append(data["roi_percentage"])
        comparison_data["Reliability Score"].append(85)  # Estimated
        comparison_data["Failure Rate %"].append(15)  # Estimated

    return pd.DataFrame(comparison_data)


# Example usage and testing
if __name__ == "__main__":
    print("🚀 Adaptive Mind Cost Analyzer - Testing Suite")

    # Test with sample data
    test_inputs = CostInputs(
        monthly_requests=150000,
        current_api_cost=0.025,
        current_failure_rate=12.0,
        downtime_cost_hour=25000,
        team_size=6,
        avg_salary=85000,
        maintenance_time_percent=25,
        industry="customer_service",
    )

    analyzer = AdaptiveMindCostAnalyzer()

    # Run basic analysis
    results = analyzer.analyze_costs(test_inputs)
    print("\n📊 Basic Analysis Results:")
    print(f"Annual Savings: ${results.annual_savings:,.0f}")
    print(f"ROI: {results.roi_percentage:.1f}%")
    print(f"Payback: {results.payback_months:.1f} months")

    # Generate comprehensive report
    report_file = analyzer.export_analysis_report(test_inputs)
    print(f"\n📄 Comprehensive report generated: {report_file}")

    # Generate comparison table
    comparison_table = generate_cost_comparison_table(150000, 0.025)
    print("\n📋 Cost Comparison Table:")
    print(comparison_table.to_string(index=False))

    print("\n✅ Cost Analysis Engine testing complete!")
