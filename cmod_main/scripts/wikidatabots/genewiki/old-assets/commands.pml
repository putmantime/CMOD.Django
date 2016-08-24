# PyMOL batch commands to prep and render a PDB file
# for ProteinBoxBot

hide everything, all
show cartoon, all
util.chainbow !resn da+dt+dg+dc+du+hetatm
set opaque_background=0
set show_alpha_checker=1
set cartoon_transparency=0
set depth_cue=0
set ray_trace_fog=0
orient
ray 1200,1000
