
import openseespy.opensees as ops
import math
from pathlib import Path



def analisis_opensees(path, permutaciones): #helper, #win
    ops.wipe()

    # bucle para generar los x análisis
    for i in range(len(permutaciones)):
        
        perfil = str(permutaciones[i][0])
        nf = permutaciones[i][2]
        amort = permutaciones[i][3]
        den = permutaciones[i][4]
        vel = permutaciones[i][5]
        capas = len(permutaciones[i][6])
        nstep = permutaciones[i][30]
        dt = float(permutaciones[i][31])
 
    # creación de elementos 
        sElemX = permutaciones[i][1]    # elementos en X
        sElemZ = permutaciones[i][46]   # espesor en Z   
        
        
# =============================================================================
#         ######## geometría de la columna ######
# =============================================================================
        # límite entre capas
        limite_capa = []
        anterior = 0
        for j in range(capas):
            espesor = permutaciones[i][8][j]
            
            limite_capa.append(espesor + anterior)
            anterior = limite_capa[j]
            print('Límite de capa: ' + str(limite_capa[j]))
        
        # creación de elementos y nodos en x
        nElemX = 1                      # elementos en x
        nNodeX = 2 * nElemX + 1         # nodos en x
        
        # creación de elementos y nodos para z
        nElemZ = 1
        
        # creación de elementos y nodos en Y y totales
        nElemY = []                     # elementos en y
        sElemY = []                     # dimension en y
        nElemT = 0
        for j in range(capas):
            espesor = permutaciones[i][8][j]
            
            nElemY.append(2 * espesor)
            nElemT += nElemY[j]           
            print('Elementos en capa ' + str(j + 1) + ': ' + str(nElemY[j]))
            sElemY.append(permutaciones[i][8][j] / nElemY[j])
            print('Tamaño de los elementos en capa ' + str(j + 1) + ': ' + str(sElemY[j]) + '\n')
        
        
        # number of nodes in vertical direction in each layer
        nNodeY = []                     # dimension en y
        nNodeT = 0
        s = 0
        for j in range(capas-1):
            nNodeY.append(4* nElemY[j])
            nNodeT += nNodeY[j]
            s+=1
            print('Nodos en capa ' + str(j + 1) + ': ' + str(nNodeY[j]))
           
        nNodeY.append(4 * (nElemY[-1] + 1))
        nNodeT += nNodeY[-1]
        print('Nodos en capa ' + str(s + 1) + ': ' + str(nNodeY[s]))
        print('Nodos totales: ' + str(nNodeT))
        
       
        #win.ui.progressBar.setValue(15)        
        
# =============================================================================
#         ######### Crear nodos del suelo ##########
# =============================================================================
        # creación de nodos de presión de poros
        ops.model('basic', '-ndm', 3, '-ndf', 4)
                
        with open(path + '/Post-proceso/' + perfil + '/ppNodesInfo.dat', 'w') as f:
            count = 0.0
            yCoord=0.0
            nodos = []
            dryNode = []
            altura_nf = 10 - nf
            
            
            for k in range(capas):
                for j in range(0, int(nNodeY[k]), 4):
                    ops.node(j+count+1,0.0, yCoord, 0.0)
                    ops.node(j+count+2, 0.0, yCoord, sElemZ)
                    ops.node(j+count+3, sElemX, yCoord, sElemZ)                    
                    ops.node(j+count+4, sElemX, yCoord, 0.0) 
                        
                    f.write(str(int(j+count+1)) + '\t' + str(0.0) + '\t' + str(yCoord) + '\t' + str(0.0) + '\n')
                    f.write(str(int(j+count+2)) + '\t' + str(0.0) + '\t' + str(yCoord) + '\t' + str(sElemZ) + '\n')
                    f.write(str(int(j+count+3)) + '\t' + str(sElemX) + '\t' + str(yCoord) + '\t' + str(sElemZ) + '\n')
                    f.write(str(int(j+count+4)) + '\t' + str(sElemX) + '\t' + str(yCoord) + '\t' + str(0.0) + '\n')
                     
                    nodos.append(str(j+count+1))
                    nodos.append(str(j+count+2))
                    nodos.append(str(j+count+3))
                    nodos.append(str(j+count+4))
                      
                    #designate node sobre la superficie de agua  
                    if yCoord>=altura_nf:
                        dryNode.append(j+count+1)
                        dryNode.append(j+count+2)
                        dryNode.append(j+count+3)
                        dryNode.append(j+count+4)
                    
                        
                    yCoord=(yCoord+sElemY[k])
                   
                    
                    
                    
                count=(count+nNodeY[k])
     
        print("Finished creating all soil nodes...")
        
         
        
