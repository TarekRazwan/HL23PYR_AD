"""
Apply Alzheimer's-related ion channel changes. Import into your model to modify mechanisms.
"""
def apply_ad_changes(sec):
    """
    Example adjustments (tune/replace with your mechanisms):
    - NaTg gbar +20%
    - Nap gbar +30%
    - Kv3.1 gbar *0.5
    - SK gbar *0.6
    - Ih gbar *0.7
    """
    if 'hh' in sec().mechs():
        m = sec().mechs()['hh']
        m.gnabar *= 1.2
        m.gkbar *= 0.7