

%clear; clc;
tic;
% script_optimizacion_vinilos.m
% este script evalua todas las combinaciones de franjas horizontales
% obligando a mantener un colchon de seguridad minimo de piezas.

% etapa 1: parametros del sistema y demandas
dem_a = 40; 
dem_l = 11; 

tapas_a_req = 2 * dem_a; 
tapas_l_req = 1 * dem_l; 

% definimos el colchon de seguridad minimo (merma controlada)
% exigimos que al menos sobren 2 tapas de agenda (1 par) y 1 de libreta
min_sobrante_a = 2;
min_sobrante_l = 1;

precio_metro = 15470;
ancho_rollo = 100;
largo_minimo = 100;

fprintf('resumen de produccion de vinilos exterior\n');
fprintf('agendas a forrar: %d (requiere %d tapas base + min. %d extras)\n', dem_a, tapas_a_req, min_sobrante_a);
fprintf('libretas a forrar: %d (requiere %d tapas base + min. %d extra)\n\n', dem_l, tapas_l_req, min_sobrante_l);

% etapa 2: definicion de los patrones maestros
p1_h = 25;   p1_a = 5; p1_l = 0;
p2_h = 20;   p2_a = 4; p2_l = 0;
p3_h = 20;   p3_a = 2; p3_l = 4;
p4_h = 15;   p4_a = 0; p4_l = 8;
p5_h = 12.5; p5_a = 0; p5_l = 6;

% limites teoricos de los ciclos contemplando el extra
max_x1 = ceil((tapas_a_req + min_sobrante_a) / p1_a);
max_x2 = ceil((tapas_a_req + min_sobrante_a) / p2_a);
max_x3 = ceil(max((tapas_a_req + min_sobrante_a) / p3_a, (tapas_l_req + min_sobrante_l) / p3_l));
max_x4 = ceil((tapas_l_req + min_sobrante_l) / p4_l);
max_x5 = ceil((tapas_l_req + min_sobrante_l) / p5_l);

% preasignamos memoria para velocidad
espacio_estimado = 1000000;
soluciones_validas(espacio_estimado) = struct('x1',0,'x2',0,'x3',0,'x4',0,'x5',0,...
    'largo',0,'costo',0,'sobrante_a',0,'sobrante_l',0,'exceso',0);

contador_soluciones = 0;

fprintf('iniciando ataque por fuerza bruta...\n');

% etapa 3: motor de fuerza bruta con validacion de holgura
for x1 = 0:max_x1
    for x2 = 0:max_x2
        for x3 = 0:max_x3
            
            agendas_obtenidas = x1*p1_a + x2*p2_a + x3*p3_a;
            libretas_acumuladas = x3*p3_l;
            
            for x4 = 0:max_x4
                for x5 = 0:max_x5
                    
                    libretas_obtenidas = libretas_acumuladas + x4*p4_l + x5*p5_l;
                    
                    % validacion 1: cubrir la demanda MAS el colchon de seguridad
                    if agendas_obtenidas >= (tapas_a_req + min_sobrante_a) && libretas_obtenidas >= (tapas_l_req + min_sobrante_l)
                        
                        % validacion 2: regla de pares exactos para las agendas totales
                        if mod(agendas_obtenidas, 2) == 0
                            
                            largo_total = x1*p1_h + x2*p2_h + x3*p3_h + x4*p4_h + x5*p5_h;
                            
                            if largo_total <= largo_minimo
                                costo_final = precio_metro;
                            else
                                costo_final = (largo_total / 100) * precio_metro;
                            end
                            
                            sobrante_a = agendas_obtenidas - tapas_a_req;
                            sobrante_l = libretas_obtenidas - tapas_l_req;
                            exceso_total = sobrante_a + sobrante_l;
                            
                            contador_soluciones = contador_soluciones + 1;
                            soluciones_validas(contador_soluciones).x1 = x1;
                            soluciones_validas(contador_soluciones).x2 = x2;
                            soluciones_validas(contador_soluciones).x3 = x3;
                            soluciones_validas(contador_soluciones).x4 = x4;
                            soluciones_validas(contador_soluciones).x5 = x5;
                            soluciones_validas(contador_soluciones).largo = largo_total;
                            soluciones_validas(contador_soluciones).costo = costo_final;
                            soluciones_validas(contador_soluciones).sobrante_a = sobrante_a;
                            soluciones_validas(contador_soluciones).sobrante_l = sobrante_l;
                            soluciones_validas(contador_soluciones).exceso = exceso_total;
                        end
                    end
                end
            end
        end
    end
end

% limpieza de memoria residual
soluciones_validas = soluciones_validas(1:contador_soluciones);

% etapa 4: ordenamiento
criterios_orden = [[soluciones_validas.largo]', [soluciones_validas.exceso]'];
[~, indices_ordenados] = sortrows(criterios_orden, [1, 2]);
soluciones_ordenadas = soluciones_validas(indices_ordenados);

fprintf('busqueda finalizada con exito\n');
fprintf('se encontraron %d combinaciones viables con margen de seguridad\n\n', length(soluciones_ordenadas));
fprintf('mostrando las 5 opciones mas eficientes:\n\n');

top_n = min(5, length(soluciones_ordenadas));

for i = 1:top_n
    opt = soluciones_ordenadas(i);
    fprintf('opcion %d\n', i);
    fprintf('largo de rollo a comprar: %g cm\n', opt.largo);
    fprintf('costo final imprenta: $%0.0f\n', opt.costo);
    
    fprintf('instrucciones para armar el archivo de impresion:\n');
    if opt.x1 > 0
        fprintf('  incluir %d franjas del patron 1 (25 cm alto: 5 agendas)\n', opt.x1);
    end
    if opt.x2 > 0
        fprintf('  incluir %d franjas del patron 2 (20 cm alto: 4 agendas)\n', opt.x2);
    end
    if opt.x3 > 0
        fprintf('  incluir %d franjas del patron 3 (20 cm alto: 2 agendas y 4 libretas)\n', opt.x3);
    end
    if opt.x4 > 0
        fprintf('  incluir %d franjas del patron 4 (15 cm alto: 8 libretas)\n', opt.x4);
    end
    if opt.x5 > 0
        fprintf('  incluir %d franjas del patron 5 (12.5 cm alto: 6 libretas)\n', opt.x5);
    end
    
    fprintf('resultado final de esta mezcla:\n');
    fprintf('sobran %d tapas de agendas y %d tapas de libretas\n\n', opt.sobrante_a, opt.sobrante_l);
end

tiempo_total = toc; 
fprintf('Tiempo de ejecución: %.4f segundos\n', tiempo_total);