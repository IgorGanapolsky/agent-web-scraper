#!/usr/bin/env python3
"""
Stripe Auto-Embed System
Automatically embeds Stripe pitch in all lead magnets, Substack posts, and outbound emails
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from app.config.logging import get_logger
from app.core.session_memory import get_session_memory_manager

logger = get_logger(__name__)


class StripeAutoEmbed:
    """Auto-embed Stripe pitch across all customer touchpoints"""
    
    def __init__(self):
        self.memory = get_session_memory_manager()
        
        # Stripe pitch templates for different contexts
        self.pitch_templates = {
            "lead_magnet": {
                "header": "🚀 **Ready to 10x Your SaaS Growth?**",
                "body": "Get instant access to our AI-powered market intelligence platform. Join 500+ SaaS founders scaling to $1M+ ARR.",
                "cta": "[Start Free Trial - No Credit Card Required](https://saasgrowthdispatch.com/trial)",
                "pricing_hint": "Plans start at $29/month • 14-day free trial • Cancel anytime",
                "placement": "top"
            },
            "substack_post": {
                "header": "📈 **Exclusive for SaaS Growth Dispatch Readers**",
                "body": "Transform insights into revenue with our AI market intelligence platform. Real SaaS founders, real results.",
                "cta": "[Claim Your Free Trial](https://saasgrowthdispatch.com/trial?utm_source=substack&utm_medium=post)",
                "pricing_hint": "💡 *Special: First 100 readers get 30% off first month*",
                "placement": "top_and_bottom"
            },
            "outbound_email": {
                "header": "P.S. Before you go...",
                "body": "I built an AI system that finds profitable SaaS opportunities automatically. It's how I discovered the insights I just shared with you.",
                "cta": "[See it in action (free trial)](https://saasgrowthdispatch.com/trial?utm_source=email&utm_medium=outreach)",
                "pricing_hint": "No credit card • 5-minute setup • Cancel anytime",
                "placement": "bottom"
            },
            "blog_post": {
                "header": "🎯 **Want More Insights Like This?**",
                "body": "Our AI platform delivers 10x more market intelligence daily. Join SaaS founders scaling from $0 to $1M+ ARR.",
                "cta": "[Start Your Free Trial](https://saasgrowthdispatch.com/trial?utm_source=blog&utm_medium=content)",
                "pricing_hint": "✨ *No credit card required • Full access for 14 days*",
                "placement": "middle_and_bottom"
            }
        }
        
        # A/B test variations
        self.ab_variations = {
            "urgency": {
                "header": "⏰ **Limited Time: Free Market Intelligence**",
                "body": "Only 50 spots left for our premium SaaS intelligence platform. Don't miss the opportunities your competitors are finding."
            },
            "social_proof": {
                "header": "✅ **Trusted by 500+ SaaS Founders**",
                "body": "Join founders like @username who scaled from $10K to $100K MRR using our market intelligence."
            },
            "value_focused": {
                "header": "💰 **Turn Market Data Into Revenue**",
                "body": "Our AI finds $10K+ opportunities daily. See what you're missing."
            }
        }
        
        logger.info("Stripe Auto-Embed system initialized")
    
    def embed_in_lead_magnet(self, content: str, magnet_type: str = "report") -> str:
        """Auto-embed Stripe pitch in lead magnets"""
        
        template = self.pitch_templates["lead_magnet"]
        
        # Create embedded pitch
        pitch_block = self._create_pitch_block(
            template, 
            utm_params={"source": "lead_magnet", "medium": magnet_type}
        )
        
        # Embed at top of content
        embedded_content = f"{pitch_block}\n\n---\n\n{content}"
        
        # Track embedding
        self._track_embedding("lead_magnet", magnet_type, len(content))
        
        logger.info(f"Stripe pitch embedded in {magnet_type} lead magnet")
        
        return embedded_content
    
    def embed_in_substack_post(self, post_content: str, post_title: str) -> str:
        """Auto-embed Stripe pitch in Substack posts"""
        
        template = self.pitch_templates["substack_post"]
        
        # Create pitch blocks for top and bottom
        top_pitch = self._create_pitch_block(
            template,
            utm_params={"source": "substack", "medium": "post_top"},
            variation="social_proof"
        )
        
        bottom_pitch = self._create_pitch_block(
            template,
            utm_params={"source": "substack", "medium": "post_bottom"},
            variation="value_focused"
        )
        
        # Embed at top and bottom
        embedded_post = f"{top_pitch}\n\n{post_content}\n\n---\n\n{bottom_pitch}"
        
        # Track embedding
        self._track_embedding("substack_post", post_title, len(post_content))
        
        logger.info(f"Stripe pitch embedded in Substack post: {post_title}")
        
        return embedded_post
    
    def embed_in_outbound_email(self, email_content: str, recipient_type: str = "prospect") -> str:
        """Auto-embed Stripe pitch in outbound emails"""
        
        template = self.pitch_templates["outbound_email"]
        
        # Create subtle bottom pitch
        pitch_block = self._create_pitch_block(
            template,
            utm_params={"source": "email", "medium": "outreach", "content": recipient_type},
            style="subtle"
        )
        
        # Embed at bottom of email
        embedded_email = f"{email_content}\n\n{pitch_block}"
        
        # Track embedding
        self._track_embedding("outbound_email", recipient_type, len(email_content))
        
        logger.info(f"Stripe pitch embedded in outbound email to {recipient_type}")
        
        return embedded_email
    
    def embed_in_blog_post(self, blog_content: str, blog_title: str) -> str:
        """Auto-embed Stripe pitch in blog posts"""
        
        template = self.pitch_templates["blog_post"]
        
        # Split content for middle insertion
        paragraphs = blog_content.split('\n\n')
        middle_index = len(paragraphs) // 2
        
        # Create pitch blocks
        middle_pitch = self._create_pitch_block(
            template,
            utm_params={"source": "blog", "medium": "content_middle"},
            style="inline"
        )
        
        bottom_pitch = self._create_pitch_block(
            template,
            utm_params={"source": "blog", "medium": "content_bottom"},
            variation="urgency"
        )
        
        # Insert pitches
        paragraphs.insert(middle_index, f"\n{middle_pitch}\n")
        embedded_content = '\n\n'.join(paragraphs) + f"\n\n---\n\n{bottom_pitch}"
        
        # Track embedding
        self._track_embedding("blog_post", blog_title, len(blog_content))
        
        logger.info(f"Stripe pitch embedded in blog post: {blog_title}")
        
        return embedded_content
    
    def _create_pitch_block(self, template: Dict, utm_params: Dict, 
                           variation: str = None, style: str = "standard") -> str:
        """Create formatted pitch block"""
        
        # Use variation if specified
        if variation and variation in self.ab_variations:
            var = self.ab_variations[variation]
            header = var["header"]
            body = var["body"]
        else:
            header = template["header"]
            body = template["body"]
        
        # Build UTM parameters
        utm_string = "&".join([f"utm_{k}={v}" for k, v in utm_params.items()])
        cta_with_utm = template["cta"].replace(")", f"&{utm_string})")
        
        # Style variations
        if style == "subtle":
            return f"{header}\n\n{body}\n\n{cta_with_utm}\n\n{template['pricing_hint']}"
        elif style == "inline":
            return f"\n> {header}\n>\n> {body}\n>\n> {cta_with_utm}\n"
        else:  # standard
            return f"🎯 {header}\n\n{body}\n\n**{cta_with_utm}**\n\n{template['pricing_hint']}"
    
    def _track_embedding(self, content_type: str, content_id: str, content_length: int):
        """Track pitch embeddings for optimization"""
        
        embedding_data = {
            "timestamp": datetime.now().isoformat(),
            "content_type": content_type,
            "content_id": content_id,
            "content_length": content_length,
            "pitch_embedded": True,
            "utm_tracking": True
        }
        
        # Store in session memory
        self.memory.store_memory_node(
            category="stripe_embeddings",
            content=embedding_data,
            tags=["auto_embed", content_type, "revenue_optimization"],
            importance_score=0.8
        )
    
    def generate_embed_analytics(self) -> Dict:
        """Generate analytics on Stripe pitch embeddings"""
        
        # Get all embedding data from memory
        embedding_nodes = [
            node for node in self.memory.memory_nodes.values()
            if node.category == "stripe_embeddings"
        ]
        
        analytics = {
            "total_embeddings": len(embedding_nodes),
            "embeddings_by_type": {},
            "average_content_length": 0,
            "recent_embeddings": [],
            "optimization_recommendations": []
        }
        
        if embedding_nodes:
            # Calculate metrics
            total_length = 0
            type_counts = {}
            
            for node in embedding_nodes[-10:]:  # Last 10 embeddings
                content = node.content
                content_type = content.get('content_type', 'unknown')
                
                type_counts[content_type] = type_counts.get(content_type, 0) + 1
                total_length += content.get('content_length', 0)
                
                analytics["recent_embeddings"].append({
                    "type": content_type,
                    "id": content.get('content_id', ''),
                    "timestamp": content.get('timestamp', '')
                })
            
            analytics["embeddings_by_type"] = type_counts
            analytics["average_content_length"] = total_length / len(embedding_nodes[-10:])
            
            # Generate recommendations
            if type_counts.get('outbound_email', 0) < 5:
                analytics["optimization_recommendations"].append(
                    "Increase Stripe pitch embedding in outbound emails"
                )
            
            if type_counts.get('substack_post', 0) < 3:
                analytics["optimization_recommendations"].append(
                    "Embed more Stripe pitches in Substack posts for monetization"
                )
        
        return analytics
    
    def create_auto_embed_templates(self) -> Dict:
        """Create templates for automatic embedding"""
        
        templates = {
            "email_templates": {
                "prospecting": {
                    "subject_lines": [
                        "Quick question about {company}'s growth strategy",
                        "Market opportunity for {company} - 2 minutes?",
                        "Found something interesting for {industry} companies"
                    ],
                    "body_template": """Hi {name},

