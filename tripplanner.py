import streamlit as st
import requests
import json
import os 
from collections import OrderedDict 
import pandas as pd
import random 

# --- CONFIGURATION AND DATA (UNCHANGED) ---

# IMPORTANT: Ensure your GROQ_API_KEY is securely set in your environment variables 
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")

CITY_PLACES = OrderedDict([
    ("Delhi", {"Religious": ["Lotus Temple", "Akshardham"], "Adventurous": ["Hauz Khas Village nightlife"], "Nature/History": ["India Gate", "Red Fort", "Qutub Minar", "Humayun's Tomb"]}),
    ("Jaipur", {"Religious": ["Govind Dev Ji Temple"], "Adventurous": ["Hot Air Ballooning"], "Nature/History": ["Hawa Mahal", "City Palace", "Amber Fort", "Jantar Mantar", "Nahargarh Fort"]}),
    ("Agra", {"Religious": [], "Adventurous": [], "Nature/History": ["Taj Mahal", "Agra Fort", "Fatehpur Sikri", "Mehtab Bagh", "Tomb of Itimad-ud-Daulah"]}),
    ("Goa", {"Religious": ["Basilica of Bom Jesus"], "Adventurous": ["Water Sports (Baga)", "Dudhsagar Falls trip"], "Nature/History": ["Baga Beach", "Fort Aguada", "Anjuna Flea Market", "Palolem Beach"]}),
    ("Mumbai", {"Religious": ["Siddhivinayak Temple"], "Adventurous": ["Trekking near Mumbai"], "Nature/History": ["Gateway of India", "Marine Drive", "Elephanta Caves", "Juhu Beach", "CSMT"]}),
])

CITY_DETAILS = {
    "Delhi": {
        "transport": {"mode": "Delhi Metro (fast, air-conditioned, *cheapest option), *Uber/Ola, Auto-rickshaws.", "cost": "Metro fares are low (₹10-60). Daily travel budget: ₹200-₹500."},
        "food": {"Budget": "Karim's, Khan Chacha, Moolchand Paranthe.", "Mid-Range": "Rajinder Da Dhaba, Indian Coffee House.", "Luxury": "Bukhara (ITC)."}
    },
    "Jaipur": {
        "transport": {"mode": "Auto-rickshaws (negotiate/apps), Metro (limited but cheap), Self-drive cabs.", "cost": "Metro fare: ₹25-₹30 max. Daily travel budget: ₹300-₹600."},
        "food": {"Budget": "Lassiwala, Rawat Kachori.", "Mid-Range": "Spice Court, Peacock Rooftop.", "Luxury": "Suvarna Mahal."}
    },
    "Agra": {
        "transport": {"mode": "Auto-rickshaws (bargain essential), Electric Cabs (Taj zone), Walking.", "cost": "Auto-rickshaw fares: ₹50-₹200 for short routes. Daily travel budget: ₹300-₹700."},
        "food": {"Budget": "Joney's Place, Mama Chicken.", "Mid-Range": "Pinch of Spice, Sheroes Hangout.", "Luxury": "Peshawri (ITC)."}
    },
    "Goa": {
        "transport": {"mode": "Rented Scooters (₹300-₹500/day, *cheapest transport), *Pilots (Bike Taxi).", "cost": "Taxi rates are high; scooter rental is the key. Daily travel budget: ₹400-₹1000."},
        "food": {"Budget": "Beach Shacks, Noronha's Corner.", "Mid-Range": "Viva Panjim, Florentine.", "Luxury": "Thalassa."}
    },
    "Mumbai": {
        "transport": {"mode": "Local Trains (*cheapest and fastest lifeline), *Uber/Ola, Kaali-Peeli Taxi (metered).", "cost": "Local train tickets are minimal (₹5-₹20). Daily travel budget: ₹150-₹400."},
        "food": {"Budget": "Bademiya, Kyani & Co., Vada Pav stalls.", "Mid-Range": "Cafe Mondegar, Leopold.", "Luxury": "The Table."}
    },
}

