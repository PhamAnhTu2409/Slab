#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import re

class CIFParser:
    """Parser for CIF files"""
    def __init__(self):
        self.eps = 1e-8
    
    def parse_cif(self, filename):
        """Parse CIF file and return structure information"""
        try:
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            content = re.sub(r'\\n', '\n', content)
            content = re.sub(r"''", '"', content)
            
            result = {
                'lattice_parameters': self._parse_lattice_parameters(content),
                'atoms': self._parse_atom_sites(content),
                'symmetry': self._parse_symmetry(content),
                'chemical_name': self._parse_chemical_name(content)
            }
            
            return result
        except Exception as e:
            raise ValueError(f"CIF parsing error: {str(e)}")
    
    def _parse_lattice_parameters(self, content):
        """Parse lattice parameters"""
        params = {}
        
        lattice_keys = {
            'a': ['_cell_length_a', '_cell_parameter_a'],
            'b': ['_cell_length_b', '_cell_parameter_b'],
            'c': ['_cell_length_c', '_cell_parameter_c'],
            'alpha': ['_cell_angle_alpha'],
            'beta': ['_cell_angle_beta'],
            'gamma': ['_cell_angle_gamma']
        }
        
        for param, keys in lattice_keys.items():
            for key in keys:
                value = self._extract_value(content, key)
                if value is not None:
                    value = re.sub(r'[\(\).]', '', str(value))
                    try:
                        params[param] = float(value)
                        break
                    except ValueError:
                        continue
        
        defaults = {'a': 1.0, 'b': 1.0, 'c': 1.0, 'alpha': 90.0, 'beta': 90.0, 'gamma': 90.0}
        for key, default in defaults.items():
            if key not in params:
                params[key] = default
        
        return params
    
    def _parse_atom_sites(self, content):
        """Parse atom sites"""
        atoms = []
        
        # Try to find loop with atomic positions
        loop_pattern = r'loop_(\s+_atom_site[^\n]*)+\s+((?:\s*[^\s]+\s+[-\.\d]+\s+[-\.\d]+\s+[-\.\d]+.*\n?)+)'
        matches = re.findall(loop_pattern, content, re.IGNORECASE | re.MULTILINE)
        
        if matches:
            for match in matches:
                header, data_block = match
                lines = data_block.strip().split('\n')
                
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        atom = {}
                        
                        headers = header.lower().split()
                        if '_atom_site_type_symbol' in headers:
                            symbol_idx = headers.index('_atom_site_type_symbol')
                            atom['element'] = parts[symbol_idx]
                        elif '_atom_site_label' in headers:
                            label_idx = headers.index('_atom_site_label')
                            atom['element'] = re.sub(r'[\d\.]', '', parts[label_idx])
                        else:
                            atom['element'] = parts[0]
                        
                        coord_keys = ['_atom_site_fract_x', '_atom_site_fract_y', '_atom_site_fract_z']
                        coords = []
                        for key in coord_keys:
                            if key in headers:
                                idx = headers.index(key)
                                try:
                                    coord_val = re.sub(r'[\(\).]', '', parts[idx])
                                    coords.append(float(coord_val))
                                except (ValueError, IndexError):
                                    coords.append(0.0)
                        
                        if len(coords) == 3:
                            atom['position'] = coords
                            atoms.append(atom)
        
        # Fallback: simple parsing
        if not atoms:
            lines = content.split('\n')
            in_atom_section = False
            
            for line in lines:
                if line.strip().startswith('_atom_site'):
                    in_atom_section = True
                    continue
                if in_atom_section and line.strip() and not line.strip().startswith('_'):
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            atom = {
                                'element': re.sub(r'[\d\.]', '', parts[0]),
                                'position': [
                                    float(re.sub(r'[\(\).]', '', parts[1])),
                                    float(re.sub(r'[\(\).]', '', parts[2])),
                                    float(re.sub(r'[\(\).]', '', parts[3]))
                                ]
                            }
                            atoms.append(atom)
                        except ValueError:
                            continue
        
        return atoms
    
    def _parse_symmetry(self, content):
        """Parse symmetry information"""
        symmetry = {}
        
        sg_patterns = [
            r'_space_group_name_H-M_alt\s+[\'"]([^\'"]+)[\'"]',
            r'_space_group_name_H-M\s+[\'"]([^\'"]+)[\'"]',
            r'_symmetry_space_group_name_H-M\s+[\'"]([^\'"]+)[\'"]'
        ]
        
        for pattern in sg_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                symmetry['space_group'] = match.group(1)
                break
        
        return symmetry
    
    def _parse_chemical_name(self, content):
        """Parse chemical name"""
        name_patterns = [
            r'_chemical_name_systematic\s+[\'"]([^\'"]+)[\'"]',
            r'_chemical_name_common\s+[\'"]([^\'"]+)[\'"]',
            r'_chemical_formula_structural\s+[\'"]([^\'"]+)[\'"]'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "From CIF file"
    
    def _extract_value(self, content, key):
        """Extract value for key from CIF content"""
        pattern = rf'{key}\s+([^\n]+)'
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            value = re.split(r'[#!]', value)[0].strip()
            value = re.sub(r'[\'"]', '', value)
            return value
        return None
    
    def lattice_parameters_to_vectors(self, a, b, c, alpha, beta, gamma):
        """Convert lattice parameters to cell vectors"""
        alpha_rad = np.radians(alpha)
        beta_rad = np.radians(beta)
        gamma_rad = np.radians(gamma)
        
        cell = np.zeros((3, 3))
        
        cell[0, 0] = a
        cell[1, 0] = b * np.cos(gamma_rad)
        cell[1, 1] = b * np.sin(gamma_rad)
        cell[2, 0] = c * np.cos(beta_rad)
        cell[2, 1] = c * (np.cos(alpha_rad) - np.cos(beta_rad) * np.cos(gamma_rad)) / np.sin(gamma_rad)
        cell[2, 2] = np.sqrt(c**2 - cell[2, 0]**2 - cell[2, 1]**2)
        
        return cell