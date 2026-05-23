"""Interactive walkthrough: Syariah Court Inheritance Certificate (IC).

Asks yes/no and short-text questions, then prints a tailored documents
checklist and next-step plan you can take to the Syariah Court counter.

This is process navigation, not legal advice. Every step cites the
Syariah Court source page.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

SOURCE_PROCESS = "https://syariahcourt.gov.sg/Inheritance/Process/Application-for-Inheritance-Certificate"
SOURCE_FEES = "https://syariahcourt.gov.sg/Inheritance/Fees"
SOURCE_OVERVIEW = "https://syariahcourt.gov.sg/en/Inheritance/Overview"
MUIS_LINE = "6359 1199"
SC_LINE = "6354 8371"


@dataclass
class State:
    answers: dict[str, str] = field(default_factory=dict)
    documents: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)


def ask_yes_no(prompt: str, default: str | None = None) -> bool:
    suffix = (
        " [y/n]: " if default is None else f" [Y/n]: " if default == "y" else " [y/N]: "
    )
    while True:
        try:
            ans = input(prompt + suffix).strip().lower()
        except EOFError:
            return default == "y"
        if not ans and default is not None:
            return default == "y"
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        print("  Please answer y or n.")


def ask_text(prompt: str, allow_blank: bool = True) -> str:
    try:
        return input(prompt + ": ").strip()
    except EOFError:
        return ""


def banner() -> None:
    print("=" * 64)
    print("Syariah Court Inheritance Certificate, interactive walkthrough")
    print("=" * 64)
    print("This is process navigation, not legal advice.")
    print(f"Authoritative source: {SOURCE_OVERVIEW}")
    print()


def run() -> State:
    s = State()
    banner()
    print(
        "I will ask a few short questions. At the end you will get a tailored "
        "checklist you can print or save.\n"
    )

    # Core facts
    s.answers["deceased_name"] = ask_text(
        "Name of the deceased (or leave blank to skip)"
    )
    s.answers["death_certificate_in_hand"] = (
        "y"
        if ask_yes_no(
            "Do you have the digital death certificate from My Legacy?", default="y"
        )
        else "n"
    )
    if s.answers["death_certificate_in_hand"] != "y":
        s.steps.append(
            "Download the digital death certificate from My Legacy at "
            "https://mylegacy.life.gov.sg using your Singpass within 30 days of death."
        )
        s.documents.append("Digital death certificate (from My Legacy)")
    else:
        s.documents.append(
            "Digital death certificate (from My Legacy) -- already in hand"
        )

    s.answers["was_muslim_at_death"] = (
        "y"
        if ask_yes_no("Was the deceased Muslim at the time of death?", default="y")
        else "n"
    )
    if s.answers["was_muslim_at_death"] != "y":
        s.flags.append(
            "If the deceased was not Muslim, the Syariah Court does not have "
            "jurisdiction. Consult a lawyer about Letters of Administration under "
            "civil law."
        )

    s.answers["domiciled_singapore"] = (
        "y"
        if ask_yes_no("Was the deceased domiciled in Singapore?", default="y")
        else "n"
    )
    if s.answers["domiciled_singapore"] != "y":
        s.flags.append(
            "If domicile was outside Singapore, AMLA may still apply to Singapore "
            "assets but the picture is more complex. Consult a Syariah-experienced "
            "lawyer."
        )

    # Family structure
    s.answers["had_spouse"] = (
        "y"
        if ask_yes_no("Did the deceased have a surviving spouse?", default=None)
        else "n"
    )
    if s.answers["had_spouse"] == "y":
        s.documents.append("Surviving spouse NRIC / FIN / passport")
        s.documents.append("Marriage certificate (Singapore or overseas)")
        s.steps.append(
            "For multiple wives (where applicable), prepare each marriage "
            "certificate and the NRIC of each surviving wife."
        )

    s.answers["had_children"] = (
        "y"
        if ask_yes_no(
            "Did the deceased have any children (biological, adopted, step)?",
            default=None,
        )
        else "n"
    )
    if s.answers["had_children"] == "y":
        s.documents.append(
            "Birth certificates and NRIC of each child (biological children only "
            "are faraid heirs; include step or adopted children for completeness)"
        )

    s.answers["parents_alive"] = (
        "y"
        if ask_yes_no(
            "Were either of the deceased's parents alive at the time of death?",
            default=None,
        )
        else "n"
    )
    if s.answers["parents_alive"] == "y":
        s.documents.append("NRIC or identification of surviving parent(s)")
        s.steps.append(
            "Parents are faraid heirs. Their shares depend on whether the deceased "
            "had children; include their details in the application."
        )

    s.answers["had_siblings"] = (
        "y"
        if ask_yes_no("Did the deceased have any surviving siblings?", default=None)
        else "n"
    )
    if s.answers["had_siblings"] == "y":
        s.documents.append(
            "NRIC of each surviving sibling (relevant in some family structures)"
        )
        s.steps.append(
            "Siblings may inherit when there are no children and no parents. The "
            "Syariah Court online tool will determine if they are needed in your case."
        )

    # Heirs overseas
    s.answers["heirs_overseas"] = (
        "y"
        if ask_yes_no("Are any of the heirs currently overseas?", default=None)
        else "n"
    )
    if s.answers["heirs_overseas"] == "y":
        s.steps.append(
            "Overseas heirs can be named in the IC without attending in person. "
            "At the probate or Letters of Administration stage at the Family "
            "Justice Courts, they may need to issue a Letter of Authorisation "
            "to a Singapore representative."
        )
        s.documents.append("Passport copy of each overseas heir")

    # Minors
    s.answers["minors"] = (
        "y"
        if ask_yes_no("Are any of the heirs minors (below 21)?", default=None)
        else "n"
    )
    if s.answers["minors"] == "y":
        s.steps.append(
            "Minor heirs are included in the IC by their parent or legal guardian. "
            "The Family Justice Courts may require a trustee to be appointed for "
            "the minor's share at the probate / LA stage. Consider a lawyer if "
            "property or large CPF / insurance amounts are involved."
        )

    # Wasiat
    s.answers["wasiat_exists"] = (
        "y"
        if ask_yes_no("Did the deceased leave a wasiat (Islamic will)?", default=None)
        else "n"
    )
    if s.answers["wasiat_exists"] == "y":
        s.steps.append(
            "Bring the wasiat to the Syariah Court. After the IC is issued, you will "
            "apply for a Grant of Probate at the Family Justice Courts. The wasiat "
            "can dispose of up to 1/3 of the net estate to non-faraid heirs."
        )
        s.documents.append("Original wasiat document and any executor identification")
    else:
        s.steps.append(
            "Without a wasiat, you will apply for Letters of Administration at the "
            "Family Justice Courts after the IC is issued."
        )

    # Asset complexity
    s.answers["foreign_property"] = (
        "y"
        if ask_yes_no("Did the deceased own property outside Singapore?", default=None)
        else "n"
    )
    if s.answers["foreign_property"] == "y":
        s.flags.append(
            "Foreign property is governed by the law of that country. The IC handles "
            "Singapore-based assets; engage a lawyer for cross-border estate steps."
        )

    s.answers["business_interest"] = (
        "y"
        if ask_yes_no(
            "Did the deceased own a business or unlisted shares?", default=None
        )
        else "n"
    )
    if s.answers["business_interest"] == "y":
        s.flags.append(
            "Business interests can be complex. Consult a lawyer; the business may "
            "need a valuation and the company constitution may govern transfer."
        )

    # Always-needed documents
    s.documents.append("Deceased's NRIC, FIN, or passport")
    s.documents.append(
        "List of assets (property, bank accounts, CPF, insurance, shares, vehicles)"
    )
    s.documents.append("List of debts (mortgage, loans, credit cards)")

    # Always-needed steps
    s.steps.extend(
        [
            f"Apply online via the SYC Portal at {SOURCE_PROCESS}. Log in with "
            "SingPass (individuals) or CorpPass (firms). Foreign applicants may "
            "apply for a SYCPass.",
            "Pay the $34 application fee by PayNow, eNETS, or credit card. "
            f"Fee schedule: {SOURCE_FEES}.",
            "Processing is within 7 days. Validity window is 60 days from first "
            "submission.",
            "Once approved, download the Statutory Declaration template from your "
            "dashboard, complete it, and affirm it before a Commissioner for Oaths.",
            "Upload the affirmed Statutory Declaration. After verification, the IC "
            "is issued in PDF for download via the portal.",
            "Bring a printout of the IC and the digital death certificate to each "
            "institution (bank, CPF, HDB, insurer, broker, LTA) to release assets.",
        ]
    )

    return s


def print_summary(s: State) -> None:
    print()
    print("=" * 64)
    print("Your tailored checklist")
    print("=" * 64)
    print(f"Authoritative source: {SOURCE_PROCESS}")
    if s.answers.get("deceased_name"):
        print(f"Deceased: {s.answers['deceased_name']}")
    print()

    print("Documents to gather:")
    for d in s.documents:
        print(f"  [ ] {d}")
    print()

    print("Steps to take:")
    for i, step in enumerate(s.steps, 1):
        print(f"  {i}. {step}")
    print()

    if s.flags:
        print("Flags to discuss with a Syariah-experienced lawyer:")
        for f in s.flags:
            print(f"  ! {f}")
        print()

    print("Contacts:")
    print(f"  Syariah Court Singapore: {SC_LINE} (Mon to Fri 8:30am to 5pm)")
    print(f"  MUIS for religious questions: {MUIS_LINE}")
    print()
    print(
        "This walkthrough is process navigation, not legal advice. For complex "
        "estates, consult a Singapore Syariah-experienced lawyer."
    )


def main() -> int:
    s = run()
    print_summary(s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
