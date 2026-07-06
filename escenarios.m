
clc; clear;

%% PARÁMETROS
maxTrabajadores = 10;
escenariosPorTrabajador = 3;

escenario = 1;

fprintf('Esc\tTrabajadores\tAgendas\tLibretas\n');
fprintf('------------------------------------------\n');

for trabajadores = 1:maxTrabajadores

    % Rango de agendas que obliga a utilizar exactamente
    % esa cantidad de trabajadores.
    minA = 12*(trabajadores-1) + 1;
    maxA = 12*trabajadores;

    % Verificar que existan suficientes valores posibles
    cantidadAgendas = maxA - minA + 1;

    if escenariosPorTrabajador > cantidadAgendas
        error(['No es posible generar %d escenarios para %d trabajadores. ', ...
            'Sólo existen %d cantidades de agendas posibles.'], ...
            escenariosPorTrabajador, ...
            trabajadores, ...
            cantidadAgendas);
    end

    % Seleccionar cantidades de agendas distintas y crecientes
    agendasVec = sort( ...
        randperm(cantidadAgendas, escenariosPorTrabajador) ...
        + minA - 1);

    for k = 1:escenariosPorTrabajador

        agendas = agendasVec(k);

        maxLibretas = 10*trabajadores;

        limiteLibretas = min( ...
            maxLibretas, ...
            round(0.83*agendas));

        libretas = randi([0 limiteLibretas]);

        fprintf('%3d\t%6d\t\t%6d\t%6d\n', ...
            escenario, ...
            trabajadores, ...
            agendas, ...
            libretas);

        escenario = escenario + 1;
    end
end