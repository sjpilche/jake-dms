"""Mock Intacct data seeder — realistic $78M creator-led media company.

All numbers are deterministic (seeded RNG). Revenue totals ~$78M/yr,
expenses ~$58M/yr, yielding ~26% operating margin. 18 months of history.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

from loguru import logger
from sqlalchemy.orm import Session

from src.db.engine import get_session, init_db
from src.db.models import (
    APAgingRow,
    ARAgingRow,
    Base,
    CashBalanceRow,
    GLAccountRow,
    GLBalanceRow,
    PlatformRevenueRow,
    PLRow,
    ProductionCostRow,
    ReconRecordRow,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RNG_SEED = 42
TODAY = date(2026, 3, 26)

# Seasonal multipliers by quarter: Q1=0.85, Q2=0.95, Q3=1.0, Q4=1.20
SEASONAL: dict[int, float] = {1: 0.85, 2: 0.95, 3: 1.0, 4: 1.20}

# Annual revenue targets (sum = ~$78M)
ANNUAL_REVENUE = {
    "YouTube": 32_000_000,
    "Facebook": 8_000_000,
    "Brand Deals": 18_000_000,
    "Licensing/OTT": 12_000_000,
    "Merchandise": 5_000_000,
    "Other": 3_000_000,
}

# Annual expense structure (~$58M)
ANNUAL_EXPENSES = {
    ("COGS", "Production - Talent"): 8_500_000,
    ("COGS", "Production - Crew"): 6_200_000,
    ("COGS", "Production - Locations"): 3_800_000,
    ("COGS", "Post-Production"): 2_500_000,
    ("COGS", "Music & Licensing"): 1_000_000,
    ("OpEx", "Salaries & Benefits"): 14_000_000,
    ("OpEx", "Platform & Tech"): 3_000_000,
    ("OpEx", "Office & Facilities"): 4_000_000,
    ("OpEx", "Marketing & Promotion"): 6_000_000,
    ("OpEx", "G&A"): 5_000_000,
    ("OpEx", "Depreciation"): 2_000_000,
    ("OpEx", "Interest & Other"): 2_000_000,
}

# Business line revenue allocation
BIZ_LINE_ALLOC = {
    "Core Content": 0.52,  # YouTube + Facebook ad rev
    "5th Quarter": 0.15,
    "Brand Deals": 0.23,
    "Licensing/OTT": 0.07,
    "Other": 0.03,
}

# DMS-style video titles (deterministic, not AI-generated)
VIDEO_TITLES = [
    "She Mocked A Homeless Man, Instantly Regrets It",
    "CEO Fires Single Mom, Then Discovers The Truth",
    "Kid Gets Bullied For Being Different, What Happens Next Is Shocking",
    "Millionaire Humiliates Waiter, Lives To Regret It",
    "Teacher Gives Up On Student, Then Learns The Real Story",
    "Man Steals From Blind Woman, Karma Takes Over",
    "Doctor Refuses To Treat Patient, Then His Boss Walks In",
    "Rich Kid Makes Fun Of Janitor, Janitor Teaches Him A Lesson",
    "Girl Gets Rejected For Her Looks, Becomes A Supermodel",
    "Husband Catches Wife Lying, The Truth Will Shock You",
    "Employee Gets Fired On First Day, CEO Finds Out Why",
    "Mother Abandons Baby, 20 Years Later She Comes Back",
    "Teenager Steals From Elderly Neighbor, Gets Caught",
    "Couple Judges Homeless Vet, Then Learns His Story",
    "Boss Humiliates Intern In Meeting, Intern Gets Revenge",
    "Father Walks Out On Family, Daughter Finds Him 15 Years Later",
    "Coach Benches Star Player, Team Learns The Reason",
    "Landlord Tries To Evict Single Dad, Judge Steps In",
    "Popular Kid Bullies New Student, Regrets It Immediately",
    "Woman Scams Elderly Man, Gets Caught On Camera",
    "Son Disrespects His Mother, Stranger Teaches Him A Lesson",
    "Restaurant Refuses To Serve Homeless Man, Owner Finds Out",
    "Babysitter Ignores Kids, Hidden Camera Catches Everything",
    "Athlete Quits Before Big Game, Coach Reveals The Truth",
    "Neighbor Steals Packages, Gets A Surprise Inside",
    "Teenager Lies To Parents, Then Everything Falls Apart",
    "Boss Fires Pregnant Employee, Lawyer Gets Involved",
    "Kid Donates Last Dollar, Gets Unexpected Reward",
    "Customer Yells At Cashier, Manager Steps In",
    "Wife Catches Husband Sneaking Out, The Truth Is Heartbreaking",
    "Student Cheats On Exam, Teacher Already Knows",
    "Man Pretends To Be Homeless, Reveals His True Identity",
    "Daughter Hides Secret From Dad, He Finds Out At Graduation",
    "Bully Picks On Smallest Kid In Class, Biggest Mistake Ever",
    "Gold Digger Tests Boyfriend, Gets A Reality Check",
    "Grandma Gets Scammed Online, Grandson Gets Justice",
    "New Employee Outperforms Everyone, Boss Gets Jealous",
    "Mom Works 3 Jobs, Son Finds Out The Reason",
    "Influencer Fakes Charity, Followers Expose The Truth",
    "Stepfather Rejects Stepson, Biological Dad Returns",
    "Store Clerk Judges Customer By Appearance, Regrets It",
    "Brother And Sister Reunite After 25 Years, Emotional Ending",
    "Tutor Gives Up On Struggling Student, Student Proves Everyone Wrong",
    "Delivery Driver Gets No Tips, One Customer Changes Everything",
    "Orphan Gets Adopted, Discovers New Family's Secret",
    "Mechanic Overcharges Single Mom, Her Son Is A Lawyer",
    "Best Friends Betray Each Other, Years Later They Meet Again",
    "Teenager Runs Away From Home, Stranger Takes Him In",
    "Executive Ignores Assistant, Assistant Saves The Company",
    "Nurse Goes Above And Beyond, Patient Returns The Favor",
]

CREW_IDS = ["CREW-A", "CREW-B", "CREW-C", "CREW-D", "CREW-E", "CREW-F", "CREW-G", "CREW-H"]

CONTENT_FORMATS = ["Long-Form", "Short", "Kids Series", "Branded", "Vertical"]
FORMAT_WEIGHTS = [0.45, 0.25, 0.15, 0.10, 0.05]

# AR Aging customers
AR_CUSTOMERS = [
    ("Google/YouTube", Decimal("2814000"), Decimal("0"), Decimal("0"), Decimal("0")),
    ("Meta Platforms", Decimal("1218000"), Decimal("412000"), Decimal("0"), Decimal("0")),
    ("Old Navy (Brand Deal)", Decimal("0"), Decimal("0"), Decimal("340000"), Decimal("0")),
    ("Samsung Electronics", Decimal("0"), Decimal("180000"), Decimal("0"), Decimal("0")),
    ("Procter & Gamble", Decimal("285000"), Decimal("0"), Decimal("0"), Decimal("0")),
    ("Amazon Studios", Decimal("0"), Decimal("0"), Decimal("0"), Decimal("186000")),
    ("Nike Inc.", Decimal("320000"), Decimal("145000"), Decimal("0"), Decimal("0")),
    ("Walmart Connect", Decimal("0"), Decimal("210000"), Decimal("0"), Decimal("0")),
    ("Disney+/Hulu", Decimal("0"), Decimal("0"), Decimal("280000"), Decimal("0")),
    ("Fox Corporation", Decimal("195000"), Decimal("0"), Decimal("0"), Decimal("0")),
    ("Samsung TV Plus", Decimal("0"), Decimal("345000"), Decimal("0"), Decimal("0")),
    ("Coca-Cola Company", Decimal("0"), Decimal("0"), Decimal("175000"), Decimal("0")),
    ("Various Small Sponsors", Decimal("187000"), Decimal("212000"), Decimal("78000"), Decimal("43000")),
]

# AP Aging vendors
AP_VENDORS = [
    ("Burbank Studio Lease", Decimal("185000"), Decimal("0"), Decimal("0"), Decimal("0")),
    ("ADP Payroll Services", Decimal("892000"), Decimal("0"), Decimal("0"), Decimal("0")),
    ("Adobe Creative Cloud", Decimal("48000"), Decimal("0"), Decimal("0"), Decimal("0")),
    ("Equipment Rental Co", Decimal("125000"), Decimal("62000"), Decimal("0"), Decimal("0")),
    ("Freelance Talent Pool", Decimal("340000"), Decimal("185000"), Decimal("92000"), Decimal("0")),
    ("Catering Services Inc", Decimal("67000"), Decimal("34000"), Decimal("0"), Decimal("0")),
    ("Insurance Providers", Decimal("112000"), Decimal("0"), Decimal("0"), Decimal("0")),
    ("Legal & Accounting", Decimal("210000"), Decimal("95000"), Decimal("0"), Decimal("0")),
    ("Cloud Services (AWS)", Decimal("38000"), Decimal("0"), Decimal("0"), Decimal("0")),
    ("Travel & Transport", Decimal("78000"), Decimal("42000"), Decimal("18000"), Decimal("0")),
]

# Cash accounts
CASH_ACCOUNTS = [
    ("Operating Account", "JPMorgan Chase", Decimal("4218347.62")),
    ("Payroll Account", "JPMorgan Chase", Decimal("1842591.18")),
    ("Reserve Account", "First Republic", Decimal("3512840.75")),
    ("Production Escrow", "City National Bank", Decimal("814226.33")),
]

# GL Chart of Accounts
GL_ACCOUNTS = [
    # Revenue
    ("4000", "YouTube Ad Revenue", "Revenue", "Platform Revenue"),
    ("4010", "Facebook Ad Revenue", "Revenue", "Platform Revenue"),
    ("4020", "TikTok Revenue", "Revenue", "Platform Revenue"),
    ("4100", "Brand Deal Revenue", "Revenue", "Sponsorship"),
    ("4110", "Sponsorship Revenue", "Revenue", "Sponsorship"),
    ("4200", "Licensing Revenue", "Revenue", "Licensing"),
    ("4210", "Syndication Revenue", "Revenue", "Licensing"),
    ("4300", "Merchandise Revenue", "Revenue", "Merchandise"),
    ("4400", "Speaking & Events", "Revenue", "Other Revenue"),
    ("4500", "5th Quarter Revenue", "Revenue", "Agency"),
    # COGS
    ("5000", "Talent Costs", "Expense", "COGS"),
    ("5010", "Crew Labor", "Expense", "COGS"),
    ("5020", "Location & Set", "Expense", "COGS"),
    ("5030", "Post-Production", "Expense", "COGS"),
    ("5040", "Music & Rights", "Expense", "COGS"),
    # OpEx
    ("6000", "Salaries & Benefits", "Expense", "Payroll"),
    ("6100", "Platform & Technology", "Expense", "Tech"),
    ("6200", "Office & Facilities", "Expense", "Facilities"),
    ("6300", "Marketing & Promotion", "Expense", "Marketing"),
    ("6400", "General & Administrative", "Expense", "G&A"),
    ("6500", "Depreciation", "Expense", "Non-Cash"),
    ("6600", "Interest & Other", "Expense", "Other"),
    # Assets
    ("1000", "Cash - Operating", "Asset", "Cash"),
    ("1010", "Cash - Payroll", "Asset", "Cash"),
    ("1020", "Cash - Reserve", "Asset", "Cash"),
    ("1030", "Cash - Production Escrow", "Asset", "Cash"),
    ("1100", "Accounts Receivable", "Asset", "AR"),
    ("1200", "Prepaid Expenses", "Asset", "Prepaid"),
    ("1300", "Equipment & Gear", "Asset", "Fixed"),
    ("1310", "Accum Depreciation", "Asset", "Fixed"),
    # Liabilities
    ("2000", "Accounts Payable", "Liability", "AP"),
    ("2100", "Accrued Expenses", "Liability", "Accrued"),
    ("2200", "Deferred Revenue", "Liability", "Deferred"),
    ("2300", "Line of Credit", "Liability", "Debt"),
    # Equity
    ("3000", "Retained Earnings", "Equity", "Equity"),
    ("3100", "Owner's Equity", "Equity", "Equity"),
]


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _quarter(month: int) -> int:
    return (month - 1) // 3 + 1


def _monthly_amount(annual: int | float, month: int, rng: random.Random) -> Decimal:
    """Distribute annual amount across months with seasonal variance + noise."""
    base = annual / 12.0
    seasonal = SEASONAL[_quarter(month)]
    noise = rng.uniform(0.92, 1.08)
    return Decimal(str(round(base * seasonal * noise, 2)))


def _generate_periods(months_back: int = 18) -> list[str]:
    """Generate YYYY-MM period strings going back N months from TODAY."""
    periods = []
    for i in range(months_back, 0, -1):
        d = TODAY.replace(day=1) - timedelta(days=i * 30)
        periods.append(d.strftime("%Y-%m"))
    return periods


# ---------------------------------------------------------------------------
# Seeder
# ---------------------------------------------------------------------------

def seed_database(session: Session) -> None:
    """Seed all mock data into the database."""
    rng = random.Random(RNG_SEED)
    periods = _generate_periods(18)

    logger.info("Seeding GL accounts...")
    _seed_gl_accounts(session)

    logger.info("Seeding GL balances...")
    _seed_gl_balances(session, periods, rng)

    logger.info("Seeding platform revenue...")
    _seed_platform_revenue(session, periods, rng)

    logger.info("Seeding P&L...")
    _seed_pl(session, periods, rng)

    logger.info("Seeding AR aging...")
    _seed_ar_aging(session)

    logger.info("Seeding AP aging...")
    _seed_ap_aging(session)

    logger.info("Seeding cash balances...")
    _seed_cash_balances(session)

    logger.info("Seeding production costs...")
    _seed_production_costs(session, rng)

    logger.info("Seeding reconciliation records...")
    _seed_recon_records(session, periods, rng)

    session.commit()
    logger.info("Mock data seeding complete")


def _seed_gl_accounts(session: Session) -> None:
    for acct_no, name, category, subcategory in GL_ACCOUNTS:
        session.add(GLAccountRow(
            account_no=acct_no, name=name, category=category, subcategory=subcategory
        ))


def _seed_gl_balances(session: Session, periods: list[str], rng: random.Random) -> None:
    # Revenue accounts
    rev_map = {
        "4000": 32_000_000, "4010": 8_000_000, "4020": 1_500_000,
        "4100": 12_000_000, "4110": 6_000_000,
        "4200": 8_000_000, "4210": 4_000_000,
        "4300": 5_000_000, "4400": 3_000_000, "4500": 11_700_000,
    }
    for period in periods:
        month = int(period.split("-")[1])
        for acct, annual in rev_map.items():
            amt = _monthly_amount(annual, month, rng)
            session.add(GLBalanceRow(
                account_no=acct, period=period,
                debit=Decimal("0"), credit=amt, net_balance=-amt,
            ))

    # Expense accounts
    exp_map = {
        "5000": 8_500_000, "5010": 6_200_000, "5020": 3_800_000,
        "5030": 2_500_000, "5040": 1_000_000,
        "6000": 14_000_000, "6100": 3_000_000, "6200": 4_000_000,
        "6300": 6_000_000, "6400": 5_000_000, "6500": 2_000_000,
        "6600": 2_000_000,
    }
    for period in periods:
        month = int(period.split("-")[1])
        for acct, annual in exp_map.items():
            amt = _monthly_amount(annual, month, rng)
            session.add(GLBalanceRow(
                account_no=acct, period=period,
                debit=amt, credit=Decimal("0"), net_balance=amt,
            ))


def _seed_platform_revenue(
    session: Session, periods: list[str], rng: random.Random
) -> None:
    platforms = {
        "YouTube": ("Core Content", 32_000_000),
        "Facebook": ("Core Content", 8_000_000),
        "Brand Deals": ("Brand Deals", 18_000_000),
        "Licensing": ("Licensing/OTT", 12_000_000),
        "Merchandise": ("Other", 5_000_000),
        "Other": ("Other", 3_000_000),
    }
    for period in periods:
        month = int(period.split("-")[1])
        for platform, (biz_line, annual) in platforms.items():
            total = _monthly_amount(annual, month, rng)
            # Split: 80% ad rev, 15% sponsorship, 5% licensing (simplified)
            ad = Decimal(str(round(float(total) * 0.80, 2)))
            spon = Decimal(str(round(float(total) * 0.15, 2)))
            lic = total - ad - spon
            session.add(PlatformRevenueRow(
                platform=platform, business_line=biz_line, period=period,
                ad_revenue=ad, sponsorship_revenue=spon,
                licensing_revenue=lic, total_revenue=total,
            ))


def _seed_pl(session: Session, periods: list[str], rng: random.Random) -> None:
    # Revenue P&L lines by business line
    rev_lines = {
        ("Revenue", "YouTube Ad Revenue", "Core Content"): 32_000_000,
        ("Revenue", "Facebook Ad Revenue", "Core Content"): 8_000_000,
        ("Revenue", "Brand Deal Revenue", "Brand Deals"): 18_000_000,
        ("Revenue", "Licensing Revenue", "Licensing/OTT"): 12_000_000,
        ("Revenue", "Merchandise Revenue", "Other"): 5_000_000,
        ("Revenue", "Other Revenue", "Other"): 3_000_000,
    }
    for period in periods:
        month = int(period.split("-")[1])
        for (cat, subcat, biz), annual in rev_lines.items():
            amt = _monthly_amount(annual, month, rng)
            session.add(PLRow(
                category=cat, subcategory=subcat, business_line=biz,
                period=period, amount=amt,
            ))

    # Expense P&L lines (allocated across business lines proportionally)
    for period in periods:
        month = int(period.split("-")[1])
        for (cat, subcat), annual in ANNUAL_EXPENSES.items():
            for biz, alloc in BIZ_LINE_ALLOC.items():
                amt = _monthly_amount(int(annual * alloc), month, rng)
                session.add(PLRow(
                    category=cat, subcategory=subcat, business_line=biz,
                    period=period, amount=amt,
                ))


def _seed_ar_aging(session: Session) -> None:
    for customer, current, d30, d60, d90 in AR_CUSTOMERS:
        total = current + d30 + d60 + d90
        session.add(ARAgingRow(
            customer=customer, current_amt=current,
            days_30=d30, days_60=d60, days_90_plus=d90,
            total=total, as_of_date=TODAY,
        ))


def _seed_ap_aging(session: Session) -> None:
    for vendor, current, d30, d60, d90 in AP_VENDORS:
        total = current + d30 + d60 + d90
        session.add(APAgingRow(
            vendor=vendor, current_amt=current,
            days_30=d30, days_60=d60, days_90_plus=d90,
            total=total, as_of_date=TODAY,
        ))


def _seed_cash_balances(session: Session) -> None:
    for acct_name, bank, balance in CASH_ACCOUNTS:
        session.add(CashBalanceRow(
            account_name=acct_name, bank_name=bank,
            balance=balance, as_of_date=TODAY,
        ))


def _seed_production_costs(session: Session, rng: random.Random) -> None:
    """Generate production costs for 50 videos over last 6 months."""
    for i, title in enumerate(VIDEO_TITLES[:50]):
        fmt = rng.choices(CONTENT_FORMATS, weights=FORMAT_WEIGHTS, k=1)[0]
        crew = rng.choice(CREW_IDS)

        # Cost ranges by format
        if fmt == "Long-Form":
            talent = Decimal(str(rng.randint(4000, 12000)))
            crew_cost = Decimal(str(rng.randint(3000, 8000)))
            location = Decimal(str(rng.randint(2000, 6000)))
            post = Decimal(str(rng.randint(1500, 4000)))
            music = Decimal(str(rng.randint(500, 2000)))
        elif fmt == "Short":
            talent = Decimal(str(rng.randint(1000, 3000)))
            crew_cost = Decimal(str(rng.randint(800, 2000)))
            location = Decimal(str(rng.randint(500, 1500)))
            post = Decimal(str(rng.randint(300, 1000)))
            music = Decimal(str(rng.randint(200, 500)))
        elif fmt == "Branded":
            talent = Decimal(str(rng.randint(8000, 25000)))
            crew_cost = Decimal(str(rng.randint(5000, 15000)))
            location = Decimal(str(rng.randint(3000, 10000)))
            post = Decimal(str(rng.randint(2000, 8000)))
            music = Decimal(str(rng.randint(1000, 3000)))
        elif fmt == "Kids Series":
            talent = Decimal(str(rng.randint(3000, 8000)))
            crew_cost = Decimal(str(rng.randint(2000, 5000)))
            location = Decimal(str(rng.randint(1000, 3000)))
            post = Decimal(str(rng.randint(1000, 3000)))
            music = Decimal(str(rng.randint(500, 1500)))
        else:  # Vertical
            talent = Decimal(str(rng.randint(800, 2000)))
            crew_cost = Decimal(str(rng.randint(500, 1500)))
            location = Decimal(str(rng.randint(300, 800)))
            post = Decimal(str(rng.randint(200, 600)))
            music = Decimal(str(rng.randint(100, 300)))

        total = talent + crew_cost + location + post + music
        prod_date = TODAY - timedelta(days=rng.randint(7, 180))

        session.add(ProductionCostRow(
            video_id=f"VID-{i+1:03d}",
            video_title=title,
            content_format=fmt,
            crew_id=crew,
            talent=talent,
            crew_cost=crew_cost,
            location=location,
            post_production=post,
            music_licensing=music,
            total_cost=total,
            production_date=prod_date,
        ))


def _seed_recon_records(
    session: Session, periods: list[str], rng: random.Random
) -> None:
    """Generate reconciliation records for last 6 months."""
    recent_periods = periods[-6:]
    for period in recent_periods:
        month = int(period.split("-")[1])
        for platform, annual in [("YouTube", 32_000_000), ("Facebook", 8_000_000)]:
            estimated = _monthly_amount(annual, month, rng)
            # Actual is close to estimated, with some variance
            variance_pct = Decimal(str(round(rng.uniform(-8.0, 8.0), 2)))
            actual = Decimal(str(round(
                float(estimated) * (1 + float(variance_pct) / 100), 2
            )))
            variance = actual - estimated
            status = "Matched" if abs(float(variance_pct)) < 5 else "Flagged"
            session.add(ReconRecordRow(
                platform=platform, period=period,
                estimated_revenue=estimated, actual_received=actual,
                variance=variance, variance_pct=variance_pct,
                status=status,
            ))


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

_seeded = False


def ensure_demo_data() -> None:
    """Initialize DB and seed mock data if empty. No-ops after first call."""
    global _seeded
    if _seeded:
        return
    init_db()
    session = get_session()
    try:
        count = session.query(GLAccountRow).count()
        if count == 0:
            logger.info("No data found — seeding mock data...")
            seed_database(session)
        else:
            logger.debug(f"Database already seeded ({count} GL accounts)")
    finally:
        session.close()
    _seeded = True
