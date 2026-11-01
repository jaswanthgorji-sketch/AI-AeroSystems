import math
import random
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AI AeroSystems | Flight Deck", page_icon="✈️", layout="wide")

AIRCRAFT = {
    "Boeing 737-800": {"family": "BOEING", "cruise": 410, "ceiling": 41000, "engines": 2, "range": "Short / medium haul"},
    "Boeing 777-300ER": {"family": "BOEING", "cruise": 490, "ceiling": 43100, "engines": 2, "range": "Long haul"},
    "Boeing 787-9": {"family": "BOEING", "cruise": 488, "ceiling": 43000, "engines": 2, "range": "Long haul"},
    "Airbus A320neo": {"family": "AIRBUS", "cruise": 405, "ceiling": 39800, "engines": 2, "range": "Short / medium haul"},
    "Airbus A350-900": {"family": "AIRBUS", "cruise": 488, "ceiling": 43100, "engines": 2, "range": "Long haul"},
    "Airbus A380-800": {"family": "AIRBUS", "cruise": 490, "ceiling": 43000, "engines": 4, "range": "Very long haul"},
}
PHASES = ["Gate", "Taxi", "Takeoff", "Climb", "Cruise", "Descent", "Approach", "Landing", "Taxi-in", "Arrived"]
PHASE_ATC = {
    "Gate": ("GROUND", "AIRO 241, request IFR clearance and start-up."),
    "Taxi": ("GROUND", "AIRO 241, taxi to runway 22 via taxiway Alpha. Hold short."),
    "Takeoff": ("TOWER", "AIRO 241, wind 220 at 08 knots, runway 22, cleared for takeoff."),
    "Climb": ("DEPARTURE", "AIRO 241, radar contact. Climb and maintain flight level 350."),
    "Cruise": ("CENTER", "AIRO 241, maintain flight level 350. Expect further clearance as filed."),
    "Descent": ("CENTER", "AIRO 241, descend to 10,000 feet. Reduce speed as appropriate."),
    "Approach": ("APPROACH", "AIRO 241, turn heading 220, descend to 3,000 feet. Expect ILS runway 22."),
    "Landing": ("TOWER", "AIRO 241, runway 22, cleared to land. Wind 220 at 06 knots."),
    "Taxi-in": ("GROUND", "AIRO 241, vacate runway when able and taxi to stand 14."),
    "Arrived": ("GROUND", "AIRO 241, taxi to stand 14. Welcome and good day."),
}
NEXT = {p: PHASES[min(i+1, len(PHASES)-1)] for i, p in enumerate(PHASES)}

