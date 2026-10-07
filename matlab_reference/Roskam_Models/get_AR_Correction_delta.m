function term2 = get_AR_Correction_delta(A, cf_ratio)
% GET_AR_CORRECTION_DELTA 
% Returns: ΔChδ / (Clδ * B2 * Ks * cos(Λc/4) * cos(Λhl))
% Based on Roskam's correction chart 

    % Aspect Ratio grid from the chart
    A_grid = [2, 3, 4, 5, 6, 8, 10];
    
    % Available flap chord ratios (cf'/c')
    cf_grid = [0.2, 0.4, 0.6];
    
    % Data Matrix (Rows: cf_grid, Columns: A_grid)
    % Extracted to follow the hyperbolic decay shown in the reference image
    data = [
        0.0350, 0.0240, 0.0175, 0.0135, 0.0110, 0.0075, 0.0055; % cf/c = 0.2
        0.0310, 0.0210, 0.0155, 0.0120, 0.0095, 0.0065, 0.0048; % cf/c = 0.4
        0.0280, 0.0185, 0.0135, 0.0105, 0.0085, 0.0055, 0.0040  % cf/c = 0.6
    ];

    % Input Clamping to prevent out-of-bounds errors
    A_input = max(min(A, max(A_grid)), min(A_grid));
    cf_input = max(min(cf_ratio, max(cf_grid)), min(cf_grid));

    % 2D Interpolation using 'makima' for smooth hyperbolic curves
    % First interpolate for each cf_grid level at the given Aspect Ratio
    vals_at_A = zeros(size(cf_grid));
    for i = 1:length(cf_grid)
        vals_at_A(i) = interp1(A_grid, data(i,:), A_input, 'makima');
    end
    
    % Finally interpolate across flap chord ratios
    term2 = interp1(cf_grid, vals_at_A, cf_input, 'linear');
end