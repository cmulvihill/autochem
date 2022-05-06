""" transition state graph data structure

Forming bonds are encoded as 0.1-order bonds
Breaking bonds are encoded as 0.9-order bonds

Otherwise, this is equivalent to any other graph

BEFORE ADDING ANYTHING, SEE IMPORT HIERARCHY IN __init__.py!!!!
"""
from automol.util import dict_
from automol.graph.base._core import bond_orders
from automol.graph.base._core import atom_stereo_parities
from automol.graph.base._core import bond_stereo_parities
from automol.graph.base._core import set_bond_orders
from automol.graph.base._core import atom_stereo_keys
from automol.graph.base._core import bond_stereo_keys
from automol.graph.base._core import add_bonds
from automol.graph.base._core import remove_bonds
from automol.graph.base._core import without_dummy_atoms
from automol.graph.base._core import without_stereo_parities
from automol.graph.base._algo import rings_bond_keys
from automol.graph.base._algo import sorted_ring_atom_keys_from_bond_keys
from automol.graph.base._stereo import stereomers as _stereomers
from automol.graph.base._canon import class_indices
from automol.graph.base._canon import stereogenic_atom_keys
from automol.graph.base._canon import stereogenic_bond_keys
from automol.graph.base._canon import to_local_stereo as _to_local_stereo
from automol.graph.base._canon import from_local_stereo as _from_local_stereo


def graph(gra, frm_bnd_keys, brk_bnd_keys):
    """ generate a transition-state graph
    """
    frm_bnd_keys = frozenset(map(frozenset, frm_bnd_keys))
    brk_bnd_keys = frozenset(map(frozenset, brk_bnd_keys))

    frm_ord_dct = {k: 0.1 for k in frm_bnd_keys}
    brk_ord_dct = {k: 0.9 for k in brk_bnd_keys}

    tsg = add_bonds(gra, frm_bnd_keys, ord_dct=frm_ord_dct, check=False)
    tsg = add_bonds(tsg, brk_bnd_keys, ord_dct=brk_ord_dct, check=False)
    return tsg


def forming_bond_keys(tsg):
    """ get the forming bonds from a transition state graph
    """
    ord_dct = bond_orders(tsg)
    frm_bnd_keys = [k for k, o in ord_dct.items() if round(o, 1) == 0.1]
    return frozenset(map(frozenset, frm_bnd_keys))


def breaking_bond_keys(tsg):
    """ get the forming bonds from a transition state graph
    """
    ord_dct = bond_orders(tsg)
    brk_bnd_keys = [k for k, o in ord_dct.items() if round(o, 1) == 0.9]
    return frozenset(map(frozenset, brk_bnd_keys))


def reverse(tsg, dummies=True):
    """ reverse a transition state graph
    """
    if not dummies:
        tsg = without_dummy_atoms(tsg)

    return graph(gra=tsg,
                 frm_bnd_keys=breaking_bond_keys(tsg),
                 brk_bnd_keys=forming_bond_keys(tsg))


def forming_rings_atom_keys(tsg):
    """ get the atom keys to rings forming in the TS graph
    """
    frm_rngs_bnd_keys = forming_rings_bond_keys(tsg)
    frm_rngs_atm_keys = tuple(map(sorted_ring_atom_keys_from_bond_keys,
                                  frm_rngs_bnd_keys))
    return frm_rngs_atm_keys


def forming_rings_bond_keys(tsg):
    """ get the bond keys to rings forming in the TS graph
    """
    frm_bnd_keys = forming_bond_keys(tsg)
    frm_rngs_bnd_keys = tuple(bks for bks in rings_bond_keys(tsg)
                              if frm_bnd_keys & bks)
    return frm_rngs_bnd_keys


def breaking_rings_atom_keys(tsg):
    """ get the atom keys to rings breaking in the TS graph
    """
    brk_rngs_bnd_keys = breaking_rings_bond_keys(tsg)
    brk_rngs_atm_keys = tuple(map(sorted_ring_atom_keys_from_bond_keys,
                                  brk_rngs_bnd_keys))
    return brk_rngs_atm_keys


def breaking_rings_bond_keys(tsg):
    """ get the bond keys to rings breaking in the TS graph
    """
    brk_bnd_keys = breaking_bond_keys(tsg)
    brk_rngs_bnd_keys = tuple(bks for bks in rings_bond_keys(tsg)
                              if brk_bnd_keys & bks)
    return brk_rngs_bnd_keys


def reactants_graph(tsg):
    """ get a graph of the reactants from a transition state graph
    """
    frm_bnd_keys = forming_bond_keys(tsg)
    ord_dct = dict_.transform_values(bond_orders(tsg), func=round)
    gra = set_bond_orders(tsg, ord_dct)
    gra = remove_bonds(gra, frm_bnd_keys)
    return gra


