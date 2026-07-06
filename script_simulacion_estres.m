
clear; clc;
tic;
% script_simulacion_estres.m
% este script ejecuta los optimizadores y luego estresa las mejores

% TRABAJO FUTURO: MEDICIÓN EMPÍRICA DE LOS ERRORES
% Si en esta iteración del proyecto se cuenta con datos reales del taller, 
% se recomienda cambiar la estimación manual por una probabilidad empírica

% Fórmula a utilizar:
% probabilidad_error = cortes_arruinados / cortes_totales_intentados;

% Ej: Si al cortar un lote de prueba de 200 tapas se arruinaron 18:
% probabilidad_error = 18 / 200;  % (Esto calculará automáticamente un 0.09)

% Ingresar este cálculo directamente en las variables de probabilidad de
% cada material (Cartón, Vinilo Exterior y Vinilo Económico) según corresponda

% Activamos el registro automático. Captura las salidas por consola
% Usamos una ruta relativa para que siempre se guarde en la misma carpeta
%diary('reporte_simulacion_estres.txt');

% PARTE 1: OPTIMIZACIÓN Y ESTRÉS PARA EL CARTÓN PIEDRA

% el script original se ejecuta de forma oculta para cargar en la memoria 
% todas las variables del proyecto (demandas, patrones de corte generados 
% y la lista de opciones de compra ordenadas por precio)
% (borrar el 'clear; clc;' de este archivo)
script_optimizacion_fuerza_bruta; 

% definimos de los parametros de la simulacion estocastica (montecarlo)
% tasa de cortes defectuosos en el taller 
% (cantidad de veces que la guillotina o el estudiante encargado arruina el material)
probabilidad_error = 0.05; 
% cantidad de "universos" paralelos que se evaluaran
num_simulaciones = 1e6;  
% contador para registrar en cuantos universos el material alcanzo a pesar de las fallas
exitos_simulacion = 0;

% se inicializan vectores de ceros para guardar la historia completa 
% esto evita que la simulacion sea una "caja negra" y permite extraer 
% estadisticas como el peor y el mejor caso del proyecto, o lo que se desee
% mostrar del mismo
historial_tapas_a = zeros(1, num_simulaciones);
historial_tapas_l = zeros(1, num_simulaciones);

fprintf('\nINICIANDO PRUEBA DE ESTRÉS PARA CARTÓN PIEDRA\n');

% extrae exclusivamente la opcion 1, que corresponde a la combinacion
% de compra mas barata encontrada por la fuerza bruta
mejor_opcion = opciones_ordenadas(1);

% se calcula la demanda real que exige el proyecto
% nota: no se incluye el factor de merma aqui, ya que justamente la merma 
% comprada actuara como colchon para absorber la probabilidad_error
base_agendas = 2 * demanda_agendas;
base_libretas = 2 * demanda_libretas;

fprintf('evaluando la opcion 1: comprar %d chicos y %d grandes\n', mejor_opcion.chicos, mejor_opcion.grandes);
fprintf('probabilidad de error por cada corte individual: %0.0f%%\n', probabilidad_error * 100);
fprintf('simulando la produccion %d veces...\n\n', num_simulaciones);

