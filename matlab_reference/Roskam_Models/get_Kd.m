function Kd = get_Kd(eta)
% GET_KD Calculates the Kd factor based on Figure (b)
%
%   INPUT:
%   eta - Ratio be/b (x-axis), range [0, 1]
%
%   OUTPUT:
%   Kd  - Empirical factor (y-axis)

    % Reference points precisely extracted from the grid in image_8c53b8.png
    eta_ref = [0,   0.2,  0.4,  0.6,  0.8,  0.9,  1.0];
    Kd_ref  = [1.0, 1.15, 1.45, 1.95, 2.90, 3.60, 4.45];

    % Clamping input between 0 and 1 to avoid extrapolation errors
    eta_input = max(min(eta, 1), 0);

    % Using 'pchip' (Piecewise Cubic Hermite Interpolating Polynomial)
    % to maintain the monotonic growth without artificial oscillations.
    Kd = interp1(eta_ref, Kd_ref, eta_input, 'pchip');
end