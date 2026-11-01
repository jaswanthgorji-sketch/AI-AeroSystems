# AI AeroSystems Flight Simulator

A Streamlit-based, interactive aviation-themed simulator with six selectable aircraft:
- Boeing 737-800, 777-300ER, 787-9
- Airbus A320neo, A350-900, A380-800

## Run it on macOS, Windows, or Linux

1. Install Python 3.10 or newer.
2. Unzip this folder.
3. Open Terminal (macOS/Linux) or Command Prompt (Windows) in this folder.
4. Install dependencies:

   `python -m pip install -r requirements.txt`

5. Start the simulator:

   `python -m streamlit run app.py`

6. Your browser should open the local simulator. If it does not, visit `http://localhost:8501`.

## Included features
- Flight phases from gate through taxi, takeoff, climb, cruise, descent, approach, landing, taxi-in and arrival.
- Interactive simulated ATC radio requests and pilot readbacks.
- Cockpit-style PFD, speed, altitude, vertical speed, heading, ground speed, engine, fuel and navigation displays.
- Aircraft selection, route setup, weather, wind, autopilot selectors and manual phase advancement.

## Important
This is a simplified educational/entertainment simulator. Aircraft performance, weather, navigation, cockpit indications and ATC phraseology are illustrative, not operationally accurate. It must not be used for real-world flight planning, pilot training, or aviation decisions.