% ciclo de montecarlo
for sim = 1:num_simulaciones
    % contadores locales de piezas "sanas" rescatadas en este universo
    tapas_a_obtenidas = 0; 
    tapas_l_obtenidas = 0;
    
    % la simulacion 1 imprime su proceso en la consola 
    % para ver visualmente que la probabilidad este funcionando
    if sim == 1
        fprintf('DETALLE PASO A PASO: SIMULACIÓN 1 (CARTÓN PIEDRA)\n');
    end
    
    % el codigo recorre el catalogo completo de patrones (plantillas de corte)
    for k = 1:num_patrones
        % solo se procesan los patrones que la opcion optima decidio utilizar
        if mejor_opcion.cortes(k) > 0
            
            % el for anidado simula el acto fisico de poner cada plancha 
            % de carton piedra sobre la mesa para cortarla
            for tablero = 1:mejor_opcion.cortes(k)
                fallas_a = 0; 
                fallas_l = 0;
                
                % se simula el paso de la guillotina o cortacarton por cada tapa de agenda
                % generamos un numero entre 0 y 1; si es mayor al error (0.05 u otro),
                % el corte fue limpio. Si es menor, el material se arruina
                for a = 1:patrones(1,k)
                    if rand() > probabilidad_error 
                        tapas_a_obtenidas = tapas_a_obtenidas + 1; 
                    else 
                        fallas_a = fallas_a + 1; 
                    end
                end
                
                % se simula el paso de la guillotina o cortacarton por cada tapa de libreta
                for l = 1:patrones(2,k)
                    if rand() > probabilidad_error 
                        tapas_l_obtenidas = tapas_l_obtenidas + 1; 
                    else 
                        fallas_l = fallas_l + 1; 
                    end
                end
                
                % impresion de la primera simulacion para auditoria
                if sim == 1
                    fprintf('carton %d (patron %d) -> agendas intentadas: %d (fallaron: %d) | libretas intentadas: %d (fallaron: %d)\n', ...
                        tablero, k, patrones(1,k), fallas_a, patrones(2,k), fallas_l);
                end
            end
        end
    end
    
    if sim == 1; fprintf('FIN DEL DETALLE DE LA SIMULACIÓN 1\n\n'); end
    
    % se guarda la cantidad acumulada de este universo paralelo en el historial general
    historial_tapas_a(sim) = tapas_a_obtenidas;
    historial_tapas_l(sim) = tapas_l_obtenidas;
    
    % validacion de exito: si despues de descontar la merma, las piezas 
    % sanas son iguales o mayores a la demanda estricta, el proyecto
    % se guarda
    if tapas_a_obtenidas >= base_agendas && tapas_l_obtenidas >= base_libretas
        exitos_simulacion = exitos_simulacion + 1;
    end
end

% calculamos la probabilidad final de que la compra sea suficiente
nivel_confianza = (exitos_simulacion / num_simulaciones) * 100;

% impresion del reporte de la etapa de carton piedra
fprintf('RESULTADOS FINALES DEL ESTRÉS (CARTÓN PIEDRA)\n');
fprintf('1. Demanda real estricta : %d tapas agenda, %d tapas libreta\n', base_agendas, base_libretas);
fprintf('2. Objetivo de corte     : %d tapas agenda, %d tapas libreta\n\n', req_agendas, req_libretas);

fprintf('Estadisticas tras %d simulaciones:\n', num_simulaciones);
fprintf('- Promedio : %0.1f tapas agenda | %0.1f tapas libreta\n', mean(historial_tapas_a), mean(historial_tapas_l));
fprintf('- Peor caso: %d tapas agenda | %d tapas libreta\n', min(historial_tapas_a), min(historial_tapas_l));
fprintf('- Mejor caso: %d tapas agenda | %d tapas libreta\n\n', max(historial_tapas_a), max(historial_tapas_l));

fprintf('CONCLUSIÓN CARTÓN PIEDRA:\n');
fprintf('Hay un %0.2f%% de confianza en que la compra cubre la demanda real\n\n\n', nivel_confianza);

% PARTE 2: OPTIMIZACIÓN Y ESTRÉS PARA LOS VINILOS (EXTERIOR)

% se ejecuta el script de vinilos de forma oculta para cargar sus 
% parametros, demandas y el espacio de soluciones evaluadas
% (borrar el 'clear; clc;' de este archivo)
script_optimizacion_vinilos; 

% se define una probabilidad de error baja (1%) ya que este vinilo es el 
% material mas costoso y rigido. Fisicamente, esto obliga a realizar un corte 
% manual mucho mas lento y controlado, reduciendo la tasa de fallas
% Notamos que al doblar este valor, la probabilidad de éxito reduce mucho
probabilidad_error_v = 0.01;
exitos_simulacion_v = 0;

