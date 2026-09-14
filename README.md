# huijo-skills

Agent Skills written to the open [Agent Skills](https://docs.github.com/copilot/concepts/agents/about-agent-skills) standard — a folder containing `SKILL.md` with YAML frontmatter (`name`, `description`) plus optional references and assets.

Nothing here is tied to a single agent. Any host that implements the Agent Skills standard can load these skills, including Codex, Claude Code, GitHub Copilot CLI, and Kiro CLI.

## Skills

| Skill | What it does |
| --- | --- |
| [`architecture-spec`](architecture-spec/SKILL.md) | Produces a two-layer architecture specification as a self-contained HTML report: a plain-language section for product and engineering readers, plus an architect appendix covering contracts, dependency direction, invariants, failure policy, migration, tests, and acceptance criteria. Inspects the codebase first, then resolves open design decisions one question per turn. |
| [`odoo-operations-report`](odoo-operations-report/SKILL.md) | 將 Odoo MCP 操作結果或既有維運紀錄整理為 HTML 與 Markdown 報告；沿用已確認的欄位與修訂，核對時間推算、流程結果及證據範圍。 |

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
| Antigravity | `~/.gemini/config/skills/` | `.agents/skills/` |

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
| Antigravity | `architecture-spec <topic>` 或自然語言觸發 (在 Antigravity 中開頭 `/` 為 UI 內建系統捷徑，自訂技能透過名稱或語意觸發) |

In Copilot CLI, `/skills list` shows loaded skills and `/skills reload` picks up a skill added mid-session.

## Notes

`architecture-spec/agents/openai.yaml` carries optional Codex-only presentation metadata (display name, default prompt). Other agents ignore unknown files in a skill directory, so it is harmless to leave in place.

`architecture-spec` 僅負責文件與分析；修改產品程式碼、建立 commit 或發佈 ADR 需另有使用者要求。`odoo-operations-report` 僅整理已有維運結果並產出報告，操作執行由對應工作流程處理。

## Odoo 維運報告

將 `odoo-operations-report/` 複製到使用中 Agent 的技能目錄即可使用；上方的 `install.sh` 也會自動發現這個技能。技能附有 HTML 與 Markdown 範本，預設輸出兩種格式，也可指定其中一種。

```text
使用 odoo-operations-report 將上述 Odoo MCP 結果整理成 HTML 與 Markdown 報告。
沿用最後確認的欄位；完成時間缺漏時，以執行開始時間加總耗時推算並註明。
```

預設不列啟動請求時間、待確認清單及獨立的日誌確認章節；使用者可依需要指定加入。實際報告可能含內部主機資訊，發佈技能時僅保留通用範本。
