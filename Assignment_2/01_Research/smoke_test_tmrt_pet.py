from ladybug.epw import EPW
from ladybug.sunpath import Sunpath
from ladybug.dt import DateTime
from ladybug_comfort.solarcal import outdoor_sky_heat_exch
from ladybug_comfort.pet import physiologic_equivalent_temperature as pet
epw=EPW(r'C:/Github_Repository/ARCH-540/Passivehouse_Tool/02_Data/EPW/CAN_BC_Vancouver.Intl.AP.718920_CWEC2020.epw')
loc=epw.location; sp=Sunpath.from_location(loc)
print(loc.city, loc.latitude, loc.longitude)
ta=epw.dry_bulb_temperature; rh=epw.relative_humidity; ws=epw.wind_speed
ir=epw.horizontal_infrared_radiation_intensity; dn=epw.direct_normal_radiation; dh=epw.diffuse_horizontal_radiation
def hour(month,day,h):
    dt=DateTime(month,day,h); i=int(round(dt.hoy)); return i
for (m,d,h) in [(1,15,12),(1,16,12),(7,15,14),(7,16,14)]:
    i=hour(m,d,h); sun=sp.calculate_sun_from_date_time(DateTime(m,d,h))
    alt=sun.altitude
    T=ta[i]; 
    print(f"\n{m}/{d} {h}:00 Ta={T:.1f} RH={rh[i]:.0f} wind10m={ws[i]:.1f} DNI={dn[i]:.0f} DHI={dh[i]:.0f} IR={ir[i]:.0f} sunAlt={alt:.1f}")
    for label,sky,fx in [('open sun',1.0,1.0),('open but shaded',1.0,0.0),('narrow court sun',0.4,1.0),('narrow court shade',0.4,0.0)]:
        r=outdoor_sky_heat_exch(T,ir[i],dh[i],dn[i],alt,sky_exposure=sky,fract_exposed=fx)
        p=pet(T,r['mrt'],1.0,rh[i],1.2,1.0)['pet']
        print(f"  {label:20s} Tmrt={r['mrt']:5.1f} (sw {r['s_dmrt']:+5.1f}, lw {r['l_dmrt']:+5.1f})  PET(met1.2,clo1.0,v=1.0 assumed)={p:5.1f}")