% se inicializan los vectores para registrar la historia de las simulaciones, 
% aprovechando la variable num_simulaciones (100.000 u otro valor) definida en la Parte 1
historial_tapas_a_v = zeros(1, num_simulaciones);
historial_tapas_l_v = zeros(1, num_simulaciones);

fprintf('\nINICIANDO PRUEBA DE ESTRÉS PARA VINILOS (OPCIÓN 1)\n');

% se extrae la opcion de compra mas economica (el rollo mas corto posible 
% que cumple con el piso minimo definido en base a la demanda a producir)
mejor_opcion_v = soluciones_ordenadas(1);

fprintf('probabilidad de error por cada corte de vinilo: %0.0f%%\n', probabilidad_error_v * 100);
fprintf('simulando el forrado %d veces...\n\n', num_simulaciones);

% ciclo de montecarlo
for sim = 1:num_simulaciones
    tapas_a_obtenidas = 0; tapas_l_obtenidas = 0;
    
    if sim == 1; fprintf('DETALLE PASO A PASO: SIMULACIÓN 1 (VINILOS)\n'); end
    
    % evaluacion de las franjas correspondientes al patron 1 (solo agendas)
    % el algoritmo verifica si la optimizacion decidio usar este patron
    if mejor_opcion_v.x1 > 0
        for franja = 1:mejor_opcion_v.x1
            fallas_a = 0;
            % se simula el riesgo para cada una de las tapas dentro de esta franja
            for a = 1:p1_a
                if rand() > probabilidad_error_v
                    tapas_a_obtenidas = tapas_a_obtenidas + 1; 
                else
                    fallas_a = fallas_a + 1; 
                end
            end
            if sim == 1; fprintf('patron 1 (franja %d) -> agendas intentadas: %d (fallaron: %d)\n', franja, p1_a, fallas_a); end
        end
    end
    
    % evaluacion de las franjas correspondientes al patron 2 (solo agendas)
    if mejor_opcion_v.x2 > 0
        for franja = 1:mejor_opcion_v.x2
            fallas_a = 0;
            for a = 1:p2_a
                if rand() > probabilidad_error_v
                    tapas_a_obtenidas = tapas_a_obtenidas + 1; 
                else
                    fallas_a = fallas_a + 1; 
                end
            end
            if sim == 1; fprintf('patron 2 (franja %d) -> agendas intentadas: %d (fallaron: %d)\n', franja, p2_a, fallas_a); end
        end
    end
    
    % evaluacion de las franjas correspondientes al patron 3 (patron mixto)
    % este patron contiene tanto piezas de agenda como de libreta
    if mejor_opcion_v.x3 > 0
        for franja = 1:mejor_opcion_v.x3
            fallas_a = 0; fallas_l = 0;
            for a = 1:p3_a
                if rand() > probabilidad_error_v
                    tapas_a_obtenidas = tapas_a_obtenidas + 1; 
                else
                    fallas_a = fallas_a + 1; 
                end
            end
            for l = 1:p3_l
                if rand() > probabilidad_error_v
                    tapas_l_obtenidas = tapas_l_obtenidas + 1; 
                else
                    fallas_l = fallas_l + 1; 
                end
            end
            if sim == 1; fprintf('patron 3 (franja %d) -> agendas intentadas: %d (fallaron: %d) | libretas intentadas: %d (fallaron: %d)\n', franja, p3_a, fallas_a, p3_l, fallas_l); end
        end
    end
    
    % evaluacion de las franjas correspondientes al patron 4 (solo libretas)
    if mejor_opcion_v.x4 > 0
        for franja = 1:mejor_opcion_v.x4
            fallas_l = 0;
            for l = 1:p4_l
                if rand() > probabilidad_error_v
                    tapas_l_obtenidas = tapas_l_obtenidas + 1; 
                else
                    fallas_l = fallas_l + 1; 
                end
            end
            if sim == 1; fprintf('patron 4 (franja %d) -> libretas intentadas: %d (fallaron: %d)\n', franja, p4_l, fallas_l); end
        end
    end
    
    % evaluacion de las franjas correspondientes al patron 5 (solo libretas)
    if mejor_opcion_v.x5 > 0
        for franja = 1:mejor_opcion_v.x5
            fallas_l = 0;
            for l = 1:p5_l
                if rand() > probabilidad_error_v
                    tapas_l_obtenidas = tapas_l_obtenidas + 1; 
                else
                    fallas_l = fallas_l + 1; 
                end
            end
            if sim == 1; fprintf('patron 5 (franja %d) -> libretas intentadas: %d (fallaron: %d)\n', franja, p5_l, fallas_l); end
        end
    end
    
    if sim == 1; fprintf('FIN DEL DETALLE DE LA SIMULACIÓN 1 (VINILOS)\n\n'); end
    
    % se registra la cantidad de franjas sanas para este universo paralelo
    historial_tapas_a_v(sim) = tapas_a_obtenidas;
    historial_tapas_l_v(sim) = tapas_l_obtenidas;
    
    % validacion de exito: el proyecto sobrevive si las piezas rescatadas cubren
    % la demanda base requerida (sin contemplar los sobrantes planificados)
    if tapas_a_obtenidas >= tapas_a_req && tapas_l_obtenidas >= tapas_l_req
        exitos_simulacion_v = exitos_simulacion_v + 1;
    end
