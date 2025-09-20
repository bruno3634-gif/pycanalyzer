# filter_demo.py
"""
Demo script showing CAN message filtering capabilities
"""

def demo_info():
    print("""
🎯 CAN Message Filtering Demo

Your CAN analyzer now supports advanced message filtering with multiple options:

📊 MAIN WINDOW FILTERING:
1. Go to 'Filters' menu
2. Choose 'Configure Main Window Filters...'
3. Add IDs to Include Filter (show only these) OR Exclude Filter (hide these)
4. Enable the filter via 'Filters' > 'Enable Main Window Include/Exclude Filter'

🔍 SEPARATE FILTER WINDOWS:
1. Go to 'Filters' menu
2. Choose 'Include Only Window' - shows only specified IDs
3. Choose 'Exclude Window' - hides specified IDs
4. Add IDs manually or use 'Auto-Add Active IDs' button

✨ FEATURES:
• Real-time filtering of CAN messages
• Support for multiple ID formats (0x100, 256, decimal)
• Auto-detection of active message IDs
• Separate windows for focused analysis
• Production/development mode compatibility

🎛️ DEMO SCENARIOS:

Scenario 1: Focus on specific ECU
- Open 'Include Only Window'
- Add IDs 0x100, 0x101 
- See only those messages

Scenario 2: Remove noisy messages  
- Open 'Exclude Window'
- Add ID 0x104
- See all messages except 0x104

Scenario 3: Main window filtering
- Use 'Configure Main Window Filters'
- Add include IDs: 0x100, 0x102
- Enable 'Main Window Include Filter'
- Main table shows only those IDs


""")

if __name__ == "__main__":
    demo_info()
