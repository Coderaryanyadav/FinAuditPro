"""
Test Companies Metadata Definitions
FinAuditPro - Test Data Architecture

Defines three completely independent test corporate entities:
1. Aryan Fintech Pvt. Ltd. (ARYAN)
2. Hitansh Fintech Pvt. Ltd. (HITANSH)
3. Jeet Fintech Pvt. Ltd. (JEET)
"""

from typing import Dict, Any

ARYAN_COMPANY: Dict[str, Any] = {
    "name": "Aryan Fintech Pvt. Ltd.",
    "short_code": "ARYAN",
    "environment": "TEST",
    "synthetic": True,
    "industry": "Financial Technology / Software Services",
    "company_type": "Private Limited Company",
    "state": "Maharashtra",
    "state_code": "27",
    "city": "Mumbai",
    "pin": "400059",
    "financial_year": "2025-26",
    "prior_financial_year": "2024-25",
    "currency": "INR",
    "gst_registered": True,
    "pan": "AAPCA1111A",
    "gstin": "27AAPCA1111A1Z1",
    "primary_contact": "Aryan Sharma",
    "email": "aryan@example.test",
    "phone": "+91 98000 11111",
    "address": "Plot 101, Bandra Kurla Complex, Bandra East, Mumbai 400051",
    "nature_of_business": "Fintech software engineering, payment orchestration APIs, and cloud microservices development.",
    "authorized_capital": 50000000.0,
    "paid_up_capital": 25000000.0,
    "bank_name": "HDFC Bank Ltd",
    "bank_account_no": "50200011112233",
    "bank_ifsc": "HDFC0000101"
}

HITANSH_COMPANY: Dict[str, Any] = {
    "name": "Hitansh Fintech Pvt. Ltd.",
    "short_code": "HITANSH",
    "environment": "TEST",
    "synthetic": True,
    "industry": "Financial Technology / SaaS",
    "company_type": "Private Limited Company",
    "state": "Maharashtra",
    "state_code": "27",
    "city": "Mumbai",
    "pin": "400001",
    "financial_year": "2025-26",
    "prior_financial_year": "2024-25",
    "currency": "INR",
    "gst_registered": True,
    "pan": "AAHCH2222H",
    "gstin": "27AAHCH2222H1Z2",
    "primary_contact": "Hitansh Mehta",
    "email": "hitansh@example.test",
    "phone": "+91 98000 22222",
    "address": "Unit 502, Nariman Point Commercial Hub, Mumbai 400021",
    "nature_of_business": "[SYNTHETIC TEST DATASET - NOT REAL CLIENT DATA] B2B SaaS subscription platform for automated treasury management and corporate expense reconciliation.",
    "authorized_capital": 60000000.0,
    "paid_up_capital": 30000000.0,
    "bank_name": "ICICI Bank Ltd",
    "bank_account_no": "00040522223344",
    "bank_ifsc": "ICIC0000004"
}

JEET_COMPANY: Dict[str, Any] = {
    "name": "Jeet Fintech Pvt. Ltd.",
    "short_code": "JEET",
    "environment": "TEST",
    "synthetic": True,
    "industry": "Financial Technology / Neo-Banking",
    "company_type": "Private Limited Company",
    "state": "Maharashtra",
    "state_code": "27",
    "city": "Pune",
    "pin": "411001",
    "financial_year": "2025-26",
    "prior_financial_year": "2024-25",
    "currency": "INR",
    "gst_registered": True,
    "pan": "AAJCJ3333J",
    "gstin": "27AAJCJ3333J1Z3",
    "primary_contact": "Jeet Patel",
    "email": "jeet@example.test",
    "phone": "+91 98000 33333",
    "address": "Tower 4, Cybercity Magarpatta, Hadapsar, Pune 411028",
    "nature_of_business": "[SYNTHETIC TEST DATASET - NOT REAL CLIENT DATA] Digital payments gateway, algorithmic settlement routing, and neo-banking ledger infrastructure.",
    "authorized_capital": 45000000.0,
    "paid_up_capital": 20000000.0,
    "bank_name": "Axis Bank Ltd",
    "bank_account_no": "91802033334455",
    "bank_ifsc": "UTIB0000123"
}

COMPANIES = {
    "ARYAN": ARYAN_COMPANY,
    "HITANSH": HITANSH_COMPANY,
    "JEET": JEET_COMPANY
}