CHEAP_OPTIONS = {
    "Delhi": {
        "Accommodation": "Gurdwara Bangla Sahib (Yatri Niwas) - Very Low-Cost / Contribution Based accommodation.", 
        "Food": "Free Langar at Gurdwara Bangla Sahib (Daily, for everyone).", 
        "Tip": "Langar is the best free food source. Book Yatri Niwas in advance.",
        "Savings_Food": 150, 
        "Savings_Stay": 400 
    },
    "Jaipur": {
        "Accommodation": "Jaipur Gujarati Samaj (Low-Cost Rooms/Dorm), Subsidized stays at ISKCON Guest House.", 
        "Food": "Subsidized Bhojanalaya at Gujarati Samaj (very cheap Thali meals).", 
        "Tip": "The Gujarati Samaj offers excellent value for both lodging and food near the city center.",
        "Savings_Food": 100,
        "Savings_Stay": 350
    },
    "Agra": {
        "Accommodation": "Various community Dharamshalas and Sikh Gurdwaras (for basic, often free/low-cost stays).", 
        "Food": "Free Langar at Agra Gurdwaras. Look for Annadanam (free meals) at major temples on festivals.", 
        "Tip": "Street food near the Taj East Gate is the cheapest way to eat. Always negotiate rickshaw fares.",
        "Savings_Food": 150,
        "Savings_Stay": 300
    },
    "Goa": {
        "Accommodation": "GTDC Residencies / Hostels (~₹450+) off-season.", 
        "Food": "Local Thali places (Fish/Veg Thali - the cheapest consistent option).", 
        "Tip": "Rent a scooter (₹300-₹500/day) for the cheapest transport. Prices skyrocket in peak season.",
        "Savings_Food": 0, 
        "Savings_Stay": 0
    },
    "Mumbai": {
        "Accommodation": "Shri Guru Singh Sabha (Dadar Gurudwara) - Low-Cost / Donation Based rooms.", 
        "Food": "Free Langar at Dadar Gurudwara. Vada Pav and Puri Bhaji from local street stalls are the cheapest meals.", 
        "Tip": "The local train/bus system is extremely cheap. The Gurudwara is one of the best value options in the city.",
        "Savings_Food": 180,
        "Savings_Stay": 450
    }
}

# --- AI GENERATION FUNCTION FOR ONE DAY (DYNAMIC) ---

def generate_single_day_itinerary(city, day_number, total_days, places_left, current_budget_status, travel_style, budget_level, preferences, num_people, per_person_budget):
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    budget_injection = ""
    local_lingo = ""

    if travel_style in ["Adventurous", "Culture/History"]:
        if city in ["Delhi", "Jaipur", "Agra"]:
            local_lingo = "When taking an auto-rickshaw, use the phrase 'Kitne ka hai?' (How much is it?) and be prepared to negotiate 20% off the quoted price."
        elif city in ["Mumbai"]:
            local_lingo = "For black/yellow taxis, insist on the meter ('Meter se chalo')."
    
    local_transport_mode = CITY_DETAILS.get(city, {}).get("transport", {}).get("mode", "local transport.")
    
    # --- BUDGET ADJUSTMENT INJECTION (The Core Dynamic Logic) ---
    if current_budget_status.get("status") == "OVER BUDGET":
        over_amount = current_budget_status.get("amount")
        budget_injection = f"CRITICAL BUDGET RECALCULATION: The group is OVER BUDGET by ₹{over_amount:,} from previous days. For Day {day_number}, **you must STRONGLY prioritize free or low-cost activities and the cheapest transport. Estimated costs must be minimal."
    elif current_budget_status.get("status") == "UNDER BUDGET":
        under_amount = current_budget_status.get("amount")
        budget_injection = f"BUDGET STATUS: The group is UNDER BUDGET by ₹{under_amount:,}. You have slight flexibility. You may include one moderately priced attraction or a slightly better food option."
    else:
         budget_injection = f"BUDGET STATUS: The group is ON TRACK. Plan Day {day_number} according to the strict daily budget of ₹{per_person_budget} per person."
    # --- END BUDGET ADJUSTMENT INJECTION ---

    
    prompt = f"""
    You are an expert travel planner creating Day {day_number} of a {total_days}-day trip for {city}.
    Group size: {num_people}. Daily budget for activities/transport: ₹{per_person_budget}.
    
    {budget_injection}
    
    The remaining available places are: {', '.join(places_left)}.
    
    **Task: Plan only Day {day_number}.**
    
    Select and order the best places from the remaining list that fit the *{travel_style}* priority and the current *budget status*.
    The itinerary MUST consider the budget.
    
    Assign a short description (20-30 words), an estimated visit duration (e.g., "2 hours"), and a travel note for each place.
    ***CRITICAL: The travel note MUST include:
    1. A specific budget-appropriate food or restaurant suggestion (matching the {budget_level} style) near the attraction.
    2. A precise, cost-saving transport tip based on the city's {local_transport_mode} (e.g., 'Take the Metro' or 'Rent a scooter').
    3. If applicable for Budget/Adventurous styles, include the Local Lingo Tip: "{local_lingo}".***
    
    Return ONLY a single JSON object. The structure MUST be:
    {{
      "Day {day_number}": [
        {{ "place": "Place Name A", "description": "Short summary.", "duration": "Duration", "notes": "Tip with food, precise transport, and optional lingo." }},
        ...
      ],
      "Estimated_Costs": {{ "estimated_entry_cost_group": 0, "estimated_transport_cost_group": 0 }} 
    }}
    Ensure the estimated costs are group totals and are strictly conservative.
    """

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "You are a professional travel planner. Respond ONLY with the requested JSON object. Adhere strictly to the JSON schema."},
            {"role": "user", "content": prompt} 
        ],
        "temperature": 0.5,
        "response_format": {"type": "json_object"} 
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            st.error(f"AI API Error: Status Code {response.status_code}. Response: {response.text}")
            return None
            
        content = response.json()["choices"][0]["message"]["content"]
        parsed_data = json.loads(content)
        
        if f"Day {day_number}" not in parsed_data or "Estimated_Costs" not in parsed_data:
            st.warning("AI did not return the expected structure. Using mock data.")
            mock_entry = 200 * num_people
            mock_transport = 200 * num_people
            parsed_data = {
                f"Day {day_number}": [{"place": "Fallback Plan (Check Places)", "description": "Budget plan failed.", "duration": "Full Day", "notes": "Check API key and prompt structure."}],
                "Estimated_Costs": {"estimated_entry_cost_group": mock_entry, "estimated_transport_cost_group": mock_transport}
            }
        
        return parsed_data

    except (json.JSONDecodeError, KeyError) as e:
        st.error(f"AI Response Error: Could not parse AI's response into JSON. Error: {e}")
        return None