def init_state():
    defaults = {
        "phase": "Gate", "altitude": 0, "ias": 0, "heading": 220,
        "distance": 0.0, "fuel": 96.0, "radio": [], "minute": 0,
        "autopilot": False, "paused": False, "clearance": False,
        "last_phase": "Gate", "vs": 0, "engine": 0.0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def add_radio(sender, text):
    st.session_state.radio.append((sender, text))
    st.session_state.radio = st.session_state.radio[-14:]

def phase_targets(phase, cruise_alt, cruise_speed):
    targets = {
        "Gate": (0, 0, 0), "Taxi": (0, 18, 0), "Takeoff": (1500, 145, 220),
        "Climb": (cruise_alt, cruise_speed, 350), "Cruise": (cruise_alt, cruise_speed, 0),
        "Descent": (10000, 280, -1500), "Approach": (3000, 180, -700),
        "Landing": (0, 145, -500), "Taxi-in": (0, 15, 0), "Arrived": (0, 0, 0)
    }
    return targets[phase]

def move_toward(value, target, step):
    if value < target: return min(value + step, target)
    return max(value - step, target)

init_state()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] {font-family: Inter, sans-serif;}
.stApp {background: radial-gradient(ellipse at 50% -20%, #1b3a53 0%, #0a1724 48%, #07111b 100%); color:#e7f1f8;}
.block-container {padding-top:1.2rem; max-width:1500px;}
h1,h2,h3 {font-family:'Barlow Condensed',sans-serif; letter-spacing:1.4px;}
div[data-testid="stMetric"] {background:#102538; border:1px solid #24465d; padding:12px 14px; border-radius:9px;}
div[data-testid="stMetricLabel"] {color:#91afc3;}
div[data-testid="stMetricValue"] {color:#e9f6ff;}
.panel {background:linear-gradient(145deg,#11283a,#0b1b2a); border:1px solid #24465d; border-radius:12px; padding:16px; margin-bottom:12px;}
.eyebrow {font-size:11px; color:#62c6d8; letter-spacing:2px; font-weight:700;}
.bigread {font-family:'Barlow Condensed'; font-size:34px; font-weight:700; color:#eaf7ff;}
.subread {font-size:11px; color:#8eacbf; letter-spacing:1px;}
.radio {background:#07131e;border:1px solid #26495f;border-radius:8px;padding:10px 12px;margin:6px 0;}
.pilot {color:#7bd4e7;font-weight:700;font-size:11px;letter-spacing:1px;}
.atc {color:#f5c66b;font-weight:700;font-size:11px;letter-spacing:1px;}
.radio-text {color:#dce9f1;font-size:13px;margin-top:4px;}
.phase {display:inline-block;padding:5px 10px;border-radius:5px;background:#123c4d;color:#7be0e5;font-weight:700;letter-spacing:1px;font-size:12px;}
.small {font-size:12px;color:#8da9bb;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="eyebrow">AI AEROSYSTEMS · FLIGHT SIMULATION SUITE</div>', unsafe_allow_html=True)
st.title("✈️ FLIGHT DECK")
st.caption("DESKTOP SIMULATOR  /  TRAINING & ENTERTAINMENT MODE  /  NOT FOR REAL-WORLD FLIGHT OPERATIONS")

with st.sidebar:
    st.markdown("## FLIGHT SETUP")
    aircraft = st.selectbox("Aircraft", list(AIRCRAFT.keys()))
    info = AIRCRAFT[aircraft]
    st.markdown(f"**{info['family']}** · {info['engines']} engines")
    st.caption(f"{info['range']} · Simulated cruise: {info['cruise']} kt")
    st.divider()
    st.markdown("### ROUTE")
    origin = st.text_input("Departure", "Helsinki (EFHK)")
    destination = st.text_input("Arrival", "Stockholm (ESSA)")
    route_nm = st.slider("Route distance (nautical miles)", 80, 3000, 250)
    st.divider()
    st.markdown("### ENVIRONMENT")
    weather = st.selectbox("Weather", ["CAVOK / Clear", "Scattered cloud", "Overcast", "Light rain", "Thunderstorm (visual only)"])
    wind_dir = st.slider("Wind direction", 0, 359, 220)
    wind_speed = st.slider("Wind speed (kt)", 0, 45, 8)
    temperature = st.slider("Outside temperature (°C)", -35, 35, 12)
    st.divider()
    st.markdown("### FLIGHT CONTROLS")
    ap = st.toggle("Autopilot", value=st.session_state.autopilot)
    st.session_state.autopilot = ap
    selected_heading = st.slider("Heading bug", 0, 359, int(st.session_state.heading))
    selected_altitude = st.select_slider("Altitude selector (ft)", options=[0, 3000, 5000, 10000, 15000, 20000, 25000, 30000, 35000, 39000], value=35000)
    selected_speed = st.slider("Speed selector (kt)", 120, 510, int(info["cruise"]))
    st.session_state.paused = st.toggle("Pause simulation", value=st.session_state.paused)
    if st.button("↻ Reset flight", use_container_width=True):
        for key in ["phase","altitude","ias","heading","distance","fuel","radio","minute","clearance","last_phase","vs","engine"]:
            if key in st.session_state: del st.session_state[key]
        st.rerun()

st.session_state.autopilot = ap
st.session_state.heading = selected_heading if ap else st.session_state.heading

# Header status
c1,c2,c3,c4 = st.columns([1.4,1,1,1])
with c1:
    st.markdown(f'<div class="panel"><div class="eyebrow">ACTIVE FLIGHT</div><div class="bigread">AIRO 241</div><div class="small">{origin} → {destination}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="panel"><div class="eyebrow">AIRCRAFT</div><div class="bigread" style="font-size:23px">{aircraft}</div><div class="small">{info["engines"]} × turbofan · {info["family"]}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="panel"><div class="eyebrow">FLIGHT PHASE</div><div style="margin-top:8px"><span class="phase">{st.session_state.phase.upper()}</span></div><div class="small" style="margin-top:9px">SIM T+ {st.session_state.minute:03d} MIN</div></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="panel"><div class="eyebrow">WEATHER</div><div class="bigread" style="font-size:23px">{wind_speed:02d} KT</div><div class="small">{weather} · {wind_dir:03d}° / {temperature}°C</div></div>', unsafe_allow_html=True)

# Flight state update
phase = st.session_state.phase
cruise_alt = min(35000, info["ceiling"] - 2000)
target_alt, target_speed, target_vs = phase_targets(phase, cruise_alt, info["cruise"])
if st.session_state.autopilot and phase in ("Climb","Cruise","Descent","Approach"):
    target_alt = selected_altitude if phase in ("Climb","Cruise") else target_alt
    target_speed = selected_speed if phase in ("Climb","Cruise") else target_speed
    st.session_state.heading = selected_heading

# Manual controls
left, right = st.columns([1.65,1])
with left:
    st.markdown("### PRIMARY FLIGHT DISPLAY")
    alt = int(st.session_state.altitude)
    ias = int(st.session_state.ias)
    hdg = int(st.session_state.heading)
    pitch = max(-18, min(18, int(st.session_state.vs / 180)))
    bank = 0 if st.session_state.autopilot else 0
    sky_y = 50 + pitch * 1.3
    st.markdown(f"""
    <div class="panel" style="padding:12px">
      <div style="display:flex;justify-content:space-between;margin-bottom:8px">
        <span class="eyebrow">PFD · PRIMARY FLIGHT DISPLAY</span><span class="small">SIM DATA · NOT CERTIFIED</span>
      </div>
      <div style="height:260px;border-radius:8px;overflow:hidden;position:relative;background:linear-gradient(to bottom,#1c6d9a 0%,#4b91ad 49%,#c0a36c 50%,#765c43 100%);border:2px solid #47677b">
        <div style="position:absolute;left:0;right:0;top:{sky_y}%;height:2px;background:#fff;box-shadow:0 0 4px #fff"></div>
        <div style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:100px;height:44px;border-top:3px solid #ffd75d;border-bottom:3px solid #ffd75d;clip-path:polygon(0 0,40% 0,50% 40%,60% 0,100% 0,100% 25%,60% 25%,50% 70%,40% 25%,0 25%);"></div>
        <div style="position:absolute;left:12px;top:12px;color:white;font:700 12px monospace">SPD<br><span style="font-size:23px">{ias:03d}</span><br>KT</div>
        <div style="position:absolute;right:12px;top:12px;text-align:right;color:white;font:700 12px monospace">ALT<br><span style="font-size:23px">{alt:05d}</span><br>FT</div>
        <div style="position:absolute;left:12px;bottom:12px;color:white;font:700 12px monospace">V/S<br><span style="font-size:19px">{int(st.session_state.vs):+d}</span><br>FPM</div>
        <div style="position:absolute;right:12px;bottom:12px;text-align:right;color:white;font:700 12px monospace">HDG<br><span style="font-size:23px">{hdg:03d}</span><br>MAG</div>
        <div style="position:absolute;left:50%;bottom:12px;transform:translateX(-50%);background:#09131dcc;color:#f7d56b;padding:4px 12px;border-radius:4px;font:700 12px monospace">AIRO 241</div>
      </div>
      <div style="display:flex;justify-content:space-between;padding:10px 4px 0;color:#9cb8c8;font:11px monospace">
        <span>FD {'ON' if st.session_state.autopilot else 'OFF'}</span><span>AP {'ENGAGED' if st.session_state.autopilot else 'DISENGAGED'}</span><span>BARO 1013</span><span>ILS { 'ARMED' if phase in ('Approach','Landing') else 'STBY'}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### FLIGHT INSTRUMENTS")
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("ALTITUDE", f"{alt:,} ft", f"{int(st.session_state.vs):+,} fpm")
    m2.metric("AIRSPEED", f"{ias} kt", f"{ias-info['cruise']:+d} vs cruise")
    m3.metric("HEADING", f"{hdg:03d}°", "MAG")
    m4.metric("GROUND SPEED", f"{max(0, ias + wind_speed*math.cos(math.radians(wind_dir-hdg))):.0f} kt", "wind adjusted")
    e1,e2,e3 = st.columns(3)
    e1.metric("ENGINE N1", f"{st.session_state.engine:.1f}%", "simulated")
    e2.metric("FUEL", f"{st.session_state.fuel:.1f}%", "remaining")
    e3.metric("DISTANCE", f"{st.session_state.distance:.1f} NM", f"of {route_nm} NM")

    st.markdown("### NAVIGATION DISPLAY")
    progress = min(100, st.session_state.distance / route_nm * 100)
    st.progress(progress/100, text=f"ROUTE PROGRESS  ·  {progress:.1f}%")
    st.markdown(f'<div class="panel"><div class="eyebrow">FMS ROUTE</div><div style="display:flex;justify-content:space-between;align-items:center;margin:10px 0"><b>{origin}</b><span style="color:#61c9d9">━━━━━━✈━━━━━━</span><b>{destination}</b></div><div class="small">DIRECT ROUTE · TRACK {hdg:03d}° · WIND {wind_dir:03d}/{wind_speed:02d} · ETA ESTIMATE {max(0,(route_nm-st.session_state.distance)/max(100,ias)*60):.0f} MIN</div></div>', unsafe_allow_html=True)

with right:
    st.markdown("### ATC RADIO · COM1")
    freq = PHASE_ATC[phase][0]
    st.markdown(f'<div class="panel"><div class="eyebrow">ACTIVE FREQUENCY</div><div class="bigread">{freq} · {{"GROUND":"121.700","TOWER":"118.100","DEPARTURE":"120.300","CENTER":"127.500","APPROACH":"119.100"}[freq]} MHz</div><div class="small">CALLSIGN AIRO 241 · SIMULATED ATC</div></div>', unsafe_allow_html=True)
    if not st.session_state.radio:
        add_radio("ATC", "AIRO 241, this is the AI AeroSystems simulation. Select REQUEST to begin.")
    for sender, msg in reversed(st.session_state.radio[-8:]):
        cls = "pilot" if sender == "PILOT" else "atc"
        st.markdown(f'<div class="radio"><div class="{cls}">{sender}</div><div class="radio-text">{msg}</div></div>', unsafe_allow_html=True)

    b1,b2 = st.columns(2)
    if b1.button("📡 ATC REQUEST", use_container_width=True):
        if phase == "Gate":
            add_radio("PILOT", f"{freq}, AIRO 241 at stand, request IFR clearance to {destination}.")
            add_radio("ATC", "AIRO 241, cleared to destination as filed. Squawk 2410. Start-up approved.")
            st.session_state.clearance = True
        else:
            add_radio("PILOT", f"{freq}, AIRO 241, request instructions.")
            add_radio("ATC", PHASE_ATC[phase][1])
        st.rerun()
    if b2.button("🗣️ READ BACK", use_container_width=True):
        add_radio("PILOT", f"AIRO 241, copied. {PHASE_ATC[phase][1]}")
        st.rerun()

    st.markdown("### FLIGHT MANAGEMENT")
    st.markdown(f'<div class="panel"><div class="eyebrow">ACTIVE FLIGHT PLAN</div><div class="small">AIRCRAFT · {aircraft}</div><div class="small">ORIGIN · {origin}</div><div class="small">DESTINATION · {destination}</div><div class="small">CRUISE LEVEL · FL{cruise_alt//100:03d}</div><div class="small">AUTOPILOT · {"ENGAGED" if ap else "OFF"}</div></div>', unsafe_allow_html=True)
    if phase not in ("Arrived",):
        if st.button(f"▶ ADVANCE TO {NEXT[phase].upper()}", type="primary", use_container_width=True):
            if phase == "Gate" and not st.session_state.clearance:
                add_radio("ATC", "AIRO 241, obtain IFR clearance before taxi in this simulation.")
            else:
                st.session_state.phase = NEXT[phase]
                st.session_state.minute += 3
                add_radio("ATC", PHASE_ATC[st.session_state.phase][1])
                st.rerun()
    if st.button("⏩ SIMULATE 1 MINUTE", use_container_width=True):
        st.session_state.minute += 1
        st.rerun()
    st.caption("Advance phase-by-phase, or let the instruments update with each simulated minute.")

# A simulation tick is deliberately user-controlled for predictable browser performance.
if st.session_state.minute > 0 and not st.session_state.paused:
    # Move aircraft toward phase targets on each rerun/tick.
    st.session_state.altitude = move_toward(st.session_state.altitude, target_alt, 1200 if phase in ("Climb","Descent","Approach") else 500)
    st.session_state.ias = move_toward(st.session_state.ias, target_speed, 18)
    st.session_state.vs = target_vs if st.session_state.altitude != target_alt else 0
    st.session_state.engine = move_toward(st.session_state.engine, 82 if phase in ("Takeoff","Climb") else 48 if phase=="Cruise" else 35, 8)
    if phase in ("Cruise","Climb","Descent","Approach"):
        st.session_state.distance = min(route_nm, st.session_state.distance + max(0.1, st.session_state.ias/60))
    st.session_state.fuel = max(0, st.session_state.fuel - (0.035 if info["engines"]==2 else 0.06))

st.markdown("---")
st.markdown('<div class="small">AI AEROSYSTEMS v1.0 · All aircraft data and flight behaviour are simplified fictional simulation values. This project is for learning and entertainment only; it is not an approved flight-training device, aircraft systems replica, navigation source, or ATC service.</div>', unsafe_allow_html=True)
