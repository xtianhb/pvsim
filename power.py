# -*- coding: utf-8 -*-
"""
Simulador solar
@author: Cristian
"""

import random
import math
import time
#import matplotlib
import matplotlib.pyplot as plt
import abc

#CONSTANTS
HLINE= "-"*40
SYS24V=24
LAPSES = {"12HOURS":12, "1DAY":24, "1WEEK":24*7, "2WEEKS":24*14, "1MONTH":24*30 }
DELTAS = {"5MINS":5, "10MINS":10, "15MINS":15, "30MINS":30}
DEF_WEATHER = [3000, 8, 19, 10]
MONTHS = ["ene", "feb", "mar", "abr", "may", "jun",\
          "jul", "ago", "sep", "oct", "nov", "dic"]

""" 
  K: month
  V[0]: Irradiance wh/wp
  V[0]: Hour of sunrise
  V[1]: Hour of sunset
  V[1]: Rainfall days
"""
SunBA = { "ene":[6500,6,20,8 ], "feb":[5500,6.5,20,10], "mar":[4500,6.5,19,10],\
          "abr":[3000,7,19,10],"may":[2500,7.5,18,9], "jun":[2000,8,18,7],\
          "jul":[2000,7.5,19,10], "ago":[3000,7.5,19,7], "sep":[4000,7.0,19,9],\
          "oct":[5000,7.0,20,11], "nov":[6000,6.5,20,10], "dic":[6500,6.5,20,10] }

"""
"""
def H_HM(Hour):
    Hour += 1/60
    H = int(Hour)
    M = int( (Hour-H)*60)
    return "%02d:%02d"%(H,M)

"""
"""    
class Device(metaclass=abc.ABCMeta):
        
    """
    """
    def __init__(self, name, NPower, V):
        self.EAcc = 0 
        self.NPower = 40 #W Just for information
        self.V = 24 
        self.I = self.NPower/self.V #A Just for information
        self.Name = name
        self.Running = True
        
    """
    """
    def Info(self):
        print(HLINE)
        print("Device %s " % (self.Name))
        print("Nominal voltage =  %d " % (self.V))
        print("Nominal power =  %.1f W" % (self.NPower ) )
    
    """
    """
    def GetCurrent(self, BatV, Hour, DeltaT):
        P = self.GetPower(Hour)
        I = P / BatV
        E = P * DeltaT/60
        Ah = I * DeltaT/60
        self.EAcc += E
        return Ah
    
    """
    """
    @abc.abstractmethod
    def GetPower(self):
        return


"""
"""
class Solar():
    
    """
    """
    def __init__(self, Sup, Voltage, Sun=DEF_WEATHER) :
        self.Sun = Sun  # [irrad, sunrise, sunset, rfp]
        self.Area = Sup # Panel surface
        self.Yield = 0.15 #Panel efficiency with irradiance
        self.Wp = 1000 * self.Yield * self.Area # W / m2
        self.EffReg = 0.9  # Regulator effiency
        self.Voltage = Voltage # Output voltage of regulator
        self.H2 =  ( self.Sun[2] - self.Sun[1] ) # Sunlight time span
        self.Pa = self.Sun[0] * math.pi / (2.0 * self.H2) # Irradiance peak power
        self.WhAc = 0 #Accumulated WattHour delivered
    
    """
    """
    def Info(self):
        #print(HLINE)
        print("Solar panels")
        #print("Solar voltage configuration = %d V" % self.Voltage)
        #print("Yield = %.2f%%" % self.Yield )
        #print("Panels area = %d m2" % (self.Area) )
        #print("Peak available power = %d Wp" % self.Wp)
        print("  Irradiance / day = %s Wh" % self.Sun[0])
    
    """
    # Hour: Current time
    # DeltaT: time span
    # Sunny: sky
    # return: AmpereHour produced at output voltage of system
    """
    def GetCurrent(self, Hour, DeltaT, Sunny=True):
        if not Sunny:
            CloudEff = 0.15
        else:
            CloudEff = 1.0
        if Hour>=self.Sun[1] and Hour<=self.Sun[2]:
            w =  math.pi / self.H2
            HC = self.Sun[1] + self.H2 / 2
            SunP = self.Pa*math.cos( w * (Hour - HC) ) #W/m2
            self.WhAc += ( SunP * (DeltaT/60.0) )
            Ah = CloudEff * self.EffReg * (DeltaT/60) *\
                self.Yield * SunP * self.Area / self.Voltage
        else:
            Ah = 0
        return Ah

