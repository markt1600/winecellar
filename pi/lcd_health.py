"""Small LCD health summaries, independent of hardware drivers."""
def failed_readings(db, start, end):
    # Count actual logged failed samples; downtime does not invent failures.
    row = db.execute("""SELECT COUNT(*),
        COALESCE(SUM(bottle_c IS NULL OR bottle_error IS NOT NULL),0),
        COALESCE(SUM(ambient_c IS NULL OR ambient_error IS NOT NULL),0),
        COALESCE(SUM(humidity_pct IS NULL OR ambient_error IS NOT NULL),0)
        FROM readings WHERE observed_at>=? AND observed_at<=?""", (start,end)).fetchone()
    return dict(zip(('bottle_c','ambient_c','humidity_pct'), row[1:] if row[0] else (None,None,None)))

def wifi_label(wifi):
    wifi = wifi or {}
    if wifi.get('state') == 'connected':
        percent = wifi.get('signalPercent')
        dbm = wifi.get('signalDbm')
        strength = f'{percent}%' if percent is not None else '--%'
        if dbm is not None: strength += f' ({dbm} dBm)'
        return f"Wi-Fi: Connected {strength} | {wifi.get('ssid','')}"
    if wifi.get('state') == 'disconnected': return 'Wi-Fi: Disconnected'
    return 'Wi-Fi: Status unavailable'