def products_graph(tsg):
    """ get a graph of the products from a transition state graph
    """
    return reactants_graph(reverse(tsg))


def conserved_atom_stereo_keys(can_tsg, prds_idx_dct=None):
    """ Determine atom stereo centers which are conserved by the reaction.

    'Conserved' means these atoms are stereogenic for both the reactants and
    the products.

    :param can_tsg: The TS graph, with stereo assignments.
    :parm prds_idx_dct: Symmetry class indices for the products, to avoid
        recalculating
    :returns: Conserved atom stereo centers.
    :rtype: frozenset
    """
    rcts_gra = reactants_graph(can_tsg)
    prds_gra = products_graph(can_tsg)
    prds_idx_dct = (class_indices(prds_gra, backbone_only=False) if
                    prds_idx_dct is None else prds_idx_dct)

    keys1 = atom_stereo_keys(rcts_gra)
    keys2 = stereogenic_atom_keys(prds_gra, assigned=True,
                                  idx_dct=prds_idx_dct)

    cons_ste_atm_keys = frozenset(keys1 & keys2)
    print(cons_ste_atm_keys)

    return cons_ste_atm_keys


def conserved_bond_stereo_keys(can_tsg, prds_idx_dct=None):
    """ Determine bond stereo centers which are conserved by the reaction.

    'Conserved' means these bonds are stereogenic for both the reactants and
    the products.

    :param can_tsg: The TS graph, with stereo assignments.
    :parm prds_idx_dct: Symmetry class indices for the products, to avoid
        recalculating
    :returns: Conserved bond stereo centers.
    :rtype: frozenset
    """
    rcts_gra = reactants_graph(can_tsg)
    prds_gra = products_graph(can_tsg)
    prds_idx_dct = (class_indices(prds_gra, backbone_only=False) if
                    prds_idx_dct is None else prds_idx_dct)

    keys1 = bond_stereo_keys(rcts_gra)
    keys2 = stereogenic_bond_keys(prds_gra, assigned=True,
                                  idx_dct=prds_idx_dct)

    cons_ste_bnd_keys = frozenset(keys1 & keys2)
    print(cons_ste_bnd_keys)

    return cons_ste_bnd_keys


def nonconserved_atom_stereo_keys(can_tsg, prds_idx_dct=None):
    """ Determine atom stereo centers which are not conserved by the reaction.

    This includes atoms which are stereogenic for the products but not for the
    reactants ("created" stereo centers) and atoms which are stereogenic for
    the reactants but not for the products ("destroyed" stereo centers).

    :param can_tsg: The TS graph, with stereo assignments.
    :parm prds_idx_dct: Symmetry class indices for the products, to avoid
        recalculating
    :returns: Created and destroyed atom stereo centers, respectively.
    :rtype: (frozenset, frozenset)
    """
    rcts_gra = reactants_graph(can_tsg)
    prds_gra = products_graph(can_tsg)
    prds_idx_dct = (class_indices(prds_gra, backbone_only=False) if
                    prds_idx_dct is None else prds_idx_dct)

    keys1 = atom_stereo_keys(rcts_gra)
    keys2 = stereogenic_atom_keys(prds_gra, assigned=True,
                                  idx_dct=prds_idx_dct)

    cre_ste_atm_keys = frozenset(keys2 - keys1)
    des_ste_atm_keys = frozenset(keys1 - keys2)

    return cre_ste_atm_keys, des_ste_atm_keys


def nonconserved_bond_stereo_keys(can_tsg, prds_idx_dct=None):
    """ Determine bond stereo centers which are not conserved by the reaction.

    This includes bonds which are stereogenic for the products but not for the
    reactants ("created" stereo centers) and bonds which are stereogenic for
    the reactants but not for the products ("destroyed" stereo centers).

    :param can_tsg: The TS graph, with stereo assignments.
    :parm prds_idx_dct: Symmetry class indices for the products, to avoid
        recalculating
    :returns: Created and destroyed bond stereo centers, respectively.
    :rtype: (frozenset, frozenset)
    """
    rcts_gra = reactants_graph(can_tsg)
    prds_gra = products_graph(can_tsg)
    prds_idx_dct = (class_indices(prds_gra, backbone_only=False) if
                    prds_idx_dct is None else prds_idx_dct)

    keys1 = bond_stereo_keys(rcts_gra)
    keys2 = stereogenic_bond_keys(prds_gra, assigned=True,
                                  idx_dct=prds_idx_dct)

    cre_ste_bnd_keys = frozenset(keys2 - keys1)
    des_ste_bnd_keys = frozenset(keys1 - keys2)

    return cre_ste_bnd_keys, des_ste_bnd_keys


