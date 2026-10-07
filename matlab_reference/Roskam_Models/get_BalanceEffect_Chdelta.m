function ratio = get_BalanceEffect_Chdelta(balance_ratio, nose_type)
% GET_BALANCEEFFECT_CHDELTA calculates the balance effect on Ch_delta.
% Reference: Roskam
% nose_type: 'sharp', 'elliptic', 'round', 'low-drag'

    % Data points for each nose configuration (extracted from FIG 8)
    switch lower(nose_type)
        case 'sharp'
            x = [0.18, 0.30, 0.40, 0.50];
            y = [1.00, 0.82, 0.67, 0.52];
        case 'elliptic'
            x = [0.18, 0.30, 0.40, 0.50];
            y = [0.86, 0.70, 0.53, 0.35];
        case 'round'
            x = [0.18, 0.30, 0.40, 0.50];
            y = [0.75, 0.53, 0.31, 0.12];
        case 'low-drag'
            % Curve labeled "ROUND NOSE (LOW-DRAG SECTION)"
            x = [0.18, 0.30, 0.40, 0.50];
            y = [0.81, 0.48, 0.22, 0.00];
        otherwise
            error('Invalid nose type. Use sharp, elliptic, round, or low-drag.');
    end

    % Using 'pchip' for smooth interpolation through the points
    ratio = interp1(x, y, balance_ratio, 'pchip', 'extrap');
end