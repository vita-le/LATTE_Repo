# Python-Based Aileron Hinge Moment Analysis Framework

A Python-based framework for the estimation and analysis of aircraft aileron hinge moments, developed as an evolution of an existing MATLAB implementation based on Roskam's semi-empirical methodology and Tornado Vortex Lattice Method (VLM).

The project aims to improve the flexibility, traceability and extensibility of the original framework, introducing standardized CPACS aircraft inputs, 3D geometry visualization and configurable aerodynamic calculation methods.

## Project Overview

The framework combines semi-empirical aerodynamic methods with geometry-based aircraft analysis to estimate aileron hinge moments under different flight and control-surface conditions.

The development builds upon a previous MATLAB project, focusing on improving its architecture, input flexibility, calculation options and visualization capabilities.

### Main Objectives

- **Uncertainty Traceability:** Introduce systematic tracking of uncertainties associated with the semi-empirical estimation methods and their input parameters.
- **Standardized Aircraft Inputs:** Extend compatibility to standardized CPACS aircraft configuration files, reducing dependence on aircraft-specific input definitions.
- **CPACS Visualization Interface:** Develop an interactive interface for aircraft geometry visualization and inspection.
- **Aerodynamic Model Extension:** Extend Tornado VLM capabilities and investigate mesh sensitivity to improve the robustness of aerodynamic calculations.
- **Modular Calculation Architecture:** Provide configurable calculation methods and options for the aerodynamic and semi-empirical variables involved in the analysis.

## Current Development Status

The following features have been implemented or are currently under development.

### Implemented Features

- **CPACS Input Integration:** Improved aircraft geometry and configuration input handling through CPACS files.
- **3D Aircraft Visualization:** Integration of 3D aircraft geometry visualization directly within the Python framework.
- **Aileron Geometry Visualization:** Dedicated visualization and inspection of aileron geometry and control-surface configurations.
- **Configurable Roskam Methodology:** Implementation of Roskam's semi-empirical hinge moment estimation methodology, with multiple selectable calculation options for the variables involved in the formulation.

### Planned Development

- **Uncertainty Tracking:** Explicit identification and propagation of uncertainties associated with semi-empirical methods and their input parameters.
- **Generalized CPACS Compatibility:** Extension of input handling to different standardized CPACS aircraft configurations.
- **Interactive CPACS Interface:** Further development of the aircraft visualization and geometry inspection interface.
- **Tornado VLM Extension:** Extension and refinement of aerodynamic analysis capabilities.
- **Mesh Sensitivity Analysis:** Investigation of aerodynamic mesh discretization effects on the resulting hinge moment estimates.

## Methodology

The framework follows an integrated analysis approach combining:

1. **Aircraft Geometry Definition:** Aircraft configuration and control-surface geometry extracted from CPACS.
2. **Geometry Visualization:** Three-dimensional inspection of aircraft geometry and aileron configurations.
3. **Aerodynamic Analysis:** Vortex Lattice Method calculations using Tornado.
4. **Semi-Empirical Estimation:** Hinge moment calculations based on Roskam's methodology.
5. **Sensitivity and Uncertainty Analysis:** Planned evaluation of model sensitivity and uncertainty contributions.

## Project Background

This project originates from a previous MATLAB-based framework developed for the preliminary estimation of fighter aircraft aileron hinge moments.

The original methodology was investigated and validated against experimental flight-test data from the NASA F/A-18 Systems Research Aircraft (SRA) program.

The Python implementation aims to provide a more flexible and extensible environment for further methodological development and aerodynamic analysis.

## Technologies

- Python
- CPACS
- Tornado VLM
- 3D Geometry Visualization
- Semi-Empirical Aerodynamic Methods

## Development Status

This project is under active development. Features and methodologies are progressively being transferred, improved and extended from the original MATLAB implementation.

Further documentation, validation cases and technical results will be added as development progresses.