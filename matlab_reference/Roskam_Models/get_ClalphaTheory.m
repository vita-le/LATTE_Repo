function Clalpha_theory = get_ClalphaTheory(tc)
% FIG 1(b) - Theoretical Section Lift Curve Slope
% Input: tc = thickness ratio (t/c)
% Output: Clalpha_theory (per rad)
% Valid range: 0 <= t/c <= 0.20

    % Validation of input range based on the figure
    if tc < 0 || tc > 0.20
        warning('t/c is outside the figure range (0-0.20). Result is extrapolated.');
    end

    % Linear regression from the plot:
    % At tc = 0,   Clalpha = 6.28 (theoretical 2*pi)
    % At tc = 0.2, Clalpha = 7.30
    % Slope m = (7.30 - 6.28) / 0.20 = 5.1
    
    slope = 5.1;
    intercept = 6.28;
    
    Clalpha_theory = slope * tc + intercept;
end