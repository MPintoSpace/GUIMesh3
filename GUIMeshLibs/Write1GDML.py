#########################################################################################################
#    GUIMesh v1                                                                                         #
#                                                                                                       #
#    Copyright (c) 2018  Marco Gui Alves Pinto mail:mgpinto11@gmail.com                                 #
#                                                                                                       #
#    This program is free software: you can redistribute it and/or modify                               #
#    it under the terms of the GNU General Public License as published by                               #
#    the Free Software Foundation, either version 3 of the License, or                                  #
#    (at your option) any later version.                                                                #
#                                                                                                       #
#    This program is distributed in the hope that it will be useful,                                    #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of                                     #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                                      #
#    GNU General Public License for more details.                                                       #
#                                                                                                       #
#    You should have received a copy of the GNU General Public License                                  #
#    along with this program.  If not, see <https://www.gnu.org/licenses/>                              #
#                                                                                                       #
#########################################################################################################

# Libraries
import os
# import GMaterials
from . import Volumes
from tkinter import filedialog as tkFileDialog
# from tkinter import simpledialog as tkSimpleDialog
from tkinter import messagebox as tkMessageBox
import datetime

# import tkFileDialog
# import tkMessageBox

MATERIALS_TEMPLATE = '''
<element name="Vacuum_el"  formula="Hv" Z="1">
    <atom value="1.008"/>
</element>

<material name="Vacuum_ref">
    <D value="0.0000000000000000000001" unit="mg/cm3"/>
    <fraction n="1.0" ref="Vacuum_el"/>
</material>
'''


def write_gdml_definition(write_dir):
    from distutils.dir_util import copy_tree
    from pathlib import Path
    if (os.path.isdir("GDMLSchema/") == True):
        to_dir = str(Path(write_dir, "GDMLSchema").resolve())
        if (os.path.isdir(to_dir) == False):
            os.makedirs(to_dir)
            from_dir = "GDMLSchema"
            copy_tree(from_dir, to_dir)
        return True
    return False


def get_triangles(shape, precision):
    opt_precision = precision
    triangles = shape.tessellate(opt_precision, True)
    if (triangles[1].__len__() > 10000):
        triangles2 = shape.tessellate(opt_precision*2, True)
        while(triangles[1].__len__() > triangles2[1].__len__() and triangles[1].__len__() > 10000):
            opt_precision = opt_precision*2
            triangles = triangles2
            triangles2 = shape.tessellate(opt_precision*2, True)
    return triangles, opt_precision

