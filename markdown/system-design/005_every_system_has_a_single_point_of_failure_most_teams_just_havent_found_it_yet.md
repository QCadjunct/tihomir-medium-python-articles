# Every System Has a Single Point of Failure — Most Teams Just Have Not Found It Yet

#### The component you forgot to make redundant is the one that will take everything down

**By Tihomir Manushev**

*Apr 2, 2026 · 5 min read*

---

October 21, 2016. A botnet of compromised security cameras, baby monitors, and printers launched a DDoS attack against Dyn, a DNS provider that handled roughly 10% of US nameserver traffic. Within hours, Twitter, Netflix, Reddit, PayPal, Amazon, GitHub, and Spotify were unreachable. Not because any of their servers were down — but because the internet could not find them. One DNS provider. No backup. Seventy-five percent of global DNS queries to those domains went unanswered.

Every team thinks about redundancy for databases and load balancers. Almost nobody thinks about it for DNS, certificate authorities, or the one engineer who knows how the deployment pipeline works. A single point of failure is any component whose failure takes down the system — and the most dangerous ones are the ones you forgot to check.

---

### The SPOFs You Already Know — And the Ones You Do Not

The obvious single points of failure get addressed early. A single database primary. A single application server. A single network link. These are covered in every architecture review because they are visible on the diagram.

The dangerous SPOFs are the invisible ones.

**Your DNS provider.** If Dyn taught anything, it is that DNS is infrastructure you do not think about until it disappears. Running a second DNS provider with automatic failover costs almost nothing relative to the blast radius of losing name resolution entirely. After the Dyn attack, 14,000 platforms — 8% of Dyn's customer base — migrated to multi-provider DNS strategies. The other 92% learned the lesson secondhand.

**Your CDN.** On June 8, 2021, a customer pushed a valid configuration change to Fastly that triggered a dormant bug deployed 27 days earlier. Within minutes, 85% of Fastly's network returned errors. Amazon, Reddit, the New York Times, and gov.uk all went down simultaneously. The irony: the synchronization mechanism that kept Fastly's global network consistent was the same mechanism that distributed the failure globally. Recovery took 49 minutes. The bug had been live for nearly a month.

**Your TLS certificates.** Eighty-one percent of companies have experienced a certificate-related outage in the past two years. Microsoft Teams went down for three hours in 2019 because an authentication certificate expired. The fix is monitoring and automated renewal — but the number of organizations that still track certificates in spreadsheets is staggering.

**Your one engineer.** The bus factor — how many people need to be hit by a bus before critical knowledge is lost. A bus factor of one means a single person's vacation, illness, or resignation creates an operational crisis. This is not a technical SPOF, but it takes systems down just as effectively.

---

### How to Find Them Before They Find You

SPOFs do not announce themselves. You have to look systematically.

**Dependency mapping** is the starting point. Draw every component, every service, every external provider, and every connection between them. Then ask one question for each: "What happens if this dies?" If the answer is "the system goes down" or "we cannot deploy fixes," you found a SPOF. Pay special attention to shared infrastructure — authentication services, config stores like Consul or etcd, service discovery, and CI/CD pipelines. These are load-bearing walls that rarely appear on the critical path in people's mental models.

**Pre-mortem analysis** inverts the usual postmortem. Instead of asking "what went wrong?" after an incident, assume the system has already failed catastrophically and work backward to identify what caused it. Research shows this technique increases the ability to correctly identify future failure causes by 30%. It surfaces risks that optimism bias hides.

**Chaos engineering** validates your assumptions with evidence. Netflix's Chaos Monkey has been randomly terminating production instances since 2011, forcing every service to handle failure gracefully. Game days — planned events where teams intentionally inject failures — test both technical systems and human response processes. Run them in staging first, then production. The failures you discover in a controlled setting are the ones that would have discovered you at 3 AM.

---

### Mitigation Is Not Just "Add Another One"

The instinct when you find a SPOF is to add redundancy. A second database. A second load balancer. A second DNS provider. This works — but naive redundancy creates new problems.

**Active-active** runs multiple identical instances simultaneously. If one fails, the others continue without interruption. This maximizes availability but requires load balancing, state synchronization, and conflict resolution. It is the most resilient and the most complex.

**Active-passive** keeps a standby instance that activates on failure. Simpler, cheaper, but the standby is idle until needed — and failover is not instant. The detection-election-switch cycle typically takes 6 to 60 seconds depending on the system.

**Graceful degradation** is the strategy most teams overlook. Not every component needs full redundancy. Some can fail partially. A recommendation engine going down should not take down the checkout flow — serve a generic "popular items" list instead. Circuit breakers isolate failing dependencies. Cached responses cover temporary outages. The goal is not zero downtime for every feature. It is zero downtime for the features that matter.

The meta-SPOF trap is real: the system you build to prevent failures can itself become a single point of failure. Facebook's 2021 outage lasted six hours partly because the internal audit tool that should have caught the BGP misconfiguration had its own software bug. The failover mechanism failed. Health check systems that go down silently leave you blind to the failures they were designed to detect. Configuration synchronization systems — like Fastly's — can turn one localized failure into a global one by faithfully distributing the problem to every node.

Every layer of redundancy adds complexity. Complexity hides new failure modes. The answer is not to avoid redundancy — it is to test it. A backup that has never been restored is not a backup. A failover that has never been triggered is not a failover. It is a hope.

---

### Conclusion

The CrowdStrike incident in July 2024 crashed 8.5 million Windows machines with a single faulty update. Estimated losses: $5.4 billion. The root cause was not a cyberattack — it was a single security vendor with kernel-level access deploying a uniform update to millions of endpoints simultaneously. One vendor. One update. One point of failure. The most expensive SPOFs are not the ones in your database layer. They are the ones in the components you never thought to question — your DNS, your CDN, your certificate renewal, your deployment pipeline, your vendor dependencies. Map them. Test them. Make the failure you discover intentional, or it will discover you on its own schedule.
