# Synthetic Data Rules

The dataset is intentionally synthetic but should behave like a plausible life-insurance Agency portfolio.

## Scale
Default generated portfolio:
- 12 agency units
- 400 agents
- 25,000 customers
- ~70,000 leads
- 35,000 policies
- several hundred thousand premium-payment records
- monthly targets for active periods
- policy status history
- incentive records

## Uganda geography
Agency units are distributed across Kampala, Wakiso/Entebbe, Jinja, Mbarara, Gulu, Mbale and Fort Portal, grouped into Central, Eastern, Western and Northern regions.

## Agent behaviour
Agents are assigned latent performance profiles:
- **Star**: high conversion, high production, high persistency
- **High-volume risk**: high production, weaker persistency
- **Steady**: moderate production and healthy persistency
- **Developing**: lower conversion and lower production
- **Inactive-risk**: low current activity / higher exit probability

This creates real analytical structure instead of fully random rows.

## Customer behaviour
Customers vary by:
- age
- region
- occupation
- income band
- product preference
- payment frequency
- premium affordability

Higher premium burden, repeated late payments, low tenure and certain agent profiles increase lapse probability.

## Products
Fictional product categories:
- Protection Plus
- Education Builder
- Family Income Plan
- Savings Growth
- Retirement Secure

No real Jubilee product terms are reproduced.

## Premium ranges
Premiums are generated in UGX with frequency-specific installment values. Annualized premium is calculated consistently from payment frequency.

## Policy statuses
Possible current statuses:
- Active
- Grace
- Lapsed
- Surrendered
- Matured
- Cancelled

The generator deliberately creates realistic differences by agent profile and payment behaviour.

## Payment behaviour
Installments can be:
- Paid on time
- Late
- Partial
- Missed

Riskier policies accumulate more late/missed payments before lapse.

## Persistency signal
The synthetic dataset is designed so that:
- Star agents have stronger persistency
- High-volume-risk agents can lead on sales but underperform on persistency
- Some agency units have deliberately weaker performance
- Higher missed-payment counts correlate with lapse

## Phase 2 chronology and validation

The initial generator had measured chronology defects; see
[the baseline validation](phase2_baseline.md). Phase 2 now constrains recruitment
by unit launch, sales by agent service dates, onboarding by first issued business,
and incentive participation by overlapping service. Converted leads require contact.
Future simulated receipts are recorded as unpaid at the fixed snapshot rather
than treated as collected cash. Maturity uses calendar-year anniversaries.

Paid allows zero to two days after the due date; Late exceeds that tolerance.
Missed means unpaid as of the snapshot, including recently due installments, and
does not by itself mean contractual delinquency. Fixed-day installment schedules,
simulated incentive qualification, and profile-driven lapse remain modelling
limitations. In particular, lapse is not derived from a contractual arrears engine;
claims above about intended behaviour must be tested before analytical use.

The generator writes a manifest containing seed 42, snapshot 2026-09-01 and hashes.
The loader rejects a stale or edited manifest. Validation and the report are
reproducible using [the Phase 2 workflow](phase2_workflow.md).

## Ethics and privacy
All identifiers and records are synthetic. No names, phone numbers, emails or sensitive real-person identifiers are generated.