"""
"""
class Rain:
    
    MaxCloudRow = 0
    
    """
    """
    def __init__(self, Days):
        self.RDays = Days
        self.LastTime = 0
        self.Sunny = True
        self.RainLong = 24 # How long rains once starts
        self.SunLong = 24  # How long is the sky clear after rain
        self.CloudRow = 0
        
        
    """
    """
    def IsSunny(self, HNow):
        if self.Sunny and (HNow-self.LastTime)>self.SunLong:
            self.LastTime = HNow
            self.Sunny = bool( random.uniform(0, 30) > self.RDays )
            if self.Sunny:
                self.MaxCloudRow = 0
        if (not self.Sunny) and (HNow-self.LastTime)>self.RainLong:
            self.LastTime = HNow
            self.Sunny = bool( random.uniform(0, 30) > self.RDays )
            if self.CloudRow > Rain.MaxCloudRow:
                Rain.MaxCloudRow = self.CloudRow
            if not self.Sunny:
                self.CloudRow += 1
            else:
                self.MaxCloudRow = 0
        return self.Sunny
    """
    """
    def Info(self):
        #print(HLINE)
        print("Clouds")
        print("  Avg coud probability = %d days / month" % self.RDays)
        print("  Rain/Sun average time is %d/%d hours" % (self.RainLong,self.SunLong) )

class BatB():
    
    LastRState = 1.0
    
    """
    """
    def __init__(self, BSer, BPar, Cap):
        self.BatS = BSer
        self.BatP = BPar 
        self.Capacity = Cap #Ah
        self.Charge = BatB.LastRState * self.Capacity * self.BatP
        self.VNom = 12 * self.BatS
        self.Res50 = True
        self.Res50_C = 0
        self.Res30 = True
        self.Res30_C = 0
        self.Res00 = True
        self.Res00_C = 0
        self.Eff = 0.95
    
    """
    """    
    def Reserve(self):
        return 100*self.Charge/self.Capacity
    
    """
    """
    def TakeAmps(self, Ah, ):
        if self.Charge > Ah:
           self.Charge -= Ah/self.Eff
        else:
            self.Charge = 0
            if self.Res00:
                self.Res00 = False
                self.Res00_C += 1
            
        if (self.Charge < (self.Capacity/2)) and self.Res50:
            self.Res50 = False
            self.Res50_C += 1
            Sim.GlobalBat50 += 1
        
        if (self.Charge < (self.Capacity/3)) and self.Res30:
            self.Res30 = False
            self.Res30_C += 1
            Sim.GlobalBat30 += 1
            
    """
    """
    def GetV(self):
        R = self.Reserve()
        Span = 13.0 - 9.5
        Delta = Span / 10
        V = 9.5 + Delta * R/10
        return V*self.BatS
    
    """
    """
    def GetCharge(self):
        return self.Charge
    
    """
    """
    def PutAmps(self, AmpH):
        if (self.Capacity - self.Charge) > AmpH:
           self.Charge += AmpH * self.Eff
        else:
            self.Charge = self.Capacity
        
        self.Res00 = True
        
        if (self.Charge > (self.Capacity/2)) and (not self.Res50):
            self.Res50 = True
            
        if (self.Charge > (self.Capacity/3)) and (not self.Res30):
            self.Res30 = True
            
    """
    """
    def AmpH(self, AmpH):
        if AmpH>0:
            self.PutAmps( AmpH )  
        elif AmpH<0:
            self.TakeAmps( abs(AmpH) )
            
    """
    """        
    def Info(self):
        #print(HLINE)
        print("Batteries")
        #print("Number of batteries = %d" % (self.BatS * self.BatP))
        #print("Nominal voltage bank = %d V" % self.VNom)
        #print("Batteries in series # = %d" % self.BatS)
        #print("Batteries in parallel = %d" % self.BatP)
        #print("Bank capacity = %d Ah" % self.Capacity)
        print("  Bank charge = %.2f%%  / %.1fAh" % ( self.Reserve(), self.Charge) ) 