end

% calculo final de la probabilidad de exito para la compra del vinilo exterior
nivel_confianza_v = (exitos_simulacion_v / num_simulaciones) * 100;

% impresion del reporte para el vinilo exterior
fprintf('RESULTADOS FINALES DEL ESTRÉS (VINILOS)\n');
fprintf('1. Demanda real estricta : %d tapas agenda, %d tapas libreta\n', tapas_a_req, tapas_l_req);
fprintf('2. Objetivo de corte     : %d tapas agenda, %d tapas libreta\n\n', tapas_a_req + min_sobrante_a, tapas_l_req + min_sobrante_l);

fprintf('Estadisticas tras %d simulaciones:\n', num_simulaciones);
fprintf('- Promedio : %0.1f tapas agenda | %0.1f tapas libreta\n', mean(historial_tapas_a_v), mean(historial_tapas_l_v));
fprintf('- Peor caso: %d tapas agenda | %d tapas libreta\n', min(historial_tapas_a_v), min(historial_tapas_l_v));
fprintf('- Mejor caso: %d tapas agenda | %d tapas libreta\n\n', max(historial_tapas_a_v), max(historial_tapas_l_v));

fprintf('CONCLUSIÓN VINILOS:\n');
fprintf('Hay un %0.2f%% de confianza en que el rollo de %g cm cubre la demanda real\n\n\n', nivel_confianza_v, mejor_opcion_v.largo);

% PARTE 3: OPTIMIZACIÓN Y ESTRÉS PARA VINILO ECONÓMICO

% se ejecuta el script base para cargar las variables del modelo de 
% optimizacion del vinilo interior/economico en la memoria
% (borrar el 'clear; clc;' de este archivo)
script_optimizacion_vinilo_economico; 

fprintf('\nINICIANDO PRUEBA DE ESTRÉS PARA VINILO ECONÓMICO\n');

% se define la demanda  para las tres piezas distintas que se obtienen 
% de este material (interiores de agenda, interiores 
% de libreta y exteriores de libreta), sin contar la merma planificada
req_real_a_int = 2 * dem_a_eco;
req_real_li_int = 2 * dem_l_eco;
req_real_le_ext = 1 * dem_l_eco;

% se define una probabilidad de error alta (10%)
% Al ser un material de menor costo, fisicamente tiende a ser mas delgado o 
% fragil aumentando la tasa de rasgaduras o cortes defectuosos en el taller
probabilidad_error_vm = 0.10; 
exitos_simulacion_vm = 0;

% se preasignan los vectores para registrar la historia independiente 
% de cada uno de los tres tipos de tapas a lo largo de las simulaciones
hist_a_int = zeros(1, num_simulaciones);
hist_li_int = zeros(1, num_simulaciones);
hist_le_ext = zeros(1, num_simulaciones);