# =============================================================================
#         ####### Condiciones de contorno en la base de la columna #########
# =============================================================================      
        ops.fix(1,*[0,1,1,0])
        ops.fix(2,*[0,1,1,0])
        ops.fix(3,*[0,1,1,0])
        ops.fix(4,*[0,1,1,0])
        ops.equalDOF(1,2,1)
        ops.equalDOF(1,3,1)
        ops.equalDOF(1,4,1)
        
        print('Fin de creación de nodos de la base de la columna\n\n') 
        

# =============================================================================
#         ####### Condiciones de contorno en los nudos restantes #########
# =============================================================================            
        
        count=0
        for k in range(5,int(nNodeT+1),4):
            ops.equalDOF(k, k + 1, *[1, 2, 3])
            ops.equalDOF(k, k + 2, *[1, 2, 3])
            ops.equalDOF(k, k + 3, *[1, 2, 3])
            
            
        print('Fin de creación equalDOF para nodos de presión de poros\n\n')
        
        for j in range(len(dryNode)):
            ops.fix(dryNode[j], *[0, 0, 0, 1])

        print("Finished creating all soil boundary conditions...")
        
        
        
        
        
# =============================================================================
#         ####### crear elemento y material de suelo #########
# =============================================================================
        
        cargas = []
        for j in range(capas):
            pendiente = permutaciones[i][9][j] 
            slope = math.atan(pendiente / 100)
            
            tipo_suelo = permutaciones[i][6][j] 
            rho = permutaciones[i][10][j]
            Gr = permutaciones[i][12][j]
            Br = permutaciones[i][13][j]
            fric = permutaciones[i][15][j]
            refpress = permutaciones[i][18][j]
            gmax = permutaciones[i][19][j]
            presscoef = permutaciones[i][20][j]
            surf = permutaciones[i][21][j]
            ev = permutaciones[i][22][j]
            cc1 = permutaciones[i][23][j]
            cc3 = permutaciones[i][24][j]
            cd1 = permutaciones[i][25][j]
            cd3 = permutaciones[i][26][j]
            ptang = permutaciones[i][27][j]
            coh = permutaciones[i][28][j]
    
            if tipo_suelo == 'No cohesivo':
                if float(surf) > 0:
                    ops.nDMaterial('PressureDependMultiYield02', j + 1, 3.0, rho, Gr, Br, fric, gmax, refpress, presscoef, ptang, 
                                   cc1, cc3, cd1, cd3, float(surf), 5.0, 3.0, *[1.0,0.0], ev, *[0.9, 0.02, 0.7, 101.0])
                else:
                    ops.nDMaterial('PressureDependMultiYield02', j + 1,3.0, rho, Gr, Br, fric, gmax, refpress, presscoef, ptang, 
                                   cc1, cc3, cd1, cd3,float(surf), *permutaciones[i][29][j], 5.0, 3.0, *[1.0,0.0], ev, *[0.9, 0.02, 0.7, 101.0])
        
            cargas.append([0.0, -9.81 * math.cos(slope), -9.81 * math.sin(slope)])
            
            
            
        print('Fin de la creación de material de suelo\n\n')
       
        
