# huijo-skills

Agent Skills written to the open [Agent Skills](https://docs.github.com/copilot/concepts/agents/about-agent-skills) standard — a folder containing `SKILL.md` with YAML frontmatter (`name`, `description`) plus optional references and assets.

Nothing here is tied to a single agent. Any host that implements the Agent Skills standard can load these skills, including Codex, Claude Code, GitHub Copilot CLI, and Kiro CLI.

## Skills

| Skill | What it does |
| --- | --- |
| [`architecture-spec`](architecture-spec/SKILL.md) | Produces a two-layer architecture specification as a self-contained HTML report: a plain-language section for product and engineering readers, plus an architect appendix covering contracts, dependency direction, invariants, failure policy, migration, tests, and acceptance criteria. Inspects the codebase first, then resolves open design decisions one question per turn. |

## Install

### With GitHub CLI (recommended)

`gh skill` resolves the correct directory per agent, so you do not need to remember paths. `--scope user` installs globally; drop it to install into the current repository only.

```bash
gh skill install huijoson/huijo-skills architecture-spec --agent codex          --scope user
gh skill install huijoson/huijo-skills architecture-spec --agent claude-code    --scope user
gh skill install huijoson/huijo-skills architecture-spec --agent github-copilot --scope user
gh skill install huijoson/huijo-skills architecture-spec --agent kiro-cli       --scope user
```

Run `gh skill install --help` for the full list of supported agents (Cursor, Gemini CLI, Amp, Goose, and others).

Already have the repo cloned? Install from disk instead:

```bash
gh skill install . architecture-spec --from-local --agent claude-code --scope user
```

### Manual copy

Clone, then copy the skill directory into your agent's skills directory.

```bash
git clone https://github.com/huijoson/huijo-skills.git
cd huijo-skills
```

| Agent | Personal (all projects) | Project-scoped |
| --- | --- | --- |
| Codex | `~/.codex/skills/` | — |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| GitHub Copilot CLI | `~/.copilot/skills/` or `~/.agents/skills/` | `.github/skills/`, `.claude/skills/`, or `.agents/skills/` |
| Kiro CLI | `~/.kiro/skills/` | — |

```bash
# example: personal install for Claude Code
mkdir -p ~/.claude/skills
cp -R architecture-spec ~/.claude/skills/
```

Or use the bundled helper, which installs into every agent it detects on your machine:

```bash
./install.sh              # detected agents, personal scope
./install.sh --list       # show what would be installed, change nothing
./install.sh claude-code  # one specific agent
```

## Use

The agent loads a skill when your prompt matches its `description`, so plain language works:

```text
請產生這次權限模組改動的白話架構圖與架構師附錄
```

You can also name the skill explicitly. The prefix differs by agent:

| Agent | Invocation |
| --- | --- |
| Codex | `$architecture-spec <topic>` |
| Claude Code | `/architecture-spec <topic>` |
| Copilot CLI | `/architecture-spec <topic>` |
| Kiro CLI | `architecture-spec <topic>` |

In Copilot CLI, `/skills list` shows loaded skills and `/skills reload` picks up a skill added mid-session.

## Notes

`architecture-spec/agents/openai.yaml` carries optional Codex-only presentation metadata (display name, default prompt). Other agents ignore unknown files in a skill directory, so it is harmless to leave in place.

This skill is documentation-and-analysis only. It does not modify product code, create commits, or publish ADRs unless you separately ask for that.
