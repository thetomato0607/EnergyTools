import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# Minimal header
st.title("Heat Pump Efficiency Visualiser")
st.caption("Interactive tool - theory explained in accompanying essay")

# Functions
def calculate_realistic_cop(T_outside_C, T_water_C, current_heat_load_kW,
                           humidity=70, include_defrost=True,
                           include_parasitics=True, system_efficiency=50,
                           include_hex_penalty=True, include_part_load=True,
                           delta_T_source=7.0, delta_T_sink=4.0,
                           max_capacity_kW=14.0):
    """
    Calculate realistic COP accounting for:
    - Heat exchanger temperature lift (separate for source and sink)
    - System efficiency (compressor losses)
    - Defrost cycles
    - Parasitic loads (fans, pumps)
    - Part-load inverter efficiency
    """

    # 1. CONVERT TO KELVIN
    T_outside_K = T_outside_C + 273.15
    T_water_K = T_water_C + 273.15

    # 2. APPLY HEAT EXCHANGER PENALTY (The "Real" Lift)
    # More realistic: different penalties for source (air) and sink (water)
    if include_hex_penalty:
        T_evap_K = T_outside_K - delta_T_source  # Harder to extract from air
        T_cond_K = T_water_K + delta_T_sink      # Easier to reject to water
    else:
        T_evap_K = T_outside_K
        T_cond_K = T_water_K

    # 3. CARNOT EFFICIENCY (Theoretical Max)
    carnot_cop = T_cond_K / (T_cond_K - T_evap_K)

    # 4. SYSTEM EFFICIENCY (Compressor losses, friction, etc)
    raw_cop = carnot_cop * (system_efficiency / 100)

    # 5. DEFROST PENALTY
    defrost_penalty = 1.0
    if include_defrost:
        if -2 <= T_outside_C <= 3 and humidity > 60:
            humidity_factor = (humidity - 60) / 40
            defrost_penalty = 0.88 - (0.05 * humidity_factor)
        elif -5 <= T_outside_C <= 5 and humidity > 70:
            defrost_penalty = 0.90

    raw_cop *= defrost_penalty

    # 6. PART-LOAD CORRECTION (Inverter Efficiency)
    # Calculate actual load factor based on demand vs capacity
    inverter_correction = 1.0
    if include_part_load:
        # Load factor: how hard the unit is working (0.0 to 1.0+)
        load_factor = current_heat_load_kW / max_capacity_kW
        load_factor = max(0.15, min(1.1, load_factor))  # Clamp: min speed 15%, slight overload 110%

        # Polynomial curve: peaks at 50% load, drops at extremes
        # Formula: -0.8x^2 + 0.8x + 0.8
        # At 50% load -> 1.0 (optimal), at 100% -> 0.8 (friction losses), at 15% -> 0.71 (cycling)
        inverter_correction = (-0.8 * (load_factor**2)) + (0.8 * load_factor) + 0.8

    raw_cop *= inverter_correction

    # 7. PARASITIC LOADS (Fans & Pumps)
    if include_parasitics and current_heat_load_kW > 0:
        compressor_power_kW = current_heat_load_kW / raw_cop
        fan_pump_power_kW = 0.150

        total_power_input = compressor_power_kW + fan_pump_power_kW
        real_cop = current_heat_load_kW / total_power_input
    else:
        real_cop = raw_cop

    return {
        'cop': real_cop,
        'carnot_cop': carnot_cop,
        'raw_cop': raw_cop,
        'defrost_penalty': defrost_penalty,
        'inverter_correction': inverter_correction if include_part_load else 1.0,
        'load_factor': (current_heat_load_kW / max_capacity_kW) if include_part_load else 1.0,
        'T_evap': T_evap_K - 273.15,
        'T_cond': T_cond_K - 273.15
    }

