function Cldelta = get_CldeltaTheory(cf_c, tc)
    % GET_CLDELTATHEORY Calculates lift curve slope derivative theory
    % Based on the power law: Cldelta = k * (cf/c)^0.6
    
    % Expanded reference thickness values to allow wider exploration
    tc_ref = [0.05, 0.08, 0.12, 0.15, 0.20];
    k_ref  = [7.8,  8.1,  8.4,  8.8,  9.2];
    
    % Input Clamping to keep tc within valid interpolation bounds
    tc_input = max(min(tc, max(tc_ref)), min(tc_ref));
    
    % Interpolate the coefficient 'k' for the given thickness
    k_interpolated = interp1(tc_ref, k_ref, tc_input, 'linear');
    
    % Calculate Cldelta using the interpolated k and the power law
    Cldelta = k_interpolated * cf_c.^0.6;
end