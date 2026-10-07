function Chalpha = get_ChalphaTheory(cf_c, tc)
% FIG 1(a) - Symmetrical airfoil
% Theoretical C_halpha (per rad)
% Regressione lineare per il range 0.1 <= cf/c <= 0.4

    % Limiti di validità del grafico
    if tc < 0 || tc > 0.16
        warning('t/c fuori dal range del grafico (0–0.16).');
    end

    % Coefficienti ottimizzati sul grafico:
    % C_halpha = a * (cf/c) + k * (t/c) + offset
    a = -1.34;      % Pendenza (più dolce della precedente)
    k = 0.69;       % Coefficiente correzione spessore
    offset = -0.202; % Intercetta per t/c = 0
    
    Chalpha = a * cf_c + k * tc + offset;
end