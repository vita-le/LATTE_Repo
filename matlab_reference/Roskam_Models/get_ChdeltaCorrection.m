function ratio = get_ChdeltaCorrection(cf_c, cl_ratio)
% GET_CHDELTACORRECTION calculates the ratio based on Roskam
% Modificata per mantenere l'ultimo valore costante fuori dai limiti (clamping).

    % Reference Cl_alpha / (Cl_alpha)_theory levels from the chart
    cl_levels = [0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.0];
    
    % X-axis grid (cf/c) points
    x_grid = [0.1, 0.2, 0.3, 0.4];
    
    % Matrix of B2 values (Rows: cl_levels, Cols: x_grid)
    data = [
        0.66, 0.60, 0.52, 0.41;  % level 0.60
        0.71, 0.67, 0.61, 0.53;  % level 0.65
        0.76, 0.73, 0.69, 0.63;  % level 0.70
        0.81, 0.79, 0.76, 0.72;  % level 0.75
        0.85, 0.84, 0.82, 0.79;  % level 0.80
        0.89, 0.88, 0.87, 0.85;  % level 0.85
        0.93, 0.92, 0.91, 0.90;  % level 0.90
        0.97, 0.96, 0.96, 0.95;  % level 0.95
        1.00, 1.00, 1.00, 1.00   % level 1.00
    ];

    % --- LOGICA DI SATURAZIONE (CLAMPING) ---
    % Vincola cf_c tra 0.1 e 0.4
    cf_c_clamped = max(min(cf_c, max(x_grid)), min(x_grid));
    
    % Vincola cl_ratio tra 0.6 e 1.0
    cl_ratio_clamped = max(min(cl_ratio, max(cl_levels)), min(cl_levels));

    % 2D Interpolation con i valori saturati
    ratio = interp2(x_grid, cl_levels, data, cf_c_clamped, cl_ratio_clamped, 'linear');
end