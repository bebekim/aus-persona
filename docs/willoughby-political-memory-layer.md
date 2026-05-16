# Willoughby Political Memory Layer

This layer adds local democratic context beside the ABS-derived persona frame.
It is designed for policy makers, councillors, a mayoral office, and council
staff who need to ask: what has this community already voted on, debated,
proposed, approved, rejected, or deferred?

The layer is source-backed. It must not invent political facts through persona
generation. Synthetic residents can be matched to issues, places, services, and
demographic cohorts, but they must never be described as real voters,
submitters, meeting attendees, or named constituents unless a verified source
record supports that claim.

## Source Families

The starter source registry lives in:

`dbt/aus_personas/seeds/local_political_memory/willoughby_political_sources.csv`

| Family | Primary authority | Intended coverage |
| --- | --- | --- |
| `election_results` | NSW Electoral Commission | Mayoral and ward councillor election contests |
| `meeting_votes` | Willoughby City Council | Council meeting items, motions, outcomes, and named votes where recorded |
| `notices_of_motion` | Willoughby City Council | Councillor-sponsored formal proposals inside agendas and minutes |
| `planning_determinations` | Willoughby Local Planning Panel | Development application determinations and panel statements |

The election timeline should use the actual NSW local government election
cycles. For Willoughby, the modern sequence is 2004, 2008, 2012, 2017, 2021,
and 2024. The 2020 ordinary election was postponed and held in December 2021.

## Event Contracts

The normalized event contracts live in:

`dbt/aus_personas/seeds/local_political_memory/willoughby_political_event_contracts.csv`

The first marts should use these grains:

| Mart | Grain | Why it matters |
| --- | --- | --- |
| `fct_local_election_contest` | One election contest per council year and contest scope | Timeline of mayoral and ward contests |
| `fct_local_election_candidate_result` | One candidate or group result in one contest | Representation and electoral competition context |
| `fct_council_meeting_item` | One agenda or minutes item | Policy, budget, service, and governance memory |
| `fct_councillor_vote` | One councillor's recorded position on one item | Accountability where named votes are recorded |
| `fct_notice_of_motion` | One formal councillor-sponsored proposal | Councillor advocacy and policy agenda setting |
| `fct_planning_determination` | One application or panel determination | Built-environment change separated from ordinary voting |
| `bridge_policy_issue_persona` | One source event mapped to one issue tag | Links political records to synthetic persona cohorts |

## Persona Use Cases

- **Mayor briefing:** show which resident cohorts are affected by a decision,
  what prior council actions relate to the issue, and which SA2s are most
  exposed.
- **Councillor preparation:** summarize ward-level community profiles against
  past motions, budget decisions, and unresolved service issues.
- **Policy design:** stress-test a proposed policy against synthetic households
  while grounding the policy history in real minutes and election records.
- **Public consultation planning:** identify which cohorts may need different
  engagement channels, then connect those cohorts to relevant prior local
  debates.
- **Planning context:** connect development applications and panel
  determinations to local housing, transport, accessibility, and amenity
  personas without implying a councillor vote occurred.

## Guardrails

1. Keep source records and generated persona prose in separate tables.
2. Store `source_id`, source URL, authority, and extraction timestamp on every
   harvested fact.
3. Treat missing named votes as unknown, not unanimous.
4. Separate council decisions from Local Planning Panel determinations.
5. Use demographic and geographic matching only at cohort level. Do not assign
   a synthetic person a real voting history.
6. Preserve the difference between evidence and interpretation. Issue tags and
   persona impacts are annotations, not primary facts.

## Ingestion Order

1. Load source registry and event contracts as dbt seeds.
2. Harvest NSW Electoral Commission results for 2024, 2021, 2017, 2012, and
   2008. Treat 2004 as an archive/manual-research lane unless an official
   machine-readable source is found.
3. Harvest council meeting agenda/minute indexes into meeting item records.
4. Parse Notices of Motion from the meeting items.
5. Parse named votes only when the minutes explicitly record them.
6. Harvest Willoughby Local Planning Panel determinations separately.
7. Add curated issue tags such as housing, transport, open space, tree canopy,
   rates, active transport, accessibility, and community facilities.

The useful first demo is not a complete scraper. It is a traceable memory card:
for any proposed mayoral or council policy, show the relevant source records,
affected local persona cohorts, and clear uncertainty where the public record is
silent.
