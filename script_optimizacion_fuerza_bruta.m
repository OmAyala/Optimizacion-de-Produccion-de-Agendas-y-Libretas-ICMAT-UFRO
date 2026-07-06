
%clear; clc;
tic;
% script_optimizacion_fuerza_bruta.m
% este script evalua todas las combinaciones posibles de compra y corte

% etapa 1: parametros del proyecto y requerimientos basicos
demanda_agendas = 40; 
demanda_libretas = 11; 
factor_merma = 0.10;   
factor_reglamento = 1.2;
cm_a_pulg = 1 / 2.54;

l_ca = 6.625; l_la = 8.5625; 
l_cl = 3.75;  l_ll = 6.375;  

area_agenda = l_ca * l_la;
area_libreta = l_cl * l_ll;

precios_base = [670, 1100]; 
dimensiones_cm = [38, 55; 55, 77];
dimensiones_pulg = dimensiones_cm * cm_a_pulg;

req_agendas = ceil(2 * demanda_agendas * (1 + factor_merma));
req_libretas = ceil(2 * demanda_libretas * (1 + factor_merma));

fprintf('resumen del plan de manufactura\n');
fprintf('cantidad de agendas a manufacturar: %d\n', demanda_agendas);
fprintf('cantidad de libretas a manufacturar: %d\n', demanda_libretas);
fprintf('tapas de agendas requeridas con merma: %d\n', req_agendas);
fprintf('tapas de libretas requeridas con merma: %d\n\n', req_libretas);

% etapa 2: generacion exhaustiva de todos los patrones de corte posibles
patrones = [];       
origen_patron = [];  
descripcion_patron = {}; 

fprintf('generando todas las combinaciones de corte posibles:\n');

% limites teoricos maximos para la fuerza bruta
max_agendas_chico = 0; max_libretas_chico = 0;
max_agendas_grande = 0; max_libretas_grande = 0;

for j = 1:2
    W_pulg = dimensiones_pulg(j, 1);
    H_pulg = dimensiones_pulg(j, 2);
    area_total = W_pulg * H_pulg;
    
    if j == 1
        texto_carton = 'carton chico 38x55 cm';
    else
        texto_carton = 'carton grande 55x77 cm';
    end
    
    rend_a_h = floor(W_pulg/l_ca) * floor(H_pulg/l_la);
    rend_a_v = floor(W_pulg/l_la) * floor(H_pulg/l_ca);
    max_agendas = max(rend_a_h, rend_a_v);
    
    rend_l_h = floor(W_pulg/l_cl) * floor(H_pulg/l_ll);
    rend_l_v = floor(W_pulg/l_ll) * floor(H_pulg/l_cl);
    max_libretas = max(rend_l_h, rend_l_v);
    
    if j == 1
        max_agendas_chico = max_agendas;
        max_libretas_chico = max_libretas;
    else
        max_agendas_grande = max_agendas;
        max_libretas_grande = max_libretas;
    end
    
    for a = 0:max_agendas
        area_ocupada = a * area_agenda;
        area_restante = area_total - area_ocupada;
        l = floor(area_restante / area_libreta);
        
        if a == 0 && l == 0
            continue;
        end
        
        patrones = [patrones, [a; l]];
        origen_patron = [origen_patron, j];
        
        desc = sprintf('%d agendas y %d libretas en %s', a, l, texto_carton);
        descripcion_patron{end+1} = desc;
        fprintf('patron %d: %s\n', length(descripcion_patron), desc);
    end
end
fprintf('\n');

% etapa 3: ataque por fuerza bruta al espacio bidimensional de compras
fprintf('iniciando ataque por fuerza bruta para evaluar factibilidad...\n\n');

% calculamos un limite superior exagerado para recorrer la cuadricula
max_cartones_chicos = ceil(max(req_agendas / max_agendas_chico, req_libretas / max_libretas_chico));
max_cartones_grandes = ceil(max(req_agendas / max_agendas_grande, req_libretas / max_libretas_grande));

idx_chicos = find(origen_patron == 1);
idx_grandes = find(origen_patron == 2);

opciones_validas = [];
opciones_solver = optimoptions('intlinprog', 'Display', 'off');
num_patrones = size(patrones, 2);

% minimizamos levemente la cantidad de cortes extras dentro de un mismo lote
f = 0.01 * sum(patrones, 1);
intcon = 1:num_patrones;
lb = zeros(1, num_patrones);
A_demanda = -patrones;
b_demanda = -[req_agendas; req_libretas];

for c = 0:max_cartones_chicos
    for g = 0:max_cartones_grandes
        % forzamos a que el modelo use exactamente c cartones chicos y g grandes
        A_eq = zeros(2, num_patrones);
        A_eq(1, idx_chicos) = 1;
        A_eq(2, idx_grandes) = 1;
        b_eq = [c; g];
        
        [y, ~, exitflag] = intlinprog(f, intcon, A_demanda, b_demanda, A_eq, b_eq, lb, [], opciones_solver);
        
        % si exitflag es mayor a 0 significa que si existe una forma de cortar esa mezcla
        if exitflag > 0
            costo_base = c * precios_base(1) + g * precios_base(2);
            costo_escalado = costo_base * factor_reglamento;
            
            opcion = struct('costo_base', costo_base, 'costo_final', costo_escalado, ...
                            'chicos', c, 'grandes', g, 'cortes', round(y));
            opciones_validas = [opciones_validas; opcion];
        end
    end
end

% etapa 4: ordenamiento y visualizacion de todas las opciones rentables
[~, idx_orden] = sort([opciones_validas.costo_base]);
opciones_ordenadas = opciones_validas(idx_orden);

fprintf('se encontraron %d combinaciones de compra validas\n', length(opciones_ordenadas));
fprintf('mostrando las 5 opciones mas economicas para analisis del equipo:\n\n');

% limitamos a las 5 mejores para no saturar la pantalla, pero calcula todas
top_n = min(5, length(opciones_ordenadas));

for i = 1:top_n
    opt = opciones_ordenadas(i);
    fprintf('opcion %d: comprar %d chicos y %d grandes\n', i, opt.chicos, opt.grandes);
    fprintf('costo base giorgio: $%d | costo final reglamento: $%0.0f\n', opt.costo_base, opt.costo_final);
    
    tapas_a = 0; tapas_l = 0;
    fprintf('instrucciones para este costo:\n');
    for k = 1:num_patrones
        if opt.cortes(k) > 0
            fprintf('  repetir %d veces el patron %d (%s)\n', opt.cortes(k), k, descripcion_patron{k});
            tapas_a = tapas_a + (patrones(1,k) * opt.cortes(k));
            tapas_l = tapas_l + (patrones(2,k) * opt.cortes(k));
        end
    end
    fprintf('resultado: sobran %d agendas y %d libretas\n\n', tapas_a - req_agendas, tapas_l - req_libretas);
end

tiempo_total = toc; 
fprintf('Tiempo de ejecución: %.4f segundos\n', tiempo_total);