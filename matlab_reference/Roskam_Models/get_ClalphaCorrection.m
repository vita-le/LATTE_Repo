function ratio = get_ClalphaCorrection(tan_phi_half, Re)
% FIG 1(c) - Section Lift Curve Slope Correction
% Supports interpolation for intermediate Reynolds numbers (Re)
% Valid range: 1e6 <= Re <= 1e8

    % 1. Reference Reynolds numbers (Log scale)
    Re_refs = [1e6, 1e7, 1e8];
    log_Re_refs = log10(Re_refs);

    % 2. Calculate the ratio for each reference line at the given tan_phi_half
    % These equations are derived from Fig 1(c) slopes and intercepts
    r6 = -1.00 * tan_phi_half + 0.90; % Re = 10^6
    r7 = -0.80 * tan_phi_half + 0.94; % Re = 10^7
    r8 = -0.75 * tan_phi_half + 0.97; % Re = 10^8
    
    r_refs = [r6, r7, r8];

    % 3. Interpolate for the actual Re using log10 scale
    if Re < 1e6 || Re > 1e8
        warning('Reynolds number %.2e is outside the 10^6 - 10^8 range. Result is extrapolated.', Re);
    end
    
    % interp1(sample_points, values, query_point, 'linear', 'extrap')
    ratio = interp1(log_Re_refs, r_refs, log10(Re), 'linear', 'extrap');
end