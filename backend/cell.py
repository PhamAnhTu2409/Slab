#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" @author: yyyu200@163.com """

import numpy as np
import copy
import re
import os
import f90nml

BOHR2ANGS = 0.52917720859

def ext_euclid(a, b):
    """Extended Euclidean algorithm"""
    if b == 0:
        return 1, 0, a
    else:
        x, y, q = ext_euclid(b, a % b)
        x, y = y, (x - (a // b) * y)
        return x, y, q

def get_atomic_weight(at):
    """Get atomic weight from element symbol"""
    sym_wt = {
        'H': 1.00794, 'He': 4.00260, 'Li': 6.941, 'Be': 9.01218, 'B': 10.811, 
        'C': 12.0107, 'N': 14.00674, 'O': 15.9994, 'F': 18.99840, 'Ne': 20.1797, 
        'Na': 22.98977, 'Mg': 24.3050, 'Al': 26.98154, 'Si': 28.0855, 'P': 30.97376, 
        'S': 32.066, 'Cl': 35.4527, 'Ar': 39.948, 'K': 39.0983, 'Ca': 40.078, 
        'Sc': 44.95591, 'Ti': 47.867, 'V': 50.9415, 'Cr': 51.9961, 'Mn': 54.93805, 
        'Fe': 55.845, 'Co': 58.93320, 'Ni': 58.6934, 'Cu': 63.546, 'Zn': 65.39, 
        'Ga': 69.723, 'Ge': 72.61, 'As': 74.92160, 'Se': 78.96, 'Br': 79.904, 
        'Kr': 83.80, 'Rb': 85.4678, 'Sr': 87.62, 'Y': 88.90585, 'Zr': 91.224, 
        'Nb': 92.90638, 'Mo': 95.94, 'Tc': 98.0, 'Ru': 101.07, 'Rh': 102.90550, 
        'Pd': 106.42, 'Ag': 107.8682, 'Cd': 112.411, 'In': 114.818, 'Sn': 118.710, 
        'Sb': 121.760, 'Te': 127.60, 'I': 126.90447, 'Xe': 131.29, 'Cs': 132.90545, 
        'Ba': 137.327, 'La': 138.9055, 'Ce': 140.116, 'Pr': 140.90765, 'Nd': 144.24, 
        'Pm': 145.0, 'Sm': 150.36, 'Eu': 151.964, 'Gd': 157.25, 'Tb': 158.92534, 
        'Dy': 162.50, 'Ho': 164.93032, 'Er': 167.26, 'Tm': 168.93421, 'Yb': 173.04, 
        'Lu': 174.967, 'Hf': 178.49, 'Ta': 180.9479, 'W': 183.84, 'Re': 186.207, 
        'Os': 190.23, 'Ir': 192.217, 'Pt': 195.078, 'Au': 196.96655, 'Hg': 200.59, 
        'Tl': 204.3833, 'Pb': 207.2, 'Bi': 208.98038, 'Po': 209.0, 'At': 210.0, 
        'Rn': 222.0, 'Fr': 223.0, 'Ra': 226.0, 'Ac': 227.0, 'Th': 232.0381, 
        'Pa': 231.03588, 'U': 238.0289, 'Np': 237.0, 'Pu': 244.0, 'Am': 243.0, 
        'Cm': 247.0, 'Bk': 247.0, 'Cf': 251.0, 'Es': 252.0, 'Fm': 257.0, 
        'Md': 258.0, 'No': 259.0, 'Lr': 262.0, 'Rf': 261.0, 'Db': 262.0, 
        'Sg': 266.0, 'Bh': 264.0, 'Hs': 277.0, 'Mt': 268.0
    }
    return str(sym_wt.get(at, "1.0"))

def parse_lines_float(key, lines):
    """Parse float value from lines"""
    tmpstr = parse_lines(key, lines)
    return np.float64(tmpstr) if tmpstr else 0.0

def parse_lines_system(filename, key):
    """Parse system parameters from QE input"""
    try:
        nml = f90nml.read(filename)
        if 'system' in nml and key in nml['system']:
            return nml['system'][key]
    except:
        pass
    return None

def parse_lines(key, lines):
    """Parse key from multiple lines"""
    for l in lines:
        res = parse_str(key, l)
        if res:
            return res
    return None

def parse_str(key, line):
    """Parse key from single line"""
    findkey = re.search(key, line)
    if findkey:
        r1 = line.split('!')[0].split(',')
        for s in r1:
            r2 = re.search(key, s)
            if r2:
                return s.split('=')[1].strip()
    return None

def fan(v1, v2):
    """Calculate angle between two vectors in degrees"""
    c = np.dot(v1, v2) / np.sqrt(v1.dot(v1)) / np.sqrt(v2.dot(v2))
    c = np.clip(c, -1.0, 1.0)  # Avoid numerical errors
    return np.arccos(c) * 180 / np.pi

def dist2(a, b=[0, 0, 0]):
    """Calculate squared distance between two points"""
    return (a[0] - b[0])**2 + (a[1] - b[1])**2 + (a[2] - b[2])**2

def mixproduct(a, b, c):
    """Calculate mixed product of three vectors"""
    return np.cross(a, b).dot(c)

class CELL(object):
    """Crystal structure cell class"""
    eps1 = 1.0e-8
    
    def __init__(self, fnam, fmt='POSCAR'):
        """
        Initialize from POSCAR, QE, or CIF format
        
        Parameters:
        fnam: filename
        fmt: 'POSCAR', 'QE', or 'CIF'
        """
        if fmt.upper() == 'CIF':
            self._init_from_cif(fnam)
        elif fmt == 'POSCAR':
            self._init_from_poscar(fnam)
        elif fmt == 'QE':
            self._init_from_qe(fnam)
        else:
            raise ValueError(f"Unsupported format: {fmt}")
    
    def _init_from_cif(self, filename):
        """Initialize from CIF file"""
        from cif_parser import CIFParser
        parser = CIFParser()
        cif_data = parser.parse_cif(filename)
        
        # Get lattice parameters
        lp = cif_data['lattice_parameters']
        self.cell = parser.lattice_parameters_to_vectors(
            lp['a'], lp['b'], lp['c'], 
            lp['alpha'], lp['beta'], lp['gamma']
        )
        
        self.alat = 1.0
        self.system = cif_data.get('chemical_name', 'From CIF file')
        
        # Process atoms
        atoms = cif_data['atoms']
        if not atoms:
            raise ValueError("No atoms found in CIF file")
        
        elements = list(set([atom['element'] for atom in atoms]))
        self.ntyp = len(elements)
        self.typ_name = elements
        self.typ_num = [0] * self.ntyp
        
        self.nat = len(atoms)
        self.atpos = np.zeros((self.nat, 3))
        self.attyp = np.zeros(self.nat, dtype=int)
        
        for i, atom in enumerate(atoms):
            self.atpos[i] = atom['position']
            element_idx = elements.index(atom['element'])
            self.attyp[i] = element_idx
            self.typ_num[element_idx] += 1
        
        self.coordsystem = "Direct"
        
        # Check positive volume
        volume = self.get_volume()
        if volume < self.eps1:
            raise ValueError("Invalid cell: non-positive volume")
        
        self.tidy_up()
    
    def _init_from_poscar(self, filename):
        """Initialize from POSCAR file with Selective dynamics support"""
        with open(filename, 'r', encoding='utf-8') as fi:
            lines = [line.strip() for line in fi if line.strip()]
        
        if len(lines) < 8:
            raise ValueError("POSCAR file too short")
        
        self.system = lines[0]
        self.alat = float(lines[1])
        
        # Parse cell vectors
        self.cell = np.zeros((3, 3))
        for i in range(3):
            self.cell[i] = [float(x) * self.alat for x in lines[2 + i].split()[:3]]
        
        # Check right-hand system
        if mixproduct(self.cell[0], self.cell[1], self.cell[2]) < -self.eps1:
            raise RuntimeError("Imported POSCAR should be right-hand system")
        
        # Parse element types and counts
        self.typ_name = lines[5].split()
        self.ntyp = len(self.typ_name)
        self.typ_num = np.array([int(x) for x in lines[6].split()[:self.ntyp]], dtype=np.int32)
        
        # Handle Selective dynamics
        coord_line_index = 7
        self.has_selective_dynamics = False
        
        if coord_line_index < len(lines) and 'selective' in lines[coord_line_index].lower():
            self.has_selective_dynamics = True
            coord_line_index += 1
        
        self.coordsystem = lines[coord_line_index]
        
        # Validate coordinate system
        if self.coordsystem[0].lower() not in ['d', 'c']:
            raise ValueError(f"Invalid coordinate system: {self.coordsystem}")
        
        # Calculate total atoms
        self.nat = int(np.sum(self.typ_num))
        
        # Initialize atom arrays
        self.attyp = np.zeros(self.nat, dtype=int)
        self.atpos = np.zeros((self.nat, 3))
        
        # Fill atom types
        atom_idx = 0
        for i in range(self.ntyp):
            for j in range(self.typ_num[i]):
                self.attyp[atom_idx] = i
                atom_idx += 1
        
        # Parse atomic positions
        atom_start = coord_line_index + 1
        for i in range(self.nat):
            if atom_start + i >= len(lines):
                raise ValueError(f"Not enough atomic positions. Expected {self.nat}, got {i}")
            
            line_parts = lines[atom_start + i].split()
            coords = []
            
            # Extract coordinates, ignoring Selective dynamics flags
            for part in line_parts:
                try:
                    coords.append(float(part))
                    if len(coords) == 3:
                        break
                except ValueError:
                    continue
            
            if len(coords) == 3:
                self.atpos[i] = coords
            else:
                # Fallback: use first three values
                try:
                    for j in range(3):
                        self.atpos[i, j] = float(line_parts[j])
                except (ValueError, IndexError):
                    raise ValueError(f"Invalid atomic position at line {atom_start + i + 1}")
        
        self.tidy_up()
    
    def _init_from_qe(self, filename):
        """Initialize from Quantum ESPRESSO input file"""
        with open(filename, 'r', encoding='utf-8') as fi:
            lines = fi.readlines()
        
        # Parse ibrav, nat, ntyp
        ibrav = parse_lines_system(filename, 'ibrav')
        nat = parse_lines_system(filename, 'nat')
        ntyp = parse_lines_system(filename, 'ntyp')
        
        if ibrav is None or nat is None or ntyp is None:
            raise ValueError("Missing required parameters in QE input")
        
        ibrav = int(ibrav)
        self.nat = int(nat)
        self.ntyp = int(ntyp)
        
        # Parse celldm or A parameter
        celldm = parse_lines_system(filename, 'celldm')
        A_param = parse_lines_system(filename, 'A')
        
        is_celldm = celldm is not None
        is_ABC = A_param is not None
        
        if is_celldm and is_ABC:
            raise ValueError("Both celldm and A specified")
        elif not is_celldm and not is_ABC and ibrav != 0:
            raise ValueError("Need celldm or A for ibrav != 0")
        
        # Initialize cell
        self.cell = np.zeros((3, 3))
        
        if ibrav == 0:
            # Free cell - read CELL_PARAMETERS
            cell_found = False
            for i, line in enumerate(lines):
                if 'CELL_PARAMETERS' in line:
                    # Determine units
                    if 'alat' in line.lower():
                        factor = float(celldm[0]) * BOHR2ANGS if is_celldm else float(A_param)
                    elif 'bohr' in line.lower():
                        factor = BOHR2ANGS
                    elif 'angstrom' in line.lower():
                        factor = 1.0
                    else:
                        factor = float(celldm[0]) * BOHR2ANGS if is_celldm else 1.0
                    
                    # Read cell vectors
                    for j in range(3):
                        if i + 1 + j < len(lines):
                            parts = lines[i + 1 + j].split()
                            if len(parts) >= 3:
                                self.cell[j] = [float(x) * factor for x in parts[:3]]
                    
                    cell_found = True
                    break
            
            if not cell_found:
                raise ValueError("CELL_PARAMETERS not found in QE input")
            
            if is_celldm:
                self.alat = float(celldm[0]) * BOHR2ANGS
            else:
                self.alat = float(A_param) if A_param else np.linalg.norm(self.cell[0])
        
        else:
            # Standard ibrav cases
            if is_celldm:
                a = float(celldm[0]) * BOHR2ANGS
                if ibrav == 1:  # Simple cubic
                    self.cell = a * np.eye(3)
                elif ibrav == 2:  # FCC
                    self.cell = a * 0.5 * np.array([[-1, 0, 1], [0, 1, 1], [-1, 1, 0]])
                elif ibrav == 3:  # BCC
                    self.cell = a * 0.5 * np.array([[1, 1, 1], [-1, 1, 1], [-1, -1, 1]])
                # Add more ibrav cases as needed
                else:
                    raise NotImplementedError(f"ibrav = {ibrav} not implemented")
                
                self.alat = a
            else:
                # Similar logic for ABC parameters
                a = float(A_param)
                if ibrav == 1:
                    self.cell = a * np.eye(3)
                elif ibrav == 2:
                    self.cell = a * 0.5 * np.array([[-1, 0, 1], [0, 1, 1], [-1, 1, 0]])
                else:
                    raise NotImplementedError(f"ibrav = {ibrav} with ABC not implemented")
                self.alat = a
        
        # Parse ATOMIC_SPECIES
        self.typ_name = []
        self.typ_num = np.zeros(self.ntyp, dtype=int)
        
        for i, line in enumerate(lines):
            if 'ATOMIC_SPECIES' in line:
                for j in range(self.ntyp):
                    if i + 1 + j < len(lines):
                        parts = lines[i + 1 + j].split()
                        if parts:
                            self.typ_name.append(parts[0])
                break
        
        # Parse ATOMIC_POSITIONS
        self.atpos = np.zeros((self.nat, 3))
        self.attyp = np.zeros(self.nat, dtype=int)
        atom_count = 0
        
        for i, line in enumerate(lines):
            if 'ATOMIC_POSITIONS' in line:
                # Determine format
                if 'crystal' in line.lower():
                    coord_type = 'crystal'
                elif 'angstrom' in line.lower():
                    coord_type = 'angstrom'
                elif 'bohr' in line.lower():
                    coord_type = 'bohr'
                elif 'alat' in line.lower():
                    coord_type = 'alat'
                else:
                    coord_type = 'crystal'  # default
                
                for j in range(self.nat):
                    if i + 1 + j < len(lines):
                        parts = lines[i + 1 + j].split()
                        if len(parts) >= 4:
                            element = parts[0]
                            coords = [float(x) for x in parts[1:4]]
                            
                            # Find element index
                            elem_idx = -1
                            for k, name in enumerate(self.typ_name):
                                if name == element:
                                    elem_idx = k
                                    break
                            
                            if elem_idx == -1:
                                raise ValueError(f"Unknown element: {element}")
                            
                            self.attyp[atom_count] = elem_idx
                            self.typ_num[elem_idx] += 1
                            
                            if coord_type == 'crystal':
                                self.atpos[atom_count] = coords
                            elif coord_type == 'angstrom':
                                self.atpos[atom_count] = self.cart2direct(coords)
                            elif coord_type == 'bohr':
                                self.atpos[atom_count] = self.cart2direct([x * BOHR2ANGS for x in coords])
                            elif coord_type == 'alat':
                                self.atpos[atom_count] = self.cart2direct([x * self.alat for x in coords])
                            
                            atom_count += 1
                break
        
        if atom_count != self.nat:
            raise ValueError(f"Expected {self.nat} atoms, found {atom_count}")
        
        self.system = "From QE input"
        self.coordsystem = "Direct"
        
        # Ensure right-hand system
        if mixproduct(self.cell[0], self.cell[1], self.cell[2]) < 0:
            # Fix by swapping axes
            self.cell = self.cell[[1, 0, 2]]  # swap x and y
            if mixproduct(self.cell[0], self.cell[1], self.cell[2]) < 0:
                self.cell = self.cell[[0, 2, 1]]  # swap y and z
        
        self.tidy_up()
    
    def get_volume(self):
        """Calculate cell volume"""
        self.volume = abs(mixproduct(self.cell[0], self.cell[1], self.cell[2]))
        return self.volume
    
    def get_rec(self):
        """Calculate reciprocal lattice vectors"""
        self.rec = np.zeros((3, 3))
        volume = self.get_volume()
        for i in range(3):
            self.rec[i] = np.cross(self.cell[(i + 1) % 3], self.cell[(i + 2) % 3]) / volume
        return self.rec
    
    def direct2cart(self, a):
        """Convert fractional to Cartesian coordinates"""
        return np.dot(a, self.cell)
    
    def cart2direct(self, a):
        """Convert Cartesian to fractional coordinates"""
        return np.dot(a, self.get_rec().T)
    
    def get_vac(self):
        """
        Calculate vacuum thickness in slab
        
        Returns:
        vacuum thickness in Angstroms
        """
        try:
            # For slabs, assume z is the vacuum direction
            if (abs(self.cell[2, 0]) < self.eps1 and 
                abs(self.cell[2, 1]) < self.eps1):
                # Orthogonal cell
                z_coords = self.atpos[:, 2]
                z_max = np.max(z_coords)
                z_min = np.min(z_coords)
                vacuum_frac = 1.0 - (z_max - z_min)
                return vacuum_frac * abs(self.cell[2, 2])
            else:
                # Non-orthogonal cell - estimate from atom distribution
                carts = np.array([self.direct2cart(pos) for pos in self.atpos])
                z_coords = carts[:, 2]
                z_max = np.max(z_coords)
                z_min = np.min(z_coords)
                cell_height = abs(self.cell[2, 2])
                return cell_height - (z_max - z_min)
        except:
            return 0.0
    
    def tidy_up(self):
        """Normalize atomic coordinates to [0, 1) and sort atoms"""
        for i in range(self.nat):
            for j in range(3):
                frac, integer = np.modf(self.atpos[i, j])
                if frac < -self.eps1:
                    self.atpos[i, j] = frac + 1.0
                elif abs(frac) <= self.eps1 or abs(frac - 1.0) <= self.eps1:
                    self.atpos[i, j] = 0.0
                else:
                    self.atpos[i, j] = frac
                
                # Ensure coordinates are in [0, 1)
                if self.atpos[i, j] < 0.0:
                    self.atpos[i, j] += 1.0
                elif self.atpos[i, j] >= 1.0:
                    self.atpos[i, j] -= 1.0
        
        self.at_sort()
    
    def at_sort(self):
        """Sort atoms by element type"""
        sort_idx = self.attyp.argsort(kind='stable')
        self.attyp = self.attyp[sort_idx]
        self.atpos = self.atpos[sort_idx]
    
    def unique(self):
        """Remove duplicate atoms"""
        # Simple uniqueness check based on fractional coordinates
        unique_mask = np.ones(self.nat, dtype=bool)
        
        for i in range(self.nat):
            if unique_mask[i]:
                for j in range(i + 1, self.nat):
                    if unique_mask[j] and np.allclose(self.atpos[i], self.atpos[j], atol=self.eps1):
                        unique_mask[j] = False
        
        self.atpos = self.atpos[unique_mask]
        self.attyp = self.attyp[unique_mask]
        self.nat = len(self.atpos)
        
        # Recalculate type counts
        self.typ_num = np.zeros(self.ntyp, dtype=int)
        for i in range(self.nat):
            self.typ_num[self.attyp[i]] += 1
    
    def print_poscar(self, filename):
        """Write structure to POSCAR file"""
        with open(filename, 'w') as f:
            f.write(f"{self.system}\n")
            f.write("1.0\n")
            for i in range(3):
                f.write(f"  {self.cell[i, 0]:15.10f} {self.cell[i, 1]:15.10f} {self.cell[i, 2]:15.10f}\n")
            
            f.write("  " + "  ".join(self.typ_name) + "\n")
            f.write("  " + "  ".join(map(str, self.typ_num)) + "\n")
            f.write("Direct\n")
            
            for i in range(self.nat):
                f.write(f"  {self.atpos[i, 0]:18.14f} {self.atpos[i, 1]:18.14f} {self.atpos[i, 2]:18.14f}\n")
    
    def print_pwinput(self, filename, aug_sys="", separation=0.04):
        """Write structure to Quantum ESPRESSO input file"""
        with open(filename, 'w') as f:
            # CONTROL namelist
            f.write("&CONTROL\n")
            f.write("  calculation='scf', pseudo_dir='./', outdir='./tmp'\n")
            f.write("  tprnfor=.true., tstress=.true., forc_conv_thr=1.0d-4\n")
            f.write("/\n")
            
            # SYSTEM namelist
            f.write("&SYSTEM\n")
            f.write(f"  ibrav=0, nat={self.nat}, ntyp={self.ntyp}\n")
            f.write("  occupations='smearing', smearing='gauss', degauss=1.0d-2\n")
            f.write("  ecutwfc=50, ecutrho=500\n")
            f.write("/\n")
            
            # ELECTRONS namelist
            f.write("&ELECTRONS\n")
            f.write("  conv_thr=1.0d-8\n")
            f.write("  mixing_beta=0.7d0\n")
            f.write("/\n")
            
            f.write("&IONS\n/\n")
            f.write("&CELL\n/\n")
            
            # ATOMIC_SPECIES
            f.write("ATOMIC_SPECIES\n")
            for i in range(self.ntyp):
                f.write(f"  {self.typ_name[i]} {get_atomic_weight(self.typ_name[i])} {self.typ_name[i]}.UPF\n")
            
            # CELL_PARAMETERS
            f.write("CELL_PARAMETERS angstrom\n")
            for i in range(3):
                f.write(f"  {self.cell[i, 0]:13.10f} {self.cell[i, 1]:13.10f} {self.cell[i, 2]:13.10f}\n")
            
            # ATOMIC_POSITIONS
            f.write("ATOMIC_POSITIONS crystal\n")
            for i in range(self.nat):
                f.write(f"  {self.typ_name[self.attyp[i]]} {self.atpos[i, 0]:13.10f} {self.atpos[i, 1]:13.10f} {self.atpos[i, 2]:13.10f}\n")
            
            # K_POINTS
            a_len = np.linalg.norm(self.cell[0])
            b_len = np.linalg.norm(self.cell[1]) 
            c_len = np.linalg.norm(self.cell[2])
            
            kx = max(1, int(1.0 / (a_len * separation) + 0.5))
            ky = max(1, int(1.0 / (b_len * separation) + 0.5))
            kz = max(1, int(1.0 / (c_len * separation) + 0.5))
            
            f.write("K_POINTS automatic\n")
            f.write(f"  {kx} {ky} {kz} 0 0 0\n")
    
    def add_vacuum(self, vacuum):
        """
        Add vacuum to slab structure
        
        Parameters:
        vacuum: vacuum thickness in Angstroms
        """
        # For slabs, assume cell is roughly orthogonal with z as vacuum direction
        z_coords = self.atpos[:, 2]
        z_max = np.max(z_coords)
        z_min = np.min(z_coords)
        
        old_height = abs(self.cell[2, 2])
        slab_height_frac = z_max - z_min
        slab_height_abs = slab_height_frac * old_height
        
        new_height = slab_height_abs + vacuum
        self.cell[2, 2] = np.sign(self.cell[2, 2]) * new_height
        
        # Adjust atomic coordinates
        for i in range(self.nat):
            self.atpos[i, 2] = (vacuum / 2.0 / new_height) + (
                (self.atpos[i, 2] - z_min) * slab_height_abs / new_height)
        
        self.tidy_up()
    
    def makeslab(self, miller_index, vacuum=15.0, layer=1, method="bf", origin_shift=0.0, length=-1.0):
        """
        Create slab from miller indices
        
        Parameters:
        miller_index: [h, k, l] Miller indices
        vacuum: vacuum thickness in Angstroms
        layer: number of layers
        method: method for slab creation
        origin_shift: shift of origin
        length: slab length (unused)
        
        Returns:
        CELL object representing the slab
        """
        # Simplified slab creation - in practice would use the full algorithm
        h, k, l = miller_index
        
        # Create transformation matrix for the slab
        if h == 0 and k == 0:
            # (001) surface
            P = np.mat([[1, 0, 0], [0, 1, 0], [0, 0, layer]], dtype=float)
        elif k == 0 and l == 0:
            # (100) surface  
            P = np.mat([[0, 0, layer], [1, 0, 0], [0, 1, 0]], dtype=float)
        elif h == 0 and l == 0:
            # (010) surface
            P = np.mat([[0, 1, 0], [0, 0, layer], [1, 0, 0]], dtype=float)
        else:
            # General surface - use Euclidean algorithm to find transformation
            p, q, _ = ext_euclid(k, l)
            
            # Find suitable transformation matrix
            k1 = np.dot(p * (k * self.cell[0] - h * self.cell[1]) + 
                        q * (l * self.cell[0] - h * self.cell[2]), 
                        l * self.cell[1] - k * self.cell[2])
            k2 = np.dot(l * (k * self.cell[0] - h * self.cell[1]) - 
                        k * (l * self.cell[0] - h * self.cell[2]), 
                        l * self.cell[1] - k * self.cell[2])
            
            if abs(k2) > self.eps1:
                i = -int(round(k1 / k2))
                p, q = p + i * l, q - i * k
            
            P = np.mat([
                [p * k + q * l, -p * h, -q * h],
                [0, l, -k],
                [h, k, l]
            ], dtype=float)
            P[2] *= layer  # Scale by number of layers
        
        # Ensure right-hand system
        if np.linalg.det(P) < 0:
            P[0, 2] *= -1
            P[1, 2] *= -1
            P[2, 2] *= -1
        
        # Create supercell
        slab = self.cell2supercell(P)
        
        # Redefine cell to have proper orientation
        slab.cell_redefine()
        
        # Add vacuum
        slab.add_vacuum(vacuum)
        
        return slab
    
    def cell2supercell(self, P):
        """
        Create supercell using transformation matrix P
        
        Parameters:
        P: 3x3 transformation matrix
        
        Returns:
        CELL object representing the supercell
        """
        from copy import deepcopy
        
        supercell = deepcopy(self)
        supercell.cell = np.array((np.mat(self.cell).T * P).T)
        
        # Check determinant
        if np.linalg.det(supercell.cell) <= 0:
            raise ValueError("Transformation results in non-positive volume")
        
        # Transform atomic positions
        Q = np.linalg.inv(P)
        for i in range(self.nat):
            supercell.atpos[i] = np.array(Q * (np.mat(self.atpos[i]).T)).flatten()
        
        # Find translation vectors in supercell coordinates
        trans = np.zeros((3, 3))
        for i in range(3):
            cell_i_frac = self.cart2direct(self.cell[i])
            trans[i] = np.array(Q * (np.mat(cell_i_frac).T)).flatten()
        
        # Find range of repetitions needed
        La, Ma, Na = 0, 0, 0
        Lb, Mb, Nb = 0, 0, 0
        
        # Simple approach: repeat in reasonable range
        ranges = 2  # Could be made smarter
        new_atoms = 0
        
        # Collect all atoms in supercell
        all_positions = []
        all_types = []
        
        for n in range(self.nat):
            for i in range(-ranges, ranges + 1):
                for j in range(-ranges, ranges + 1):
                    for k in range(-ranges, ranges + 1):
                        new_pos = supercell.atpos[n] + i * trans[0] + j * trans[1] + k * trans[2]
                        all_positions.append(new_pos)
                        all_types.append(supercell.attyp[n])
                        new_atoms += 1
        
        # Update supercell
        supercell.nat = new_atoms
        supercell.atpos = np.array(all_positions)
        supercell.attyp = np.array(all_types)
        
        # Recalculate type counts
        supercell.typ_num = np.zeros(supercell.ntyp, dtype=int)
        for i in range(supercell.nat):
            supercell.typ_num[supercell.attyp[i]] += 1
        
        supercell.tidy_up()
        supercell.unique()
        
        return supercell
    
    def cell_redefine(self):
        """
        Redefine cell to have x-axis parallel to surface and z perpendicular
        """
        a1, a2, a3 = self.cell
        
        # Convert to Cartesian for all atoms
        carts = np.array([self.direct2cart(pos) for pos in self.atpos])
        
        # Redefine cell: a1, a2 stay in plane, a3 becomes cross product
        n_vec = np.cross(a1, a2)
        self.cell = np.array([a1, a2, n_vec * np.dot(a3, n_vec) / np.dot(n_vec, n_vec)])
        
        # Convert back to fractional
        for i in range(self.nat):
            self.atpos[i] = self.cart2direct(carts[i])
        
        self.tidy_up()
        
        # Make cell orthogonal in xy plane
        a1, a2, a3 = self.cell
        new_a1 = np.array([np.linalg.norm(a1), 0, 0])
        new_a2 = np.array([np.dot(a1, a2) / np.linalg.norm(a1), 
                          np.sqrt(np.linalg.norm(a2)**2 - (np.dot(a1, a2) / np.linalg.norm(a1))**2), 0])
        new_a3 = np.array([0, 0, np.linalg.norm(a3)])
        
        self.cell = np.array([new_a1, new_a2, new_a3])
    
    def __str__(self):
        """String representation of cell"""
        return f"CELL: {self.nat} atoms, {self.ntyp} types\nCell:\n{self.cell}\n"

def CELL_auto(filename):
    """
    Auto-detect file format and create CELL object
    
    Parameters:
    filename: path to structure file
    
    Returns:
    CELL object
    """
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == '.cif':
        return CELL(filename, fmt='CIF')
    elif ext in ['.vasp', '.poscar']:
        return CELL(filename, fmt='POSCAR')
    elif ext in ['.in', '.txt']:
        return CELL(filename, fmt='QE')
    else:
        # Try to detect by content
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read(1000)
        
        if 'CELL_PARAMETERS' in content:
            return CELL(filename, fmt='QE')
        elif any(keyword in content for keyword in ['_cell_length', '_atom_site']):
            return CELL(filename, fmt='CIF')
        else:
            # Default to POSCAR
            return CELL(filename, fmt='POSCAR')

if __name__ == '__main__':
    # Test code
    print("SlabMaker CELL module")
    print("Formats: POSCAR, QE, CIF")