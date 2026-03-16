"""
Demo seed data constants -- shared between demo_runner.py and routers/demo.py.
"""

DEMO_TRANSCRIPT = """[00:00] Vignesh Kumar (HivePro): Good morning Sarah, Mike. Thanks for joining the Q1 review.

[00:15] Sarah Chen (Acme Corp): Thanks Vignesh. We have a few things to discuss today. Overall we're happy with the platform but there are some concerns.

[01:30] Vignesh: Let's start with the wins. Your vulnerability detection rate improved 23% this quarter, and mean-time-to-remediate dropped from 14 days to 9 days.

[02:00] Sarah: That's great to hear. Our board was pleased with the reduction in critical findings. The CISO specifically mentioned HivePro in his last update.

[03:15] Mike Torres (Acme Corp): On the technical side though, we've been having issues with the Qualys connector since the 4.3.0 update. Scans on our DMZ subnet 10.0.2.0/24 are returning incomplete results -- about 40% fewer assets detected than before.

[04:00] Vignesh: I'm aware of that ticket, CS-142. It's been escalated to our engineering team. We identified a regression in the asset discovery module.

[05:00] Mike: When can we expect a fix? Our next compliance audit is in three weeks and we need full coverage.

[05:30] Vignesh: Engineering has a hotfix targeted for next Tuesday. I'll make sure you get early access to the patch. We'll also run a validation scan together to confirm full coverage.

[06:30] Sarah: Good. Also, our renewal is coming up in April. We'd like to discuss expanding to cover our new APAC datacenter -- about 5000 additional assets across Singapore and Tokyo.

[08:00] Vignesh: Absolutely. I'll have our team prepare a scope expansion proposal by end of week. We have a new APAC deployment option that might reduce latency for those sites.

[09:00] Mike: One more thing -- we've been evaluating CrowdStrike's vulnerability management module as a potential complement. Not a replacement, but we want to understand where the overlap is and whether it makes sense to consolidate.

[10:00] Vignesh: I understand. Let me set up a technical comparison session with our product team so we can walk through the differentiation clearly.

[11:30] Sarah: That would be helpful. We're not looking to replace HivePro -- the threat intelligence integration is our main reason for staying. But the board is asking us to rationalize our security stack.

[12:00] Sarah: Before we wrap up, I want to make sure the P1 ticket from last week about the scanner outage is fully resolved. It affected our compliance audit timeline.

[13:00] Vignesh: Confirmed -- that was resolved on Friday. The root cause was a memory leak in the scan orchestrator. I'll send you the RCA report today.

[14:00] Mike: Can we get a technical deep-dive session with your engineering team next week? I want to understand the architecture changes in 4.3.0 better.

[15:00] Vignesh: I'll set that up for Wednesday or Thursday. Let me summarize the action items:
1. Hotfix for Qualys connector by Tuesday
2. Scope expansion proposal for APAC by Friday
3. CrowdStrike comparison session within two weeks
4. RCA report for scanner outage sent today
5. Technical deep-dive session next week

[16:00] Sarah: Perfect. Thanks Vignesh. Talk soon.

[16:15] Vignesh: Thank you Sarah, Mike. Have a great day."""


DEMO_TICKET = {
    "jira_id": "DEMO-001",
    "summary": (
        "Critical: HivePro scanner failing to detect vulnerabilities "
        "on 10.0.2.0/24 subnet after Qualys connector update to v4.3.0"
    ),
    "description": (
        "Since upgrading the Qualys connector to v4.3.0 last Tuesday, "
        "vulnerability scans on subnet 10.0.2.0/24 (DMZ) are returning "
        "approximately 40% fewer assets than before the upgrade. This is "
        "affecting our compliance posture ahead of next month's audit. "
        "The issue appears to be specific to the asset discovery module -- "
        "scans on other subnets are functioning normally. We need this "
        "resolved urgently as our compliance window closes in 3 weeks."
    ),
    "severity": "P1",
}
