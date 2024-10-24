def create_projectile_file1(projectile, element, mass, energy, output_file):
    with open(output_file, 'w') as f:
        f.write("#\n")
        f.write(f"#  {projectile}-{element}\n")
        f.write("#\n")
        f.write("# General\n")
        f.write("#\n")
        f.write(f"projectile {projectile}\n")
        f.write(f"element {element}\n")
        f.write(f"mass {mass}\n")
        f.write(f"energy {energy}\n")
        f.write("#\n")
        f.write("# Parameters\n")
        f.write("#\n")
        f.write("ldmodel 1\n")
        f.write("colenhance n\n")
        f.write("rwdadjust p 1.01064\n")
        f.write("awdadjust p 0.90536\n")
        f.write("rvadjust n 1.07278\n")
        f.write("gadjust 7 14 0.93711\n")
        f.write("gadjust 7 13 0.99164\n")
        f.write("gadjust 6 13 0.35753\n")
        

def create_projectile_file2(projectile, element, mass, energy, output_file):
    with open(output_file, 'w') as f:
        f.write("#\n")
        f.write(f"#  {projectile}-{element}\n")
        f.write("#\n")
        f.write("# General\n")
        f.write("#\n")
        f.write(f"projectile {projectile}\n")
        f.write(f"element {element}\n")
        f.write(f"mass {mass}\n")
        f.write(f"energy {energy}\n")
        f.write("#\n")
        f.write("# Parameters\n")
        f.write("#\n")
        f.write("ldmodel 1\n")
        f.write("colenhance y\n")
        f.write("rwdadjust p 0.96542\n")
        f.write("awdadjust p 0.98631\n")
        f.write("rvadjust n 1.03316\n")
        f.write("gadjust 7 14 0.79573\n")
        f.write("gadjust 7 13 0.87446\n")
        f.write("gadjust 6 13 0.87431\n")

def create_projectile_file3(projectile, element, mass, energy, output_file):
    with open(output_file, 'w') as f:
        f.write("#\n")
        f.write(f"#  {projectile}-{element}\n")
        f.write("#\n")
        f.write("# General\n")
        f.write("#\n")
        f.write(f"projectile {projectile}\n")
        f.write(f"element {element}\n")
        f.write(f"mass {mass}\n")
        f.write(f"energy {energy}\n")
        f.write("#\n")
        f.write("# Parameters\n")
        f.write("#\n")
        f.write("ldmodel 2\n")
        f.write("colenhance n\n")
        f.write("rwdadjust p 0.92096\n")
        f.write("awdadjust p 0.98631\n")
        f.write("rvadjust n 1.02386\n")
        f.write("gadjust 7 14 0.56371\n")
        f.write("gadjust 7 13 0.59914\n")
        f.write("gadjust 6 13 0.91254\n")

def create_projectile_file4(projectile, element, mass, energy, output_file):
    with open(output_file, 'w') as f:
        f.write("#\n")
        f.write(f"#  {projectile}-{element}\n")
        f.write("#\n")
        f.write("# General\n")
        f.write("#\n")
        f.write(f"projectile {projectile}\n")
        f.write(f"element {element}\n")
        f.write(f"mass {mass}\n")
        f.write(f"energy {energy}\n")
        f.write("#\n")
        f.write("# Parameters\n")
        f.write("#\n")
        f.write("ldmodel 2\n")
        f.write("colenhance y\n")
        f.write("rwdadjust p 1.01064\n")
        f.write("awdadjust p 0.91759\n")
        f.write("rvadjust n 1.04943\n")
        f.write("gadjust 7 14 0.66501\n")
        f.write("gadjust 7 13 0.52107\n")
        f.write("gadjust 6 13 0.85869\n")

def create_projectile_file5(projectile, element, mass, energy, output_file):
    with open(output_file, 'w') as f:
        f.write("#\n")
        f.write(f"#  {projectile}-{element}\n")
        f.write("#\n")
        f.write("# General\n")
        f.write("#\n")
        f.write(f"projectile {projectile}\n")
        f.write(f"element {element}\n")
        f.write(f"mass {mass}\n")
        f.write(f"energy {energy}\n")
        f.write("#\n")
        f.write("# Parameters\n")
        f.write("#\n")
        f.write("ldmodel 5\n")
        f.write("colenhance n\n")
        f.write("rwdadjust p 0.84125\n")
        f.write("awdadjust p 0.49658\n")
        f.write("rvadjust n 1.20762\n")
        f.write("gadjust 7 14 0.84252\n")
        f.write("gadjust 7 13 1.98420\n")
        f.write("gadjust 6 13 1.04279\n")