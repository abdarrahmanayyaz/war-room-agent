#!/bin/bash
echo "WAR ROOM — Setting up..."
python3 -m venv venv
source venv/bin/activate
pip install streamlit anthropic requests beautifulsoup4 lxml
mkdir -p data
# Initialize empty JSON files if they don't exist
for f in applications.json scouted.json outreach.json followups.json daily_log.json; do
    [ ! -f "data/$f" ] && echo "[]" > "data/$f"
done
echo ""
echo "Setup complete. Run: source venv/bin/activate && streamlit run app.py"
echo ""
echo "Optional: Install auto-scout (runs daily at 7am):"
echo "  python scheduler.py install"
