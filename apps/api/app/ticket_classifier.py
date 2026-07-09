from __future__ import annotations

import re
from typing import Any


EXCLUDED_PATTERNS: tuple[tuple[str, str, str], ...] = (
    (r"\bdaily (it )?meeting\b", "meeting", "internal_meeting"),
    (r"\bonsite monitoring and support\b", "admin_internal", "internal_admin"),
    (r"\bterms of service\b", "vendor_notice", "vendor_notice"),
    (r"\bwelcome to .*protect hub\b", "vendor_notice", "vendor_notice"),
    (r"\bpreference center\b", "vendor_notice", "vendor_notice"),
    (r"\bnewsletter\b|\bcptc today\b", "newsletter", "newsletter"),
    (r"\btraining\b", "training", "training"),
    (r"\bticket survey\b|your ticket is complete|unsubscribe", "notification", "ticket_noise"),
)

SUPPORT_PATTERNS: tuple[tuple[str, str, bool], ...] = (
    (r"drive has .*used|system_volume|% used|disk space|passed (90|95)|low disk", "disk_space_alert", True),
    (r"no recent backup|backup failed|backup failure|c1 backup|\bbackup\b", "backup_alert", True),
    (r"\bvpn\b|globalprotect|forticlient|radius", "vpn_issue", False),
    (r"outlook|office 365|microsoft 365|\bm365\b|mailbox|email|e-mail", "microsoft_365_issue", False),
    (r"sharepoint|teams|onedrive", "microsoft_365_issue", False),
    (r"scan to email|scanner|printer|print spooler", "printer_scan_issue", False),
    (r"\bonsite\b|on-site|field visit|site visit", "onsite_support", False),
    (r"server .*down|service .*down|website .*down|is down again|unable to login|cannot login", "access_or_availability_issue", False),
    (r"edr|safetica|darktrace|crowdstrike|sentinelone|security alert", "security_alert", True),
    (r"password|locked out|account lock|login", "access_or_availability_issue", False),
)


def _text(*parts: Any) -> str:
    values: list[str] = []
    for part in parts:
        if isinstance(part, dict):
            values.extend(str(value) for value in part.values() if value is not None)
        elif part is not None:
            values.append(str(part))
    return " ".join(values).lower()


def _matches(pattern: str, text: str) -> bool:
    return bool(re.search(pattern, text, flags=re.IGNORECASE))


def classify_ticket(
    title: str | None,
    description: str | None = None,
    raw: dict[str, Any] | None = None,
    notes_text: str | None = None,
) -> dict[str, Any]:
    text = _text(title, description, raw or {}, notes_text)

    for pattern, ticket_class, reason in EXCLUDED_PATTERNS:
        if _matches(pattern, text):
            return {
                "ticket_class": ticket_class,
                "is_support_issue": False,
                "is_system_generated": ticket_class in {"vendor_notice", "notification"},
                "analytics_exclude": True,
                "analytics_exclude_reason": reason,
            }

    for pattern, ticket_class, is_system_generated in SUPPORT_PATTERNS:
        if _matches(pattern, text):
            return {
                "ticket_class": ticket_class,
                "is_support_issue": True,
                "is_system_generated": is_system_generated,
                "analytics_exclude": False,
                "analytics_exclude_reason": None,
            }

    source = str((raw or {}).get("source") or "")
    ticket_type = str((raw or {}).get("ticketType") or "")
    system_generated = source == "8" or ticket_type == "5"
    return {
        "ticket_class": "general_support_issue",
        "is_support_issue": True,
        "is_system_generated": system_generated,
        "analytics_exclude": False,
        "analytics_exclude_reason": None,
    }


def ticket_class_label(ticket_class: str | None) -> str:
    labels = {
        "access_or_availability_issue": "Access or Availability",
        "admin_internal": "Internal Admin",
        "backup_alert": "Backup Alert",
        "disk_space_alert": "Disk Space Alert",
        "general_support_issue": "General Support",
        "meeting": "Meeting",
        "microsoft_365_issue": "Microsoft 365",
        "newsletter": "Newsletter",
        "notification": "Notification",
        "onsite_support": "Onsite Support",
        "printer_scan_issue": "Printer or Scan",
        "security_alert": "Security Alert",
        "training": "Training",
        "vendor_notice": "Vendor Notice",
        "vpn_issue": "VPN Issue",
    }
    return labels.get(ticket_class or "", "General Support")