# Sidebar - more compact
with st.sidebar:
    st.header("System Configuration")

    system_efficiency = st.slider(
        "System Efficiency (% of Carnot)",
        40, 60, 50, 1
    )

    heat_load = st.slider(
        "Heat Demand (kW)",
        1.0, 12.0, 6.0, 0.5
    )

    max_capacity = st.slider(
        "Unit Max Capacity (kW)",
        8.0, 16.0, 14.0, 0.5,
        help="Rated capacity affects part-load efficiency"
    )

    st.divider()
    st.subheader("Model Realism")

    include_hex_penalty = st.checkbox("Heat Exchanger Losses", value=True)

    if include_hex_penalty:
        col1, col2 = st.columns(2)
        with col1:
            delta_T_source = st.slider("ΔT Source (°C)", 3.0, 10.0, 7.0, 0.5,
                                      help="Temperature penalty extracting heat from air")
        with col2:
            delta_T_sink = st.slider("ΔT Sink (°C)", 2.0, 8.0, 4.0, 0.5,
                                    help="Temperature penalty rejecting heat to water")
    else:
        delta_T_source = 7.0
        delta_T_sink = 4.0

    include_part_load = st.checkbox("Part-Load (Inverter)", value=True,
                                   help="Inverter efficiency varies with load")
    include_defrost = st.checkbox("Defrost Cycles", value=True)
    include_parasitics = st.checkbox("Parasitic Loads", value=True)

    if include_defrost:
        humidity = st.slider("Relative Humidity (%)", 30, 90, 70, 5)
    else:
        humidity = 0

# Main controls - clean layout
water_temp = st.slider("Water Flow Temperature (°C)", 35.0, 55.0, 45.0, 1.0,
                      help="Underfloor: 35-40°C | Radiators: 45-55°C")

outdoor_temp = st.slider("Outdoor Temperature (°C)", -15.0, 15.0, 5.0, 1.0)

# Calculate current performance
result = calculate_realistic_cop(
    outdoor_temp,
    water_temp,
    heat_load,
    humidity=humidity,
    include_defrost=include_defrost,
    include_parasitics=include_parasitics,
    system_efficiency=system_efficiency,
    include_hex_penalty=include_hex_penalty,
    include_part_load=include_part_load,
    delta_T_source=delta_T_source,
    delta_T_sink=delta_T_sink,
    max_capacity_kW=max_capacity
)

current_cop = result['cop']
carnot_cop = result['carnot_cop']
raw_cop = result['raw_cop']
electrical_power = heat_load / current_cop

# Results - just numbers, no explanation
st.subheader("Performance Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Carnot Limit", f"{carnot_cop:.2f}")
with col2:
    st.metric("Ideal COP", f"{raw_cop:.2f}")
with col3:
    st.metric("Real COP", f"{current_cop:.2f}")
with col4:
    st.metric("Power Draw", f"{electrical_power:.2f} kW")

# Compact status indicator
if current_cop >= 3.5:
    st.success(f"Delivering {heat_load:.1f} kW using {electrical_power:.2f} kW (COP = {current_cop:.2f})")
elif current_cop >= 2.5:
    st.info(f"Delivering {heat_load:.1f} kW using {electrical_power:.2f} kW (COP = {current_cop:.2f})")
else:
    st.warning(f"Delivering {heat_load:.1f} kW using {electrical_power:.2f} kW (COP = {current_cop:.2f})")