"""
"""
class Sim:
    
    GBATR = "Battery Reserve"
    GSOLAR = "Solar output"
    GDEV = "Device current"
    GlobalBatRMin = 100
    GlobalDevsOffTime = 0
    TotalSimTime = 0
    GlobalBat50 = 0
    GlobalBat30 = 0
    MaxCloudRow = 0
    """
    """
    def __init__(self, RainM, Panel, Battery, Devices, Month="jun"):
        self.RainM = RainM
        self.Solar = Panel
        self.Bat = Battery
        self.Devs = Devices
        self.HStart = 9
        self.HNow = 9
        self.DNow = 0
        self.Lapse = 24
        self.DeltaT = 1
        self.Data={}
        self.BatRMin = 100
        self.Discharging = False
        self.Warn50 = False
        self.DevsOffTime = 0
        self.Month = Month
        self.DevsRunning = True
        
    """
    """   
    def UpdateBatMin(self):
        R = self.Bat.Reserve()
        if self.Bat.Reserve() < self.BatRMin:
            self.BatRMin = R
        if self.BatRMin < Sim.GlobalBatRMin:
            Sim.GlobalBatRMin = self.BatRMin
        
    """
    """   
    def Info(self):
        pass
    
    """
    """    
    def SimInfo(self):
        self.Info()
        self.Solar.Info()
        self.Bat.Info()
        #for dev in self.Devs:
        #    dev.Info()
        self.RainM.Info()
     
    """
    """
    def ConfigSim(self, HStart=9, Lapse=24, DeltaT=10, Weather=DEF_WEATHER):
        self.HStart = HStart
        self.Lapse = Lapse # Horas
        self.HNow = self.HStart
        self.DeltaT = DeltaT
        self.Solar.Sun = Weather
        
    """
    """
    def printdbg(self, EqAh, SolarAh, Sunny):
        print("%02dd %s C=%03d%% %.1fAh V=%.1fV EqAh=%.1fAh AhS=%.1fAh Sunny=%s"\
                      % (self.DNow,\
                         H_HM(self.HNow),\
                         self.Bat.Reserve(),\
                         self.Bat.GetCharge(),\
                         self.Bat.GetV(),\
                         EqAh,\
                         SolarAh,\
                         Sunny )  ) 
        if self.HNow >= self.Solar.Sun[1] and\
               self.HNow <= self.Solar.Sun[2] and\
               self.Discharging == True:
                   self.Discharging = False
                   print("Solar charging battery")
                   
        if (self.HNow < self.Solar.Sun[1] or\
           self.HNow > self.Solar.Sun[2]) and\
           self.Discharging == False:
               self.Discharging = True
               print("Battery discharging")
    
    """
    """
    def CheckLevels(self):
        if self.Bat.Reserve() > 55 and self.Warn50==True:
                self.Warn50 = False
        if self.Bat.Reserve() < 50 and self.Warn50==False:
            print("Battery <50% !")
            self.Warn50 = True
    """
    """
    def IncrementTime(self):
        self.HNow += self.DeltaT/60.0
        if self.HNow >= 24:
           self.HNow = 0.0 
           self.DNow += 1.0
        self.ElapsedTime += self.DeltaT
        Sim.TotalSimTime += self.DeltaT
    
    """
    """
    def InitRun(self):
        self.ElapsedTime = 0  # minutos
        self.EndTime = self.Lapse * 60.0  # minutos
        self.HNow = self.HStart  # Current time in h
        self.DNow = 0
        P0 = 0
        for Dev in self.Devs:
            P0 += Dev.GetPower(self.HStart)/Dev.V 
        self.Data = { "t":[0],\
                     Sim.GBATR : [self.Bat.Reserve()],
                     Sim.GSOLAR: [0], 
                     Sim.GDEV: [P0] }
        
    """
    """
    def CalcValues(self):
        Sunny = self.RainM.IsSunny( self.ElapsedTime/60 )
        SolarAh = self.Solar.GetCurrent(self.HNow, self.DeltaT, Sunny)
        SolarOutput = SolarAh*self.Solar.Voltage
        EqAh = 0
        if self.DevsRunning and self.Bat.Reserve()<55:
                self.DevsRunning = False
        if not self.DevsRunning and self.Bat.Reserve()>=60:
                self.DevsRunning = True
        if self.DevsRunning:
            for Dev in self.Devs:
                EqAh += Dev.GetCurrent(self.Bat.GetV(), self.HNow, self.DeltaT)
        else:
            self.DevsOffTime += self.DeltaT
            Sim.GlobalDevsOffTime += self.DeltaT
        NetAh = SolarAh - EqAh
        return EqAh, NetAh, SolarOutput
    
    """
    """
    def Run(self):
        self.InitRun()
        while self.ElapsedTime <= self.EndTime:
            EqAh, NetAh, SolarOutput = self.CalcValues()
            self.Bat.AmpH(NetAh)
            self.UpdateBatMin()
            self.IncrementTime()
            self.Data["t"].append( self.ElapsedTime/60 )
            self.Data[Sim.GBATR].append( self.Bat.Reserve() )
            self.Data[Sim.GSOLAR].append( SolarOutput )
            self.Data[Sim.GDEV].append( self.DevsRunning * 60*EqAh/self.DeltaT )
            
        BatB.LastRState = self.Bat.Reserve()/100.0

    """
    """    
    def Results(self):
        print("Results")
        print("  Battery lowest reserve: %d%% " % self.BatRMin)
        print("  Battery drop below 50%%: %d times" % ( self.Bat.Res50_C) )
        #print("Battery drop below 30%%: %d times" % ( self.Bat.Res30_C) )
        print("  Battery final state: %d%%" % ( self.Bat.Reserve() ) )
        print("  Device turned off: %d hours / %.1f%%" % (\
              self.DevsOffTime/60,\
              100*self.DevsOffTime/60/self.Lapse) )
        print("Clouds in a row: %d", )

    """
    """
    def Graph(self, Graphs):
        plt.rc('font', size=12)
        X = [ x/24 for x in self.Data["t"] ]
        #print("Saving graph")
        for graph in Graphs:
            fig, ax = plt.subplots( nrows=1, ncols=1, figsize=(15,7) )
            Y = self.Data[ graph[0] ]
            m = " " + self.Month
            ax.set(xlabel='time (days)', ylabel = graph[0] + m  )
            ax.grid()
            ax.plot(X, Y, "-")
            plt.savefig("report/"+self.Month+graph[0]+".png")
            plt.close(fig)
    
    """
    """
    @classmethod
    def GlobalInfo(cls):
        print(HLINE)
        print("Global results")
        print("  Battery global lowest reserve: %d%%"%cls.GlobalBatRMin)
        print("  Global devices turned off: %0.2f%%"%\
              (100.0*cls.GlobalDevsOffTime/cls.TotalSimTime) )
        print("  Battery drop below 50%%: %d times"% Sim.GlobalBat50)
        print("  Battery drop below 30%%: %d times"% Sim.GlobalBat30)
        
            

