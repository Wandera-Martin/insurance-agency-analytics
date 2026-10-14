from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from dataset import manifest

SEED = 42

AS_OF = date(2026, 9, 1)
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw"


def rand_date(start: date, end: date) -> date:
    days = (end - start).days
    if days < 0:
        raise ValueError("No valid dates in the requested interval")
    return start + timedelta(days=random.randint(0, days))


def main() -> None:
    """Generate the same nine synthetic datasets with the pinned environment."""
    random.seed(SEED)
    np.random.seed(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    agency_specs = [
        ("U001", "Kampala Central", "Kampala", "Kampala", "Central", 1.15),
        ("U002", "Kampala East", "Kampala", "Kampala", "Central", 0.86),
        ("U003", "Kampala North", "Kampala", "Kampala", "Central", 1.00),
        ("U004", "Wakiso", "Wakiso", "Wakiso", "Central", 0.98),
        ("U005", "Entebbe", "Entebbe", "Wakiso", "Central", 1.02),
        ("U006", "Jinja", "Jinja", "Jinja", "Eastern", 1.05),
        ("U007", "Mbale", "Mbale", "Mbale", "Eastern", 0.95),
        ("U008", "Mbarara", "Mbarara", "Mbarara", "Western", 1.10),
        ("U009", "Fort Portal", "Fort Portal", "Kabarole", "Western", 1.00),
        ("U010", "Gulu", "Gulu", "Gulu", "Northern", 0.92),
        ("U011", "Lira", "Lira", "Lira", "Northern", 0.94),
        ("U012", "Masaka", "Masaka", "Masaka", "Central", 1.03),
    ]
    agency_units = []
    for i, (uid, name, branch, district, region, factor) in enumerate(agency_specs, 1):
        agency_units.append(
            {
                "agency_unit_id": uid,
                "agency_name": name,
                "branch": branch,
                "district": district,
                "region": region,
                "manager_id": f"M{i:03d}",
                "launch_date": rand_date(date(2018, 1, 1), date(2024, 1, 1)),
                "status": "Active",
                "unit_factor": factor,
            }
        )
    agency_df = pd.DataFrame(agency_units)
    agency_df.drop(columns=["unit_factor"]).to_csv(OUT / "agency_units.csv", index=False)

    profiles = {
        "Star": {"weight": 0.18, "conv": 0.30, "lapse": 0.055, "prod": 1.45},
        "High-volume risk": {"weight": 0.12, "conv": 0.33, "lapse": 0.22, "prod": 1.55},
        "Steady": {"weight": 0.42, "conv": 0.22, "lapse": 0.10, "prod": 1.00},
        "Developing": {"weight": 0.20, "conv": 0.13, "lapse": 0.15, "prod": 0.68},
        "Inactive-risk": {"weight": 0.08, "conv": 0.07, "lapse": 0.18, "prod": 0.40},
    }
    pnames = list(profiles)
    pweights = [profiles[p]["weight"] for p in pnames]

    agents = []
    for i in range(1, 401):
        unit = random.choice(agency_specs)
        profile = random.choices(pnames, weights=pweights, k=1)[0]
        launch = next(u["launch_date"] for u in agency_units if u["agency_unit_id"] == unit[0])
        join = rand_date(max(date(2021, 1, 1), launch), date(2026, 5, 31))
        status = random.choices(["Active", "Inactive", "Exited"], weights=[0.82, 0.10, 0.08], k=1)[
            0
        ]
        exit_date = None
        if status == "Exited":
            exit_date = rand_date(join + timedelta(days=90), AS_OF)
        exp = max(0, (AS_OF - join).days / 365.25)
        grade = (
            "Trainee"
            if exp < 0.5
            else "Junior"
            if exp < 1.2
            else "Standard"
            if exp < 2.5
            else "Senior"
            if exp < 4
            else "Elite"
        )
        agents.append(
            {
                "agent_id": f"A{i:04d}",
                "agency_unit_id": unit[0],
                "gender": random.choice(["Male", "Female"]),
                "join_date": join,
                "status": status,
                "experience_years": round(exp, 2),
                "agent_grade": grade,
                "supervisor_id": f"S{random.randint(1, 35):03d}",
                "exit_date": exit_date,
                "profile": profile,
            }
        )
    agents_df = pd.DataFrame(agents)
    agents_df.drop(columns=["profile"]).to_csv(OUT / "agents.csv", index=False)

    districts = [
        ("Kampala", "Central"),
        ("Wakiso", "Central"),
        ("Mukono", "Central"),
        ("Masaka", "Central"),
        ("Jinja", "Eastern"),
        ("Mbale", "Eastern"),
        ("Iganga", "Eastern"),
        ("Soroti", "Eastern"),
        ("Mbarara", "Western"),
        ("Kabarole", "Western"),
        ("Kabale", "Western"),
        ("Hoima", "Western"),
        ("Gulu", "Northern"),
        ("Lira", "Northern"),
        ("Arua", "Northern"),
    ]
    occupations = [
        "Teacher",
        "Trader",
        "Civil Servant",
        "Health Worker",
        "Engineer",
        "Driver",
        "Farmer",
        "Accountant",
        "SME Owner",
        "IT Professional",
        "Other",
    ]
    income_bands = ["<500k", "500k-1M", "1M-2M", "2M-5M", "5M+"]
    channels = [
        "Agent Referral",
        "Customer Referral",
        "Digital",
        "Event",
        "Walk-in",
        "Employer/Group",
    ]

    customers = []
    for i in range(1, 25001):
        district, region = random.choice(districts)
        dob = rand_date(date(1958, 1, 1), date(2005, 12, 31))
        customers.append(
            {
                "customer_id": f"C{i:06d}",
                "gender": random.choice(["Male", "Female"]),
                "date_of_birth": dob,
                "marital_status": random.choices(
                    ["Single", "Married", "Divorced", "Widowed"],
                    weights=[0.35, 0.54, 0.06, 0.05],
                    k=1,
                )[0],
                "occupation": random.choice(occupations),
                "district": district,
                "region": region,
                "income_band": random.choices(
                    income_bands, weights=[0.18, 0.28, 0.27, 0.20, 0.07], k=1
                )[0],
                "acquisition_channel": random.choice(channels),
                "created_date": rand_date(date(2022, 1, 1), AS_OF),
            }
        )
    customers_df = pd.DataFrame(customers)
    customers_df.to_csv(OUT / "customers.csv", index=False)

    # Only agents with service overlapping the sales observation window can sell.
    selling_agents = [a for a in agents if (a["exit_date"] or AS_OF) >= date(2023, 1, 1)]

    # Leads: around 70k
    leads = []
    for i in range(1, 70001):
        a = random.choice(selling_agents)
        service_end = a["exit_date"] or AS_OF
        lead_date = rand_date(max(a["join_date"], date(2023, 1, 1)), service_end)
        conv_p = profiles[a["profile"]]["conv"] * next(
            s[5] for s in agency_specs if s[0] == a["agency_unit_id"]
        )
        converted = random.random() < min(conv_p, 0.55)
        contacted = random.random() < (0.90 if converted else 0.72)
        contacted = contacted or converted
        app_completed = contacted and random.random() < (0.72 if converted else 0.36)
        app_submitted = app_completed and random.random() < (0.82 if converted else 0.35)
        application_status = (
            "Approved"
            if converted
            else (
                random.choice(["Declined", "Withdrawn", "Submitted"]) if app_submitted else "None"
            )
        )
        customer_id = f"C{random.randint(1, 25000):06d}" if converted else None
        conversion_date = lead_date + timedelta(days=random.randint(2, 30)) if converted else None
        if conversion_date:
            conversion_date = min(conversion_date, service_end)
        leads.append(
            {
                "lead_id": f"L{i:07d}",
                "agent_id": a["agent_id"],
                "customer_id": customer_id,
                "lead_date": lead_date,
                "source": random.choice(["Referral", "Digital", "Event", "Walk-in", "Employer"]),
                "contact_status": "Contacted" if contacted else "Uncontacted",
                "appointment_status": (
                    "Completed" if app_completed else ("Booked" if contacted else "None")
                ),
                "application_status": application_status,
                "converted": converted,
                "conversion_date": conversion_date,
            }
        )
    leads_df = pd.DataFrame(leads)
    leads_df.to_csv(OUT / "leads.csv", index=False)

    products = {
        "Protection Plus": (10, 70000, 220000, 20_000_000, 120_000_000),
        "Education Builder": (15, 90000, 350000, 15_000_000, 80_000_000),
        "Family Income Plan": (12, 80000, 300000, 20_000_000, 100_000_000),
        "Savings Growth": (10, 120000, 500000, 10_000_000, 70_000_000),
        "Retirement Secure": (20, 150000, 650000, 20_000_000, 150_000_000),
    }
    freqs = ["Monthly", "Quarterly", "Semi-Annual", "Annual"]
    freq_weights = [0.70, 0.14, 0.06, 0.10]
    mult = {"Monthly": 12, "Quarterly": 4, "Semi-Annual": 2, "Annual": 1}

    # Use converted leads preferentially
    converted_leads = leads_df[leads_df["converted"]].copy()
    converted_records = converted_leads.to_dict("records")
    policies = []
    policy_agent_profiles = {}
    for i in range(1, 35001):
        if i <= len(converted_records):
            lr = converted_records[i - 1]
            a = next(x for x in agents if x["agent_id"] == lr["agent_id"])
            customer_id = lr["customer_id"]
            issue_date = max(pd.to_datetime(lr["conversion_date"]).date(), date(2023, 1, 1))
        else:
            a = random.choice(selling_agents)
            customer_id = f"C{random.randint(1, 25000):06d}"
            issue_date = rand_date(max(a["join_date"], date(2023, 1, 1)), a["exit_date"] or AS_OF)
        product = random.choice(list(products))
        term, low, high, sa_low, sa_high = products[product]
        freq = random.choices(freqs, weights=freq_weights, k=1)[0]
        monthly_equiv = random.randrange(low // 5000, high // 5000 + 1) * 5000
        premium = (
            monthly_equiv
            if freq == "Monthly"
            else monthly_equiv * 3
            if freq == "Quarterly"
            else monthly_equiv * 6
            if freq == "Semi-Annual"
            else monthly_equiv * 12
        )
        annualized = premium * mult[freq]
        sum_assured = random.randrange(sa_low // 1_000_000, sa_high // 1_000_000 + 1) * 1_000_000
        maturity = (pd.Timestamp(issue_date) + pd.DateOffset(years=term)).date()
        base_lapse = profiles[a["profile"]]["lapse"]
        # younger policies have slightly lower realized lapse because less time exposed
        exposure = max((AS_OF - issue_date).days / 365.25, 0)
        lapse_prob = min(base_lapse * min(exposure / 1.2, 1.0), 0.35)
        r = random.random()
        status = "Active"
        lapse_date = None
        surrender_date = None
        if r < lapse_prob:
            status = "Lapsed"
            earliest = issue_date + timedelta(days=90)
            lapse_date = rand_date(earliest, AS_OF) if earliest <= AS_OF else None
            if lapse_date is None:
                status = "Active"
        elif r < lapse_prob + 0.025 * min(exposure, 1):
            status = "Surrendered"
            earliest = issue_date + timedelta(days=180)
            surrender_date = rand_date(earliest, AS_OF) if earliest <= AS_OF else None
            if surrender_date is None:
                status = "Active"
        elif random.random() < 0.03 and exposure > 0.2:
            status = "Grace"
        policy_id = f"P{i:06d}"
        policy_agent_profiles[policy_id] = a["profile"]
        policies.append(
            {
                "policy_id": policy_id,
                "customer_id": customer_id,
                "agent_id": a["agent_id"],
                "product_name": product,
                "distribution_channel": "Agency",
                "issue_date": issue_date,
                "policy_term_years": term,
                "payment_frequency": freq,
                "premium_amount": premium,
                "annualized_premium": annualized,
                "sum_assured": sum_assured,
                "maturity_date": maturity,
                "policy_status": status,
                "lapse_date": lapse_date,
                "surrender_date": surrender_date,
            }
        )
    policies_df = pd.DataFrame(policies)
    policies_df.to_csv(OUT / "policies.csv", index=False)

    # Onboarding cannot follow first issued business, including converted leads.
    first_issue = policies_df.groupby("customer_id")["issue_date"].min().to_dict()
    for customer in customers:
        first = first_issue.get(customer["customer_id"], AS_OF)
        customer["created_date"] = min(customer["created_date"], first)
    pd.DataFrame(customers).to_csv(OUT / "customers.csv", index=False)

    # Premium payments
    payments = []
    status_hist = []
    payment_id = 1
    hist_id = 1
    methods = ["Mobile Money", "Bank Transfer", "Card", "Payroll"]
    for p in policies:
        issue = p["issue_date"]
        freq = p["payment_frequency"]
        interval = (
            30
            if freq == "Monthly"
            else 91
            if freq == "Quarterly"
            else 182
            if freq == "Semi-Annual"
            else 365
        )
        cutoff = p["lapse_date"] or p["surrender_date"] or AS_OF
        # initial status
        status_hist.append(
            {
                "status_history_id": f"H{hist_id:08d}",
                "policy_id": p["policy_id"],
                "status": "Active",
                "status_date": issue,
                "reason": "Policy issued",
            }
        )
        hist_id += 1
        due = issue
        risk = profiles[policy_agent_profiles[p["policy_id"]]]["lapse"]
        while due <= AS_OF and due <= cutoff:
            late_p = min(0.08 + risk * 0.35, 0.20)
            miss_p = min(0.015 + risk * 0.22, 0.10)
            partial_p = 0.025
            x = random.random()
            if x < miss_p:
                status = "Missed"
                paid = 0
                paydate = None
            elif x < miss_p + partial_p:
                status = "Partial"
                paid = round(p["premium_amount"] * random.uniform(0.35, 0.8), 2)
                paydate = due + timedelta(days=random.randint(1, 12))
            elif x < miss_p + partial_p + late_p:
                status = "Late"
                paid = p["premium_amount"]
                paydate = due + timedelta(days=random.randint(3, 28))
            else:
                status = "Paid"
                paid = p["premium_amount"]
                paydate = due + timedelta(days=random.randint(0, 2))
            # A future simulated receipt is not observed cash at this snapshot.
            if paydate and paydate > AS_OF:
                status, paid, paydate = "Missed", 0, None
            payments.append(
                {
                    "payment_id": f"PM{payment_id:09d}",
                    "policy_id": p["policy_id"],
                    "due_date": due,
                    "payment_date": paydate,
                    "amount_due": p["premium_amount"],
                    "amount_paid": paid,
                    "payment_status": status,
                    "payment_method": random.choice(methods),
                }
            )
            payment_id += 1
            due += timedelta(days=interval)
        if p["policy_status"] == "Lapsed" and p["lapse_date"]:
            status_hist.append(
                {
                    "status_history_id": f"H{hist_id:08d}",
                    "policy_id": p["policy_id"],
                    "status": "Lapsed",
                    "status_date": p["lapse_date"],
                    "reason": "Premium discontinuance",
                }
            )
            hist_id += 1
        elif p["policy_status"] == "Surrendered" and p["surrender_date"]:
            status_hist.append(
                {
                    "status_history_id": f"H{hist_id:08d}",
                    "policy_id": p["policy_id"],
                    "status": "Surrendered",
                    "status_date": p["surrender_date"],
                    "reason": "Customer surrender",
                }
            )
            hist_id += 1
        elif p["policy_status"] == "Grace":
            grace_date = max(issue, AS_OF - timedelta(days=random.randint(5, 40)))
            status_hist.append(
                {
                    "status_history_id": f"H{hist_id:08d}",
                    "policy_id": p["policy_id"],
                    "status": "Grace",
                    "status_date": grace_date,
                    "reason": "Premium overdue",
                }
            )
            hist_id += 1

    pd.DataFrame(payments).to_csv(OUT / "premium_payments.csv", index=False)
    pd.DataFrame(status_hist).to_csv(OUT / "policy_status_history.csv", index=False)

    # Monthly targets Jan 2025-Sep 2026 for agents active in the month
    targets = []
    tid = 1
    months = pd.date_range("2025-01-01", "2026-09-01", freq="MS").date
    for a in agents:
        for m in months:
            if a["join_date"] > m:
                continue
            if a["exit_date"] and a["exit_date"] < m:
                continue
            prod = profiles[a["profile"]]["prod"]
            policy_target = max(3, round(random.normalvariate(12 * prod, 2)))
            premium_target = max(
                2_000_000,
                round(random.normalvariate(18_000_000 * prod, 3_000_000) / 100_000) * 100_000,
            )
            targets.append(
                {
                    "target_id": f"T{tid:08d}",
                    "agent_id": a["agent_id"],
                    "target_month": m,
                    "policy_target": policy_target,
                    "premium_target": premium_target,
                    "new_customer_target": max(2, int(policy_target * 0.8)),
                }
            )
            tid += 1
    pd.DataFrame(targets).to_csv(OUT / "sales_targets.csv", index=False)

    # Incentives
    campaigns = [
        ("Q4 Growth Sprint", date(2025, 10, 1), date(2025, 12, 31), 25_000_000, 500_000),
        ("Protection Push", date(2026, 3, 1), date(2026, 4, 30), 20_000_000, 400_000),
        ("Mid-Year Agency Challenge", date(2026, 6, 1), date(2026, 7, 31), 30_000_000, 650_000),
    ]
    incentives = []
    iid = 1
    for cname, start, end, threshold, amount in campaigns:
        eligible = [
            a for a in agents if a["join_date"] <= end and (a["exit_date"] or AS_OF) >= start
        ]
        for a in random.sample(eligible, k=min(250, len(eligible))):
            qualified = random.random() < (
                0.68 if a["profile"] in ["Star", "High-volume risk"] else 0.36
            )
            incentives.append(
                {
                    "incentive_id": f"I{iid:07d}",
                    "agent_id": a["agent_id"],
                    "campaign_name": cname,
                    "start_date": start,
                    "end_date": end,
                    "threshold": threshold,
                    "incentive_amount": amount if qualified else 0,
                    "qualified": qualified,
                }
            )
            iid += 1
    pd.DataFrame(incentives).to_csv(OUT / "incentives.csv", index=False)

    print("Generated:")
    for f in sorted(OUT.glob("*.csv")):
        with f.open(encoding="utf-8") as stream:
            print(f.name, sum(1 for _ in stream) - 1)

    (OUT / "manifest.json").write_text(json.dumps(manifest(OUT), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
