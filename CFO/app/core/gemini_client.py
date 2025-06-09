"""
Gemini Ultra API client for advanced content analysis and generation.
Uses Vertex AI for paid subscriptions.
"""

import json
import logging
import os
from typing import Any, Optional

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel

    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Google Gemini Ultra API via Vertex AI."""

    def __init__(self, api_key: Optional[str] = None, project_id: Optional[str] = None):
        """
        Initialize Gemini client with Vertex AI (paid) or fallback to free tier.

        Args:
            api_key: Gemini API key. If None, loads from GEMINI_API_KEY env var
            project_id: Google Cloud Project ID. If None, loads from GOOGLE_CLOUD_PROJECT env var
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        # For now, use free tier with paid API key (you enabled billing on the key)
        # Once IAM is set up, we can switch to Vertex AI
        self._init_free_tier()

        # TODO: Uncomment this when IAM permissions are set up
        # if VERTEX_AVAILABLE and self.project_id:
        #     self._init_vertex_ai()
        # else:
        #     self._init_free_tier()

    def _init_vertex_ai(self):
        """Initialize Vertex AI client (paid subscription)."""
        try:
            # Initialize Vertex AI
            vertexai.init(project=self.project_id, location="us-central1")
            self.model = GenerativeModel("gemini-1.5-pro")
            self.use_vertex = True
            logger.info(
                f"Vertex AI Gemini client initialized successfully (Project: {self.project_id})"
            )
        except Exception as e:
            logger.warning(
                f"Vertex AI initialization failed: {e}, falling back to free tier"
            )
            self._init_free_tier()

    def _init_free_tier(self):
        """Initialize free tier client as fallback."""
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-1.5-pro")
            self.use_vertex = False
            logger.info("Free tier Gemini client initialized (may have quota limits)")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            raise

    def generate_json_summary(self, prompt: str, content: str) -> dict[str, Any]:
        """
        Generate JSON-formatted summary using Gemini.

        Args:
            prompt: System prompt for the task
            content: Content to analyze

        Returns:
            Dict containing parsed JSON response
        """
        try:
            full_prompt = f"""
{prompt}

Content to analyze:
\"\"\"
{content}
\"\"\"

CRITICAL: Respond with ONLY valid JSON. No explanations, no markdown formatting, no code blocks.
Start your response with {{ and end with }}. Do not include anything else.
"""

            if hasattr(self, "use_vertex") and self.use_vertex:
                # Vertex AI call
                response = self.model.generate_content(full_prompt)
                response_text = response.text
            else:
                # Free tier call
                response = self.model.generate_content(full_prompt)
                response_text = response.text

            # Parse JSON response - handle common Gemini formatting issues
            try:
                # Clean up response text
                clean_text = response_text.strip()

                # Remove markdown code blocks if present
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]

                # Remove any leading/trailing whitespace again
                clean_text = clean_text.strip()

                # Try to parse JSON
                if clean_text:
                    return json.loads(clean_text)
                else:
                    logger.warning("Empty response from Gemini")
                    return {"error": "Empty response", "raw_response": response_text}

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON, returning raw response: {e}")
                logger.debug(f"Raw response was: {response_text}")
                return {"error": "Invalid JSON", "raw_response": response_text}

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return {"error": str(e)}

    def summarize_reddit_thread(
        self, comments: list[str], search_term: str
    ) -> list[dict[str, str]]:
        """
        Analyze Reddit thread comments to extract business pain points.

        Args:
            comments: List of Reddit comments
            search_term: Original search query for context

        Returns:
            List of pain point dictionaries with label, explanation, gsheet_link
        """
        if not comments:
            return []

        combined_comments = "\\n\\n".join(comments)

        prompt = f"""
You are an expert SaaS market researcher analyzing Reddit discussions to identify business pain points and opportunities.

CONTEXT: Analyzing discussions about "{search_term}" to find actionable business insights.

TASK: Extract the 3 most significant pain points from this Reddit discussion. Focus on:
- Business problems that could be solved with software/services
- Frustrations that indicate market gaps
- Workflow inefficiencies mentioned by users
- Cost/time wasters that businesses face

For each pain point, provide:
- pain_point_label: Concise business problem (max 8 words)
- explanation: Why this is painful and what it costs businesses (2-3 sentences)
- gsheet_link: Leave empty for now

PRIORITIZE pain points that:
✅ Affect multiple users/businesses
✅ Have clear business impact (time, money, efficiency)
✅ Could be solved with technology/services
✅ Show strong emotional language (frustration, complaints)

AVOID generic complaints or one-off issues.

Respond in JSON array format:
[
  {{
    "pain_point_label": "Short business problem description",
    "explanation": "Why this costs businesses time/money and the impact on operations...",
    "gsheet_link": ""
  }},
  ...
]
"""

        result = self.generate_json_summary(prompt, combined_comments)

        # Ensure we return a list format
        if isinstance(result, list):
            return result[:3]  # Limit to top 3
        elif isinstance(result, dict) and "error" not in result:
            return [result]  # Single result
        else:
            logger.error(f"Unexpected Gemini response format: {result}")
            return []

    def analyze_sentiment(self, text: str) -> dict[str, Any]:
        """
        Analyze sentiment and emotional intensity of text.

        Args:
            text: Text to analyze

        Returns:
            Dict with sentiment analysis results
        """
        prompt = """
Analyze the sentiment and emotional intensity of the provided text.

Return a JSON object with:
- sentiment: "positive", "negative", or "neutral"
- intensity: "low", "medium", or "high"
- confidence: float between 0.0 and 1.0
- key_emotions: array of detected emotions (anger, frustration, excitement, etc.)
- business_impact: "low", "medium", or "high" - how much this affects business decisions

Focus on business and professional context.
"""

        return self.generate_json_summary(prompt, text)

    def extract_business_insights(
        self, content: str, context: str = ""
    ) -> dict[str, Any]:
        """
        Extract strategic business insights from content.

        Args:
            content: Content to analyze
            context: Additional context for analysis

        Returns:
            Dict with business insights
        """
        prompt = f"""
You are a business strategy consultant analyzing market discussions.

Context: {context}

Extract strategic business insights including:
- market_gaps: Unfulfilled needs or opportunities
- competitor_weaknesses: Areas where existing solutions fail
- customer_personas: Types of users expressing these needs
- solution_opportunities: Potential product/service ideas
- market_size_indicators: Signs of market demand/size
- urgency_level: How urgent these problems are (low/medium/high)

Return as JSON object with these exact keys.
"""

        return self.generate_json_summary(prompt, content)

    def compare_with_gpt_analysis(
        self, content: str, gpt_results: list[dict]
    ) -> dict[str, Any]:
        """
        Compare Gemini analysis with GPT results for validation.

        Args:
            content: Original content
            gpt_results: GPT analysis results

        Returns:
            Dict with comparison and consensus
        """
        gpt_summary = json.dumps(gpt_results, indent=2)

        prompt = f"""
You are analyzing content that was already analyzed by GPT-4.

GPT-4 Analysis:
{gpt_summary}

Now analyze the same content independently and then:
1. Identify points where you agree with GPT-4
2. Identify points where you disagree or see additional insights
3. Provide a consensus recommendation combining both analyses

Return JSON with:
- gemini_analysis: Your independent analysis (same format as GPT)
- agreement_points: List of agreements with GPT
- disagreement_points: List of disagreements with explanations
- consensus_insights: Combined top 3 insights from both models
- confidence_score: 0.0-1.0 how confident you are in consensus
"""

        return self.generate_json_summary(prompt, content)
