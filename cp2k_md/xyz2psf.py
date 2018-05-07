#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  3 22:57:34 2018

@author: Ivan Infante  
"""
import numpy as np
import argparse
from general.common import atomic_mass

def make_bond_matrix(n_atoms, coords):
    #Build a tensor made (n_atoms, axes, n_atoms), where axes = x-x0, y-y0, z-z0
    dist = np.stack(
            np.stack(
                    (coords[i_atm, i_ax] - coords[:, i_ax]) ** 2 for i_ax in range(coords.shape[1]) 
                    ) 
            for i_atm in range(n_atoms) 
            )      
    # Builds the bond distance matrix between atoms 
    r = np.stack(
            np.sqrt(np.sum(dist[i_atm, :, :], axis=0)) for i_atm in range(n_atoms)
            )
    return r 

def make_connectivity(r, bond_tresh):
    bonds = []
    angles = []
    dihedrals = []
    # This is a bit old-fashioned programming but it works. 
    # Loop over i, j to find connectivity between atoms, i.e. bonds 
    for i in range(r.shape[0]):
        for j in range(r.shape[0]):
            if ( (r[i, j] > 0.5) & (r[i, j] < bond_tresh) ):
                if( (i < j) ):
                #print(i,j)
                    bonds.extend((i+1,j+1))
    # Now loop also over k to find atoms that are connected by an angle 
                for k in range(r.shape[0]):
                    if ( (r[j, k] > 0.5) & (r[j, k] < bond_tresh) ):
                        if ( (i != j) & (i < k) & (j !=k)):
                            #print(i+1, j+1, k+1) 
                            angles.extend((i+1,j+1,k+1))
    # and finally loop over l to find dihedrals 
                        for l in range(r.shape[0]):
                            if ( (r[k, l] > 0.5) & (r[k, l] < bond_tresh) ):
                                if ( (i < j) & (i !=k) & (i < l) & (j !=k) & (j!=l) & ( k != l ) ):
                                            #print(i+1, j+1, k+1, l+1)
                                        dihedrals.extend( (i+1,j+1,k+1,l+1) )
    return bonds, angles, dihedrals

def print_connectivity(connects, n_lines):
    # This is a generic function that prints either bond, angles or dihedrals in psf format. 
    connects_list = '\n'
    for iconnect in range(0, len(connects) - n_lines, n_lines):
        fmt = '{:10d}' * n_lines + '\n'
        connects_list += fmt.format(*connects[iconnect:iconnect+n_lines])
    rest_lines = n_lines - len(connects)%n_lines
    if (rest_lines > 0):
        fmt = '{:10d}' * rest_lines
        connects_list += fmt.format(*connects[len(connects)-rest_lines:len(connects)])
    return connects_list 
   
def main(filename, idx, isolated, bond_tresh): 
    # Read some info from xyz file     
    atoms_lig = np.loadtxt(filename, skiprows=2, usecols=0, dtype=np.str)
    coords = np.loadtxt(filename, skiprows=2, usecols=(1,2,3))
    charges = np.loadtxt(filename, skiprows=2, usecols=4) 
    atoms_real = np.loadtxt(filename, skiprows=2, usecols=5, dtype=np.str)
    
    n_atoms = coords.shape[0] # Number of atoms

    # Compute the bond matrix 
    r = make_bond_matrix(n_atoms, coords)

    # Time to retrieve unique bonds, angles and dihedrals 
    bonds, angles, dihedrals = make_connectivity(r, bond_tresh)

    # Write PSF file
    g = 'PSF EXT \n \n'
    title = '{:10d} !NTITLE\n'.format(1)
    t_text = '   PSF generated by Ivan script \n \n'

    # Print atoms types and charges 
    atoms = '{:10d} !NATOM\n'.format(n_atoms) 
    atoms_list = g + title + t_text + atoms
    for iatom in range(n_atoms):
        atoms_list += '{:10d} MOL{:<4d}  R{:<7d} {:<7d}  {:<6s}  {:<6s}{:10.6f}     {:8.3f}           {:1d}\n'.format(
                iatom+1, idx, idx, 1, atoms_lig[iatom], atoms_lig[iatom], 
                charges[iatom], atomic_mass(atoms_real[iatom].lower()), 0) 
    
    # Print Bonds 
    n_bonds = int(len(bonds)/2) # Number of bonds 
    bonds_list = '\n\n{:10d} !NBOND'.format(n_bonds)
    if not isolated: 
    	bonds_list += print_connectivity(bonds, 8) # This is a bit hard-coding but that's the psf format. Same for angles and dihedrals  

    # Print angles 
    n_angles = int(len(angles)/3) # Number of angles 
    angles_list = '\n\n\n{:10d} !NTHETA'.format(n_angles)
    if not isolated:
    	angles_list += print_connectivity(angles, 9)

    # Print dihedrals  
    n_dihedrals = int(len(dihedrals)/4) # Number of angles 
    dihedrals_list = '\n\n\n{:10d} !NPHI'.format(n_dihedrals)
    if not isolated: 
    	dihedrals_list += print_connectivity(dihedrals, 8)

    endfile = '\n\n\n         0 !NIMPHI\n\n\n         0 !NDON\n\n\n         0 !NACC\n\n\n         0 !NNB\n\n\n'

    print(atoms_list+bonds_list+angles_list+dihedrals_list+endfile)

def read_cmd_line(parser):
    """
    Parse Command line options.
    """
    args = parser.parse_args()

    attributes = ['file', 'id', 'isolated', 'bond_tresh']

    return [getattr(args, p) for p in attributes]

if __name__ == "__main__":
    msg = "xyz2psf -file <path/to/filename> -id <id number>"

    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument(
        '-file', required=True, help='path to the xyz file to be converted in psf')
    parser.add_argument(
        '-id', required=True, type=int, help='Id number for the fragment used in the cp2k calculation')
    parser.add_argument(
        '-isolated', action='store_true', help='Consider atoms as isolated with no connectivity')
    parser.add_argument(
        '-bond_tresh', required=False, type=float, default=1.6, help='Consider bonds only below this treshold')
    main(*read_cmd_line(parser))


