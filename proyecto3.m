clear; clc;
% script_optimizacion_vinilo_maestro.m
% este script resuelve ambos escenarios y calcula el remanente en centimetros

% variable de control principal
usar_mismo_color = false; % cambiar a true si son diseños del mismo color

% etapa 1: parametros base y demandas
dem_a = 481; 
dem_l = 279;

% colchones de seguridad minimos (merma controlada en pares)
min_sob_a = 2; 
min_sob_li = 2; 
min_sob_le = 1;

tapas_a_req = (2 * dem_a) + min_sob_a;
tapas_li_req = (2 * dem_l) + min_sob_li;
tapas_le_req = (1 * dem_l) + min_sob_le;

% parametros de la tienda china
precio_45 = 2500; util_45 = 280;
precio_50 = 3990; util_50 = 480;
opciones_solver = optimoptions('intlinprog', 'Display', 'off');

% limites dinamicos para los ciclos de busqueda (peor caso)
largo_est_a = tapas_a_req * 8; 
largo_est_li = tapas_li_req * 3.5; 
largo_est_le = tapas_le_req * 4.5; 
largo_total_est = largo_est_a + largo_est_li + largo_est_le;

max_r1 = ceil(largo_total_est / util_45);
max_r2 = ceil(largo_total_est / util_50);

fprintf('resumen de produccion de vinilos interiores y contraportadas\n');
fprintf('interiores agenda requeridos con extra: %d\n', tapas_a_req);
fprintf('interiores libreta requeridos con extra: %d\n', tapas_li_req);
fprintf('exteriores libreta requeridos con extra: %d\n\n', tapas_le_req);

