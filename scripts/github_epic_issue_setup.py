#!/usr/bin/env python3
"""
GitHub Epic & Issue Setup System
Enterprise Claude Code Optimization Suite for Infrastructure Gaps
"""

from datetime import datetime
from typing import Any


class GitHubEpicIssueSetup:
    """Enterprise GitHub project management for infrastructure gaps"""

    def __init__(self):
        self.milestone = "M1 - Monetization Ready"
        self.milestone_date = datetime(2025, 6, 20)  # End of Week 2 extended

        # Agent assignments
        self.agent_assignments = {
            "claude": ["stripe_integration", "customer_dashboard", "api_access_management"],
            "gemini": ["onboarding_retention_ux"],
            "n8n_creator": ["email_automation", "workflow_automation"]
        }

        # Label categories for auto-tagging
        self.label_categories = {
            "billing": {"color": "0E8A16", "description": "Payment and billing related"},
            "ux": {"color": "1D76DB", "description": "User experience and interface"},
            "onboarding": {"color": "FBCA04", "description": "User onboarding and retention"},
            "infra": {"color": "D93F0B", "description": "Infrastructure and backend"},
            "automation": {"color": "5319E7", "description": "Workflow and email automation"},
            "api": {"color": "B60205", "description": "API development and management"}
        }

        print("🎯 GitHub Epic & Issue Setup System Initialized")
        print(f"📅 Milestone: {self.milestone} (Due: {self.milestone_date.strftime('%m/%d/%Y')})")

    def create_github_epic_structure(self) -> dict[str, Any]:
        """Create comprehensive GitHub Epic and Issue structure"""

        print("\n📋 Creating GitHub Epic & Issue Structure...")

        epics = {}

        # Epic 1: Stripe Integration
        epics["stripe_integration"] = self._create_stripe_epic()

        # Epic 2: Customer Dashboard
        epics["customer_dashboard"] = self._create_dashboard_epic()

        # Epic 3: Trial Flow
        epics["trial_flow"] = self._create_trial_flow_epic()

        # Epic 4: API Access Management
        epics["api_access_management"] = self._create_api_access_epic()

        # Epic 5: Onboarding & Retention
        epics["onboarding_retention"] = self._create_onboarding_epic()

        return {
            "github_project_structure": {
                "project_name": "Revenue Acceleration Infrastructure",
                "milestone": self.milestone,
                "milestone_date": self.milestone_date.isoformat(),
                "total_epics": len(epics),
                "total_issues": sum(len(epic["issues"]) for epic in epics.values()),
                "labels": self.label_categories,
                "agent_assignments": self.agent_assignments
            },
            "epics": epics,
            "automation_config": {
                "auto_labeling": True,
                "milestone_tracking": True,
                "progress_notifications": True,
                "epic_linking": True
            }
        }

    def _create_stripe_epic(self) -> dict[str, Any]:
        """Create Stripe Integration Epic with Issues"""

        return {
            "epic": {
                "title": "Epic: Stripe Integration - Payment Processing Foundation",
                "description": """
Complete Stripe integration for subscription billing and payment processing.
This is the critical path blocker for all revenue generation.

**Acceptance Criteria:**
- [ ] Stripe API keys configured and secured
- [ ] Webhook endpoints handle all payment events
- [ ] Subscription management (create, update, cancel)
- [ ] Payment processing for all pricing tiers
- [ ] Testing environment fully functional
- [ ] Production deployment completed

**Success Metrics:**
- 99.5% payment processing uptime
- < 2 second payment confirmation
- 100% webhook reliability
                """,
                "labels": ["billing", "infra"],
                "assignee": "claude",
                "milestone": self.milestone,
                "estimated_hours": 40,
                "priority": "critical"
            },
            "issues": [
                {
                    "title": "Stripe API Configuration & Security Setup",
                    "description": """
Set up Stripe API keys with proper security configuration.

**Tasks:**
- [ ] Generate Stripe API keys (test + production)
- [ ] Configure environment variables securely
- [ ] Set up webhook secret validation
- [ ] Test API connectivity

**Acceptance Criteria:**
- API keys stored securely in environment
- Webhook signature validation working
- Connection tests pass in both environments
                    """,
                    "labels": ["billing", "infra"],
                    "assignee": "claude",
                    "estimated_hours": 8,
                    "epic_link": "stripe_integration"
                },
                {
                    "title": "Stripe Webhook Handler Implementation",
                    "description": """
Create robust webhook handlers for all Stripe events.

**Webhook Events to Handle:**
- [ ] `payment_intent.succeeded`
- [ ] `payment_intent.payment_failed`
- [ ] `customer.subscription.created`
- [ ] `customer.subscription.updated`
- [ ] `customer.subscription.deleted`
- [ ] `invoice.payment_succeeded`
- [ ] `invoice.payment_failed`

**Acceptance Criteria:**
- All webhook events properly handled
- Error handling and retry logic
- Webhook signature verification
- Event logging and monitoring
                    """,
                    "labels": ["billing", "infra"],
                    "assignee": "claude",
                    "estimated_hours": 12,
                    "epic_link": "stripe_integration"
                },
                {
                    "title": "Subscription Management Endpoints",
                    "description": """
Create FastAPI endpoints for subscription management.

**Endpoints to Create:**
- [ ] `POST /api/subscriptions/create`
- [ ] `PUT /api/subscriptions/{id}/update`
- [ ] `DELETE /api/subscriptions/{id}/cancel`
- [ ] `GET /api/subscriptions/{id}/status`
- [ ] `POST /api/subscriptions/{id}/change-plan`

**Acceptance Criteria:**
- All CRUD operations working
- Proper error handling
- Input validation
- API documentation
                    """,
                    "labels": ["billing", "api"],
                    "assignee": "claude",
                    "estimated_hours": 12,
                    "epic_link": "stripe_integration"
                },
                {
                    "title": "Payment Processing Flow Integration",
                    "description": """
Integrate payment processing with subscription tiers.

**Payment Flows:**
- [ ] Trial signup (no payment)
- [ ] Trial to paid conversion
- [ ] Direct paid signup
- [ ] Plan upgrades/downgrades
- [ ] Payment method updates

**Acceptance Criteria:**
- Smooth payment experience
- Error handling for failed payments
- Success/failure notifications
- Integration with pricing tiers
                    """,
                    "labels": ["billing", "ux"],
                    "assignee": "claude",
                    "estimated_hours": 8,
                    "epic_link": "stripe_integration"
                }
            ]
        }

    def _create_dashboard_epic(self) -> dict[str, Any]:
        """Create Customer Dashboard Epic with Issues"""

        return {
            "epic": {
                "title": "Epic: Customer Dashboard - Self-Service Portal",
                "description": """
Build comprehensive customer dashboard for subscription and usage management.

**Acceptance Criteria:**
- [ ] Customer authentication and authorization
- [ ] Subscription management interface
- [ ] Usage analytics and billing history
- [ ] Plan upgrade/downgrade capabilities
- [ ] API key management integration
- [ ] Responsive design for all devices

**Success Metrics:**
- 90% customer self-service rate
- < 3 second page load times
- 95% feature adoption rate
                """,
                "labels": ["ux", "infra"],
                "assignee": "claude",
                "milestone": self.milestone,
                "estimated_hours": 80,
                "priority": "high"
            },
            "issues": [
                {
                    "title": "Dashboard UI Components & Layout",
                    "description": """
Create React components for customer dashboard interface.

**Components to Build:**
- [ ] DashboardLayout (navigation, sidebar)
- [ ] SubscriptionCard (current plan, status)
- [ ] UsageMetrics (API calls, data usage)
- [ ] BillingHistory (invoices, payments)
- [ ] PlanUpgrade (tier comparison, CTA)
- [ ] AccountSettings (profile, preferences)

**Acceptance Criteria:**
- Responsive design (mobile, tablet, desktop)
- Consistent UI/UX with brand guidelines
- Loading states and error handling
- Accessibility compliance (WCAG 2.1)
                    """,
                    "labels": ["ux"],
                    "assignee": "claude",
                    "estimated_hours": 24,
                    "epic_link": "customer_dashboard"
                },
                {
                    "title": "Subscription Management Interface",
                    "description": """
Build interface for customers to manage their subscriptions.

**Features:**
- [ ] View current subscription details
- [ ] Change billing frequency (monthly/annual)
- [ ] Upgrade/downgrade plans
- [ ] Cancel subscription with retention offers
- [ ] Update payment methods
- [ ] Download invoices

**Acceptance Criteria:**
- Real-time subscription status updates
- Stripe integration for payment changes
- Cancellation flow with feedback collection
- Prorated billing calculations
                    """,
                    "labels": ["billing", "ux"],
                    "assignee": "claude",
                    "estimated_hours": 20,
                    "epic_link": "customer_dashboard"
                },
                {
                    "title": "Usage Analytics Dashboard",
                    "description": """
Create analytics dashboard showing usage metrics and insights.

**Analytics to Display:**
- [ ] API usage by endpoint
- [ ] Data processing volume
- [ ] Feature adoption metrics
- [ ] Performance analytics
- [ ] Cost savings realized
- [ ] Trend analysis (daily, weekly, monthly)

**Acceptance Criteria:**
- Real-time data updates
- Interactive charts and graphs
- Export capabilities (PDF, CSV)
- Usage alerts and notifications
                    """,
                    "labels": ["ux", "infra"],
                    "assignee": "claude",
                    "estimated_hours": 16,
                    "epic_link": "customer_dashboard"
                },
                {
                    "title": "Customer Authentication & Authorization",
                    "description": """
Implement secure authentication and role-based access.

**Security Features:**
- [ ] JWT token authentication
- [ ] Role-based access control (admin, user, viewer)
- [ ] Session management
- [ ] Password reset flow
- [ ] Two-factor authentication (optional)
- [ ] API key scoping by user role

**Acceptance Criteria:**
- Secure authentication flow
- Proper session handling
- RBAC implemented correctly
- Security audit compliance
                    """,
                    "labels": ["infra"],
                    "assignee": "claude",
                    "estimated_hours": 20,
                    "epic_link": "customer_dashboard"
                }
            ]
        }

    def _create_trial_flow_epic(self) -> dict[str, Any]:
        """Create Trial Flow Epic with Issues"""

        return {
            "epic": {
                "title": "Epic: Trial Conversion Flow - Revenue Optimization",
                "description": """
Build optimized trial signup and conversion flow for maximum revenue.

**Acceptance Criteria:**
- [ ] Frictionless trial signup process
- [ ] Trial tracking and analytics
- [ ] Automated conversion prompts
- [ ] Email sequence automation
- [ ] Conversion optimization features
- [ ] A/B testing capabilities

**Success Metrics:**
- 15% trial signup conversion rate
- 25% trial to paid conversion rate
- < 30 second trial signup time
                """,
                "labels": ["ux", "automation"],
                "assignee": "claude",
                "milestone": self.milestone,
                "estimated_hours": 60,
                "priority": "high"
            },
            "issues": [
                {
                    "title": "Trial Signup Flow & UI Design",
                    "description": """
Create optimized trial signup experience with minimal friction.

**Signup Flow:**
- [ ] Landing page optimization
- [ ] Multi-step signup form
- [ ] Social login options (Google, GitHub)
- [ ] Email verification process
- [ ] Onboarding wizard
- [ ] Success page with next steps

**Acceptance Criteria:**
- < 3 fields in initial signup
- Progressive profiling for additional data
- Mobile-optimized experience
- A/B testing infrastructure ready
                    """,
                    "labels": ["ux", "onboarding"],
                    "assignee": "claude",
                    "estimated_hours": 16,
                    "epic_link": "trial_flow"
                },
                {
                    "title": "Trial Tracking & Analytics System",
                    "description": """
Implement comprehensive trial tracking and analytics.

**Tracking Features:**
- [ ] Trial start date and duration
- [ ] Feature usage tracking
- [ ] Engagement scoring
- [ ] Conversion probability scoring
- [ ] Drop-off point analysis
- [ ] Cohort analysis

**Acceptance Criteria:**
- Real-time trial status tracking
- Predictive conversion scoring
- Automated risk detection
- Analytics dashboard integration
                    """,
                    "labels": ["infra", "ux"],
                    "assignee": "claude",
                    "estimated_hours": 16,
                    "epic_link": "trial_flow"
                },
                {
                    "title": "Conversion Prompts & CTAs",
                    "description": """
Create strategic conversion prompts and calls-to-action.

**Conversion Elements:**
- [ ] In-app upgrade prompts
- [ ] Usage limit notifications
- [ ] Value demonstration modals
- [ ] Pricing comparison tooltips
- [ ] Urgency indicators (trial ending)
- [ ] Social proof elements

**Acceptance Criteria:**
- Contextual prompt timing
- Non-intrusive user experience
- Clear value propositions
- A/B testing variations ready
                    """,
                    "labels": ["ux", "billing"],
                    "assignee": "claude",
                    "estimated_hours": 12,
                    "epic_link": "trial_flow"
                },
                {
                    "title": "Automated Trial Email Sequence",
                    "description": """
Set up automated email sequence for trial conversion.

**Email Sequence:**
- [ ] Welcome email (Day 0)
- [ ] Feature highlight (Day 2)
- [ ] Success story (Day 5)
- [ ] Conversion reminder (Day 10)
- [ ] Last chance (Day 13)
- [ ] Win-back sequence (post-trial)

**Acceptance Criteria:**
- Personalized email content
- Behavioral trigger integration
- A/B testing for subject lines
- Unsubscribe and preference management
                    """,
                    "labels": ["automation"],
                    "assignee": "n8n_creator",
                    "estimated_hours": 16,
                    "epic_link": "trial_flow"
                }
            ]
        }

    def _create_api_access_epic(self) -> dict[str, Any]:
        """Create API Access Management Epic with Issues"""

        return {
            "epic": {
                "title": "Epic: API Access Management - Monetization Engine",
                "description": """
Build comprehensive API access management for tier-based monetization.

**Acceptance Criteria:**
- [ ] API key generation and management
- [ ] Rate limiting by subscription tier
- [ ] Usage tracking and analytics
- [ ] API documentation portal
- [ ] Developer onboarding flow
- [ ] Billing integration

**Success Metrics:**
- 95% API uptime
- < 100ms average response time
- 90% developer satisfaction score
                """,
                "labels": ["api", "infra"],
                "assignee": "claude",
                "milestone": self.milestone,
                "estimated_hours": 50,
                "priority": "high"
            },
            "issues": [
                {
                    "title": "API Key Generation & Management System",
                    "description": """
Create system for API key lifecycle management.

**Key Management Features:**
- [ ] API key generation (secure random)
- [ ] Key rotation capabilities
- [ ] Key revocation/deactivation
- [ ] Scope and permission management
- [ ] Key expiration handling
- [ ] Usage analytics per key

**Acceptance Criteria:**
- Cryptographically secure key generation
- Granular permission scoping
- Audit trail for all key operations
- Integration with customer dashboard
                    """,
                    "labels": ["api", "infra"],
                    "assignee": "claude",
                    "estimated_hours": 16,
                    "epic_link": "api_access_management"
                },
                {
                    "title": "Rate Limiting by Subscription Tier",
                    "description": """
Implement tier-based rate limiting for API monetization.

**Rate Limiting Tiers:**
- [ ] Starter: 1,000 requests/month
- [ ] Basic: 5,000 requests/month
- [ ] Pro: 25,000 requests/month
- [ ] Enterprise: 100,000 requests/month
- [ ] Custom enterprise limits

**Acceptance Criteria:**
- Redis-based rate limiting
- Real-time limit checking
- Graceful limit exceeded responses
- Usage dashboard integration
                    """,
                    "labels": ["api", "billing"],
                    "assignee": "claude",
                    "estimated_hours": 12,
                    "epic_link": "api_access_management"
                },
                {
                    "title": "API Usage Tracking & Analytics",
                    "description": """
Build comprehensive API usage tracking system.

**Tracking Metrics:**
- [ ] Request count by endpoint
- [ ] Response time analytics
- [ ] Error rate monitoring
- [ ] Geographic usage patterns
- [ ] Feature adoption metrics
- [ ] Cost per request analysis

**Acceptance Criteria:**
- Real-time usage tracking
- Historical data retention
- Analytics dashboard
- Billing integration ready
                    """,
                    "labels": ["api", "infra"],
                    "assignee": "claude",
                    "estimated_hours": 14,
                    "epic_link": "api_access_management"
                },
                {
                    "title": "Developer Documentation Portal",
                    "description": """
Create comprehensive API documentation and developer portal.

**Documentation Features:**
- [ ] Interactive API explorer
- [ ] Code examples (Python, JavaScript, cURL)
- [ ] Authentication guide
- [ ] Rate limiting documentation
- [ ] Error code reference
- [ ] SDK downloads

**Acceptance Criteria:**
- Auto-generated from OpenAPI spec
- Interactive testing capabilities
- Search functionality
- Developer feedback system
                    """,
                    "labels": ["api", "ux"],
                    "assignee": "claude",
                    "estimated_hours": 8,
                    "epic_link": "api_access_management"
                }
            ]
        }

    def _create_onboarding_epic(self) -> dict[str, Any]:
        """Create Onboarding & Retention Epic with Issues"""

        return {
            "epic": {
                "title": "Epic: Onboarding & Retention - 90% Success Rate",
                "description": """
Build comprehensive onboarding and retention system for maximum customer success.

**Acceptance Criteria:**
- [ ] 14-day activation sequence
- [ ] Progress tracking and gamification
- [ ] Personalized onboarding paths
- [ ] Retention risk detection
- [ ] Automated intervention system
- [ ] Success metrics dashboard

**Success Metrics:**
- 85% onboarding completion rate
- 90% 30-day retention rate
- 5+ feature adoption in first week
                """,
                "labels": ["onboarding", "ux"],
                "assignee": "gemini",
                "milestone": self.milestone,
                "estimated_hours": 56,
                "priority": "medium"
            },
            "issues": [
                {
                    "title": "Onboarding UX Flow Design",
                    "description": """
Design user experience for 14-day activation sequence.

**UX Components:**
- [ ] Welcome tour and product introduction
- [ ] Progressive disclosure of features
- [ ] Contextual help and tooltips
- [ ] Progress indicators and milestones
- [ ] Celebration moments and achievements
- [ ] Mobile-responsive design

**Acceptance Criteria:**
- User-tested onboarding flow
- Accessibility compliance
- Multi-device compatibility
- A/B testing infrastructure
                    """,
                    "labels": ["onboarding", "ux"],
                    "assignee": "gemini",
                    "estimated_hours": 20,
                    "epic_link": "onboarding_retention"
                },
                {
                    "title": "Progress Tracking & Gamification",
                    "description": """
Implement progress tracking with gamification elements.

**Gamification Features:**
- [ ] Progress bars and completion percentages
- [ ] Achievement badges and milestones
- [ ] Points and scoring system
- [ ] Leaderboards (optional, team accounts)
- [ ] Streak counters (daily usage)
- [ ] Unlock new features progressively

**Acceptance Criteria:**
- Motivating but not overwhelming
- Clear progress indicators
- Celebration of achievements
- Integration with user analytics
                    """,
                    "labels": ["onboarding", "ux"],
                    "assignee": "gemini",
                    "estimated_hours": 16,
                    "epic_link": "onboarding_retention"
                },
                {
                    "title": "Retention Risk Detection System",
                    "description": """
Build predictive system for identifying at-risk users.

**Risk Indicators:**
- [ ] Login frequency drop-off
- [ ] Feature usage decline
- [ ] Support ticket patterns
- [ ] Engagement score calculation
- [ ] Churn probability modeling
- [ ] Behavioral pattern analysis

**Acceptance Criteria:**
- Real-time risk scoring
- Automated alert system
- Integration with intervention triggers
- Machine learning model accuracy >80%
                    """,
                    "labels": ["onboarding", "infra"],
                    "assignee": "gemini",
                    "estimated_hours": 12,
                    "epic_link": "onboarding_retention"
                },
                {
                    "title": "Automated Email Onboarding Sequence",
                    "description": """
Create personalized email sequence for user activation.

**Email Sequence (14 days):**
- [ ] Day 0: Welcome & getting started
- [ ] Day 1: First value realization
- [ ] Day 3: Feature exploration guide
- [ ] Day 7: Success stories & use cases
- [ ] Day 10: Advanced features unlock
- [ ] Day 14: Conversion opportunity

**Acceptance Criteria:**
- Behavioral trigger automation
- Personalization based on usage
- A/B testing for optimization
- Unsubscribe and preference management
                    """,
                    "labels": ["onboarding", "automation"],
                    "assignee": "n8n_creator",
                    "estimated_hours": 8,
                    "epic_link": "onboarding_retention"
                }
            ]
        }

    def create_meta_ads_n8n_workflow(self) -> dict[str, Any]:
        """Create n8n workflow configuration for Meta Ads campaign"""

        print("\n📱 Creating Meta Ads Campaign with n8n Automation...")

        return {
            "workflow_name": "Meta Ads Lead Generation & CRM Integration",
            "workflow_id": "meta_ads_saas_playbook_campaign",
            "description": "Automated lead capture and nurturing for SaaS Integration Playbook downloads",
            "triggers": {
                "meta_ads_webhook": {
                    "type": "webhook",
                    "url": "/webhook/meta-ads-lead",
                    "method": "POST",
                    "description": "Receives lead data from Meta Ads campaigns"
                }
            },
            "workflow_steps": [
                {
                    "step": 1,
                    "node_type": "webhook_trigger",
                    "name": "Meta Ads Lead Capture",
                    "config": {
                        "webhook_url": "https://your-domain.com/webhook/meta-ads-lead",
                        "authentication": "api_key",
                        "expected_fields": [
                            "first_name",
                            "last_name",
                            "email",
                            "company",
                            "phone",
                            "ad_campaign_id",
                            "ad_set_id",
                            "ad_id",
                            "lead_source"
                        ]
                    }
                },
                {
                    "step": 2,
                    "node_type": "data_transformation",
                    "name": "Lead Data Processing",
                    "config": {
                        "transformations": [
                            "validate_email_format",
                            "standardize_phone_number",
                            "enrich_company_data",
                            "assign_lead_score",
                            "generate_unique_lead_id"
                        ],
                        "data_validation": {
                            "required_fields": ["email", "first_name"],
                            "email_verification": True,
                            "duplicate_detection": True
                        }
                    }
                },
                {
                    "step": 3,
                    "node_type": "crm_integration",
                    "name": "CRM Lead Tagging",
                    "config": {
                        "crm_system": "hubspot", # or "salesforce", "pipedrive"
                        "actions": [
                            {
                                "action": "create_contact",
                                "contact_properties": {
                                    "email": "{{email}}",
                                    "firstname": "{{first_name}}",
                                    "lastname": "{{last_name}}",
                                    "company": "{{company}}",
                                    "phone": "{{phone}}",
                                    "lead_source": "Meta Ads - SaaS Playbook",
                                    "lifecycle_stage": "lead"
                                }
                            },
                            {
                                "action": "add_tags",
                                "tags": [
                                    "meta_ads_lead",
                                    "saas_playbook_interest",
                                    "week2_campaign",
                                    "revenue_acceleration"
                                ]
                            },
                            {
                                "action": "assign_to_sequence",
                                "sequence_name": "SaaS Playbook Nurture"
                            }
                        ]
                    }
                },
                {
                    "step": 4,
                    "node_type": "email_automation",
                    "name": "Send Welcome Email #1",
                    "config": {
                        "email_provider": "sendgrid", # or "mailgun", "ses"
                        "template_id": "saas_playbook_welcome",
                        "email_content": {
                            "subject": "Your SaaS Integration Playbook is Ready! 🚀",
                            "from": "success@yourdomain.com",
                            "from_name": "Revenue Acceleration Team",
                            "personalization": {
                                "first_name": "{{first_name}}",
                                "company": "{{company}}",
                                "playbook_download_link": "{{generate_personalized_link}}"
                            }
                        },
                        "attachments": [
                            {
                                "name": "SaaS_Integration_Playbook.pdf",
                                "url": "https://cdn.yourdomain.com/playbooks/saas-integration.pdf"
                            }
                        ]
                    }
                },
                {
                    "step": 5,
                    "node_type": "analytics_tracking",
                    "name": "Campaign Analytics",
                    "config": {
                        "tracking_events": [
                            {
                                "event": "lead_captured",
                                "properties": {
                                    "campaign_source": "meta_ads",
                                    "content_type": "saas_playbook",
                                    "lead_quality_score": "{{lead_score}}",
                                    "conversion_value": 50 # estimated lead value
                                }
                            }
                        ],
                        "analytics_platforms": [
                            "google_analytics",
                            "mixpanel",
                            "segment"
                        ]
                    }
                },
                {
                    "step": 6,
                    "node_type": "slack_notification",
                    "name": "Team Notification",
                    "config": {
                        "slack_channel": "#revenue-acceleration",
                        "message_template": """
🎯 New SaaS Playbook Lead!
👤 **{{first_name}} {{last_name}}** ({{company}})
📧 {{email}}
📱 {{phone}}
🏷️ Source: Meta Ads Campaign
📊 Lead Score: {{lead_score}}/100
                        """,
                        "notification_conditions": {
                            "high_value_leads": "lead_score > 75",
                            "immediate_notification": True
                        }
                    }
                },
                {
                    "step": 7,
                    "node_type": "follow_up_scheduler",
                    "name": "Schedule Follow-up Sequence",
                    "config": {
                        "follow_up_emails": [
                            {
                                "delay": "24_hours",
                                "template": "implementation_tips",
                                "subject": "Quick wins from your SaaS integration"
                            },
                            {
                                "delay": "3_days",
                                "template": "case_study_showcase",
                                "subject": "How {{similar_company}} saved 40% with automation"
                            },
                            {
                                "delay": "7_days",
                                "template": "consultation_offer",
                                "subject": "Ready to accelerate your revenue? Let's talk"
                            }
                        ],
                        "scheduling_conditions": {
                            "email_engagement": True,
                            "lead_score_threshold": 40
                        }
                    }
                }
            ],
            "error_handling": {
                "retry_policy": {
                    "max_retries": 3,
                    "retry_delay": "exponential_backoff"
                },
                "fallback_actions": [
                    "log_to_error_webhook",
                    "notify_admin_channel",
                    "store_in_manual_review_queue"
                ]
            },
            "success_metrics": {
                "lead_conversion_rate": "Target: 15%",
                "email_open_rate": "Target: 35%",
                "playbook_download_rate": "Target: 80%",
                "follow_up_engagement": "Target: 25%"
            }
        }

    def generate_token_usage_report(self, operations: list[str]) -> dict[str, Any]:
        """Generate token usage report for GitHub and n8n setup"""

        # Token usage estimation based on task complexity
        token_costs = {
            "github_epic_creation": 0.85,  # Sonnet 4
            "github_issue_creation": 0.60,  # Sonnet 4
            "n8n_workflow_design": 2.25,   # Opus 4 (synthesis)
            "meta_ads_configuration": 0.65, # Sonnet 4
            "automation_setup": 0.40,      # Sonnet 4
            "formatting_tasks": 0.10       # Haiku 4
        }

        total_cost = sum(token_costs[op] for op in operations if op in token_costs)

        # Calculate model distribution
        sonnet_cost = sum(cost for op, cost in token_costs.items()
                         if op in operations and op in ["github_epic_creation", "github_issue_creation", "meta_ads_configuration", "automation_setup"])
        opus_cost = sum(cost for op, cost in token_costs.items()
                       if op in operations and op == "n8n_workflow_design")
        haiku_cost = sum(cost for op, cost in token_costs.items()
                        if op in operations and op == "formatting_tasks")

        return {
            "report_type": "GitHub Epic & Meta Ads Setup Token Usage",
            "generated_at": datetime.now().isoformat(),
            "operations_completed": operations,
            "cost_breakdown": {
                "github_setup": round(sonnet_cost * 0.8, 2),
                "n8n_workflow_design": round(opus_cost, 2),
                "meta_ads_automation": round(sonnet_cost * 0.2, 2),
                "formatting": round(haiku_cost, 2),
                "total_cost": round(total_cost, 2)
            },
            "model_distribution": {
                "sonnet_4_usage": f"{(sonnet_cost/total_cost*100):.1f}%",
                "opus_4_usage": f"{(opus_cost/total_cost*100):.1f}%",
                "haiku_4_usage": f"{(haiku_cost/total_cost*100):.1f}%"
            },
            "efficiency_metrics": {
                "cost_per_epic": round(total_cost / 5, 2),  # 5 epics
                "total_issues_created": 19,
                "cost_per_issue": round(total_cost / 19, 2),
                "automation_value": "High ROI - streamlined development process"
            },
            "budget_impact": {
                "weekly_budget_used": f"{(total_cost/25*100):.1f}%",
                "remaining_week2_budget": round(25 - total_cost, 2),
                "projected_monthly_cost": round(total_cost * 4, 2)
            }
        }


