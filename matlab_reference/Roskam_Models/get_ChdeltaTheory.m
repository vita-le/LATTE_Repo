function Chdelta = get_ChdeltaTheory(cf_c, tc)
    % GET_CHDELTATHEORY calculates (ch_delta) theory for a Symmetric Airfoil.
    % Reference: FIG 7(d) - Subsonic speeds.
    
    % tc_grid: thickness-to-chord ratio (the labeled lines)
    tc_grid = [0, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15];
    
    % cf_grid: flap-to-chord ratio (the x-axis values)
    cf_grid = [0.1, 0.2, 0.3, 0.4];
    
    % Z Matrix: (ch_delta) values (per rad)
    % Digitized to match the slopes and intercepts of image_8b637c.png
    Z = [ -0.88, -0.91, -0.95, -0.99;   % t/c = 0
          -0.84, -0.88, -0.93, -0.98;   % t/c = 0.04
          -0.80, -0.85, -0.91, -0.96;   % t/c = 0.06
          -0.77, -0.82, -0.88, -0.94;   % t/c = 0.08
          -0.74, -0.79, -0.86, -0.92;   % t/c = 0.10
          -0.70, -0.76, -0.83, -0.90;   % t/c = 0.12
          -0.64, -0.72, -0.81, -0.89 ]; % t/c = 0.15

    % Input Clamping: Caps values within grid limits to prevent NaN
    tc_input = max(min(tc, max(tc_grid)), min(tc_grid));
    cf_input = max(min(cf_c, max(cf_grid)), min(cf_grid));
    
    % 2D Linear Interpolation
    Chdelta = interp2(cf_grid, tc_grid, Z, cf_input, tc_input, 'linear');
end