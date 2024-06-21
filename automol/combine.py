"""
    Handle information for multiple species
      (1) van der Waals wells,
      (2) reaction path points
"""

from automol import form, geom


# Combines via geometry
def formula_string(*geos):
    """get the overall combined stoichiometry"""
    fml = form.join_sequence(list(map(geom.formula, geos)))
    return form.string2(fml)


def fake_vdw_geometry(*geos):
    """put two geometries together in a fake well"""
    return geom.join_sequence(geos)


def fake_vdw_frequencies_new(*geos):
    """generate fake frequencies to fill in the missing internal modes of a fake well"""

    def _external_mode_count(geo):
        return 3 if geom.is_atom(geo) else 5 if geom.is_linear(geo) else 6

    fake_geo = fake_vdw_geometry(*geos)
    nfake = sum(map(_external_mode_count, geos)) - _external_mode_count(fake_geo)
    return tuple(30.0 + i * 20.0 for i in range(nfake))


def fake_vdw_frequencies(geo1, geo2):
    """Set fake frequencies"""

    freqs = [30.0, 50.0, 70.0, 100.0, 200.0]
    ntrans = 5

    # Check atom types
    is_atom_i = geom.is_atom(geo1)
    is_linear_i = geom.is_linear(geo1)
    is_atom_j = geom.is_atom(geo2)
    is_linear_j = geom.is_linear(geo2)
    if is_atom_i and is_atom_j:
        ntrans = 0
    else:
        if is_atom_i:
            ntrans -= 3
        if is_atom_j:
            ntrans -= 3
        if is_linear_i:
            ntrans -= 2
        if is_linear_j:
            ntrans -= 2

    return tuple(freqs[0:ntrans])


# Combines by elec levels
def electronic_energy_levels(elec_levels_i, elec_levels_j):
    """Put two elec levels together for two species"""

    # Combine the energy levels
    init_elec_levels = []
    for _, elec_level_i in enumerate(elec_levels_i):
        for _, elec_level_j in enumerate(elec_levels_j):
            init_elec_levels.append(
                [elec_level_i[0] + elec_level_j[0], elec_level_i[1] * elec_level_j[1]]
            )

    # See if any levels repeat and thus need to be added together
    elec_levels = []
    for level in init_elec_levels:
        # Put level in in final list
        if level not in elec_levels:
            elec_levels.append(level)
        # Add the level to the one in the list
        else:
            idx = elec_levels.index(level)
            elec_levels[idx][1] += level[1]

    # Sort the levels by the value of the energy
    elec_levels = sorted(elec_levels, key=lambda x: x[0])

    return tuple(map(tuple, elec_levels))