fprintf('probabilidad de error por cada corte: %0.0f%%\n', probabilidad_error_vm * 100);
fprintf('simulando el proceso %d veces...\n\n', num_simulaciones);

% ciclo de montecarlo
for sim = 1:num_simulaciones
    obt_a_int = 0; obt_li_int = 0; obt_le_ext = 0;
    
    if sim == 1; fprintf('DETALLE PASO A PASO: SIMULACIÓN 1 (VINILO ECONÓMICO)\n'); end
    
    % el script evalua dinamicamente cual camino logico tomo el optimizador:
    % ¿se uso el mismo color para todo (unificado) o colores distintos (desacoplado)?
    if usar_mismo_color
        
        % CASO 1: MODELO UNIFICADO
        if ~isempty(soluciones)
            mejor_opt = soluciones_ordenadas(1);
            
            % se recorren los 9 patrones maestros diseñados para el rollo unico
            for k = 1:9 
                if mejor_opt.cortes(k) > 0
                    for franja = 1:mejor_opt.cortes(k)
                        fallas_a = 0; fallas_li = 0; fallas_le = 0;
                        
                        % simulacion de riesgo para los interiores de agenda
                        for p = 1:rendimientos(k, 1); if rand() > probabilidad_error_vm; obt_a_int = obt_a_int + 1; else; fallas_a = fallas_a + 1; end; end
                        % simulacion de riesgo para los interiores de libreta
                        for p = 1:rendimientos(k, 2); if rand() > probabilidad_error_vm; obt_li_int = obt_li_int + 1; else; fallas_li = fallas_li + 1; end; end
                        % simulacion de riesgo para los exteriores de libreta
                        for p = 1:rendimientos(k, 3); if rand() > probabilidad_error_vm; obt_le_ext = obt_le_ext + 1; else; fallas_le = fallas_le + 1; end; end
                        
                        if sim == 1; fprintf(' patron %d (franja %d) -> a_int fallidos: %d | li_int fallidos: %d | le_ext fallidos: %d\n', k, franja, fallas_a, fallas_li, fallas_le); end
                    end
                end
            end
        end
        
    else
        
        % CASO 2: MODELO DESACOPLADO
        % se asume que las agendas y libretas usan colores distintos 
        % sus planes de corte se simulan de forma completamente independiente
        if ~isempty(soluciones_agendas) && ~isempty(soluciones_libretas)
            real y estricta
            % subproblema A: estres sobre los rollos de color para agendas
            for k = 1:3
                if opt_a_mejor.cortes(k) > 0
                    for franja = 1:opt_a_mejor.cortes(k)
                        fallas_a = 0;
                        for p = 1:rend_a(k); if rand() > probabilidad_error_vm; obt_a_int = obt_a_int + 1; else; fallas_a = fallas_a + 1; end; end
                        if sim == 1; fprintf(' [Agendas] patron %d (franja %d) -> a_int fallidos: %d\n', k, franja, fallas_a); end
                    end
                end
            end
            
            % subproblema B: estres sobre los rollos de color para libretas
            for k = 1:6
                if opt_l_mejor.cortes(k) > 0
                    for franja = 1:opt_l_mejor.cortes(k)
                        fallas_li = 0; fallas_le = 0;
                        for p = 1:rend_l(k, 1); if rand() > probabilidad_error_vm; obt_li_int = obt_li_int + 1; else; fallas_li = fallas_li + 1; end; end
                        for p = 1:rend_l(k, 2); if rand() > probabilidad_error_vm; obt_le_ext = obt_le_ext + 1; else; fallas_le = fallas_le + 1; end; end
                        if sim == 1; fprintf(' [Libretas] patron %d (franja %d) -> li_int fallidos: %d | le_ext fallidos: %d\n', k, franja, fallas_li, fallas_le); end
                    end
                end
            end
        end
    end
    
    if sim == 1; fprintf('FIN DEL DETALLE DE LA SIMULACIÓN 1 (VINILO ECONÓMICO)\n\n'); end
    
    % se registra el resultado de las tres piezas obtenidas en este universo
    hist_a_int(sim) = obt_a_int;
    hist_li_int(sim) = obt_li_int;
    hist_le_ext(sim) = obt_le_ext;
    
    % validacion de exito (multiple): el proyecto solo es viable si las tres 
    % piezas de material sobreviven en cantidades iguales o mayores a la demanda
    if obt_a_int >= req_real_a_int && obt_li_int >= req_real_li_int && obt_le_ext >= req_real_le_ext
        exitos_simulacion_vm = exitos_simulacion_vm + 1;
    end
