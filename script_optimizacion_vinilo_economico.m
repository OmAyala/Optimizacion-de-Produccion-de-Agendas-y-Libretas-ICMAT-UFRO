
%clear; clc;
tic;
% script_optimizacion_vinilo_economico.m
% este script resuelve ambos escenarios y calcula el remanente en centimetros

% variable de control principal
usar_mismo_color = true; % cambiar a true si son diseños del mismo color

% etapa 1: parametros base y demandas
dem_a_eco = 40; 
dem_l_eco = 11;

% colchon de seguridad proporcional (merma)
factor_merma_vm = 0.20; % 20% extra para absorber una falla alta

tapas_a_req = ceil(2 * dem_a_eco * (1 + factor_merma_vm));
tapas_li_req = ceil(2 * dem_l_eco * (1 + factor_merma_vm));
tapas_le_req = ceil(1 * dem_l_eco * (1 + factor_merma_vm));

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
                
                % VALIDACIÓN FÍSICA Y SOBRANTES POR ROLLO (NO CONCATENAR
                % LOS ROLLOS EN UN SOLO ROLLO DEL LARGO TOTAL)
                piezas_45 = []; for k = 1:3; piezas_45 = [piezas_45, repmat(alturas(k), 1, cortes(k))]; end
                piezas_50 = []; for k = 4:9; piezas_50 = [piezas_50, repmat(alturas(k), 1, cortes(k))]; end
                
                piezas_45 = sort(piezas_45, 'descend');
                piezas_50 = sort(piezas_50, 'descend');
                
                % Simulamos tener r1 rollos fisicos de 45cm (arreglos)
                espacios_45 = ones(1, r1) * util_45; 
                exito_45 = true;
                for p = 1:length(piezas_45)
                    ubicado = false;
                    for b = 1:r1
                        if espacios_45(b) >= piezas_45(p)
                            espacios_45(b) = espacios_45(b) - piezas_45(p);
                            ubicado = true; break;
                        end
                    end
                    if ~ubicado; exito_45 = false; break; end
                end
                
                % Simulamos tener r2 rollos fisicos de 50cm (arreglos)
                espacios_50 = ones(1, r2) * util_50; 
                exito_50 = true;
                for p = 1:length(piezas_50)
                    ubicado = false;
                    for b = 1:r2
                        if espacios_50(b) >= piezas_50(p)
                            espacios_50(b) = espacios_50(b) - piezas_50(p);
                            ubicado = true; break;
                        end
                    end
                    if ~ubicado; exito_50 = false; break; end
                end
                
                if ~exito_45 || ~exito_50
                    continue; 
                end
                % FIN VALIDACIÓN FÍSICA
                
                piezas_generadas = rendimientos' * cortes;
                
                exc_a = piezas_generadas(1) - (2 * dem_a_eco);
                exc_li = piezas_generadas(2) - (2 * dem_l_eco);
                exc_le = piezas_generadas(3) - (1 * dem_l_eco);
                
                % Guardamos los arreglos con los remanentes exactos de cada rollo
                sol = struct('r1', r1, 'r2', r2, 'costo', (r1 * precio_45) + (r2 * precio_50), ...
                             'cortes', cortes, 'exc_a', exc_a, 'exc_li', exc_li, 'exc_le', exc_le, ...
                             'exc_tot', exc_a + exc_li + exc_le, ...
                             'detalles_45', espacios_45, 'detalles_50', espacios_50, ...
                             'sob_cm_45', sum(espacios_45), 'sob_cm_50', sum(espacios_50));
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
            if opt.r1 > 0; fprintf('sobrantes en cada rollo de 45cm: %s cm\n', mat2str(opt.detalles_45)); end
            if opt.r2 > 0; fprintf('sobrantes en cada rollo de 50cm: %s cm\n', mat2str(opt.detalles_50)); end
            fprintf('\n');
        end
    else
        fprintf('alerta: no se encontro ninguna combinacion posible.\n');
    end

