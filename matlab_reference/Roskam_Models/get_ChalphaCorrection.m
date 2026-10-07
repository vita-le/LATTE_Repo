function ratio = get_ChalphaCorrection(cf_c, factor)
% GET_CHALPHACORRECTION Calculates the experimental/theoretical Ch_alpha ratio.
% Modificata per mantenere l'ultimo valore costante fuori dai limiti (clamping).

    % 1. Reference levels for the lift curve slope factor
    factor_levels = [0.7, 0.8, 0.85, 0.9, 1.0];
    
    % 2. X-axis grid (cf/c) points
    x_grid = [0.1, 0.2, 0.3, 0.4];
    
    % 3. Matrix of digitized values 
    data = [
        -0.11, -0.023,  0.064,  0.151;  % level 0.7
         0.35,  0.417,  0.484,  0.551;  % level 0.8
         0.54,  0.593,  0.646,  0.699;  % level 0.85
         0.72,  0.756,  0.792,  0.828;  % level 0.9
         1.00,  1.000,  1.000,  1.000   % level 1.0
    ];

    % --- MODIFICA PER ESTRAPOLAZIONE COSTANTE ---
    % Vincoliamo gli input entro i limiti della griglia (Saturation)
    cf_c_clamped = max(min(cf_c, max(x_grid)), min(x_grid));
    factor_clamped = max(min(factor, max(factor_levels)), min(factor_levels));

    % 4. 2D Linear Interpolation
    % Utilizziamo i valori "clamped" così l'interpolazione non uscirà mai dai bordi.
    ratio = interp2(x_grid, factor_levels, data, cf_c_clamped, factor_clamped, 'linear');
end