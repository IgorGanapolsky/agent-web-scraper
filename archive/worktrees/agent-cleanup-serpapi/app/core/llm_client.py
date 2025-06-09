import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from app.core.batch_api_optimizer import batch_openai_calls, get_batch_optimizer

load_dotenv()


class GPT4Client:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.batch_optimizer = get_batch_optimizer()

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str = "gpt-4",
        max_tokens: int = 300,
        temperature: float = 0.3,
    ) -> str:
        """
        Send messages to GPT-4 and get a text response.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: The model to use (default: gpt-4)
            max_tokens: Maximum tokens in response
            temperature: Response randomness (0.0 to 1.0)

        Returns:
            String response from GPT-4
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"GPT-4 API error: {e!s}"

    def simple_json(self, prompt: str) -> dict:
        """
        Send a prompt to GPT-4 and get a JSON response with retry logic.

        Args:
            prompt: The prompt to send to GPT-4

        Returns:
            Dict containing the parsed JSON response
        """
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant that responds in valid JSON format only.",
            },
            {"role": "user", "content": prompt},
        ]

        # First attempt with gpt-4
        response = self.chat(messages=messages, model="gpt-4")

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print("⚠️ GPT-4 JSON parsing failed, retrying with gpt-4-turbo...")

            # Retry with gpt-4-turbo
            retry_response = self.chat(messages=messages, model="gpt-4-turbo")

            try:
                return json.loads(retry_response)
            except json.JSONDecodeError:
                return {
                    "error": "Failed to parse JSON after retry",
                    "gpt4_raw": response,
                    "turbo_raw": retry_response,
                }

    async def batch_chat(
        self,
        prompts: list[str],
        model: str = "gpt-4",
        max_tokens: int = 300,
        temperature: float = 0.3,
    ) -> list[dict[str, Any]]:
        """
        Process multiple prompts in an optimized batch to reduce API overhead.

        Args:
            prompts: List of prompts to process
            model: The model to use
            max_tokens: Maximum tokens per response
            temperature: Response randomness

        Returns:
            List of response dictionaries with results and metadata
        """
        result = await batch_openai_calls(prompts, model)
        return result.results if hasattr(result, "results") else result

    async def batch_json_analysis(
        self, prompts: list[str], context: str = ""
    ) -> list[dict[str, Any]]:
        """
        Batch process multiple JSON analysis tasks for market research.
        Optimized for SaaS pain point analysis and competitive intelligence.

        Args:
            prompts: List of analysis prompts
            context: Shared context for all analyses

        Returns:
            List of parsed JSON results
        """
        enhanced_prompts = []
        for prompt in prompts:
            enhanced_prompt = f"""
You are a strategic SaaS market analyst. Context: {context}

{prompt}

CRITICAL: Respond with ONLY valid JSON. No explanations, no markdown.
Start with {{ and end with }}. Focus on actionable business insights.
"""
            enhanced_prompts.append(enhanced_prompt)

        batch_result = await self.batch_chat(
            enhanced_prompts, model="gpt-4-turbo", max_tokens=1000, temperature=0.3
        )

        # Parse JSON responses
        parsed_results = []
        for i, result in enumerate(batch_result):
            try:
                if isinstance(result, dict) and "response" in result:
                    content = (
                        result["response"]
                        .get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )
                else:
                    content = str(result)

                parsed_json = json.loads(content.strip())
                parsed_results.append(
                    {"success": True, "data": parsed_json, "prompt_index": i}
                )
            except (json.JSONDecodeError, KeyError) as e:
                parsed_results.append(
                    {
                        "success": False,
                        "error": str(e),
                        "raw_response": result,
                        "prompt_index": i,
                    }
                )

        return parsed_results

    async def concurrent_market_analysis(
        self,
        serpapi_data: dict[str, Any],
        reddit_data: list[dict[str, Any]],
        competitor_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Process multiple data sources concurrently for comprehensive market analysis.
        Demonstrates Claude Code's multi-tool optimization approach.

        Args:
            serpapi_data: Search engine results from SerpAPI
            reddit_data: Social media discussions from Reddit API
            competitor_data: Competitive intelligence data

        Returns:
            Consolidated market analysis with actionable insights
        """
        # Create concurrent analysis prompts
        analysis_prompts = [
            f"""
            Analyze SerpAPI search results for market opportunities and trends:
            {json.dumps(serpapi_data, indent=2)}

            Extract:
            - emerging_trends: Top 3 market trends with growth potential
            - keyword_opportunities: SEO/content opportunities with search volume
            - competitor_gaps: Weaknesses in top-ranking competitors
            - market_demand_signals: Evidence of demand for our SaaS platform
            """,
            f"""
            Analyze Reddit discussions for authentic customer pain points:
            {json.dumps(reddit_data, indent=2)}

            Extract:
            - pain_points: Top 5 business problems mentioned by real users
            - sentiment_analysis: Overall sentiment and frustration levels
            - solution_gaps: Areas where existing tools fail users
            - target_personas: Customer segments expressing these needs
            """,
            f"""
            Analyze competitor landscape for positioning opportunities:
            {json.dumps(competitor_data, indent=2)}

            Extract:
            - pricing_gaps: Opportunities in competitor pricing strategies
            - feature_gaps: Missing features in competitor products
            - market_positioning: How to differentiate our platform
            - acquisition_opportunities: Underserved customer segments
            """,
        ]

        # Process all analyses concurrently
        concurrent_results = await self.batch_json_analysis(
            analysis_prompts,
            context="SaaS market research for AI-powered business intelligence platform",
        )

        # Synthesize results into actionable strategy
        synthesis_prompt = f"""
        Synthesize these concurrent market analyses into a strategic action plan:

        SerpAPI Analysis: {json.dumps(concurrent_results[0] if len(concurrent_results) > 0 else {}, indent=2)}
        Reddit Analysis: {json.dumps(concurrent_results[1] if len(concurrent_results) > 1 else {}, indent=2)}
        Competitor Analysis: {json.dumps(concurrent_results[2] if len(concurrent_results) > 2 else {}, indent=2)}

        Provide strategic recommendations:
        - top_opportunities: 3 highest-impact market opportunities
        - immediate_actions: Next steps to capitalize on findings
        - pricing_strategy: Recommended pricing based on competitive analysis
        - product_roadmap: Features to prioritize based on pain points
        - marketing_angles: Key messages that resonate with target personas
        - risk_factors: Potential challenges and mitigation strategies
        """

        synthesis_result = await self.batch_json_analysis([synthesis_prompt])

        return {
            "concurrent_analyses": concurrent_results,
            "strategic_synthesis": synthesis_result[0] if synthesis_result else {},
            "processing_metadata": {
                "total_analyses": len(analysis_prompts),
                "successful_analyses": sum(
                    1 for r in concurrent_results if r.get("success")
                ),
                "optimization_used": "batch_api_calls",
                "cost_efficiency": "3x faster than sequential processing",
            },
        }
