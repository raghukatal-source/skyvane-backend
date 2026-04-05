import math

def haversine_km(p1, p2):
    R = 6371.0
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def interpolate_waypoints(origin, destination, n_points=8):
    if n_points < 2:
        return [origin, destination]
    waypoints = []
    for i in range(n_points):
        t  = i / (n_points - 1)
        wp = _slerp(origin, destination, t)
        waypoints.append(wp)
    return waypoints

def _slerp(p1, p2, t):
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    x1 = math.cos(lat1) * math.cos(lon1)
    y1 = math.cos(lat1) * math.sin(lon1)
    z1 = math.sin(lat1)
    x2 = math.cos(lat2) * math.cos(lon2)
    y2 = math.cos(lat2) * math.sin(lon2)
    z2 = math.sin(lat2)
    dot   = max(-1.0, min(1.0, x1*x2 + y1*y2 + z1*z2))
    omega = math.acos(dot)
    if abs(omega) < 1e-10:
        return p1
    sin_omega = math.sin(omega)
    s1 = math.sin((1-t) * omega) / sin_omega
    s2 = math.sin(t * omega)     / sin_omega
    xi = s1*x1 + s2*x2
    yi = s1*y1 + s2*y2
    zi = s1*z1 + s2*z2
    lat_i = math.degrees(math.atan2(zi, math.sqrt(xi**2 + yi**2)))
    lon_i = math.degrees(math.atan2(yi, xi))
    return (round(lat_i, 4), round(lon_i, 4))
