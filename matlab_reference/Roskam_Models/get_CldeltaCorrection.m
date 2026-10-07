function ratio = get_CldeltaCorrection(cf_c, cl_ratio)
% GET_CLDELTAEFFICIENCY calculates the flap effectiveness ratio.
% Reference: Roskam
% Inputs:
%   cf_c     : Control surface chord ratio (x-axis)
%   cl_ratio : Ratio of Cl_alpha / (Cl_alpha)_theory (replaces 'mode')

    % Define the reference grid for Cl_alpha ratios and cf_c
    % Values are mapped from the original equations for consistency
    cl_ratios_ref = [0.7, 0.8, 0.9, 1.0];
    cf_grid       = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6];
    
    % Matrix of values (Rows: cl_ratios_ref, Columns: cf_grid)
    % Row 1: 0.08 + 0.55 * cf_c^0.9
    % Row 2: 0.38 + 0.45 * cf_c^0.7
    % Row 3: 0.68 + 0.25 * cf_c^0.5 (Typical 'wing' value)
    % Row 4: 1.0 (Theoretical)
    data = [
        0.15, 0.23, 0.31, 0.37, 0.44, 0.50;  % cl_ratio = 0.7
        0.47, 0.52, 0.57, 0.63, 0.66, 0.71;  % cl_ratio = 0.8
        0.76, 0.79, 0.82, 0.84, 0.86, 0.87;  % cl_ratio = 0.9
        1.00, 1.00, 1.00, 1.00, 1.00, 1.00   % cl_ratio = 1.0
    ];

    % Clamping to prevent NaN for inputs outside the reference grid
    cl_input = max(min(cl_ratio, 1.0), 0.7);
    cf_input = max(min(cf_c, 0.6), 0.1);

    % 2D Interpolation to handle intermediate cl_alpha ratios
    ratio = interp2(cf_grid, cl_ratios_ref, data, cf_input, cl_input, 'linear');
end