# Optional detailed breakdown
with st.expander("Detailed Breakdown"):
    st.write(f"**Evaporator Temperature:** {result['T_evap']:.1f}°C (outdoor air: {outdoor_temp:.1f}°C)")
    st.write(f"**Condenser Temperature:** {result['T_cond']:.1f}°C (water flow: {water_temp:.1f}°C)")
    st.write(f"**Temperature Lift:** {result['T_cond'] - result['T_evap']:.1f}°C")
    st.write("---")
    st.write(f"**Carnot COP:** {carnot_cop:.2f}")
    st.write(f"**System Efficiency:** {system_efficiency}% → COP = {carnot_cop * system_efficiency/100:.2f}")
    st.write(f"**Defrost Penalty:** {result['defrost_penalty']:.2%}")
    if include_part_load:
        st.write(f"**Load Factor:** {result['load_factor']:.1%} ({heat_load:.1f}kW / {max_capacity:.1f}kW)")
        st.write(f"**Inverter Correction:** {result['inverter_correction']:.2%}")
    st.write(f"**Pre-Parasitic COP:** {raw_cop:.2f}")

    if include_parasitics:
        compressor_power = heat_load / raw_cop
        parasitic_power = 0.150
        st.write(f"**Compressor Power:** {compressor_power:.3f} kW")
        st.write(f"**Parasitic Power:** {parasitic_power:.3f} kW")
        st.write(f"**Final COP:** {current_cop:.2f}")

    efficiency_loss = ((carnot_cop - current_cop) / carnot_cop) * 100
    st.write("---")
    st.write(f"**Total Efficiency Loss:** {efficiency_loss:.1f}% from Carnot limit")

# Graph - minimal annotations
st.subheader("COP vs Outdoor Temperature")

outdoor_range = np.linspace(-15, 15, 100)

# Calculate COP curves
carnot_curve = []
ideal_curve = []
real_curve = []

for t in outdoor_range:
    result_temp = calculate_realistic_cop(
        t, water_temp, heat_load,
        humidity=humidity,
        include_defrost=include_defrost,
        include_parasitics=include_parasitics,
        system_efficiency=system_efficiency,
        include_hex_penalty=include_hex_penalty,
        include_part_load=include_part_load,
        delta_T_source=delta_T_source,
        delta_T_sink=delta_T_sink,
        max_capacity_kW=max_capacity
    )
    carnot_curve.append(result_temp['carnot_cop'])
    ideal_curve.append(result_temp['raw_cop'])
    real_curve.append(result_temp['cop'])

fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(outdoor_range, carnot_curve, label='Carnot Limit',
        color='#00d9ff', linewidth=2, linestyle='--', alpha=0.7)
ax.plot(outdoor_range, ideal_curve, label=f'Ideal ({system_efficiency}%)',
        color='#00cc66', linewidth=2, linestyle='-.')
ax.plot(outdoor_range, real_curve, label='Real-World',
        color='#ff3366', linewidth=3)
ax.plot(outdoor_temp, current_cop, 'o', color='#ffcc00',
        markersize=12, label='Current', zorder=5)

# Minimal defrost zone (visual only)
if include_defrost and humidity > 60:
    ax.axvspan(-2, 3, alpha=0.1, color='blue')

ax.axhline(y=1, color='gray', linestyle=':', linewidth=2, alpha=0.5)

ax.set_xlabel('Outdoor Temperature (°C)', fontsize=12)
ax.set_ylabel('COP', fontsize=12)
ax.set_title(f'Water: {water_temp}°C | Load: {heat_load} kW', fontsize=11)
ax.grid(True, alpha=0.3)
ax.legend(fontsize=9)
ax.set_ylim(0, min(max(carnot_curve) * 1.1, 20))

st.pyplot(fig, clear_figure=True)

# Seasonal comparison - just data
st.subheader("Seasonal Performance")
col1, col2, col3, col4 = st.columns(4)

temps = [-5, 0, 7, 12]
labels = ["Winter -5°C", "Freezing 0°C", "Mild 7°C", "Spring 12°C"]

for i, (temp, label) in enumerate(zip(temps, labels)):
    result_temp = calculate_realistic_cop(temp, water_temp, heat_load, humidity,
                                    include_defrost, include_parasitics,
                                    system_efficiency, include_hex_penalty,
                                    include_part_load, delta_T_source, delta_T_sink,
                                    max_capacity)
    with [col1, col2, col3, col4][i]:
        st.metric(label, f"{result_temp['cop']:.2f}")

# Minimal footer
st.divider()
st.caption("Accompanying essay explains: Carnot cycle, system losses, defrost physics, and modeling assumptions")