if usar_mismo_color
    fprintf('ejecutando escenario 1: mismo color modelo unificado\n\n');
    
    rendimientos = [
        2, 0, 0; % p1 (rollo 45cm): h=16
        0, 5, 0; % p2 (rollo 45cm): h=15.5
        0, 0, 3; % p3 (rollo 45cm): h=12.5
        3, 0, 0; % p4 (rollo 50cm): h=21
        2, 0, 0; % p5 (rollo 50cm): h=16
        0, 5, 0; % p6 (rollo 50cm): h=15.5
        0, 3, 0; % p7 (rollo 50cm): h=9
        0, 0, 4; % p8 (rollo 50cm): h=15
        0, 0, 3  % p9 (rollo 50cm): h=12.5
    ];
    alturas = [16, 15.5, 12.5, 21, 16, 15.5, 9, 15, 12.5];

    A_demanda = [-rendimientos', [0; 0; 0], [0; 0; 0]];
    b_demanda = -[tapas_a_req; tapas_li_req; tapas_le_req];

    Aeq = zeros(2, 11);
    Aeq(1, 1:9) = rendimientos(:, 1)'; Aeq(1, 10) = -2;
    Aeq(2, 1:9) = rendimientos(:, 2)'; Aeq(2, 11) = -2;
    beq = [0; 0];

    f = [0.01 * sum(rendimientos, 2); 0; 0];
    intcon = 1:11;
    lb = zeros(11, 1);
    soluciones = [];
    
    fprintf('iniciando busqueda hibrida...\n');
    fprintf('espacio: max %d rollos de 45cm y %d de 50cm\n\n', max_r1, max_r2);

    for r1 = 0:max_r1
        for r2 = 0:max_r2
            if r1 == 0 && r2 == 0; continue; end
            A_long = zeros(2, 11);
            A_long(1, 1:3) = alturas(1:3); 
            A_long(2, 4:9) = alturas(4:9); 
            b_long = [r1 * util_45; r2 * util_50];
            
            [x, ~, exitflag] = intlinprog(f, intcon, [A_demanda; A_long], [b_demanda; b_long], Aeq, beq, lb, [], opciones_solver);
            
            if exitflag > 0
                cortes = round(x(1:9));
                piezas_generadas = rendimientos' * cortes;
                
                % calculo de los centimetros de rollo sobrantes
                largo_usado_45 = alturas(1:3) * cortes(1:3);
                largo_usado_50 = alturas(4:9) * cortes(4:9);
                sob_cm_45 = (r1 * util_45) - largo_usado_45;
                sob_cm_50 = (r2 * util_50) - largo_usado_50;
                
                exc_a = piezas_generadas(1) - (2 * dem_a);
                exc_li = piezas_generadas(2) - (2 * dem_l);
                exc_le = piezas_generadas(3) - (1 * dem_l);
                
                % penalizamos ligeramente el exceso en tapas para empatar
                sol = struct('r1', r1, 'r2', r2, 'costo', (r1 * precio_45) + (r2 * precio_50), ...
                             'cortes', cortes, 'exc_a', exc_a, 'exc_li', exc_li, 'exc_le', exc_le, ...
                             'exc_tot', exc_a + exc_li + exc_le, ...
                             'sob_cm_45', sob_cm_45, 'sob_cm_50', sob_cm_50);
                soluciones = [soluciones; sol];
            end
        end
    end

    if ~isempty(soluciones)
        % ordenamos por costo, y luego por el mayor remanente util en cm (negativo para orden descendente)
        criterios_orden = [[soluciones.costo]', -([soluciones.sob_cm_45]' + [soluciones.sob_cm_50]')];
        [~, indices_ordenados] = sortrows(criterios_orden, [1, 2]);
        soluciones_ordenadas = soluciones(indices_ordenados);
        
        fprintf('busqueda finalizada con exito\n');
        top_n = min(5, length(soluciones_ordenadas));
        fprintf('mostrando las %d opciones mas eficientes:\n\n', top_n);
        
        for i = 1:top_n
            opt = soluciones_ordenadas(i);
            fprintf('opcion %d\n', i);
            fprintf('comprar %d rollos estandar de 45cm y %d rollos extendidos de 50cm\n', opt.r1, opt.r2);
            fprintf('costo total en tienda china: $%0.0f\n', opt.costo);
            fprintf('instrucciones de corte manual:\n');
            if opt.cortes(1) > 0; fprintf('  repetir %d veces patron 1 en rollo 45 (16 cm alto: 2 agendas int)\n', opt.cortes(1)); end
            if opt.cortes(2) > 0; fprintf('  repetir %d veces patron 2 en rollo 45 (15.5 cm alto: 5 libretas int)\n', opt.cortes(2)); end
            if opt.cortes(3) > 0; fprintf('  repetir %d veces patron 3 en rollo 45 (12.5 cm alto: 3 libretas ext)\n', opt.cortes(3)); end
            if opt.cortes(4) > 0; fprintf('  repetir %d veces patron 4 en rollo 50 (21 cm alto: 3 agendas int)\n', opt.cortes(4)); end
            if opt.cortes(5) > 0; fprintf('  repetir %d veces patron 5 en rollo 50 (16 cm alto: 2 agendas int)\n', opt.cortes(5)); end
            if opt.cortes(6) > 0; fprintf('  repetir %d veces patron 6 en rollo 50 (15.5 cm alto: 5 libretas int)\n', opt.cortes(6)); end
            if opt.cortes(7) > 0; fprintf('  repetir %d veces patron 7 en rollo 50 (9 cm alto: 3 libretas int)\n', opt.cortes(7)); end
            if opt.cortes(8) > 0; fprintf('  repetir %d veces patron 8 en rollo 50 (15 cm alto: 4 libretas ext)\n', opt.cortes(8)); end
            if opt.cortes(9) > 0; fprintf('  repetir %d veces patron 9 en rollo 50 (12.5 cm alto: 3 libretas ext)\n', opt.cortes(9)); end
            fprintf('resultado final de esta mezcla:\n');
            fprintf('sobran %d int agendas, %d int libretas y %d ext libretas\n', opt.exc_a, opt.exc_li, opt.exc_le);
            fprintf('y quedaran sin cortar: %d cm del rollo de 45cm y %d cm del rollo de 50cm\n\n', opt.sob_cm_45, opt.sob_cm_50);
        end
    else
        fprintf('alerta: no se encontro ninguna combinacion posible.\n');
    end

else
    fprintf('ejecutando escenario 2: colores distintos modelo desacoplado\n\n');
    
    % --- subproblema a: solo agendas ---
    fprintf('calculando rollos color a solo agendas\n');
    rend_a = [2; 3; 2]; alturas_a = [16, 21, 16];
    A_dem_a = [-rend_a', 0]; b_dem_a = -tapas_a_req;
    Aeq_a = [rend_a', -2]; beq_a = 0;
    f_a = [0.01 * rend_a; 0]; intcon_a = 1:4; lb_a = zeros(4, 1);
    sol_agendas = [];

    for r1 = 0:max_r1
        for r2 = 0:max_r2
            if r1 == 0 && r2 == 0; continue; end
            A_long = zeros(2, 4);
            A_long(1, 1) = alturas_a(1); A_long(2, 2:3) = alturas_a(2:3);
            [x, ~, exitflag] = intlinprog(f_a, intcon_a, [A_dem_a; A_long], [b_dem_a; [r1 * util_45; r2 * util_50]], Aeq_a, beq_a, lb_a, [], opciones_solver);
            if exitflag > 0
                cortes = round(x(1:3));
                piezas = rend_a' * cortes;
                
                largo_usado_45 = alturas_a(1) * cortes(1);
                largo_usado_50 = alturas_a(2:3) * cortes(2:3);
                
                sol = struct('r1', r1, 'r2', r2, 'costo', (r1*precio_45) + (r2*precio_50), ...
                             'cortes', cortes, 'exc', piezas - (2 * dem_a), ...
                             'sob_cm_45', (r1 * util_45) - largo_usado_45, ...
                             'sob_cm_50', (r2 * util_50) - largo_usado_50);
                sol_agendas = [sol_agendas; sol];
            end
        end
    end
    
    if ~isempty(sol_agendas)
        % ordenamos por costo, y luego por mayor cantidad de material sobrante en cm
        criterios_orden = [[sol_agendas.costo]', -([sol_agendas.sob_cm_45]' + [sol_agendas.sob_cm_50]')];
        [~, idx] = sortrows(criterios_orden, [1, 2]);
        sol_agendas_ordenadas = sol_agendas(idx);
        top_n_a = min(5, length(sol_agendas_ordenadas));
        
        fprintf('mostrando las %d opciones mas eficientes para agendas:\n\n', top_n_a);
        for i = 1:top_n_a
            opt = sol_agendas_ordenadas(i);
            fprintf('opcion agendas %d\n', i);
            fprintf('comprar %d rollos de 45cm y %d rollos de 50cm (costo: $%d)\n', opt.r1, opt.r2, opt.costo);
            if opt.cortes(1) > 0; fprintf('  cortar %d franjas de 16cm en rollo 45\n', opt.cortes(1)); end
            if opt.cortes(2) > 0; fprintf('  cortar %d franjas de 21cm en rollo 50\n', opt.cortes(2)); end
            if opt.cortes(3) > 0; fprintf('  cortar %d franjas de 16cm en rollo 50\n', opt.cortes(3)); end
            fprintf('sobran %d interiores de agenda\n', opt.exc);
            fprintf('y quedaran sin cortar: %d cm del rollo de 45cm y %d cm del rollo de 50cm\n\n', opt.sob_cm_45, opt.sob_cm_50);
        end
        opt_a_mejor = sol_agendas_ordenadas(1);
    else
        fprintf('alerta: no hay solucion posible para agendas.\n');
        opt_a_mejor = struct('costo', 0);
    end
    
    % --- subproblema b: solo libretas ---
    fprintf('calculando rollos color b solo libretas\n');
    rend_l = [5, 0; 0, 3; 5, 0; 3, 0; 0, 4; 0, 3]; alturas_l = [15.5, 12.5, 15.5, 9, 15, 12.5];
    A_dem_l = [-rend_l', [0; 0]]; b_dem_l = -[tapas_li_req; tapas_le_req];
    Aeq_l = [rend_l(:, 1)', -2]; beq_l = 0;
    f_l = [0.01 * sum(rend_l, 2); 0]; intcon_l = 1:7; lb_l = zeros(7, 1);
    sol_libretas = [];

    for r1 = 0:max_r1
        for r2 = 0:max_r2
            if r1 == 0 && r2 == 0; continue; end
            A_long = zeros(2, 7);
            A_long(1, 1:2) = alturas_l(1:2); A_long(2, 3:6) = alturas_l(3:6);
            [x, ~, exitflag] = intlinprog(f_l, intcon_l, [A_dem_l; A_long], [b_dem_l; [r1 * util_45; r2 * util_50]], Aeq_l, beq_l, lb_l, [], opciones_solver);
            if exitflag > 0
                cortes = round(x(1:6));
                piezas = rend_l' * cortes;
                
                largo_usado_45 = alturas_l(1:2) * cortes(1:2);
                largo_usado_50 = alturas_l(3:6) * cortes(3:6);
                
                sol = struct('r1', r1, 'r2', r2, 'costo', (r1*precio_45) + (r2*precio_50), ...
                             'cortes', cortes, 'exc_li', piezas(1) - (2 * dem_l), 'exc_le', piezas(2) - (1 * dem_l), ...
                             'sob_cm_45', (r1 * util_45) - largo_usado_45, ...
                             'sob_cm_50', (r2 * util_50) - largo_usado_50);
                sol_libretas = [sol_libretas; sol];
            end
        end
    end
    
    if ~isempty(sol_libretas)
        criterios_orden = [[sol_libretas.costo]', -([sol_libretas.sob_cm_45]' + [sol_libretas.sob_cm_50]')];
        [~, idx_l] = sortrows(criterios_orden, [1, 2]);
        sol_libretas_ordenadas = sol_libretas(idx_l);
        top_n_l = min(5, length(sol_libretas_ordenadas));
        
        fprintf('mostrando las %d opciones mas eficientes para libretas:\n\n', top_n_l);
        for i = 1:top_n_l
            opt = sol_libretas_ordenadas(i);
            fprintf('opcion libretas %d\n', i);
            fprintf('comprar %d rollos de 45cm y %d rollos de 50cm (costo: $%d)\n', opt.r1, opt.r2, opt.costo);
            if opt.cortes(1) > 0; fprintf('  cortar %d franjas de 15.5cm en rollo 45 (5 int)\n', opt.cortes(1)); end
            if opt.cortes(2) > 0; fprintf('  cortar %d franjas de 12.5cm en rollo 45 (3 ext)\n', opt.cortes(2)); end
            if opt.cortes(3) > 0; fprintf('  cortar %d franjas de 15.5cm en rollo 50 (5 int)\n', opt.cortes(3)); end
            if opt.cortes(4) > 0; fprintf('  cortar %d franjas de 9.0cm en rollo 50 (3 int)\n', opt.cortes(4)); end
            if opt.cortes(5) > 0; fprintf('  cortar %d franjas de 15.0cm en rollo 50 (4 ext)\n', opt.cortes(5)); end
            if opt.cortes(6) > 0; fprintf('  cortar %d franjas de 12.5cm en rollo 50 (3 ext)\n', opt.cortes(6)); end
            fprintf('sobran %d interiores y %d exteriores de libreta\n', opt.exc_li, opt.exc_le);
            fprintf('y quedaran sin cortar: %d cm del rollo de 45cm y %d cm del rollo de 50cm\n\n', opt.sob_cm_45, opt.sob_cm_50);
        end
        opt_l_mejor = sol_libretas_ordenadas(1);
    else
        fprintf('alerta: no hay solucion posible para libretas.\n');
        opt_l_mejor = struct('costo', 0);
    end

    if ~isempty(sol_agendas) && ~isempty(sol_libretas)
        fprintf('resumen de costos para la mejor combinacion desacoplada:\n');
        fprintf('costo agendas color a: $%d | costo libretas color b: $%d\n', opt_a_mejor.costo, opt_l_mejor.costo);
        fprintf('costo total del proyecto: $%d\n', opt_a_mejor.costo + opt_l_mejor.costo);
    end
end