#-----------------------------------------------------------------------------------------
#  5. CREATE SOIL ELEMENTS
#-----------------------------------------------------------------------------------------
               
        count=0
        alpha=1.5e-6
        
        with open(path + '/Post-proceso/' + perfil + '/ppElemInfo.dat', 'w') as f:
            # crear elemento de suelo
            for k in range(capas):
                for j in range(int(nElemY[k])):
                    nI = 4 * (j + count + 1) - 3
                    nJ = nI + 1
                    nK = nI + 2
                    nL = nI + 3
                    nM = nI + 4
                    nN = nI + 5
                    nO = nI + 6
                    nP = nI + 7
                    f.write(str(j+count+1) +'\t'+ str(nI) + '\t'+ str(nJ) + '\t'+ str(nK) + '\t'+ str(nL) + '\t'+ 
                            str(nM) + '\t'+ str(nN) + '\t'+ str(nO) + '\t'+ str(nP) + '\n')
                    
                    Bc = permutaciones[i][14][k]
                    ev = permutaciones[i][22][k]
                    
                    ops.element('SSPbrickUP', (j + count + 1), *[nI, nJ, nK, nL, nM, nN, nO, nP], (k+1), float(Bc), 
                                1.0, 1.0, 1.0, 1.0, float(ev), alpha,cargas[k][0], cargas[k][1], cargas[k][2])
                    
                    
                count=(count+int(nElemY[k]))
        print('Fin de la creación del elemento del suelo\n\n')
        
        #win.ui.progressBar.setValue(25)
        
        
# =============================================================================
#         ######### Amortiguamiento de Lysmer ##########
# =============================================================================       
        
        ops.model('basic', '-ndm', 3, '-ndf', 3)
        
        # definir nodos y coordenadas del amortiguamiento
        dashF = nNodeT + 1
        dashX = nNodeT + 2
        dashZ = nNodeT + 3
        
        ops.node(dashF, 0.0, 0.0, 0.0)
        ops.node(dashX, 0.0, 0.0, 0.0)
        ops.node(dashZ, 0.0, 0.0, 0.0)
        
        
        # definir restricciones para los nodos de amortiguamiento
        ops.fix(dashF, 1, 1, 1)
        ops.fix(dashX, 0, 1, 1)
        ops.fix(dashZ, 1, 1, 0)
        
        # definir equalDOF para el amortiguamiento en la base del suelo
        ops.equalDOF(1, dashX, 1)
        ops.equalDOF(1, dashZ, 3)
        
        print('Fin de la creación de condiciones de contorno de los nodos de amortiguamiento\n\n')
        
        # definir el material de amortiguamiento
        colArea = sElemX * sElemZ
        dashpotCoeff = vel * den * colArea
        ops.uniaxialMaterial('Viscous', capas + 1, dashpotCoeff, 1.0)
        
        # definir el elemento 
        ops. element('zeroLength', nElemT + 1, *[dashF, dashX], '-mat', capas + 1, '-dir', *[1])
        ops. element('zeroLength', nElemT + 2, *[dashF, dashZ], '-mat', capas + 1, '-dir', *[3])
        
        print('Fin de la creación del elemento de amortiguamiento\n\n')
        

#-----------------------------------------------------------------------------------------
#  9. DEFINE ANALYSIS PARAMETERS
#-----------------------------------------------------------------------------------------    
          
        # amortiguamiento de Rayleigh
        # frecuencia menor
        omega1 = 2 * math.pi * 0.2 
        # frecuencia mayor
        omega2 = 2 * math.pi * 20
        
        
        a0 = 2.0 * (amort / 100) * omega1 * omega2 / (omega1 + omega2)
        a1 = 2.0 * (amort / 100) / (omega1 + omega2)
        print('Coeficientes de amortiguamiento' +'\n'+ 'a0: ' + format(a0, '.6f') + '\n' + 'a1: ' + format(a1, '.6f') + '\n\n')
        
        #win.ui.progressBar.setValue(35)
        
              
# =============================================================================
#         ######## Determinación de análisis estático #########
# =============================================================================
        #---DETERMINE STABLE ANALYSIS TIME STEP USING CFL CONDITION
        # se determina a partir de un análisis transitorio de largo tiempo
        duration = nstep * dt
        
        # tamaño mínimo del elemento y velocidad máxima
        minSize = sElemY[0]
        vsMax = permutaciones[i][11][0]
        for j in range(1,capas):
            if sElemY[j] < minSize:
                minSize = sElemY[j]
            if permutaciones[i][11][j] > vsMax:
                vsMax = permutaciones[i][11][j]
        
        # trial analysis time step        
        kTrial = minSize / (vsMax**0.5)
       
        # tiempo de análisis y pasos de tiempo
        if dt <= kTrial:
            nStep = nstep
            dT = dt
        else:
            nStep = int(math.floor(duration / kTrial) + 1)
            dT = duration / nStep
            
        print('Número de pasos en el análisis: ' + str(nStep) + '\n')
        print('Incremento de tiempo: ' + str(dT) + '\n\n')


