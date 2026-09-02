from realestate.geo import haversine_km


def test_same_point_is_zero_distance():
    assert haversine_km(-34.6037, -58.3816, -34.6037, -58.3816) == 0


def test_known_distance_caba_to_la_plata():
    # Obelisco (CABA) a Plaza Moreno (La Plata): ~50-60 km en línea recta.
    distance = haversine_km(-34.6037, -58.3816, -34.9205, -57.9536)
    assert 45 < distance < 65
