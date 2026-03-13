# Demo

`docs/skillsible-demo.cast` is an asciinema recording, so GitHub shows it as raw JSON instead of
playing it inline.

Use one of these paths instead:

## Play locally

```bash
uvx --from asciinema asciinema play docs/skillsible-demo.cast
```

## Re-record locally

```bash
chmod +x scripts/demo_session.sh
TERM=xterm-256color uvx --from asciinema asciinema rec -q -c "./scripts/demo_session.sh" docs/skillsible-demo.cast
```

## What the demo covers

- `skillsible validate`
- `skillsible lock`
- `skillsible diff`
- `skillsible plan`
- `skillsible apply --dry-run`

## Files

- Recording: [`docs/skillsible-demo.cast`](./skillsible-demo.cast)
- Script: [`scripts/demo_session.sh`](../scripts/demo_session.sh)