I noticed {company} is working in {industry}, and I thought you might be interested in something that could give you a competitive edge.

Our AI system automatically discovers pain points and market opportunities by analyzing thousands of conversations across Reddit, GitHub, and other platforms.

**For {industry} specifically, we've identified:**
• {opportunity_1}
• {opportunity_2} 
• {opportunity_3}

This kind of market intelligence usually takes weeks to research manually. Our system finds opportunities like this daily.

Worth a 5-minute conversation?

Best,
Igor""",
                    "auto_embed": True
                },
                "follow_up": {
                    "subject_lines": [
                        "Following up on {company}'s market opportunities",
                        "Those {industry} insights I mentioned",
                        "Quick update on {topic}"
                    ],
                    "body_template": """Hi {name},

Following up on my previous email about market opportunities for {company}.

I just wanted to share one specific insight that might be relevant:

{specific_insight}

This is exactly the type of intelligence our platform delivers daily. Thought it might be valuable for {company}'s strategy.

Interested in seeing more?

Best,
Igor""",
                    "auto_embed": True
                }
            },
            "substack_templates": {
                "market_analysis": {
                    "title_format": "Market Analysis: {topic} - Week of {date}",
                    "intro_template": "This week's market analysis reveals {key_insight}. Here's what SaaS founders need to know:",
                    "auto_embed": True,
                    "embed_frequency": "every_post"
                },
                "opportunity_spotlight": {
                    "title_format": "Opportunity Spotlight: {niche} ({size} market)",
                    "intro_template": "Our AI discovered a high-potential opportunity in {niche}. Here's the complete analysis:",
                    "auto_embed": True,
                    "embed_frequency": "every_post"
                }
            },
            "lead_magnet_templates": {
                "market_report": {
                    "title_format": "The {industry} Market Report - {month} {year}",
                    "description": "Comprehensive analysis of {industry} market opportunities, pain points, and revenue potential.",
                    "auto_embed": True,
                    "embed_style": "prominent"
                },
                "opportunity_guide": {
                    "title_format": "10 Untapped Opportunities in {industry}",
                    "description": "AI-discovered market opportunities with validated demand and low competition.",
                    "auto_embed": True,
                    "embed_style": "prominent"
                }
            }
        }
        
        # Store templates in memory
        self.memory.store_memory_node(
            category="auto_embed_templates",
            content=templates,
            tags=["templates", "auto_embed", "revenue_optimization"],
            importance_score=1.0
        )
        
        return templates


def demo_auto_embed_system():
    """Demonstrate the auto-embed system"""
    
    embed_system = StripeAutoEmbed()
    
    print("🎯 Stripe Auto-Embed System Demo")
    print("=" * 50)
    
    # Demo lead magnet embedding
    sample_report = """# SaaS Market Analysis Report
    