# Main function called to write all GDML files
def Write_Files(obj_list, world_list):
    print("GDML STARTED")
    write_dir = tkFileDialog.askdirectory()
    print(write_dir)
    gdml_local_definition = write_gdml_definition(write_dir)
    counter = 1
    define_list = ['<position name="center" x="0" y="0" z="0"/>\n', '<rotation name="identity" x="0" y="0" z="0"/>\n']
    solid_list = ['<box name="WorldBox" x="' + str(world_list[0]) + '" y="' + str(world_list[1]) + '" z="' + str(
        world_list[2]) + '" lunit="m"/>\n']
    logical_volume_list = []
    physical_volume_list = []
    material_list = []
    material_added = []
    gdml_name_list = []
    i = 0
    for obj in obj_list:
        i = i + 1
        if obj.VolumeGDMLoption == 1:
            # material list
            if obj.VolumeMaterial.Nelements != 0:
                if obj.VolumeMaterial.Name not in MATERIALS_TEMPLATE and obj.VolumeMaterial.Name not in material_added:
                    material = '<material name="' + str(
                        obj.VolumeMaterial.Name) + '">\n' + '<D unit="g/cm3" value="' + str(
                        obj.VolumeMaterial.Density) + '"/>\n'
                    for i in range(0, obj.VolumeMaterial.Nelements):
                        material += '<fraction n="' + str(obj.VolumeMaterial.ElementFractions[i]) + '" ref="' + str(
                            obj.VolumeMaterial.Elements[i]) + '"/>\n'
                    material += '</material>\n'
                    material_list.append(material)
                    material_added.append(obj.VolumeMaterial.Name)
            vol_numb = counter
            precision = obj.VolumeMMD
            # the number represents the precision of the tessellation #returns matrix with triangles vertices
            triangles = obj.VolumeCAD.Shape.tessellate(precision, True)
            count = 0
            gdml_name = str(obj.VolumeCAD.Label)  # + str(vol_numb)
            # if (len(triangles[0]) > 300):
            #     print(obj.VolumeCAD.Label)
            if gdml_name in gdml_name_list:
                print("\t " + gdml_name + " not unique")
                gdml_name = gdml_name + "_" + str(vol_numb)
                counter += 1
            gdml_name_list.append(gdml_name)
            # define
            for tri in triangles[0]:
                define_list.append(' <position name="' + gdml_name + '_v' + str(count) + '" unit="mm" x="' + str(
                    tri[0]) + '" y="' + str(tri[1]) + '" z="' + str(tri[2]) + '"/>\n')
                count = count + 1
            # tessellated
            count = 0
            triangle_list = []
            for tri in triangles[1]:
                triangle_list.append(
                    '<triangular vertex1="' + gdml_name + '_v' + str(tri[0]) + '" vertex2="' + gdml_name + '_v' + str(
                        tri[1]) + '" vertex3="' + gdml_name + '_v' + str(tri[2]) + '"/>\n')
                count += 3
            tessellated = '<tessellated aunit="deg" lunit="mm" name="' + gdml_name + '_solid">\n' + ''.join(
                triangle_list) + '</tessellated>\n'
            solid_list.append(tessellated)
            # logical volume
            material_ref = str(obj.VolumeMaterial.Name)
            logical_volume_list.append(
                '''<volume name="{gdml_name}_LV">\n<materialref ref="{material_ref}"/>\n<solidref ref="{gdml_name}_solid"/>\n</volume>\n'''.format_map(
                    locals()))
            # physical volume
            physical_volume_list.append(
                '''<physvol name="{gdml_name}_PV">\n<volumeref ref="{gdml_name}_LV"/>\n<positionref ref="center"/>\n<rotationref ref="identity"/>\n</physvol>\n'''.format_map(
                    locals()))
    F = open(str(write_dir) + "/unnamed.gdml", "w")
    F.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
    if gdml_local_definition:
        F.write(
            '<gdml xmlns:gdml="./GDMLSchema" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xsi:noNamespaceSchemaLocation="./GDMLSchema/gdml.xsd" >\n')
    else:
        F.write(
        '<gdml xmlns:gdml="http://www.lcsim.org/schemas/gdml/1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://service-spi.web.cern.ch/service-spi/app/releases/GDML/schema/gdml.xsd" >\n')
    F.write('<define>\n')
    for d in define_list:
        F.write(d)
    F.write('</define>\n')
    # write material information
    F.write('<materials>\n')
    F.write(MATERIALS_TEMPLATE)
    for m in material_list:
        F.write(m)
    F.write('</materials>\n')
    # write solid information (world volume)
    F.write('<solids>\n')
    for s in solid_list:
        F.write(s)
    F.write('</solids>\n')
    # write structure
    F.write('<structure>\n')
    for lv in logical_volume_list:
        F.write(lv)
    F.write('<volume name="World">\n')
    F.write('<materialref ref="Vacuum_ref"/>\n')
    F.write('<solidref ref="WorldBox"/>\n')
    for pv in physical_volume_list:
        F.write(pv)
    F.write('</volume>\n')
    F.write('</structure>\n')
    F.write('<setup name="Default" version="1.0">\n')
    F.write('<world ref="World"/>\n')
    F.write('</setup>\n')
    F.write('</gdml>')
    F.close()
    print("GDML FINISHED")
    tkMessageBox.showinfo("Message", 'GDML Files ready.')
# Note: A number is added to each volumes label to avoid that two different volumes have the same name. This can be seen in the mother and in the volumes GDMLs
