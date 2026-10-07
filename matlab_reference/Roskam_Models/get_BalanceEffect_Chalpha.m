function ratio = get_BalanceEffect_Chalpha(balance_ratio, nose_type)
% GET_BALANCEEFFECT_CHALPHA 
% Calculates the aerodynamic balance effect based on Roskam
% Input: balance_ratio (float), nose_type (string: 'sharp', 'elliptic', 'round')
% Output: ratio (float)

    switch lower(nose_type)
        case 'sharp'
            % Data points for Sharp Nose curve
            x = [0.18 0.5];
            y = [1.00 0.30];
        case 'elliptic'
            % Data points for Elliptic Nose curve
            x = [0.17 0.5];
            y = [0.90 0.20];
        case 'round'
            % Data points for Round Nose curve
            x = [0.15 0.5];
            y = [0.93 0.02];
        otherwise
            error('Invalid nose type. Please use "sharp", "elliptic", or "round".');
    end

    % Linear interpolation with extrapolation to cover the 0.1 - 0.5 range
    ratio = interp1(x, y, balance_ratio, 'linear', 'extrap');
end