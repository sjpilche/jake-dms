"""Sage Intacct XML API async client.

Handles auth envelope, pagination, error handling, retry logic.
Mock mode returns demo data when INTACCT_MOCK_MODE=true.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from uuid import uuid4

import httpx
import xmltodict
from loguru import logger
from pydantic import BaseModel, ConfigDict

from src.core.config import get_settings


class IntacctError(Exception):
    """Raised when the Intacct API returns an error."""

    def __init__(self, code: str, message: str, detail: str = "") -> None:
        self.code = code
        self.message = message
        self.detail = detail
        super().__init__(f"Intacct [{code}]: {message}")


class IntacctRecord(BaseModel):
    """Generic record wrapper for Intacct API responses."""
    model_config = ConfigDict(strict=False)
    data: dict


class IntacctClient:
    """Async XML API client for Sage Intacct."""

    MAX_RETRIES = 3
    RETRY_DELAY = 2.0  # seconds
    PAGE_SIZE = 1000

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def read_by_query(
        self,
        obj: str,
        query: str = "",
        fields: list[str] | None = None,
        pagesize: int | None = None,
    ) -> list[dict]:
        """Read records from Intacct using readByQuery."""
        if self.settings.INTACCT_MOCK_MODE:
            return self._mock_read(obj, query)

        fields_xml = ",".join(fields) if fields else "*"
        ps = pagesize or self.PAGE_SIZE
        fn = f"""<readByQuery>
            <object>{obj}</object>
            <query>{query}</query>
            <fields>{fields_xml}</fields>
            <pagesize>{ps}</pagesize>
        </readByQuery>"""

        result = await self._execute(fn)
        return self._extract_records(result, obj)

    async def read_report(
        self, report_name: str, filters: dict | None = None
    ) -> list[dict]:
        """Read a custom report from Intacct."""
        if self.settings.INTACCT_MOCK_MODE:
            return []

        filter_xml = ""
        if filters:
            filter_xml = "<filters>" + "".join(
                f"<filter><field>{k}</field><value>{v}</value></filter>"
                for k, v in filters.items()
            ) + "</filters>"

        fn = f"""<readReport>
            <report>{report_name}</report>
            {filter_xml}
        </readReport>"""

        result = await self._execute(fn)
        return self._extract_records(result, "data")

    async def create(self, obj: str, data: dict) -> dict:
        """Create a record in Intacct."""
        if self.settings.INTACCT_MOCK_MODE:
            logger.info(f"[MOCK] Would create {obj}: {data}")
            return {"RECORDNO": "MOCK-001", **data}

        fields = "".join(f"<{k}>{v}</{k}>" for k, v in data.items())
        fn = f"<create><{obj}>{fields}</{obj}></create>"
        return await self._execute(fn)

    async def create_statistical_journal(
        self,
        journal_id: str,
        entries: list[dict],
        description: str = "",
    ) -> dict:
        """Write statistical journal entries to Intacct."""
        if self.settings.INTACCT_MOCK_MODE:
            logger.info(f"[MOCK] Would write stat journal {journal_id}: {len(entries)} entries")
            return {"RECORDNO": "MOCK-STAT-001"}

        entry_xml = ""
        for e in entries:
            entry_xml += f"""<GLENTRY>
                <ACCOUNTNO>{e['account_no']}</ACCOUNTNO>
                <TR_TYPE>1</TR_TYPE>
                <TRX_AMOUNT>{e['amount']}</TRX_AMOUNT>
                <MEMO>{e.get('memo', '')}</MEMO>
            </GLENTRY>"""

        fn = f"""<create><GLBATCH>
            <JOURNAL>{journal_id}</JOURNAL>
            <BATCH_TITLE>{description}</BATCH_TITLE>
            <ENTRIES>{entry_xml}</ENTRIES>
        </GLBATCH></create>"""

        return await self._execute(fn)

    async def get_cash_balances(self) -> list[dict]:
        """Read cash/checking account balances."""
        return await self.read_by_query(
            "CHECKINGACCOUNT",
            fields=["BANKACCOUNTID", "BANKNAME", "CURRENTBALANCE", "LASTACTIVITYDATE"],
        )

    async def get_ar_aging(self) -> list[dict]:
        """Read AR invoices for aging analysis."""
        return await self.read_by_query(
            "ARINVOICE",
            query="STATE = 'Posted'",
            fields=["CUSTOMERID", "CUSTOMERNAME", "TOTALDUE", "TOTALPAID",
                     "TOTALBALANCE", "WHENCREATED", "WHENDUE"],
        )

    async def get_gl_balances(self, period: str) -> list[dict]:
        """Read GL balances for a given period (YYYY-MM)."""
        return await self.read_by_query(
            "GLENTRY",
            query=f"BATCH_DATE >= '{period}-01' AND BATCH_DATE <= '{period}-31'",
            fields=["ACCOUNTNO", "ACCOUNTTITLE", "DEBIT", "CREDIT", "AMOUNT"],
        )

    async def get_project_costs(self, project_id: str = "") -> list[dict]:
        """Read project accounting costs."""
        query = f"PROJECTID = '{project_id}'" if project_id else ""
        return await self.read_by_query(
            "APBILL",
            query=query,
            fields=["PROJECTID", "VENDORNAME", "TOTALDUE", "DESCRIPTION",
                     "WHENCREATED"],
        )

    async def get_revenue_schedules(self) -> list[dict]:
        """Read revenue recognition schedules."""
        return await self.read_by_query(
            "REVRECSCHEDULE",
            fields=["RECORDNO", "REVRECTEMPLATE", "TOTALAMOUNT",
                     "AMOUNTRECOGNIZED", "AMOUNTDEFERRED"],
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _execute(self, function_xml: str) -> dict:
        """Execute an Intacct API call with retry logic."""
        envelope = self._build_envelope(function_xml)
        client = await self._get_client()

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                resp = await client.post(
                    self.settings.INTACCT_ENDPOINT,
                    content=envelope,
                    headers={"Content-Type": "application/xml"},
                )
                resp.raise_for_status()
                parsed = xmltodict.parse(resp.text)
                self._check_errors(parsed)
                return parsed
            except httpx.HTTPStatusError as e:
                logger.warning(f"Intacct HTTP {e.response.status_code} (attempt {attempt})")
                if attempt == self.MAX_RETRIES:
                    raise
                await asyncio.sleep(self.RETRY_DELAY * attempt)
            except IntacctError:
                raise
            except Exception as e:
                logger.warning(f"Intacct request failed (attempt {attempt}): {e}")
                if attempt == self.MAX_RETRIES:
                    raise
                await asyncio.sleep(self.RETRY_DELAY * attempt)

        raise IntacctError("MAX_RETRIES", "All retry attempts exhausted")

    def _build_envelope(self, function_xml: str) -> str:
        s = self.settings
        cid = str(uuid4())[:8]
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<request>
  <control>
    <senderid>{s.INTACCT_SENDER_ID}</senderid>
    <password>{s.INTACCT_SENDER_PASSWORD}</password>
    <controlid>{cid}</controlid>
    <uniqueid>false</uniqueid>
    <dtdversion>3.0</dtdversion>
    <includewhitespace>false</includewhitespace>
  </control>
  <operation>
    <authentication>
      <login>
        <userid>{s.INTACCT_USER_ID}</userid>
        <companyid>{s.INTACCT_COMPANY_ID}</companyid>
        <password>{s.INTACCT_USER_PASSWORD}</password>
      </login>
    </authentication>
    <content>
      <function controlid="fn-{cid}">
        {function_xml}
      </function>
    </content>
  </operation>
</request>"""

    @staticmethod
    def _check_errors(parsed: dict) -> None:
        """Check parsed XML response for Intacct errors."""
        try:
            result = parsed["response"]["operation"]["result"]
            if result.get("status") == "failure":
                err = result.get("errormessage", {}).get("error", {})
                if isinstance(err, list):
                    err = err[0]
                raise IntacctError(
                    code=err.get("errorno", "UNKNOWN"),
                    message=err.get("description2", err.get("description", "Unknown error")),
                    detail=err.get("correction", ""),
                )
        except (KeyError, TypeError):
            pass

    @staticmethod
    def _extract_records(parsed: dict, obj: str) -> list[dict]:
        """Extract record list from nested Intacct response."""
        try:
            data = parsed["response"]["operation"]["result"]["data"]
            if data is None:
                return []
            records = data.get(obj.lower(), data.get(obj, []))
            if isinstance(records, dict):
                return [records]
            return records if isinstance(records, list) else []
        except (KeyError, TypeError, AttributeError):
            return []

    @staticmethod
    def _mock_read(obj: str, query: str) -> list[dict]:
        """Return mock data for demo/test mode."""
        logger.debug(f"[MOCK] read_by_query({obj}, {query})")
        mock_data: dict[str, list[dict]] = {
            "CHECKINGACCOUNT": [
                {"BANKACCOUNTID": "OPER-001", "BANKNAME": "JPMorgan Chase",
                 "CURRENTBALANCE": "4218347.62", "LASTACTIVITYDATE": "2026-03-25"},
                {"BANKACCOUNTID": "PAY-001", "BANKNAME": "JPMorgan Chase",
                 "CURRENTBALANCE": "1842591.18", "LASTACTIVITYDATE": "2026-03-25"},
                {"BANKACCOUNTID": "RES-001", "BANKNAME": "First Republic",
                 "CURRENTBALANCE": "3512840.75", "LASTACTIVITYDATE": "2026-03-20"},
                {"BANKACCOUNTID": "ESC-001", "BANKNAME": "City National Bank",
                 "CURRENTBALANCE": "814226.33", "LASTACTIVITYDATE": "2026-03-24"},
            ],
            "ARINVOICE": [
                {"CUSTOMERID": "GOOG", "CUSTOMERNAME": "Google/YouTube",
                 "TOTALDUE": "2814000", "TOTALPAID": "0", "TOTALBALANCE": "2814000",
                 "WHENCREATED": "2026-03-01", "WHENDUE": "2026-03-31"},
                {"CUSTOMERID": "META", "CUSTOMERNAME": "Meta Platforms",
                 "TOTALDUE": "1630000", "TOTALPAID": "0", "TOTALBALANCE": "1630000",
                 "WHENCREATED": "2026-02-15", "WHENDUE": "2026-04-15"},
            ],
        }
        return mock_data.get(obj, [])