else
    fprintf('ejecutando escenario 2: colores distintos modelo desacoplado\n\n');
    
    % subproblema a: solo agendas
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
                
                % VALIDACIÓN FÍSICA Y SOBRANTES (AGENDAS) (LO MISMO DE
                % ANTES PARA NO FUSIONAR TODO EN UN UNICO ROLLO GRANDE,
                % SINO TENERLOS POR SEPARADO)
                piezas_45 = repmat(alturas_a(1), 1, cortes(1));
                piezas_50 = []; 
                for k = 2:3; piezas_50 = [piezas_50, repmat(alturas_a(k), 1, cortes(k))]; end
                
                piezas_45 = sort(piezas_45, 'descend');
                piezas_50 = sort(piezas_50, 'descend');
                
                espacios_45 = ones(1, r1) * util_45; exito_45 = true;
                for p = 1:length(piezas_45)
                    ubicado = false;
                    for b = 1:r1; if espacios_45(b) >= piezas_45(p); espacios_45(b) = espacios_45(b) - piezas_45(p); ubicado = true; break; end; end
                    if ~ubicado; exito_45 = false; break; end
                end
                
                espacios_50 = ones(1, r2) * util_50; exito_50 = true;
                for p = 1:length(piezas_50)
                    ubicado = false;
                    for b = 1:r2; if espacios_50(b) >= piezas_50(p); espacios_50(b) = espacios_50(b) - piezas_50(p); ubicado = true; break; end; end
                    if ~ubicado; exito_50 = false; break; end
                end
                
                if ~exito_45 || ~exito_50; continue; end
                % FIN VALIDACIÓN FÍSICA

                piezas = rend_a' * cortes;
                
                sol = struct('r1', r1, 'r2', r2, 'costo', (r1*precio_45) + (r2*precio_50), ...
                             'cortes', cortes, 'exc', piezas - (2 * dem_a_eco), ...
                             'detalles_45', espacios_45, 'detalles_50', espacios_50, ...
                             'sob_cm_45', sum(espacios_45), 'sob_cm_50', sum(espacios_50));
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
            if opt.r1 > 0; fprintf('sobrantes en cada rollo de 45cm: %s cm\n', mat2str(opt.detalles_45)); end
            if opt.r2 > 0; fprintf('sobrantes en cada rollo de 50cm: %s cm\n', mat2str(opt.detalles_50)); end
            fprintf('\n');
        end
        opt_a_mejor = sol_agendas_ordenadas(1);
    else
        fprintf('alerta: no hay solucion posible para agendas.\n');
        opt_a_mejor = struct('costo', 0);
    end
    
    % subproblema b: solo libretas
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
                
                % VALIDACIÓN FÍSICA Y SOBRANTES (LIBRETAS) (IGUAL QUE ANTES
                % PARA NO TENER UN ROLLO UNICO Y GRANDE QUE MIDA LA
                % SUMATORIA DE LOS ROLLOS INDICIDUALES, SINO QUE CADA ROLLO
                % SE CALCULE Y SE MUESTRE DE FORMA INDEPENDIENTE)
                piezas_45 = []; for k = 1:2; piezas_45 = [piezas_45, repmat(alturas_l(k), 1, cortes(k))]; end
                piezas_50 = []; for k = 3:6; piezas_50 = [piezas_50, repmat(alturas_l(k), 1, cortes(k))]; end
                
                piezas_45 = sort(piezas_45, 'descend');
                piezas_50 = sort(piezas_50, 'descend');
                
                espacios_45 = ones(1, r1) * util_45; exito_45 = true;
                for p = 1:length(piezas_45)
                    ubicado = false;
                    for b = 1:r1; if espacios_45(b) >= piezas_45(p); espacios_45(b) = espacios_45(b) - piezas_45(p); ubicado = true; break; end; end
                    if ~ubicado; exito_45 = false; break; end
                end
                
                espacios_50 = ones(1, r2) * util_50; exito_50 = true;
                for p = 1:length(piezas_50)
                    ubicado = false;
                    for b = 1:r2; if espacios_50(b) >= piezas_50(p); espacios_50(b) = espacios_50(b) - piezas_50(p); ubicado = true; break; end; end
                    if ~ubicado; exito_50 = false; break; end
                end
                
                if ~exito_45 || ~exito_50; continue; end
                % FIN VALIDACIÓN FÍSICA 

                piezas = rend_l' * cortes;
                
                sol = struct('r1', r1, 'r2', r2, 'costo', (r1*precio_45) + (r2*precio_50), ...
                             'cortes', cortes, 'exc_li', piezas(1) - (2 * dem_l_eco), 'exc_le', piezas(2) - (1 * dem_l_eco), ...
                             'detalles_45', espacios_45, 'detalles_50', espacios_50, ...
                             'sob_cm_45', sum(espacios_45), 'sob_cm_50', sum(espacios_50));
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
            if opt.r1 > 0; fprintf('sobrantes en cada rollo de 45cm: %s cm\n', mat2str(opt.detalles_45)); end
            if opt.r2 > 0; fprintf('sobrantes en cada rollo de 50cm: %s cm\n', mat2str(opt.detalles_50)); end
            fprintf('\n');
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

tiempo_total = toc; 
fprintf('Tiempo de ejecución: %.4f segundos\n', tiempo_total);