This comprehensive report analyzes the current SaaS market landscape...
    
## Key Findings
1. Market opportunity in HR tech: $2.3B
2. Growing demand for AI-powered solutions
3. Underserved SMB segment
    
## Recommendations
SaaS founders should focus on..."""
    
    embedded_report = embed_system.embed_in_lead_magnet(sample_report, "market_report")
    print("📄 Lead Magnet with Embedded Pitch:")
    print(embedded_report[:200] + "...")
    print()
    
    # Demo Substack post embedding
    sample_post = """Today I want to share some insights about the SaaS market that most founders are missing.
    
The data shows that 73% of SaaS companies are focusing on the wrong market segments..."""
    
    embedded_post = embed_system.embed_in_substack_post(sample_post, "Weekly SaaS Insights")
    print("📝 Substack Post with Embedded Pitch:")
    print(embedded_post[:200] + "...")
    print()
    
    # Demo outbound email embedding
    sample_email = """Hi Sarah,
    
I noticed YourCompany is working in the HR tech space, and I thought you might be interested in a market opportunity I discovered.
    
Our AI found that 'employee onboarding automation' has 340% growth in discussions with minimal competition.
    
Worth a quick conversation?
    
Best,
Igor"""
    
    embedded_email = embed_system.embed_in_outbound_email(sample_email, "hr_tech_prospect")
    print("📧 Outbound Email with Embedded Pitch:")
    print(embedded_email)
    print()
    
    # Generate analytics
    analytics = embed_system.generate_embed_analytics()
    print("📊 Embedding Analytics:")
    print(json.dumps(analytics, indent=2))
    
    # Create templates
    templates = embed_system.create_auto_embed_templates()
    print("\n📋 Auto-Embed Templates Created:")
    print(f"• Email templates: {len(templates['email_templates'])}")
    print(f"• Substack templates: {len(templates['substack_templates'])}")
    print(f"• Lead magnet templates: {len(templates['lead_magnet_templates'])}")
    
    return embed_system


if __name__ == "__main__":
    demo_auto_embed_system()