# --- UTILITY FUNCTION FOR SAVINGS CALCULATIONS ---

def calculate_savings(city, num_people):
    cheap_data = CHEAP_OPTIONS.get(city, {})
    food_savings_per_day = cheap_data.get("Savings_Food", 0) * 2 
    stay_savings_per_day = cheap_data.get("Savings_Stay", 0) 
    total_savings = (food_savings_per_day + stay_savings_per_day) * num_people
    return total_savings

# --- STREAMLIT APP ---
st.set_page_config(page_title="SmartTrip AI: Dynamic Budget Planner", layout="wide")

# --- SESSION STATE INITIALIZATION ---
if 'current_city' not in st.session_state: st.session_state.current_city = "Delhi"
if 'planning_active' not in st.session_state: st.session_state.planning_active = False
if 'planned_days' not in st.session_state: st.session_state.planned_days = 0
if 'full_itinerary' not in st.session_state: st.session_state.full_itinerary = {}
if 'places_to_visit' not in st.session_state: st.session_state.places_to_visit = []
if 'total_actual_spend' not in st.session_state: st.session_state.total_actual_spend = 0
if 'total_planned_budget' not in st.session_state: st.session_state.total_planned_budget = 0
if 'daily_actual_expenses' not in st.session_state: st.session_state.daily_actual_expenses = {}
if 'day_data_current' not in st.session_state: st.session_state.day_data_current = {}
# New state for the toggle button
if 'show_cheap_options' not in st.session_state: st.session_state.show_cheap_options = False