#----------------------------------------------------------------------------------------
#  7. GRAVITY ANALYSIS
#-----------------------------------------------------------------------------------------
        ops.model('basic', '-ndm', 3, '-ndf', 4)
           

        ops.updateMaterialStage('-material', int(k+1), '-stage', 0)
        
        # algoritmo de análisis estático
        ops.constraints(permutaciones[i][32][0], float(permutaciones[i][32][1]), float(permutaciones[i][32][2]))
        ops.test(permutaciones[i][34][0], float(permutaciones[i][34][1]), int(permutaciones[i][34][2]), int(permutaciones[i][34][3]))
        ops.algorithm(permutaciones[i][38][0])
        ops.numberer(permutaciones[i][33][0])
        ops.system(permutaciones[i][36][0])
        ops.integrator(permutaciones[i][35][0], float(permutaciones[i][35][1]), float(permutaciones[i][35][2]))
        ops.analysis(permutaciones[i][37][0])
        
        print('Inicio de análisis estático elástico\n\n')
        
        ops.start()
        ops.analyze(20, 5.0e2)
      
        print('Fin de análisis estático elástico\n\n')
        
        #win.ui.progressBar.setValue(40)
        
        # update materials to consider plastic behavior
        
      
# =============================================================================
          
        ops.updateMaterialStage('-material', int(k+1), '-stage', 1)
        
      
# =============================================================================
        
        
        # plastic gravity loading
        print('Inicio de análisis estático plástico\n\n')
        

        ok=ops.analyze(40, 5.0e-2)
            
                    
        if ok != 0:
            error = 'Error de convergencia en análisis estático de modelo' + str(perfil) + '\n\n'
            print(error)
     
            break

        print('Fin de análisis estático plástico\n\n')
      
        
#-----------------------------------------------------------------------------------------
#  11. UPDATE ELEMENT PERMEABILITY VALUES FOR POST-GRAVITY ANALYSIS
#-----------------------------------------------------------------------------------------

        ini= 1
        aum = 0
        sum = 0
        for j in range(capas):
            #Layer 3
            ops.setParameter('-val', permutaciones[i][16][j], ['-eleRange', int(ini+aum),int(nElemY[j]+sum)], 'xPerm')
            ops.setParameter('-val', permutaciones[i][17][j], ['-eleRange', int(ini+aum),int(nElemY[j]+sum)], 'yPerm')
            ops.setParameter('-val', permutaciones[i][16][j], ['-eleRange', int(ini+aum),int(nElemY[j]+sum)], 'zPerm')
            
            ini = nElemY[j] + sum
            sum += nElemY[j]
            aum = 1
            
        print( "Finished updating permeabilities for dynamic analysis...")
        
        
        
# =============================================================================
#         ########### Grabadores dinámicos ##########
# =============================================================================

        ops.setTime(0.0)
        ops.wipeAnalysis()
        ops.remove('recorders')
        
        # tiempo de la grabadora
        recDT = 10 * dt
        path_acel = path + '/Post-proceso/' + perfil + '/dinamico/aceleraciones/'

        ops.recorder('Node', '-file', path_acel + 'accelerationx.out', '-time', '-dT', recDT, '-node', *nodos, '-dof', 1, 'accel')
      
        
        print('Fin de creación de grabadores\n\n')        
        #win.ui.progressBar.setValue(50)
        
        
