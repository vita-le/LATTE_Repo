function Ka = get_Ka(eta)
% FIG 5(a)

    x = [0 0.2 0.4 0.6 0.8 1.0];
    y = [1.0 1.25 1.7 2.4 3.3 4.3];

    Ka = interp1(x, y, eta, 'pchip');
end

