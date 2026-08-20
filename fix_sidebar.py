import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

vars_dark = {
    'var(--bg-base)': '#100e0c',
    'var(--bg-panel)': '#161210',
    'var(--bg-card)': '#1e1a17',
    'var(--bg-inset)': '#252019',
    'var(--bg-popover)': '#1a1612',
    'var(--border-main)': '#3d3530',
    'var(--text-primary)': '#d4cfc9',
    'var(--text-muted)': '#7a6f68',
    'var(--text-dim)': '#4a4038',
}

start_idx = content.find('/* ═══ 3. SIDEBAR')
end_idx = content.find('/* ═══ 5. HERO BANNER')

if start_idx != -1 and end_idx != -1:
    sidebar_css = content[start_idx:end_idx]
    for var, hex_val in vars_dark.items():
        sidebar_css = sidebar_css.replace(var, hex_val)
    
    new_content = content[:start_idx] + sidebar_css + content[end_idx:]
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Sidebar CSS fixed successfully.")
else:
    print("Could not find boundaries.")
