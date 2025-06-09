# 🧹 MAJOR PROJECT CLEANUP PLAN

## Current State: DISASTER 🚨
- 20+ Python scripts in root directory
- 15+ .md files scattered everywhere  
- Outdated documentation (SaaS Growth Dispatch?)
- Inconsistent naming conventions
- High cognitive load for developers
- Confusing for Claude Code context

## Target State: ORGANIZED ✨
- Clean root directory with only essential files
- Organized documentation in docs/
- Archived legacy files
- Updated and accurate README
- Clear project structure

## Phase 1: Root Directory Cleanup

### Move to Archive (Legacy Files):
```
archive/legacy/
├── autonomous_cto_execution.py
├── demo_email_campaign.py
├── demo_revenue_deployment.py
├── execute_first_dollar_mission.py
├── execute_revenue_deployment.py
├── execute_revenue_strategy.py
├── real_stripe_client.py
├── real_stripe_dashboard.py
├── setup_production_environment.py
└── deploy_n8n_automation_production.py
```

### Move to Scripts Directory:
```
scripts/deployment/
├── setup_production_environment.py
└── deploy_n8n_automation_production.py

scripts/revenue/
├── execute_revenue_deployment.py
├── execute_revenue_strategy.py
└── real_stripe_client.py
```

### Consolidate Documentation:
```
docs/
├── README.md (keep updated)
├── ARCHITECTURE.md (combine architecture docs)
├── DEPLOYMENT.md (combine deployment docs)
├── BUSINESS_MODEL.md (update business model)
└── archive/
    ├── old-readmes/
    └── outdated-plans/
```

## Phase 2: Update Core Files

### Fix README.md:
- Update project description (what does this actually do?)
- Remove outdated revenue claims
- Add clear setup instructions
- Link to proper documentation

### Fix Wiki:
- Update "SaaS Growth Dispatch" to actual project name
- Update architecture diagram
- Remove outdated roadmap items
- Clean up technologies list

### Update pyproject.toml:
- Verify dependencies are current
- Remove unused dependencies
- Update project metadata

## Phase 3: File Organization

### Root Directory (ONLY):
```
/
├── README.md
├── pyproject.toml
├── Makefile
├── .env.template
├── .gitignore
├── app/
├── scripts/
├── tests/
├── docs/
├── data/
└── archive/
```

### Archive Structure:
```
archive/
├── legacy-scripts/
├── outdated-docs/
├── old-configs/
└── deprecated-features/
```

## Phase 4: Documentation Audit

### Questions to Answer:
1. What does this project actually do TODAY?
2. What revenue claims are accurate?
3. Which features are actively used?
4. What's the current tech stack?
5. How do users actually run this?

### Actions:
- Rewrite README from scratch
- Update all documentation
- Fix Wiki completely
- Remove outdated claims
- Add accurate setup guide

## Success Metrics:
- Root directory: <10 files
- Documentation: Accurate and current
- Clear project purpose
- Easy onboarding for new developers
- Reduced cognitive load
- Better Claude Code context

## Estimated Impact:
- 80% reduction in root directory files
- 90% more accurate documentation
- 50% faster onboarding
- Much cleaner Git Worktree experience