def to_local_stereo(can_tsg):
    """ Convert a TS graph to index-based stereo assignments, where parities
    are defined relative to the ordering of indices rather than the absolute
    stereo priority.

    :param can_tsg: a TS graph with absolute stereo assignments
    :returns: a TS graph with index-based stereo assignments
    """
    rcts_gra = reactants_graph(can_tsg)
    frm_bnd_keys = forming_bond_keys(can_tsg)
    brk_bnd_keys = breaking_bond_keys(can_tsg)

    rcts_gra = _to_local_stereo(rcts_gra)
    loc_tsg = graph(rcts_gra, frm_bnd_keys, brk_bnd_keys)
    return loc_tsg


def from_local_stereo(loc_tsg):
    """ Convert a TS graph from index-based stereo assignments back to absolute
    stereo assignments, where parities are independent of atom ordering.

    :param loc_tsg: a TS graph with index-based stereo assignments
    :returns: a TS graph with absolute stereo assignments
    """
    rcts_gra = reactants_graph(loc_tsg)
    frm_bnd_keys = forming_bond_keys(loc_tsg)
    brk_bnd_keys = breaking_bond_keys(loc_tsg)

    rcts_gra = _from_local_stereo(rcts_gra)
    can_tsg = graph(rcts_gra, frm_bnd_keys, brk_bnd_keys)
    return can_tsg


def stereomers(tsg):
    """ Expand all possible stereo assignments for the reactants in this TS
    graph. (Ignores stereo assignments already present, if any.)

    :param tsg: The TS graph, without stereo assignments.
    :returns: All possible TS graphs with stereo assignments for the reactants.
    """
    rcts_gra = reactants_graph(tsg)
    frm_bnd_keys = forming_bond_keys(tsg)
    brk_bnd_keys = breaking_bond_keys(tsg)

    rcts_gra = without_stereo_parities(rcts_gra)
    rcts_sgrs = _stereomers(rcts_gra)
    can_tsgs = tuple(
        graph(rcts_sgr, frm_bnd_keys, brk_bnd_keys) for rcts_sgr in rcts_sgrs)
    return can_tsgs


def compatible_reverse_stereomers(can_tsg):
    """ Given a TS graph with stereo assignments, expand all possible reverse
    graphs compatble with the forward graph.

    :param can_tsg: A TS graph, with canonical stereo assignments.
    :returns: All possible reverse TS graphs.
    """
    prds_gra = products_graph(can_tsg)
    prds_idx_dct = class_indices(prds_gra, backbone_only=False)

    frm_bnd_keys = forming_bond_keys(can_tsg)
    brk_bnd_keys = breaking_bond_keys(can_tsg)
    cons_atm_keys = sorted(
        conserved_atom_stereo_keys(can_tsg, prds_idx_dct=prds_idx_dct))
    cons_bnd_keys = sorted(
        conserved_bond_stereo_keys(can_tsg, prds_idx_dct=prds_idx_dct))

    # 1. Determine local stereo assignments for conserved stereo centers
    loc_tsg = to_local_stereo(can_tsg)
    cons_loc_atm_pars = dict_.values_by_key(
        atom_stereo_parities(loc_tsg), cons_atm_keys)
    cons_loc_bnd_pars = dict_.values_by_key(
        bond_stereo_parities(loc_tsg), cons_bnd_keys)

    # 2. Expand all possibile assignments for the products and convert them to
    #    local stereo assignments.
    prds_gra = without_stereo_parities(products_graph(can_tsg))
    prds_can_gras = list(_stereomers(prds_gra))
    prds_loc_gras = list(map(_to_local_stereo, prds_can_gras))

    # 3. Find possibilities which match the assignments for the conserved
    #    stereo centers.
    rev_can_tsgs = []
    for prds_can_gra, prds_loc_gra in zip(prds_can_gras, prds_loc_gras):
        prd_cons_loc_atm_pars = dict_.values_by_key(
            atom_stereo_parities(prds_loc_gra), cons_atm_keys)
        prd_cons_loc_bnd_pars = dict_.values_by_key(
            bond_stereo_parities(prds_loc_gra), cons_bnd_keys)

        if (prd_cons_loc_atm_pars == cons_loc_atm_pars and
                prd_cons_loc_bnd_pars == cons_loc_bnd_pars):
            # Form the reverse graph, with canonical stereo assignments
            rev_can_tsg = graph(prds_can_gra, brk_bnd_keys, frm_bnd_keys)
            rev_can_tsgs.append(rev_can_tsg)

    return rev_can_tsgs