# --- CUSTOM CSS BLOCK (UNCHANGED) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;600;800&display=swap');
html, body, p, h1, h2, h3, h4, h5, h6, li, div, label, span, button {
    font-family: 'Poppins', sans-serif;
}
.stButton>button {
    background-color: #FF6B6B; 
    color: white;
    font-weight: 600;
    padding: 10px 24px;
    border-radius: 12px;
    border: 2px solid #FF6B6B;
    transition: all 0.2s ease-in-out;
    box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
}
.trip-tip-box {
    background-color: #f7f9f9; 
    padding: 15px;
    border-radius: 10px;
    border-left: 5px solid #007BFF; 
    margin-top: 10px;
    font-size: 0.9em;
}
</style>
""", unsafe_allow_html=True)

# --- MAIN LAYOUT ---
st.title("💸 SmartTrip AI: Dynamic Budget Planner")
st.caption("Plans your trip day-by-day, adjusting the next day's itinerary based on your actual spending.")
st.divider()

# --- SIDEBAR (UNCHANGED) ---
with st.sidebar:
    st.header("⚙ Plan Configuration")
    
    with st.expander("1. Destination & Group", expanded=True):
        city = st.selectbox("Destination City", list(CITY_PLACES.keys()))
        
        # Reset state on city change
        if city != st.session_state.current_city:
            st.session_state.current_city = city
            st.session_state.planning_active = False
            st.session_state.planned_days = 0
            st.session_state.full_itinerary = {}
            st.session_state.daily_actual_expenses = {}
            st.session_state.total_actual_spend = 0
            st.session_state.total_planned_budget = 0
            st.session_state.day_data_current = {}
            st.session_state.show_cheap_options = False # Reset the toggle
            
        col_d, col_p = st.columns(2)
        days = col_d.slider("Days", 1, 5, 3)
        num_people = col_p.slider("People", 1, 10, 2)

    with st.expander("2. Budget & Style", expanded=True):
        per_person_budget = st.number_input("Daily Budget (₹)", 500, 10000, 1500, 100)
        budget_level = st.radio("Style", ["Budget", "Mid-Range", "Luxury"], index=1)

    with st.expander("3. Interests", expanded=True):
        travel_style = st.selectbox("Priority", ["Culture/History", "Religious", "Nature/Relaxed", "Adventurous"])
        preferences = st.text_area("Notes", "Local coffee, walking tours...")

    with st.expander("4. Select Places", expanded=False):
        all_places = [p for sub in CITY_PLACES[city].values() for p in sub]
        selected_places = st.multiselect("Select Places", all_places, default=all_places[:4], key=f'places_{city}')


# ------------------------------------------------------------------
# --- RELOCATED: MUST TRY FOOD PLACES SECTION ---
# ------------------------------------------------------------------

city_food_data = CITY_DETAILS.get(city, {}).get("food", {})

st.header("🍜 Local Delights: Must-Try Food Places")
st.markdown("Use these recommendations for meals when traveling between itinerary points.")
col_b, col_m, col_l = st.columns(3)

col_b.subheader("💰 Budget")
col_b.info(city_food_data.get("Budget", "N/A"))

col_m.subheader("🍽 Mid-Range")
col_m.info(city_food_data.get("Mid-Range", "N/A"))

col_l.subheader("💎 Luxury")
col_l.info(city_food_data.get("Luxury", "N/A"))

st.divider()

# ------------------------------------------------------------------
# --- NEW SECTION: TRAVEL TIPS & LOCAL HACKS ---
# ------------------------------------------------------------------

st.header("🗺 Travel Tips & Local Hacks")
city_data = CITY_DETAILS.get(city, {})
cheap_data = CHEAP_OPTIONS.get(city, {})

st.subheader("🚎 Transportation Guide")
st.markdown(f"*Primary Modes:* {city_data.get('transport', {}).get('mode', 'N/A')}")
st.markdown(f"*Expected Cost/Day:* {city_data.get('transport', {}).get('cost', 'N/A')}")

# Toggle function
def toggle_cheap_options():
    st.session_state.show_cheap_options = not st.session_state.show_cheap_options
    st.rerun() # Re-run script to show/hide the content

button_label = "💡 Hide Extreme Budget Options" if st.session_state.show_cheap_options else "🚨 Show Extreme Budget Options (Free/Cheap Stay & Food)"

if st.button(button_label, type="secondary", on_click=toggle_cheap_options):
    pass # Handled by the toggle function

if st.session_state.show_cheap_options:
    st.subheader("🆓 Cheapest/Free Options (For Ultra-Budget Travelers)")
    col_acc, col_food = st.columns(2)
    
    with col_acc:
        st.markdown("*Accommodation (Low-Cost/Donation-Based)*")
        st.warning(cheap_data.get('Accommodation', 'N/A'))
        
    with col_food:
        st.markdown("*Free/Cheapest Consistent Food*")
        st.warning(cheap_data.get('Food', 'N/A'))
        
    st.caption(f"*Pro Tip:* {cheap_data.get('Tip', 'N/A')}")

st.divider()

# ------------------------------------------------------------------
# --- START PLANNING BUTTON ---
# ------------------------------------------------------------------

if st.button("✨ START Day-by-Day Planning", type="primary"):
    if not selected_places:
        st.error("Please select places in the sidebar.")
    else:
        # Reset state and initialize for planning
        st.session_state.planned_days = 0
        st.session_state.full_itinerary = {}
        st.session_state.daily_actual_expenses = {}
        st.session_state.places_to_visit = selected_places[:] 
        st.session_state.total_actual_spend = 0
        st.session_state.day_data_current = {}
        
        total_group_budget = num_people * per_person_budget
        st.session_state.total_planned_budget = total_group_budget * days 
        
        st.session_state.planning_active = True
        st.rerun() 

# --- DYNAMIC PLANNING LOOP ---

if st.session_state.get('planning_active', False):
    
    total_group_budget = num_people * per_person_budget
    current_day_key = f"Day {st.session_state.planned_days + 1}"
    
    # Check if we are planning or waiting for input
    if st.session_state.planned_days < days:
        
        # --- CONDITIONAL CHECK FOR PLAN GENERATION ---
        if current_day_key not in st.session_state.full_itinerary:
            
            # 1. CALCULATE CURRENT BUDGET STATUS (Based on prior days' actual spending)
            days_completed = st.session_state.planned_days
            budget_for_days_completed = total_group_budget * days_completed
            budget_variance = budget_for_days_completed - st.session_state.total_actual_spend
            
            current_budget_status = {"status": "ON TRACK", "amount": 0}
            if budget_variance > 0:
                current_budget_status = {"status": "UNDER BUDGET", "amount": budget_variance}
            elif budget_variance < 0:
                current_budget_status = {"status": "OVER BUDGET", "amount": abs(budget_variance)}
            
            # 2. GENERATE NEXT DAY'S ITINERARY
            with st.spinner(f"AI is dynamically planning {current_day_key}... (Current Status: {current_budget_status['status']})"):
                day_data = generate_single_day_itinerary(
                    city, current_day_key[4:], days, st.session_state.places_to_visit, current_budget_status, 
                    travel_style, budget_level, preferences, num_people, per_person_budget
                )
                
            if day_data:
                # Store the plan and cost estimates
                st.session_state.full_itinerary[current_day_key] = day_data[current_day_key]
                st.session_state.day_data_current = day_data # Store the estimates/status needed for the form
                
                # Update places left
                planned_places = [item['place'] for item in day_data[current_day_key]]
                st.session_state.places_to_visit = [p for p in st.session_state.places_to_visit if p not in planned_places]
            else:
                st.error("Failed to retrieve the itinerary for this day. Planning halted.")
                st.session_state.planning_active = False
                st.stop() 

        
        # --- DISPLAY THE PLAN AND THE EXPENSE FORM FOR THE CURRENT DAY ---
        
        day_data = st.session_state.day_data_current 
        
        days_completed = st.session_state.planned_days
        budget_for_days_completed = total_group_budget * days_completed
        budget_variance = budget_for_days_completed - st.session_state.total_actual_spend
        current_budget_status = {"status": "ON TRACK", "amount": abs(budget_variance)}
        
        st.subheader(f"Planning {current_day_key}: Budget Check")
        st.info(f"*Overall Budget Status:* {current_budget_status['status']} by *₹{current_budget_status['amount']:,}* based on your spending for the first {days_completed} day(s).")
        st.divider()

        st.header(f"📅 {current_day_key} Plan")
        
        for item in st.session_state.full_itinerary[current_day_key]:
            st.markdown(f"{item.get('place')}** ({item.get('duration')})")
            st.caption(item.get('description'))
            st.markdown(f"<div class='trip-tip-box'>👉 {item.get('notes')}</div>", unsafe_allow_html=True)
            st.markdown("---")

        # --- DAILY EXPENSE INPUT FORM ---
        with st.form(key=f'expense_form_{current_day_key}'):
            st.markdown(f"{current_day_key}: Actual Expenses Tracking**")
            
            estimated_costs = day_data["Estimated_Costs"]
            total_estimated_daily = estimated_costs.get('estimated_entry_cost_group', 0) + estimated_costs.get('estimated_transport_cost_group', 0)
            
            food_incidental_guess = total_group_budget - total_estimated_daily
            if food_incidental_guess < 0: food_incidental_guess = 0
            
            estimated_total_spend = total_estimated_daily + food_incidental_guess
            
            st.info(f"AI Estimated Group Cost (Activities/Transport): *₹{total_estimated_daily:,}* (Daily Group Budget: ₹{total_group_budget:,})")
            
            actual_expense = st.number_input(
                f"Input *Total Group Spend* for {current_day_key} (All Expenses including Food)", 
                min_value=0, 
                value=estimated_total_spend if estimated_total_spend > 0 else 1500,
                step=100
            )
            
            submitted = st.form_submit_button("✅ Save Expenses & Plan Next Day", type="primary")

            if submitted:
                # Update state and trigger the next planning iteration
                st.session_state.daily_actual_expenses[current_day_key] = actual_expense
                st.session_state.total_actual_spend += actual_expense
                st.session_state.planned_days += 1
                st.rerun() 
        
        # Safely halt the script to wait for the form submission
        st.stop() 
    
    # If the loop finished (all days planned)
    else:
        st.session_state.planning_active = False
        st.success("🎉 Trip planning complete! Review the full report below.")

# --- DISPLAY FULL REPORT (ONLY AFTER PLANNING IS COMPLETE) ---

if st.session_state.get('planned_days', 0) == days:
    
    st.header("✨ Full Trip Summary")
    
    # --- Langar/Dharamshala Savings Metric ---
    if budget_level.startswith("Budget"):
        total_savings_potential = calculate_savings(city, num_people) * days
        st.info(
            f"💡 *Hyper-Budget Saving Score:* By utilizing local low-cost options, your group could potentially save *₹{total_savings_potential:,}* over your {days}-day trip!"
        )
        st.divider()

    # The Transportation/Cheap Options display is now earlier in the script, so only the report remains here.
    
    # --- FINAL EXPENSE REPORT (Actual Spend vs. Budget) ---
    st.header("🧾 Final Expense Report (Actual Spend vs. Budget)")
    
    total_trip_budget = st.session_state.total_planned_budget
    total_actual_spend = st.session_state.total_actual_spend
    variance = total_trip_budget - total_actual_spend
    
    c_act1, c_act2, c_act3 = st.columns(3)
    
    c_act1.metric("Total Planned Budget", f"₹{total_trip_budget:,}")
    c_act2.metric("Total Actual Spend", f"₹{total_actual_spend:,}")
    
    if variance >= 0:
        c_act3.metric("Budget Variance (Savings)", f"₹{variance:,}", "Under Budget")
        st.success("🎉 FINAL STATUS: You completed the trip under budget!")
    else:
        c_act3.metric("Budget Variance (Overrun)", f"₹{abs(variance):,}", f"₹{abs(variance):,}", delta_color="inverse")
        st.error("⚠ FINAL STATUS: The trip exceeded the total budget. The AI applied cost-cutting measures, but spending was high.")
        
    st.subheader("Daily Spending Summary")
    
    # Create DataFrame for Visualization
    daily_report_list = []
    for day_key in sorted(st.session_state.daily_actual_expenses.keys()):
        daily_report_list.append({
            'Day': day_key,
            'Daily Budget (₹)': total_group_budget,
            'Actual Group Spend (₹)': st.session_state.daily_actual_expenses[day_key]
        })
    
    daily_report_df = pd.DataFrame(daily_report_list)
    daily_report_df = daily_report_df.set_index('Day')

    st.dataframe(daily_report_df)
    st.bar_chart(daily_report_df)

    st.divider()

    # --- FULL ITINERARY RECAP ---
    st.subheader("📆 Complete Itinerary Recap")
    for key in sorted(st.session_state.full_itinerary.keys()):
        day_data = st.session_state.full_itinerary[key]
        with st.expander(f"📅 *{key}*", expanded=False):
            for item in day_data:
                st.markdown(f"{item.get('place')}** ({item.get('duration')})")
                st.caption(item.get('description'))
                st.markdown(f"<div class='trip-tip-box'>👉 {item.get('notes')}</div>", unsafe_allow_html=True)
                st.markdown("---")