end

% calculamos la probabilidad final para el vinilo economico
nivel_confianza_vm = (exitos_simulacion_vm / num_simulaciones) * 100;

% impresion del reporte de la etapa de vinilo economico
fprintf('RESULTADOS FINALES DEL ESTRÉS (VINILO ECONÓMICO)\n');
fprintf('1. Demanda real estricta : %d a_int | %d li_int | %d le_ext\n', req_real_a_int, req_real_li_int, req_real_le_ext);
fprintf('2. Objetivo de corte     : %d a_int | %d li_int | %d le_ext\n\n', tapas_a_req, tapas_li_req, tapas_le_req);

fprintf('Estadisticas tras %d simulaciones:\n', num_simulaciones);
fprintf('- Promedio : %0.1f a_int | %0.1f li_int | %0.1f le_ext\n', mean(hist_a_int), mean(hist_li_int), mean(hist_le_ext));
fprintf('- Peor caso: %d a_int | %d li_int | %d le_ext\n', min(hist_a_int), min(hist_li_int), min(hist_le_ext));
fprintf('- Mejor caso: %d a_int | %d li_int | %d le_ext\n\n', max(hist_a_int), max(hist_li_int), max(hist_le_ext));

fprintf('CONCLUSIÓN VINILO ECONÓMICO:\n');
fprintf('Hay un %0.2f%% de confianza en que la compra cubre la demanda real\n', nivel_confianza_vm);

% PARTE 4: RESUMEN GLOBAL DEL PROYECTO

% imprimimos los resultados de los tres materiales
% Ademas imprime las demandas base utilizadas
% como mecanismo de control, permitiendo detectar visualmente 
% si los scripts originales se desincronizaron por un error de tipeo
% Antes de correr el código se debería corregir en los 3 anteriores
% los valores de demanda de agendas y libretas

fprintf('\n\nRESUMEN FINAL DE CONFIANZA DEL PROYECTO\n');
fprintf('Tras ejecutar %d universos paralelos por cada material:\n\n', num_simulaciones);

% Reporte Cartón Piedra (script 1)
fprintf('1. Cartón Piedra     : %0.2f%% de éxito (asumiendo %0.0f%% de prob. de falla)\n', nivel_confianza, probabilidad_error * 100);
fprintf('Manufactura simulada : %d agendas y %d libretas\n\n', demanda_agendas, demanda_libretas);

% Reporte Vinilo Exterior (script 2)
fprintf('2. Vinilo Exterior   : %0.2f%% de éxito (asumiendo %0.0f%% de prob. de falla)\n', nivel_confianza_v, probabilidad_error_v * 100);
fprintf('Manufactura simulada : %d agendas y %d libretas\n\n', dem_a, dem_l); 

% Reporte Vinilo Económico (script 3)
fprintf('3. Vinilo Económico  : %0.2f%% de éxito (asumiendo %0.0f%% de prob. de falla)\n', nivel_confianza_vm, probabilidad_error_vm * 100);
fprintf('Manufactura simulada : %d agendas y %d libretas\n\n', dem_a_eco, dem_l_eco);

tiempo_total = toc; 
fprintf('Simulación terminada. Tiempo total de ejecución: %.4f segundos\n\n\n\n\n', tiempo_total);

% Cerramos el registro al final del script
% Cada vez que corramos el script sobreescribira el archivo creado y
% añadira la simualcion nueva
%diary off;