# Autotask AI Product Roadmap

## Purpose

Autotask AI is an internal technician assistant that pulls read-only ticket history from Autotask, cleans and indexes that history, finds relevant past tickets, and uses a local CPU-based AI model to help technicians answer questions and find likely solutions.

This roadmap keeps the project focused on three outcomes:

1. Make technicians faster.
2. Improve long-term customer service.
3. Keep customer data local and usable without a GPU.

Roadmap entries require normal requirements discovery, security review, approval, implementation, and validation before development begins.

## Current Foundation

The repository already contains the following foundation:

- Read-only Autotask company, ticket, and ticket-note synchronization.
- Local PostgreSQL and pgvector storage.
- Ticket and note document creation.
- Local Ollama embeddings and CPU-only answer generation.
- Retrieval of relevant past tickets before an answer is produced.
- Noise filtering for alerts, surveys, automated messages, and other low-value content.
- Recurring-issue analytics.
- Technician web interface and operations scheduling.
- Guardrails that separate ticket-history evidence from general guidance.

## Roadmap Priorities

### 1. Real-Time Technician Updates

Add a WebSocket-based update channel so the application can notify technicians without requiring a browser refresh.

Possible events include:

- A ticket was assigned or reassigned.
- A customer added a response.
- A ticket status or priority changed.
- Another technician updated the ticket.
- An AI summary or analysis finished.
- A scheduled sync or knowledge job completed or failed.

Primary benefit: faster awareness and less time spent refreshing or repeatedly checking Autotask.

### 2. Redis Caching

Add Redis for short-lived caching of frequently requested or expensive results.

Initial cache candidates include:

- Ticket summaries.
- Similar-ticket search results.
- Common technician questions.
- Customer ticket-history summaries.
- Dashboard and operations status data.
- Completed AI answers that are safe to reuse.

Primary benefit: faster responses, fewer repeated database searches, and fewer repeated local AI calls on CPU-only hardware.

### 3. Predictive Service Intelligence

Add a scoring layer that uses past ticket outcomes to make practical predictions without requiring a large GPU model.

Possible predictions include:

- Most likely cause of a new issue.
- Most successful fix used on similar tickets.
- Expected time to resolve.
- Likelihood that escalation will be required.
- Likelihood that the issue is part of a wider outage or recurring customer problem.
- Recommended documentation, vendor, or internal specialist.

The first version should use explainable rules, ticket similarity, counts, and lightweight statistical models. A prediction must show the evidence behind it and must not be presented as certain.

Primary benefit: technicians receive useful next-step suggestions before spending time manually searching old tickets.

### 4. Automated Ticket Routing

Add technician assignment recommendations based on:

- Technician skills and past successful work.
- Current workload and availability.
- Customer familiarity.
- Ticket category and priority.
- Similar-ticket history.
- Escalation requirements.

The first version should recommend an assignee rather than automatically changing Autotask. Automatic assignment should remain a later, separately approved option.

Primary benefit: the right technician sees the right ticket sooner.

### 5. Ticket Health Analytics

Add clear ticket-health information and technician questions covering:

- How many days a ticket has been open.
- Total labor hours entered against the ticket.
- Time since the last technician update.
- Time waiting on the customer, vendor, or technician.
- Number of technicians involved.
- Number of customer responses.
- SLA risk and overdue status.
- Tickets with unusually high labor compared with similar tickets.

Example questions:

- Which tickets have been open longer than 30 days?
- Which tickets have more than 20 labor hours?
- Which tickets have stopped moving?
- Which customers are consuming the most support time?

Before implementation, confirm that the required Autotask ticket, time-entry, status-history, and SLA fields are included in the read-only extraction design.

Primary benefit: technicians and managers can identify stalled, expensive, or at-risk tickets quickly.

### 6. Technician Performance Assistant

Expand the assistant from ticket search into guided troubleshooting.

Possible capabilities include:

- Suggest the next troubleshooting step.
- Recommend related tickets and internal documents.
- Identify steps that appear to be missing.
- Warn when symptoms match a known outage.
- Recommend escalation when prior similar tickets required it.
- Produce a customer-ready update for technician review.
- Produce a clean internal work-note draft for technician review.

All suggestions must remain reviewable by the technician before being written back to Autotask.

Primary benefit: more consistent troubleshooting and documentation.

### 7. Customer Success Intelligence

Use ticket history to identify long-term customer needs rather than only responding to individual tickets.

Possible outputs include:

- Customers with increasing ticket volume.
- Repeated issues by customer, device, location, or service.
- Systems that may need replacement or redesign.
- Training opportunities for customer staff.
- Preventative maintenance recommendations.
- Potential standards, documentation, or project work that would reduce future tickets.
- Customer health summaries for account reviews.

Primary benefit: move support from reactive ticket handling toward proactive customer improvement.

### 8. Local CPU AI Optimization

Keep the architecture local-first and CPU-capable.

Required design principles include:

- Retrieve strong matching evidence before asking the AI model to write an answer.
- Prefer rules, database calculations, similarity scoring, and lightweight models when they solve the problem well.
- Cache safe repeated results.
- Use smaller local models for normal technician requests.
- Offer a slower deep-dive path only when more detailed generation is needed.
- Refuse or clearly qualify answers when matching ticket evidence is weak.
- Keep cloud-model support optional and sanitized if it is added later.

Primary benefit: useful local AI without requiring GPU hardware or exposing customer ticket data.

## Recommended Delivery Order

### Near Term

1. Confirm ticket-age, time-entry, status-history, and SLA fields available through the existing read-only Autotask connection.
2. Ticket health analytics.
3. Redis caching.
4. Real-time technician updates.

### Next

5. Technician performance assistant.
6. Customer success intelligence.

### Later

7. Predictive service intelligence.
8. Automated ticket routing recommendations.
9. Separately evaluate approved automatic routing only after recommendation accuracy is proven.

## Success Measures

Future roadmap work should be measured using practical results such as:

- Reduced average technician search time.
- Reduced time to first useful action.
- Reduced ticket resolution time.
- Reduced repeat tickets for the same issue.
- Increased use of known successful fixes.
- Reduced number of stalled or overdue tickets.
- Reduced repeated CPU AI work through caching.
- Technician acceptance and correction rates for AI suggestions.
- Customer issues identified proactively before they become repeated tickets.
