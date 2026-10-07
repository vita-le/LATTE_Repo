function ad = get_ad(deflection, cf_c)
% GET_ALPHA_DELTA Calculates flap effectiveness (ad) for intermediate cf/c ratios
%
% INPUTS:
% deflection - Flap deflection angle in degrees (0 to 50)
% cf_c       - Flap-to-chord ratio (range 0.2 to 0.4)
%
% OUTPUT:
% ad         - Interpolated flap effectiveness value

    % 1. Define the grid based on your provided chart (image_ce2800.png)
    % Deflection points (x-axis)
    def_grid = [0, 10, 20, 30, 40, 50]; 
    
    % cf/c ratios (the different colored lines)
    cfc_grid = [0.2, 0.3, 0.4];
    
    % 2. Define the matrix of alpha_delta values (ad)
    % Each row corresponds to a cfc_grid value, each column to a def_grid value
    % Values estimated from the trends in your second image:
    ad_matrix = [ ...
        0.45, 0.44, 0.43, 0.38, 0.32, 0.24;   % cf/c = 0.2
        0.56, 0.55, 0.54, 0.50, 0.44, 0.34;   % cf/c = 0.3
        0.60, 0.59, 0.58, 0.54, 0.48, 0.40];  % cf/c = 0.4

    % 3. Clamp inputs to the available data range to avoid NaN
    deflection = max(0, min(50, deflection));
    cf_c = max(0.2, min(0.4, cf_c));

    % 4. Perform 2D linear interpolation
    % 'linear' provides a smooth transition between the provided curves
    ad = interp2(def_grid, cfc_grid, ad_matrix, deflection, cf_c, 'linear');
end