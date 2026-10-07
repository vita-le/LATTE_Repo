function term1 = get_AR_Correction_alpha(A)
% GET_AR_CORRECTION_ALPHA calculates the aspect ratio correction term.
% Based on FIG 4(b) data points.
    x = [2 3 4 6 8 10];
    y = [0.0183 0.014 0.011 0.007 0.0045 0.0035];
    
    % Using 'pchip' for a smooth, non-oscillatory curve
    term1 = interp1(x, y, A, 'pchip');
end