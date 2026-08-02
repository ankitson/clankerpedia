# Toolbox helpers. Skill distribution is owned by the devdocker/dotfiles chezmoi
# wiring. These commands only refresh external snapshots in the canonical tree.

# Compose AGENTS.md from context/fragments via bin/frag. Run after editing a
# fragment, ~/AGENTS.env.md, or the wiki INDEX.md.
agents:
  @bin/frag context/templates/AGENTS.md.j2 -I context/fragments -I ~ -I ~/hroot/allplace/wiki -o AGENTS.md

skills-list:
  @bin/skillctl list

skills-check:
  @bin/skillctl check

skills-test:
  python -B -m unittest discover -s tests -v

summarize-test:
  python -B -m unittest discover -s bin/tests -p 'test_summarize.py' -v

test-td-reschedule-overdue:
  python -B -m unittest discover -s bin/tests -p 'test_td_reschedule_overdue.py' -v

web-clip-test:
  python -B -m unittest discover -s tests -p 'test_web_clip.py' -v

web-clip-browser-test:
  WEB_CLIP_BROWSER_TEST=1 python -B -m unittest discover -s tests -p 'test_web_clip.py' -v

skills-sync *names:
  @bin/skillctl sync {{names}}

skills-add source *args:
  @bin/skillctl add {{source}} {{args}}

skills-router name *args:
  @bin/skillctl router {{name}} {{args}}

web-clip url output="clips":
  @bin/web-clip {{url}} -o {{output}}

summarize *args:
  @bin/summarize {{args}}

network-listeners *args:
  @bin/network-listeners {{args}}

wezterm-win-trace *args:
  @bin/wezterm-win-trace {{args}}

# Show the build+deploy plan for keeping every host on one wezterm commit (dry-run).
wezterm-sync *args:
  @bin/wezterm-sync {{args}}

# Build the canonical ref and deploy to every reachable host (server + mac + windows).
wezterm-sync-apply ref="main" *args:
  @bin/wezterm-sync --ref {{ref}} --apply {{args}}

# Kept as a short alias for interactive use.
list: skills-list

# Run the focused regression test for the scheduled WezTerm sender.
test-resume-session:
  python -B -m unittest discover -s bin/tests -v

# Run the focused regression test for the remote editor launcher.
test-remeddy:
  python -B -m unittest discover -s bin/tests -p 'test_remeddy.py' -v
