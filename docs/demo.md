# Demo

[![skillsible demo](./skillsible-demo.gif)](./skillsible-demo.gif)

`docs/skillsible-demo.cast` is the source recording used to generate the GIF above.

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

## Transcript

```text
$ uv run skillsible validate -f /tmp/tmp.u92k1ls4yq/skills.yml
Valid manifest: /tmp/tmp.u92k1ls4yq/skills.yml
- agents: codex, claude-code
- skills: 1
- tools: 1
- mcps: 0

$ uv run skillsible lock -f /tmp/tmp.u92k1ls4yq/skills.yml -o /tmp/tmp.u92k1ls4yq/skillsible.lock
Wrote lockfile: /tmp/tmp.u92k1ls4yq/skillsible.lock
- skills: 1
- tools: 1
- mcps: 0

$ uv run skillsible diff -f /tmp/tmp.u92k1ls4yq/skills.yml -l /tmp/tmp.u92k1ls4yq/skillsible.lock
No drift: /tmp/tmp.u92k1ls4yq/skills.yml matches /tmp/tmp.u92k1ls4yq/skillsible.lock

$ uv run skillsible plan -f /tmp/tmp.u92k1ls4yq/skills.yml -l /tmp/tmp.u92k1ls4yq/skillsible.lock
Plan for /tmp/tmp.u92k1ls4yq/skills.yml
- install writing-clearly-and-concisely for codex from /tmp/tmp.u92k1ls4yq/demo-skill-repo @ 85d5609b92a046bee1b1bd7871180df00e8c21c6 [global]
- install writing-clearly-and-concisely for claude-code from /tmp/tmp.u92k1ls4yq/demo-skill-repo @ 85d5609b92a046bee1b1bd7871180df00e8c21c6 [global]
- tool gh for codex [cli] (binary=gh)
- tool gh for claude-code [cli] (binary=gh)

$ uv run skillsible apply --dry-run -f /tmp/tmp.u92k1ls4yq/skills.yml -l /tmp/tmp.u92k1ls4yq/skillsible.lock
$ npx skills add /tmp/tmp.u92k1ls4yq/demo-skill-repo @ 85d5609b92a046bee1b1bd7871180df00e8c21c6 --skill writing-clearly-and-concisely --agent codex -y -g
$ npx skills add /tmp/tmp.u92k1ls4yq/demo-skill-repo @ 85d5609b92a046bee1b1bd7871180df00e8c21c6 --skill writing-clearly-and-concisely --agent claude-code -y -g
$ command -v gh
$ command -v gh
```

## Files

- Recording: [`docs/skillsible-demo.cast`](./skillsible-demo.cast)
- Script: [`scripts/demo_session.sh`](../scripts/demo_session.sh)
