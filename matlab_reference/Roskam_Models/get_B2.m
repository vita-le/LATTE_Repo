function B2 = get_B2(cf_c, cb_cf)
% GET_B2 Calculates the B2 coefficient based on Figure 5(c)
% Inputs:
%   cf_c  : Control surface chord ratio (x-axis)
%   cb_cf : Balance chord ratio (parameter for curves)
%
% This version uses high-fidelity data points extracted manually from the image.

    % X-axis grid points (Control Surface Chord Ratio)
    grid_cf_c = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6];
    
    % Curve parameters (Balance Chord Ratio)
    grid_cb_cf = [0, 0.2, 0.3, 0.4, 0.5, 0.6];

    % Data Matrix (Z-values = B2) corresponding to the grids above.
    % Rows correspond to grid_cb_cf (0 to 0.6)
    % Columns correspond to grid_cf_c (0.05 to 0.6)
    B2_table = [
        0.50, 0.71, 0.94, 1.10, 1.22, 1.32, 1.41; % cb/cf = 0.0
        0.44, 0.62, 0.84, 1.00, 1.13, 1.24, 1.33; % cb/cf = 0.2
        0.39, 0.56, 0.78, 0.93, 1.06, 1.17, 1.26; % cb/cf = 0.3
        0.32, 0.49, 0.70, 0.85, 0.98, 1.09, 1.18; % cb/cf = 0.4
        0.22, 0.39, 0.60, 0.76, 0.89, 1.00, 1.09; % cb/cf = 0.5
        0.10, 0.24, 0.45, 0.62, 0.76, 0.88, 0.98  % cb/cf = 0.6
    ];

    % Use 'makima' (Modified Akima cubic Hermite interpolation)
    % It is better than 'spline' for avoiding overshoots in aerodynamic data
    B2 = interp2(grid_cf_c, grid_cb_cf, B2_table, cf_c, cb_cf, 'makima');
end