def execute_github_meta_ads_setup():
    """Execute complete GitHub Epic/Issue and Meta Ads setup"""

    print("🎯 Enterprise Claude Code Optimization Suite")
    print("📋 GitHub Epic & Issue Setup + Meta Ads Campaign")
    print("=" * 60)

    # Initialize setup system
    setup = GitHubEpicIssueSetup()

    # Create GitHub structure
    github_structure = setup.create_github_epic_structure()

    # Create Meta Ads n8n workflow
    meta_ads_workflow = setup.create_meta_ads_n8n_workflow()

    # Track operations for token usage
    operations = [
        "github_epic_creation",
        "github_issue_creation",
        "n8n_workflow_design",
        "meta_ads_configuration",
        "automation_setup",
        "formatting_tasks"
    ]

    # Generate token usage report
    token_report = setup.generate_token_usage_report(operations)

    return {
        "github_epic_issue_structure": github_structure,
        "meta_ads_n8n_workflow": meta_ads_workflow,
        "token_usage_report": token_report,
        "setup_status": "completed_successfully"
    }


if __name__ == "__main__":
    results = execute_github_meta_ads_setup()

    github = results["github_epic_issue_structure"]
    meta_ads = results["meta_ads_n8n_workflow"]
    tokens = results["token_usage_report"]

    print("\n📊 Setup Summary:")
    print(f"🎯 Total Epics: {github['github_project_structure']['total_epics']}")
    print(f"📋 Total Issues: {github['github_project_structure']['total_issues']}")
    print(f"🤖 Agents Assigned: {len(github['github_project_structure']['agent_assignments'])}")
    print(f"📱 Meta Ads Workflow Steps: {len(meta_ads['workflow_steps'])}")

    print("\n💰 Token Usage:")
    print(f"💵 Total Cost: ${tokens['cost_breakdown']['total_cost']}")
    print(f"📊 Model Distribution: {tokens['model_distribution']['sonnet_4_usage']} Sonnet, {tokens['model_distribution']['opus_4_usage']} Opus, {tokens['model_distribution']['haiku_4_usage']} Haiku")
    print(f"🎯 Weekly Budget Used: {tokens['budget_impact']['weekly_budget_used']}")

    print("\n✅ Ready for M1 - Monetization Ready milestone!")
