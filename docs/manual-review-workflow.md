# Manual review workflow

MAIE deliberately holds opportunities for a person to inspect before any alert is sent:

```text
Collector -> Opportunity Queue -> Manual Review -> Approved -> Notification
```

When opportunity analysis persists a viable deal through `OpportunityRepository`, MAIE
automatically creates its `Queue` record. A queue record is unique per opportunity, so the
same opportunity has one review lifecycle.

## Statuses

| Status | Meaning |
| --- | --- |
| `NEW` | Awaiting a reviewer. |
| `REVIEWING` | A reviewer is inspecting the opportunity. |
| `APPROVED` | The opportunity passed review and is eligible for notification. |
| `REJECTED` | The opportunity failed review and must not be notified. |
| `ARCHIVED` | The queue item is retained for history but is no longer active. |

The queue repository records the review time for every status change and retains optional
review notes. Notification consumers must select only `APPROVED` queue items; opportunity
analysis must persist items through `OpportunityRepository` rather than directly calling
notification providers.

## CLI

All commands use the configured database. `--database-url` is useful for a separate SQLite
file, for example during local testing.

```bash
maie queue list
maie queue list --status new
maie queue review <queue-id> --notes "Checking photos"
maie queue approve <queue-id> --notes "Condition and margin verified"
maie queue reject <queue-id> --notes "Missing accessories"
maie queue archive <queue-id>
```

Each command prints the queue item ID, status, related opportunity ID, and its notes.