# =============================================================================
#         ######### Determinación de análisis dinámico ##########
# =============================================================================
        
        
        # objeto de serie temporal para el historial de fuerza
        
        path_vel = path + '/Pre-proceso/' + perfil + '/TREASISL2.txt'
        
 
        ops.timeSeries('Path', 1, '-dt', dt, '-filePath', path_vel, '-factor', dashpotCoeff)
        
   
        ops.pattern('Plain', 10, 1)
        ops.load(1, *[1.0, 0.0, 0.0, 0.0])    #CAMBIO REALIZADO OJO
        
        print('Fin de creación de carga dinámica\n\n')
       
        
        # algoritmo de análisis dinámico
        ops.constraints(permutaciones[i][39][0], float(permutaciones[i][39][1]), float(permutaciones[i][39][2]))
        ops.test(permutaciones[i][41][0], float(permutaciones[i][41][1]), int(permutaciones[i][41][2]), int(permutaciones[i][41][3]))
        ops.algorithm(permutaciones[i][45][0])
        ops.numberer(permutaciones[i][40][0])
        ops.system(permutaciones[i][43][0])
        ops.integrator(permutaciones[i][42][0], float(permutaciones[i][42][1]), float(permutaciones[i][42][2]))
        ops.analysis(permutaciones[i][44][0])
# =============================================================================
#         ops.rayleigh(a0, a1, 0.0, 0.0)
# =============================================================================
        
        print('Inicio de análisis dinámico\n\n')
        #win.ui.progressBar.setValue(85)
        ok = ops.analyze(nStep, dT)
        
    
    
        if ok != 0:
            error = 'Error de convergencia en análisis dinámico de modelo' + str(permutaciones[i][0]) + '\n\n'
            print(error)
            curTime=ops.getTime()
            mTime=curTime
            print('cursTime:' + str(curTime))
            curStep=(curTime/dT)
            print('cursStep:' + str(curStep))
            rStep=(nStep-curStep)*2.0
            remStep=int(nStep-curStep)*2.0
            print('remSTep:' + str(curStep))
            dT=(dT/2)
            print('dT:' + str(dT))
            
            ops.analyze(remStep,dT)

        
                            
            if ok != 0:
                 error = 'Error de convergencia en análisis dinámico de modelo' + str(permutaciones[i][0]) + '\n\n'
                 print(error)
                 curTime=ops.getTime()
                 print('cursTime:' + str(curTime))
                 curStep=(curTime-mTime)/dT
                 print('cursStep:' + str(curStep))
                 remStep=int(rStep-curStep)*2
                 print('remSTep:' + str(curStep))
                 dT=(dT/2)
                 print('dT:' + str(dT))
                 
                 ops.analyze(remStep,dT)

     
        
        print('Fin de análisis dinámico\n\n')


       
        
  
    ops.wipe()      

#win.ui.progressBar.setValue(100) 
        
        
       
        
                  
# =============================================================================
#         ######### PERMUTACIONES ##########
# =============================================================================       
        

path = 'C:/Users/Franco/Desktop/V_TFT/Geometry'


permuta = [['Perfil', #Perfil nombre 
            2.0, # Ancho de columna X
            10.0, # ANivel freatico
            2.0, #amortiguamiento
            2.396, #5 densidad
            762.0, #6 velocidad 
            ['No cohesivo'], #6
            ['Estrato 1'], #7
            [10.0], #8 espesores
            [2.0], #9 grade
            [2.1], #10 # rho
            [190.0], #11 # Vs 
            [222900.0],  # Gr
            [220000.0], #Br
            [2.2e6], # Gc
            [29.0], #15 Angulo f
            [0.01], #vPerm
            [0.01], #hPerm
            [80.0], #18 refPress
            [0.1], #gmax PeakshearStra
            [0.0], #20 presscoef
            [20], #21 surf
            [0.47], #ev
            [0.06], #cc1
            [0.23], #cc3
            [0.5], #25 cd1
            [0.27], #cd3
            [27.0], #ptang
            [0.0], # coh
            [[]],#29 
            2001, #30
            '0.020', 
            ['Penalty', 1e14, 1e14], 
            ['Plain'], 
            ['NormDispIncr', 1e-5, 30, 1], 
            ['Newmark', 0.5, 0.25], #35
            ['SparseGeneral'], 
            ['Transient'], 
            ['Newton', 0.0],
            ['Penalty', 1.0e14, 1.0e14], 
            ['Plain'], #40
            ['NormDispIncr', 1.0e-3, 55, 1], 
            ['Newmark', 0.5, 0.25], 
            ['SparseGeneral'], 
            ['Transient'], 
            ['Newton', 0.0], #45
            2.0]] #46


analisis_opensees(path, permuta)
