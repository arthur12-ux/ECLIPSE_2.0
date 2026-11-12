from radiators_24_Grand_Challenge import Radiator_sizing_new
from heat_pipes_24_Grand_Challenge import Thermal_modeling_new
import numpy as np
import pandas as pd

# read in excel file

data_rad = pd.read_csv(
        "Thermal_Surrogate_Input.txt",
        sep="\t",
    )
d_new = data_rad.values.tolist()
q = [item[0] for item in d_new]
th = [item[1] for item in d_new]
print(q)
print(th)
Lrada = np.zeros(len(q))
Wrada = np.zeros(len(q))
areaa = np.zeros(len(q))
M_RADa = np.zeros(len(q))
M_ITCSa = np.zeros(len(q))
M_ETCSa = np.zeros(len(q))

for i in range(len(q)):
    Lrad, Wrad = Radiator_sizing_new(num_panels=10,n=0.9,e=0.85,th=th[i],alpha=0.09,Trad=330,Q=q[i],Earthshine_prop=[1400,0.3,385000,255],Surf_temp_prop=[-85,'hot'],Lunshine_prop=[-85,0,'hot'])
    area = Lrad*Wrad
    M_RAD = area*7.75
    M_ITCS,x = Thermal_modeling_new(Q=q[i],Cp=4200,Tout=310,Tin=290,rho=1000,Di=0.05,v=1e-6,Hab_prop=[4,4,4],Wrad=1,Lrad=5,pump_prop=[332,1130,386.1,1.121,0.45],state='ITCS',MHx_ITCS=0)
    M_ETCS = Thermal_modeling_new(Q=q[i], Cp=2200, Tout=330, Tin=310, rho=730, Di=0.025, v=0.21e-6, Hab_prop=[4, 4, 4],Wrad=1, Lrad=5, pump_prop=[332, 1130, 386.1, 1.121, 0.45], state='ETCS', MHx_ITCS=x)
    Lrada[i] = Lrad
    Wrada[i] = Wrad
    areaa[i] = area
    M_RADa[i] = M_RAD
    M_ITCSa[i] = M_ITCS
    M_ETCSa[i] = M_ETCS

file = {'Lrad (m)':Lrada,'Wrad (m)':Wrada,'area (m^2)':areaa,'Radiator Mass (kg)':M_RADa,'Mass of Inner Cooling Loop (kg)':M_ITCSa,'Mass of Outer Cooling Loop (kg)':M_ETCSa}
data = pd.DataFrame(file)
data.to_csv('Outputs_Surrogate_Thermal.csv')

    # write to excel file

