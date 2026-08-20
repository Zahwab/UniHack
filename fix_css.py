import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define variables for the dark theme (these were the hardcoded ones)
vars_dark = {
    '--bg-base': '#100e0c',
    '--bg-panel': '#161210',
    '--bg-card': '#1e1a17',
    '--bg-inset': '#252019',
    '--bg-popover': '#1a1612',
    '--border-main': '#3d3530',
    '--text-primary': '#d4cfc9',
    '--text-muted': '#7a6f68',
    '--text-dim': '#4a4038',
}

# The replacements (reverse mapping)
replacements = {v: f'var({k})' for k, v in vars_dark.items()}

# We only want to replace these in specific parts of the CSS (not hero banner or sidebar if we want them dark).
# Actually, if we want the sidebar to switch themes too, we should replace them everywhere. Let's replace everywhere except hero banner.
# Actually, the user said "UI UX are not relatable fix all", meaning light mode should probably apply everywhere (or sidebar can stay dark, let's keep sidebar dark for contrast, but main content light).

# Let's just replace all occurrences of these hex colors in the main CSS block (between <style> and </style>).
# We'll inject the :root definition at the top of the CSS block.

root_css = """:root {
    --bg-base:      #100e0c;
    --bg-panel:     #161210;
    --bg-card:      #1e1a17;
    --bg-inset:     #252019;
    --bg-popover:   #1a1612;
    --accent-fire:  #e85d04;
    --accent-teal:  #00b4d8;
    --accent-gold:  #f4a261;
    --accent-green: #52b788;
    --accent-red:   #e63946;
    --border-main:  #3d3530;
    --text-primary: #d4cfc9;
    --text-muted:   #7a6f68;
    --text-dim:     #4a4038;
}
"""

style_start = content.find('<style>')
style_end = content.find('</style>')

css_content = content[style_start+7:style_end]

# Don't touch hero banner colors
hero_start = css_content.find('/* ═══ 5. HERO BANNER ═══ */')
hero_end = css_content.find('/* ═══ 6. METRIC TILES ═══ */')

css_before_hero = css_content[:hero_start]
css_hero = css_content[hero_start:hero_end]
css_after_hero = css_content[hero_end:]

for hex_val, var_val in replacements.items():
    css_before_hero = css_before_hero.replace(hex_val, var_val)
    css_after_hero = css_after_hero.replace(hex_val, var_val)

new_css_content = '\\n' + root_css + css_before_hero + css_hero + css_after_hero

new_content = content[:style_start+7] + new_css_content + content[style_end:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("CSS variables injected successfully.")
