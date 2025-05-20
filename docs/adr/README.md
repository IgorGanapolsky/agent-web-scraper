# Architecture Decision Records (ADR)

This directory contains Architecture Decision Records (ADRs) for the Agent Web Scraper project.

## What is an ADR?

An Architecture Decision Record is a document that captures an important architectural decision made along with its context and consequences.

## ADR Structure

Each ADR follows this structure:

```markdown
# [short title of solved problem and solution]

- **Status**: [proposed | accepted | deprecated | superseded]
- **Date**: YYYY-MM-DD

## Context and Problem Statement

[Describe the context and problem statement, e.g., in free form using two to three sentences.]

## Decision Drivers

* [driver 1, e.g., a force, facing concern, ...]
* [driver 2, e.g., a force, facing concern, ...]
* ...

## Considered Options

* [option 1]
* [option 2]
* [option 3]

## Decision Outcome

Chosen option: "[option 1]"

### Positive Consequences

* [e.g., improvement of quality attribute satisfaction, follow-up decisions required, ...]

### Negative Consequences

* [e.g., compromising other quality attributes, follow-up decisions required, ...]

## Pros and Cons of the Options

### [option 1]

* Good, because [argument a]
* Good, because [argument b]
* Bad, because [argument c]

### [option 2]

* Good, because [argument a]
* Good, because [argument b]
* Bad, because [argument c]

## Links

* [Link type] [Link to ADR] <!-- example: Refined by [ADR-0005](0005-example.md) -->
```

## ADR List

1. [0001-use-playwright-for-web-scraping.md](0001-use-playwright-for-web-scraping.md)
2. [0002-google-sheets-integration.md](0002-google-sheets-integration.md)
3. [0003-async-architecture.md](0003-async-architecture.md)
