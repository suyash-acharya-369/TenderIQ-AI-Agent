import os
import re

base_dir = r"c:\Users\AUSHI SHARMA\Desktop\TENDER SEO AI AGENT\stitch_tenderiq_ai_platform"
opp_file = os.path.join(base_dir, "opportunities_tenderiq_ai", "code.html")
notif_file = os.path.join(base_dir, "notifications_tenderiq_ai", "code.html")

with open(opp_file, 'r', encoding='utf-8') as f:
    opp_content = f.read()

# Extract from <html> to </head> (but we want to keep our own title)
# Actually, let's just extract the tailwind config and styles from <head>
head_match = re.search(r'(<script id="tailwind-config".*?</style>)', opp_content, re.DOTALL)
head_boilerplate = head_match.group(1) if head_match else ""

# Extract <aside> block
aside_match = re.search(r'(<nav class="hidden md:flex.*?</nav>)', opp_content, re.DOTALL)
aside_html = aside_match.group(1) if aside_match else ""

# Extract <header> block
header_match = re.search(r'(<header.*?</header>)', opp_content, re.DOTALL)
header_html = header_match.group(1) if header_match else ""

with open(notif_file, 'r', encoding='utf-8') as f:
    notif_content = f.read()

# Inject tailwind
if "</head>" in notif_content and head_boilerplate:
    notif_content = notif_content.replace("</head>", f"{head_boilerplate}\n</head>")

# Replace sidebar-container with aside
if '<div id="sidebar-container"></div>' in notif_content:
    notif_content = notif_content.replace('<div id="sidebar-container"></div>', aside_html)

# Replace header-container with header
if '<div id="header-container"></div>' in notif_content:
    # Need to wrap main content in the flex-1 div like other pages to make aside work
    wrapper_start = '<div class="flex-1 flex flex-col min-h-screen ml-0 md:ml-64 w-full">\n' + header_html
    notif_content = notif_content.replace('<div id="header-container"></div>', wrapper_start)
    notif_content = notif_content.replace('</main>\n    </div>', '</main>\n    </div>\n    </div>')

with open(notif_file, 'w', encoding='utf-8') as f:
    f.write(notif_content)

print("Layout stitched successfully.")
