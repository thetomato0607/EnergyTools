# EnergyTools
A clean, minimal physics-based tool that models how heat pump efficiency (COP) changes with outdoor temperature. Built as part of my UCL Physics personal portfolio to create simple, understandable tools for clean-energy decision-making.

Features
Input: outdoor temperature, desired indoor temperature
Computes COP using a simple thermodynamic model
Estimates energy consumption vs a gas boiler
Generates a clean temperature–COP graph
Single-screen, elegant visualisation (Streamlit / Jupyter)

Physics Used
Coefficient of Performance (COP) for heat pumps
Carnot cycle approximation
Real-world adjustment factor
Thermal physics fundamentals (entropy, heat transfer)

Assumptions
Steady-state temperature
Approximate real-world COP = 0.4 × COP_carnot
No auxiliary heating

Why I Built This
To demonstrate that physics-based modelling can be simple, transparent, and accessible.
This project reflects my interest in clean energy, modelling, and creating tools that help people intuitively understand energy systems.

Tech Stack
Python
Streamlit / Jupyter
matplotlib
numpy

What I Learned
Applying thermal physics to real systems
Designing minimal but powerful visual tools
Communicating physics assumptions clearly
Building tools without unnecessary complexity
