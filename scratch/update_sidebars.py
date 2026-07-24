import os
import re

base_dir = r"c:\Users\AUSHI SHARMA\Desktop\TENDER SEO AI AGENT\stitch_tenderiq_ai_platform"
pages = ["dashboard_tenderiq_ai", "opportunities_tenderiq_ai", "sources_tenderiq_ai", "ai_analysis_tenderiq_ai", "notifications_tenderiq_ai"]

nav_item = """<li>
<a class="flex items-center gap-3 px-3 py-2 rounded-lg text-secondary dark:text-secondary-fixed-dim hover:text-on-surface dark:hover:text-on-surface-variant hover:bg-surface-variant dark:hover:bg-surface-container-highest transition-colors duration-200" href="/notifications">
<span class="material-symbols-outlined" data-icon="notifications">notifications</span>
<span class="font-body-md text-body-md">Notification Center</span>
</a>
</li>
</ul>"""

for page in pages:
    path = os.path.join(base_dir, page, "code.html")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # We will just replace `</ul>` with our nav item and `</ul>`
    # But wait, there might be multiple `</ul>`s. Let's look for the Settings one.
    settings_item = """<span class="material-symbols-outlined" data-icon="settings">settings</span>
<span class="font-body-md text-body-md">Settings</span>
</a>
</li>
</ul>"""
    
    if settings_item in content:
        content = content.replace(settings_item, settings_item.replace("</ul>", nav_item))
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {page}")
    else:
        print(f"Settings item not found in {page}")
