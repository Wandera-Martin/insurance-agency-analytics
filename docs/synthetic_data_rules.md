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

## Data-quality learning
The clean v1 generator respects keys and date logic. Separate quality-check SQL is supplied. Future exercises can intentionally inject duplicates, missing values and category inconsistencies for data-quality practice.

## Ethics and privacy
All identifiers and records are synthetic. No names, phone numbers, emails or sensitive real-person identifiers are generated.