"""
"""
def SolarSim(Di):
    MySPanel = Solar( Sup=Di["Sup"], Voltage=12*Di["BatS"] )
    MyBattery = BatB( BSer=Di["BatS"], BPar=Di["BatP"], Cap=Di["BatC"] )
    MyRain = Rain( Days=SunBA[Di["Month"]][3] )
    MySim = Sim(RainM=MyRain, Panel=MySPanel, Battery=MyBattery,\
                Devices=Di["Devices"], Month=Di["Month"])
    MySim.ConfigSim(    HStart=0,\
                        Lapse=Di["Lapse"],\
                        DeltaT=Di["DeltaT"],\
                        Weather=SunBA[Di["Month"]] )
    print(HLINE)
    print(MySim.Month.upper())
    MySim.SimInfo()
    MySim.Run()
    MySim.Results()
    MySim.Graph( Di["Graphs"]  )
    return
  
"""
# Custom implementation of a device
"""
class Device1(Device):

    """
    #  Custom energy profile
    #  Hour: Current hour
    #  DeltaT: Time span
    """
    def GetPower(self, Hour):
        P = self.V * 1.65
        return P

"""
# Custom implementation of a device
"""
class Device2(Device):

    """
    #  Custom energy profile
    #  Hour: Current hour
    #  DeltaT: Time span
    """
    def GetPower(self, Hour):
        if Hour>8 and Hour<19:
            P = 1
        else:
            P = 5
        return P

"""
# Connect bat result
# Add log to file
"""
def main():
    random.seed(a=time.time(), version=2) #seed for pRNG cloud days
    print("Solar panel simulator")
    print(HLINE)
    PDi = {"Sup":5, "BatS":2, "BatP":1, "BatC":180,\
         "Lapse": LAPSES["1MONTH"], "DeltaT": DELTAS["30MINS"] }
    PDi["Graphs"] = [ [Sim.GBATR] , [Sim.GSOLAR] ]
    PDi["Devices"] = [ Device1("MyEq1", 40, 24), Device2("MyEq2", 2, 24) ]
    print("Default parameters:")
    print("Panels surface (m2) = %d" % ( PDi["Sup"] ) )
    print("Batteries in series #: = %d" % ( PDi["BatS"] ) )
    print("Batteries series in parallel #: = %d" % ( PDi["BatP"] ) )
    print("One battery capacity Ah: = %d" % ( PDi["BatC"] ) ) 
    for Dev in PDi["Devices"]:
        print("%s: %dW, %dV, %dA" % ( Dev.Name, Dev.NPower, Dev.V, Dev.I ) )
    
    Enter = "n"
    #Enter = input("Want to change default parameters? (y/n): ")
    if Enter=="y":
        PDi["Sup"] = int( input("Panel surface in m2: ") )
        PDi["BatS"] = int(input("Batteries in series: ") )
        PDi["BatP"] = int(input("Batteries series in parallel: ") )
        PDi["BatC"] = int(input("Battery capacity: ") )  

    for m in MONTHS:
        PDi["Month"] = m
        SolarSim(PDi)

    Sim.GlobalInfo()
"""
"""   
if __name__ == "__main__":
    main()
 